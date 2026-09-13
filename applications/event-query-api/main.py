import os
from typing import Any

import psycopg2
from fastapi import FastAPI
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from starlette.responses import Response

app = FastAPI(title="Event Query API")

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "eventdb")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")


def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )


def rows_to_dicts(cursor, rows) -> list[dict[str, Any]]:
    columns = [column.name for column in cursor.description]
    return [dict(zip(columns, row)) for row in rows]


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "event-query-api"}


@app.get("/events")
async def recent_events(limit: int = 25):
    limit = max(1, min(limit, 100))
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, event_type, source, severity, message, status,
                       original_timestamp, processed_timestamp
                FROM processed_events
                ORDER BY processed_timestamp DESC
                LIMIT %s
                """,
                (limit,),
            )
            return {"events": rows_to_dicts(cur, cur.fetchall())}


@app.get("/events/stats")
async def event_stats():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT severity, COUNT(*) AS count
                FROM processed_events
                GROUP BY severity
                ORDER BY count DESC
                """
            )
            severity_counts = rows_to_dicts(cur, cur.fetchall())

            cur.execute(
                """
                SELECT status, COUNT(*) AS count
                FROM processed_events
                GROUP BY status
                ORDER BY count DESC
                """
            )
            status_counts = rows_to_dicts(cur, cur.fetchall())

    return {
        "severity_counts": severity_counts,
        "status_counts": status_counts,
    }


@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
