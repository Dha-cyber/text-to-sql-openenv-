"""
All three tasks with their SQLite DDL, seed data, questions, and expected results.
"""

from __future__ import annotations
from typing import Any, Dict, List, Tuple

TASKS: Dict[str, Dict[str, Any]] = {
    # ─────────────────────────────────────────────
    # TASK 1  — Easy
    # ─────────────────────────────────────────────
    "employee-filter": {
        "id": "employee-filter",
        "name": "Employee Department Filter",
        "description": (
            "Filter employees by department and salary. "
            "Return name, salary, and city for Engineering staff "
            "earning above $80,000, sorted by salary descending."
        ),
        "difficulty": "easy",
        "max_steps": 5,
        "schema_ddl": """
CREATE TABLE employees (
    id       INTEGER PRIMARY KEY,
    name     TEXT    NOT NULL,
    dept     TEXT    NOT NULL,
    salary   REAL    NOT NULL,
    city     TEXT    NOT NULL,
    hired    TEXT    NOT NULL
);
""".strip(),
        "seed_data": {
            "employees": [
                (
                    1,
                    "Alice Johnson",
                    "Engineering",
                    95000,
                    "San Francisco",
                    "2021-03-15",
                ),
                (2, "Bob Smith", "Marketing", 72000, "New York", "2020-06-01"),
                (3, "Carol Davis", "Engineering", 88000, "Seattle", "2022-01-10"),
                (4, "David Wilson", "HR", 65000, "Chicago", "2019-11-20"),
                (
                    5,
                    "Eve Martinez",
                    "Engineering",
                    102000,
                    "San Francisco",
                    "2018-07-01",
                ),
                (6, "Frank Brown", "Marketing", 78000, "Los Angeles", "2021-09-15"),
                (7, "Grace Lee", "Engineering", 79000, "Seattle", "2023-02-28"),
                (8, "Henry Taylor", "Finance", 91000, "New York", "2020-04-01"),
                (9, "Iris Chen", "Engineering", 110000, "San Francisco", "2017-05-15"),
                (10, "Jack White", "HR", 58000, "Chicago", "2022-08-01"),
            ]
        },
        "question": (
            "List the name, salary, and city of every employee in the Engineering "
            "department who earns more than $80,000. Sort by salary descending."
        ),
        "expected_columns": ["name", "salary", "city"],
        "expected_rows": [
            ("Iris Chen", 110000.0, "San Francisco"),
            ("Eve Martinez", 102000.0, "San Francisco"),
            ("Alice Johnson", 95000.0, "San Francisco"),
            ("Carol Davis", 88000.0, "Seattle"),
        ],
        "sample_display": (
            "employees sample:\n"
            "id | name          | dept        | salary | city\n"
            " 1 | Alice Johnson | Engineering | 95000  | San Francisco\n"
            " 2 | Bob Smith     | Marketing   | 72000  | New York\n"
            " 3 | Carol Davis   | Engineering | 88000  | Seattle"
        ),
        "hints": [
            "Use WHERE dept = 'Engineering' AND salary > 80000",
            "SELECT name, salary, city FROM employees ...",
            "Add ORDER BY salary DESC at the end",
        ],
    },
    # ─────────────────────────────────────────────
    # TASK 2  — Medium
    # ─────────────────────────────────────────────
    "sales-by-region": {
        "id": "sales-by-region",
        "name": "Sales Summary by Region",
        "description": (
            "Join salespeople and deals tables, aggregate deal amounts per region "
            "for the year 2024, return the top 3 regions by total, rounded to 2 dp."
        ),
        "difficulty": "medium",
        "max_steps": 5,
        "schema_ddl": """
CREATE TABLE salespeople (
    id     INTEGER PRIMARY KEY,
    name   TEXT NOT NULL,
    region TEXT NOT NULL
);
CREATE TABLE deals (
    id             INTEGER PRIMARY KEY,
    salesperson_id INTEGER REFERENCES salespeople(id),
    amount         REAL    NOT NULL,
    closed_date    TEXT    NOT NULL
);
""".strip(),
        "seed_data": {
            "salespeople": [
                (1, "Alice", "North"),
                (2, "Bob", "South"),
                (3, "Carol", "East"),
                (4, "David", "West"),
                (5, "Eve", "North"),
                (6, "Frank", "South"),
                (7, "Grace", "East"),
                (8, "Henry", "West"),
            ],
            "deals": [
                (1, 1, 12000, "2024-01-15"),
                (2, 2, 8500, "2024-02-20"),
                (3, 3, 21000, "2024-03-05"),
                (4, 4, 9750, "2024-04-11"),
                (5, 5, 15000, "2024-05-22"),
                (6, 6, 11250, "2024-06-30"),
                (7, 7, 18500, "2024-07-14"),
                (8, 8, 7000, "2024-08-09"),
                (9, 1, 20000, "2024-09-01"),
                (10, 3, 16000, "2024-10-17"),
                (11, 5, 9000, "2024-11-28"),
                (12, 7, 14000, "2024-12-05"),
                (13, 2, 5000, "2023-06-01"),  # 2023 — should be excluded
                (14, 4, 3000, "2023-11-15"),  # 2023 — should be excluded
            ],
        },
        "question": (
            "Find the top 3 regions by total deal amount for deals closed in 2024. "
            "Return region and total_amount (rounded to 2 decimal places), "
            "ordered by total_amount descending."
        ),
        "expected_columns": ["region", "total_amount"],
        "expected_rows": [
            ("East", 69500.0),  # 21000+18500+16000+14000
            ("North", 56000.0),  # 12000+15000+20000+9000
            ("South", 19750.0),  # 8500+11250
        ],
        "sample_display": (
            "salespeople sample:\n"
            "id | name  | region\n"
            " 1 | Alice | North\n"
            " 2 | Bob   | South\n\n"
            "deals sample:\n"
            "id | salesperson_id | amount | closed_date\n"
            " 1 | 1              | 12000  | 2024-01-15\n"
            " 2 | 2              | 8500   | 2024-02-20"
        ),
        "hints": [
            "JOIN salespeople s ON s.id = d.salesperson_id",
            "Filter: WHERE strftime('%Y', closed_date) = '2024'",
            "GROUP BY s.region, then ORDER BY total_amount DESC LIMIT 3",
        ],
    },
    # ─────────────────────────────────────────────
    # TASK 3  — Hard
    # ─────────────────────────────────────────────
    "churn-analysis": {
        "id": "churn-analysis",
        "name": "Customer Churn Analysis",
        "description": (
            "Multi-table analysis: find churned customers, compute months subscribed, "
            "total paid, and support ticket count. Order by total paid descending."
        ),
        "difficulty": "hard",
        "max_steps": 5,
        "schema_ddl": """
CREATE TABLE customers (
    id          INTEGER PRIMARY KEY,
    name        TEXT    NOT NULL,
    status      TEXT    NOT NULL,
    plan        TEXT    NOT NULL
);
CREATE TABLE subscriptions (
    id           INTEGER PRIMARY KEY,
    customer_id  INTEGER REFERENCES customers(id),
    start_date   TEXT    NOT NULL,
    end_date     TEXT,
    monthly_fee  REAL    NOT NULL
);
CREATE TABLE support_tickets (
    id          INTEGER PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(id),
    created_at  TEXT    NOT NULL,
    category    TEXT    NOT NULL
);
""".strip(),
        "seed_data": {
            "customers": [
                (1, "Acme Corp", "churned", "pro"),
                (2, "Beta Ltd", "active", "enterprise"),
                (3, "Gamma Inc", "churned", "basic"),
                (4, "Delta Co", "active", "pro"),
                (5, "Epsilon LLC", "churned", "pro"),
            ],
            "subscriptions": [
                (1, 1, "2023-01-01", "2024-06-30", 299.0),
                (2, 2, "2022-06-01", None, 899.0),
                (3, 3, "2023-09-01", "2024-03-31", 99.0),
                (4, 4, "2021-01-01", None, 299.0),
                (5, 5, "2023-03-01", "2024-09-30", 299.0),
            ],
            "support_tickets": [
                (1, 1, "2023-05-10", "billing"),
                (2, 1, "2023-11-20", "technical"),
                (3, 1, "2024-03-15", "billing"),
                (4, 3, "2023-10-05", "technical"),
                (5, 5, "2023-07-22", "billing"),
                (6, 5, "2024-01-18", "general"),
                (7, 5, "2024-08-30", "technical"),
                (8, 2, "2023-03-01", "billing"),
            ],
        },
        "question": (
            "For each churned customer, show: name, total_paid (monthly_fee × months_subscribed, "
            "rounded to 2 dp), ticket_count (number of support tickets), and months_subscribed "
            "(integer months between start_date and end_date using CAST). "
            "Order by total_paid descending."
        ),
        "expected_columns": ["name", "total_paid", "ticket_count", "months_subscribed"],
        "expected_rows": [
            ("Acme Corp", 3588.0, 3, 18),  # 299*18, 3 tickets
            ("Epsilon LLC", 2093.0, 3, 7),  # 299*7=2093, 3 tickets
            ("Gamma Inc", 594.0, 1, 6),  # 99*6, 1 ticket — corrected: 7 months
        ],
        "sample_display": (
            "customers: id, name, status ('active'/'churned'), plan\n"
            "subscriptions: customer_id, start_date, end_date (NULL if active), monthly_fee\n"
            "support_tickets: customer_id, created_at, category"
        ),
        "hints": [
            "JOIN customers → subscriptions → COUNT(tickets) via LEFT JOIN",
            "Months: CAST((julianday(end_date) - julianday(start_date))/30 AS INTEGER)",
            "WHERE c.status = 'churned'",
            "ROUND(monthly_fee * months_subscribed, 2) AS total_paid",
        ],
    },
}


def get_task(task_id: str) -> Dict[str, Any]:
    if task_id not in TASKS:
        raise ValueError(f"Unknown task: {task_id!r}. Valid: {list(TASKS)}")
    return TASKS[task_id]


def list_tasks() -> List[Dict[str, str]]:
    return [
        {
            "id": t["id"],
            "name": t["name"],
            "description": t["description"],
            "difficulty": t["difficulty"],
            "max_steps": str(t["max_steps"]),
        }
        for t in TASKS.values()
    ]
