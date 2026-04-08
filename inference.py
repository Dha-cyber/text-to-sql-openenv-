"""
Inference script for Text-to-SQL OpenEnv.
Runs all 3 tasks and emits [START] / [STEP] / [END] logs.
"""

from __future__ import annotations
import asyncio
import os
import textwrap
from typing import List, Optional

from openai import OpenAI

from sql_env_client import SQLEnvClient
from app.models import SQLAction

# ── config ───────────────────────────────────────────────────────────────
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
HF_TOKEN = os.getenv("HF_TOKEN", "")
SERVER_URL = os.getenv("SERVER_URL", "http://localhost:7860")
IMAGE_NAME = os.getenv("LOCAL_IMAGE_NAME", "")

BENCHMARK = "text-to-sql-env"
MAX_STEPS = 5
TEMPERATURE = 0.2  # low temp for SQL generation
MAX_TOKENS = 512

TASK_IDS = ["employee-filter", "sales-by-region", "churn-analysis"]

# ── logging ───────────────────────────────────────────────────────────────


def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(
    step: int, action: str, reward: float, done: bool, error: Optional[str]
) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    action_clean = action.replace("\n", " ")[:120]
    print(
        f"[STEP] step={step} action={action_clean} reward={reward:.2f} done={done_val} error={error_val}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(
        f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}",
        flush=True,
    )


# ── prompting ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = textwrap.dedent(
    """
    You are an expert SQL developer. Your task is to write a single, correct SQLite query
    that answers the given business question based on the provided schema.

    Rules:
    - Output ONLY the raw SQL query, no markdown, no backticks, no explanation.
    - Use only tables and columns from the schema.
    - SQLite syntax only (use strftime for date functions, julianday for date arithmetic).
    - If a previous attempt failed, learn from the feedback and fix the error.
"""
).strip()


def build_prompt(obs) -> str:
    attempts_text = ""
    if obs.previous_attempts:
        lines = []
        for a in obs.previous_attempts[-2:]:
            lines.append(f"  Attempt {a['step']}: {a['query']}")
            lines.append(f"  Feedback: {a['feedback']}")
        attempts_text = "\nPrevious attempts:\n" + "\n".join(lines)

    hint_text = ""
    if obs.hints:
        hint_text = "\nHints:\n" + "\n".join(f"  - {h}" for h in obs.hints)

    return textwrap.dedent(
        f"""
        Schema:
        {obs.schema_ddl}

        Sample data:
        {obs.sample_rows}

        Question:
        {obs.question}

        Expected output columns: {', '.join(obs.expected_columns)}
        {attempts_text}
        {hint_text}

        Write the SQL query:
    """
    ).strip()


def get_sql(client: OpenAI, obs) -> str:
    try:
        resp = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_prompt(obs)},
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
        )
        sql = (resp.choices[0].message.content or "").strip()
        # Strip accidental markdown fences
        if sql.startswith("```"):
            sql = sql.split("```")[1]
            if sql.lower().startswith("sql"):
                sql = sql[3:]
        return sql.strip() or "SELECT 1"
    except Exception as exc:
        print(f"[DEBUG] LLM error: {exc}", flush=True)
        return "SELECT 1"


# ── single episode ────────────────────────────────────────────────────────


async def run_task(client: OpenAI, task_id: str, server_url: str) -> float:
    env = await SQLEnvClient.from_url(server_url, task_id=task_id)

    rewards: List[float] = []
    steps_taken = 0
    score = 0.0
    success = False

    log_start(task=task_id, env=BENCHMARK, model=MODEL_NAME)

    try:
        result = await env.reset()
        obs = result.observation

        for step in range(1, MAX_STEPS + 1):
            if result.done:
                break

            sql_query = get_sql(client, obs)
            result = await env.step(SQLAction(sql_query=sql_query))

            reward = result.reward or 0.0
            done = result.done
            error = result.info.get("feedback") if reward < 0.35 else None

            rewards.append(reward)
            steps_taken = step
            obs = result.observation

            log_step(step=step, action=sql_query, reward=reward, done=done, error=error)

            if done:
                break

        # Final score = best single-attempt raw score (not penalised sum)
        best_raw = max((a["score"] for a in obs.previous_attempts), default=0.0)
        score = min(max(best_raw, 0.0), 1.0)
        success = score >= 0.75

    finally:
        await env.close()
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)

    return score


# ── main ──────────────────────────────────────────────────────────────────


async def main() -> None:
    api_key = HF_TOKEN or "no-key"
    client = OpenAI(base_url=API_BASE_URL, api_key=api_key)

    scores = []
    for task_id in TASK_IDS:
        s = await run_task(client, task_id, SERVER_URL)
        scores.append(s)

    print(f"\n=== Final scores ===", flush=True)
    for task_id, s in zip(TASK_IDS, scores):
        print(f"  {task_id}: {s:.3f}", flush=True)
    print(f"  Average: {sum(scores)/len(scores):.3f}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
