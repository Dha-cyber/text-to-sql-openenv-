from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class SQLObservation(BaseModel):
    task_id: str
    task_name: str
    description: str
    schema_ddl: str
    question: str
    sample_rows: str
    expected_columns: List[str]
    step: int
    max_steps: int
    previous_attempts: List[Dict[str, Any]]
    last_error: Optional[str] = None
    hints: List[str] = []


class SQLAction(BaseModel):
    sql_query: str
    reasoning: Optional[str] = None


class StepResponse(BaseModel):
    observation: SQLObservation
    reward: float
    done: bool
    info: Dict[str, Any]


class ResetRequest(BaseModel):
    task_id: Optional[str] = None


class ResetResponse(BaseModel):
    observation: SQLObservation
    done: bool


class StateResponse(BaseModel):
    session_id: str
    task_id: str
    step: int
    total_reward: float
    done: bool
    observation: SQLObservation
