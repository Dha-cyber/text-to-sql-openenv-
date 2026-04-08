"""
Core environment state machine.
One SQLiteConnection per session is kept in memory.
"""

from __future__ import annotations
import sqlite3
import uuid
from typing import Any, Dict, Optional, Tuple

from .models import SQLAction, SQLObservation, StepResponse, ResetResponse
from .tasks import get_task, TASKS
from .graders import grade_attempt


class SQLEnv:
    def __init__(self, task_id: str = "employee-filter"):
        self.session_id: str = str(uuid.uuid4())
        self.task_id: str = task_id
        self._task: Dict[str, Any] = get_task(task_id)
        self._conn: Optional[sqlite3.Connection] = None
        self._step: int = 0
        self._total_reward: float = 0.0
        self._done: bool = False
        self._attempts: list = []
        self._last_obs: Optional[SQLObservation] = None

    # ── helpers ──────────────────────────────────────────────────────────

    def _build_db(self) -> sqlite3.Connection:
        """Create fresh in-memory SQLite DB and seed it."""
        conn = sqlite3.connect(":memory:")
        conn.execute("PRAGMA journal_mode=WAL")
        for stmt in self._task["schema_ddl"].split(";"):
            stmt = stmt.strip()
            if stmt:
                conn.execute(stmt)
        for table, rows in self._task["seed_data"].items():
            if rows:
                placeholders = ",".join("?" * len(rows[0]))
                conn.executemany(f"INSERT INTO {table} VALUES ({placeholders})", rows)
        conn.commit()
        return conn

    def _build_obs(self, last_error: Optional[str] = None) -> SQLObservation:
        return SQLObservation(
            task_id=self._task["id"],
            task_name=self._task["name"],
            description=self._task["description"],
            schema_ddl=self._task["schema_ddl"],
            question=self._task["question"],
            sample_rows=self._task["sample_display"],
            expected_columns=self._task["expected_columns"],
            step=self._step,
            max_steps=self._task["max_steps"],
            previous_attempts=self._attempts[-3:],  # last 3 attempts in context
            last_error=last_error,
            hints=self._task["hints"],
        )

    # ── public API ───────────────────────────────────────────────────────

    def reset(self) -> ResetResponse:
        if self._conn:
            self._conn.close()
        self._conn = self._build_db()
        self._step = 0
        self._total_reward = 0.0
        self._done = False
        self._attempts = []
        obs = self._build_obs()
        self._last_obs = obs
        return ResetResponse(observation=obs, done=False)

    def step(self, action: SQLAction) -> StepResponse:
        if self._done:
            return StepResponse(
                observation=self._last_obs,
                reward=0.0,
                done=True,
                info={"message": "Episode already finished. Call reset()."},
            )

        self._step += 1
        max_steps = self._task["max_steps"]

        score, breakdown, feedback = grade_attempt(
            sql_query=action.sql_query,
            conn=self._conn,
            expected_columns=self._task["expected_columns"],
            expected_rows=self._task["expected_rows"],
        )

        # Efficiency penalty: -0.02 per extra step beyond step 1
        penalty = 0.02 * max(0, self._step - 1)
        reward = max(0.0, round(score - penalty, 4))

        self._total_reward += reward
        self._attempts.append(
            {
                "step": self._step,
                "query": action.sql_query[:200],
                "score": score,
                "reward": reward,
                "feedback": feedback,
            }
        )

        # Episode ends when: perfect score OR max steps reached
        perfect = breakdown.get("correct_data", 0.0) == 0.25
        done = perfect or self._step >= max_steps
        self._done = done

        last_error = None if score > 0.30 else feedback
        obs = self._build_obs(last_error=last_error)
        self._last_obs = obs

        return StepResponse(
            observation=obs,
            reward=reward,
            done=done,
            info={
                "score_raw": score,
                "breakdown": breakdown,
                "feedback": feedback,
                "step": self._step,
                "total_reward": self._total_reward,
            },
        )

    def state(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "task_id": self.task_id,
            "step": self._step,
            "total_reward": self._total_reward,
            "done": self._done,
            "observation": self._last_obs.dict() if self._last_obs else None,
        }

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None
