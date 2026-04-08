
# Text-to-SQL OpenEnv

An RL environment where an agent must write SQLite queries to answer
business questions given a database schema and sample data.

## Why this domain

Text-to-SQL is one of the highest-value LLM tasks in enterprise software.
This environment enables:

- Training agents to write correct SQL via trial-and-error
- Evaluating LLMs on realistic business queries
- Benchmarking SQL reasoning across difficulty levels

## Action space

```json
{
  "sql_query": "SELECT name, salary FROM employees WHERE ...",
  "reasoning": "(optional) why you chose this query"
}
```

## Observation space

| Field             | Type      | Description                        |
| ----------------- | --------- | ---------------------------------- |
| schema_ddl        | string    | CREATE TABLE statements            |
| question          | string    | Natural language business question |
| sample_rows       | string    | Human-readable sample data         |
| expected_columns  | list[str] | Columns the answer must include    |
| previous_attempts | list      | Last 3 queries + feedback          |
| hints             | list[str] | Progressive hints                  |

## Reward function

| Component          | Weight | Condition                     |
| ------------------ | ------ | ----------------------------- |
| non_empty          | 0.10   | Query is non-empty            |
| syntax_valid       | 0.20   | No parse error                |
| executes           | 0.25   | No runtime error              |
| correct_columns    | 0.20   | All expected columns returned |
| correct_data       | 0.25   | Result set matches expected   |
| efficiency_penalty | −0.02  | Per step after the first      |

## Tasks

| ID              | Difficulty | Description                                |
| --------------- | ---------- | ------------------------------------------ |
| employee-filter | Easy       | Single-table filter, ORDER BY              |
| sales-by-region | Medium     | 2-table JOIN, GROUP BY, date filter        |
| churn-analysis  | Hard       | 3-table JOIN, date arithmetic, aggregation |

## Baseline scores

| Task            | Score |
| --------------- | ----- |
| employee-filter | ~0.95 |
| sales-by-region | ~0.70 |
| churn-analysis  | ~0.55 |

## Setup

```bash
pip install -r requirements.txt
uvicorn app.main:app --port 7860
```

## Docker

```bash
docker build -t text-to-sql-env .
docker run -p 7860:7860 text-to-sql-env
```

## Inference

```bash
export HF_TOKEN=your_token
export API_BASE_URL=https://router.huggingface.co/v1
export MODEL_NAME=Qwen/Qwen2.5-72B-Instruct
export SERVER_URL=http://localhost:7860
python inference.py
```
