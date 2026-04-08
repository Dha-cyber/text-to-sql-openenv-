"""
FastAPI server — exposes OpenEnv-compliant REST API.
"""

from __future__ import annotations
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .environment import SQLEnv
from .models import ResetRequest, SQLAction, StepResponse, ResetResponse, StateResponse
from .tasks import list_tasks

app = FastAPI(
    title="Text-to-SQL OpenEnv",
    description="An environment for training and evaluating SQL query generation agents.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── singleton session (single-agent evaluation pattern) ──────────────────
_env: Optional[SQLEnv] = None


def _get_env() -> SQLEnv:
    global _env
    if _env is None:
        _env = SQLEnv()
    return _env


# ── endpoints ────────────────────────────────────────────────────────────


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/tasks")
def tasks():
    return {"tasks": list_tasks()}


@app.post("/reset", response_model=ResetResponse)
def reset(body: ResetRequest = ResetRequest()):
    global _env
    task_id = body.task_id or "employee-filter"
    _env = SQLEnv(task_id=task_id)
    result = _env.reset()
    return result


class StepRequest(BaseModel):
    action: Dict[str, Any]


@app.post("/step", response_model=StepResponse)
def step(body: StepRequest):
    env = _get_env()
    try:
        action = SQLAction(**body.action)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return env.step(action)


@app.get("/state", response_model=StateResponse)
def state():
    env = _get_env()
    s = env.state()
    if s["observation"] is None:
        raise HTTPException(status_code=400, detail="Call /reset first.")
    from .models import SQLObservation

    return StateResponse(
        session_id=s["session_id"],
        task_id=s["task_id"],
        step=s["step"],
        total_reward=s["total_reward"],
        done=s["done"],
        observation=SQLObservation(**s["observation"]),
    )
