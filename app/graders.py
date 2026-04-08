"""
Deterministic graders. Each returns a float in [0.0, 1.0].

Scoring breakdown per task attempt:
  0.10  — query is non-empty
  0.20  — query parses without sqlite3 error (syntax valid)
  0.25  — query executes against the live DB without runtime error
  0.20  — returned column names match expected (order-insensitive)
  0.25  — returned data rows match expected (set comparison, values normalised)
"""

from __future__ import annotations
import sqlite3
from typing import Any, Dict, List, Optional, Tuple


def _normalize_value(v: Any) -> Any:
    """Round floats to 2 dp so 2093.0 == 2093.00."""
    if isinstance(v, float):
        return round(v, 2)
    return v


def _normalize_row(row: Tuple) -> Tuple:
    return tuple(_normalize_value(v) for v in row)


def grade_attempt(
    sql_query: str,
    conn: sqlite3.Connection,
    expected_columns: List[str],
    expected_rows: List[Tuple],
) -> Tuple[float, Dict[str, float], str]:
    """
    Returns (total_score, breakdown_dict, feedback_str).
    """
    breakdown: Dict[str, float] = {
        "non_empty": 0.0,
        "syntax_valid": 0.0,
        "executes": 0.0,
        "correct_columns": 0.0,
        "correct_data": 0.0,
    }
    feedback_parts: List[str] = []

    # ── non-empty ────────────────────────────────
    if not sql_query or not sql_query.strip():
        return 0.0, breakdown, "Empty query submitted."
    breakdown["non_empty"] = 0.10
    feedback_parts.append("Query received.")

    # ── syntax / parse check ─────────────────────
    try:
        conn.execute(f"EXPLAIN {sql_query.strip()}")
        breakdown["syntax_valid"] = 0.20
        feedback_parts.append("Syntax OK.")
    except sqlite3.Error as exc:
        feedback_parts.append(f"Syntax error: {exc}")
        total = sum(breakdown.values())
        return total, breakdown, " | ".join(feedback_parts)

    # ── execution ────────────────────────────────
    try:
        cursor = conn.execute(sql_query.strip())
        rows = cursor.fetchall()
        col_names = (
            [d[0].lower() for d in cursor.description] if cursor.description else []
        )
        breakdown["executes"] = 0.25
        feedback_parts.append(f"Executed, returned {len(rows)} rows.")
    except sqlite3.Error as exc:
        feedback_parts.append(f"Runtime error: {exc}")
        total = sum(breakdown.values())
        return total, breakdown, " | ".join(feedback_parts)

    # ── column names ─────────────────────────────
    expected_cols_lower = [c.lower() for c in expected_columns]
    # Allow extra columns; we care that ALL expected columns are present
    if all(ec in col_names for ec in expected_cols_lower):
        breakdown["correct_columns"] = 0.20
        feedback_parts.append("Column names match.")
    else:
        missing = [c for c in expected_cols_lower if c not in col_names]
        feedback_parts.append(f"Missing columns: {missing}.")

    # ── data correctness ─────────────────────────
    # Re-index result to expected column order
    try:
        idx = [col_names.index(c) for c in expected_cols_lower]
        result_set = set(_normalize_row(tuple(row[i] for i in idx)) for row in rows)
        expected_set = set(_normalize_row(r) for r in expected_rows)

        if result_set == expected_set:
            breakdown["correct_data"] = 0.25
            feedback_parts.append("Data is correct!")
        else:
            missing_rows = expected_set - result_set
            extra_rows = result_set - expected_set
            parts = []
            if missing_rows:
                parts.append(f"Missing rows: {list(missing_rows)[:2]}")
            if extra_rows:
                parts.append(f"Extra rows: {list(extra_rows)[:2]}")
            feedback_parts.append(" | ".join(parts))
    except (ValueError, IndexError):
        feedback_parts.append("Could not map result columns to expected.")

    total = sum(breakdown.values())
    return round(total, 4), breakdown, " | ".join(feedback_parts)
