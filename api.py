"""
API Backend — Week 4 deliverable, part 1.

Serves your Postgres data as JSON, so the dashboard (a webpage) can display it.

Run it:
    uvicorn api:app --reload --port 8000

Then open http://localhost:8000/docs in your browser — FastAPI auto-generates
an interactive page where you can test every endpoint by clicking, no extra tools needed.
"""

import os
from datetime import datetime, timezone

import psycopg2
import psycopg2.extras
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Incident Intelligence API")
POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "localhost")

# Allows your React dashboard (running on a different port) to call this API.
# In a real production system you'd restrict this to your actual frontend's URL.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_connection():
    return psycopg2.connect(
        host=POSTGRES_HOST,
        port=5432,
        dbname="incident_db",
        user="incident_user",
        password="incident_pass",
        cursor_factory=psycopg2.extras.RealDictCursor,  # returns rows as dicts, not tuples
    )


from pydantic import BaseModel


class FeedbackInput(BaseModel):
    correct: bool
    correction_note: str | None = None


@app.on_event("startup")
def ensure_feedback_columns():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SET lock_timeout = '5s';")  # fail fast with a clear error instead of hanging forever
    cur.execute("ALTER TABLE anomalies ADD COLUMN IF NOT EXISTS feedback_correct BOOLEAN;")
    cur.execute("ALTER TABLE anomalies ADD COLUMN IF NOT EXISTS correction_note TEXT;")
    conn.commit()
    cur.close()
    conn.close()


@app.post("/anomalies/{anomaly_id}/feedback")
def submit_feedback(anomaly_id: int, feedback: FeedbackInput):
    """Records whether the AI's explanation was actually correct, per anomaly."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE anomalies SET feedback_correct = %s, correction_note = %s WHERE id = %s",
        (feedback.correct, feedback.correction_note, anomaly_id),
    )
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "recorded", "anomaly_id": anomaly_id, "correct": feedback.correct}


import json

import redis
from fastapi import Header, HTTPException

REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
INGEST_API_KEY = os.environ.get("INGEST_API_KEY")
r = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)


class IngestLogInput(BaseModel):
    route: str
    status_code: int
    response_time_ms: int | None = None
    message: str
    user_id: int | None = None


@app.post("/ingest")
def ingest_log(log: IngestLogInput, x_api_key: str = Header(default=None)):
    """
    Real external log ingestion endpoint. A company's app can POST logs here
    instead of us only using the fake generator. Requires a valid API key.
    """
    if not INGEST_API_KEY:
        raise HTTPException(status_code=503, detail="Ingestion is not configured on this server yet.")
    if x_api_key != INGEST_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key.")

    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "route": log.route,
        "user_id": log.user_id,
        "status_code": log.status_code,
        "response_time_ms": log.response_time_ms,
        "message": log.message,
    }
    r.xadd("logs_stream", {"data": json.dumps(event)})
    return {"status": "accepted"}


@app.get("/")
def root():
    return {"status": "Incident Intelligence API is running"}


@app.get("/system-health")
def get_system_health():
    """Shows when each pipeline stage last did something — a live view into the backend."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT MAX(timestamp) as last_log FROM logs;")
    last_log = cur.fetchone()["last_log"]

    cur.execute("SELECT MAX(timestamp) as last_anomaly FROM anomalies;")
    last_anomaly = cur.fetchone()["last_anomaly"]

    cur.execute("SELECT MAX(timestamp) as last_explained FROM anomalies WHERE explanation IS NOT NULL;")
    last_explained = cur.fetchone()["last_explained"]

    cur.execute("SELECT MAX(timestamp) as last_alerted FROM anomalies WHERE alerted = TRUE;")
    last_alerted = cur.fetchone()["last_alerted"]

    cur.execute("SELECT COUNT(*) as count FROM incidents;")
    incident_count = cur.fetchone()["count"]

    cur.execute("SELECT COUNT(*) as count FROM anomalies WHERE feedback_correct IS NOT NULL;")
    feedback_count = cur.fetchone()["count"]

    cur.execute("SELECT COUNT(*) as count FROM anomalies WHERE feedback_correct = FALSE AND feedback_processed = TRUE;")
    corrections_learned = cur.fetchone()["count"]

    cur.close()
    conn.close()

    return {
        "ingestion": {"last_activity": last_log},
        "detection": {"last_activity": last_anomaly},
        "explanation": {"last_activity": last_explained},
        "triage": {"last_activity": last_alerted},
        "vector_db": {"incident_count": incident_count},
        "feedback": {"total_given": feedback_count, "corrections_learned": corrections_learned},
    }


@app.get("/anomalies")
def get_anomalies(limit: int = 50):
    """Most recent flagged anomalies, newest first."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, log_id, timestamp, template, rule_matched, route, status_code, response_time_ms, message,
               severity, explanation, matched_incident, feedback_correct
        FROM anomalies
        ORDER BY id DESC
        LIMIT %s
        """,
        (limit,),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


@app.get("/stats")
def get_stats():
    """Count of anomalies grouped by type — powers the summary cards/chart."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT rule_matched, COUNT(*) as count FROM anomalies GROUP BY rule_matched;")
    by_rule = cur.fetchall()

    cur.execute("SELECT COUNT(*) as total FROM logs;")
    total_logs = cur.fetchone()["total"]

    cur.execute("SELECT COUNT(*) as total FROM anomalies;")
    total_anomalies = cur.fetchone()["total"]

    cur.close()
    conn.close()
    return {
        "total_logs": total_logs,
        "total_anomalies": total_anomalies,
        "by_rule": by_rule,
    }


@app.get("/logs/recent")
def get_recent_logs(limit: int = 50):
    """Most recent raw logs, newest first — for a live activity feed."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, timestamp, route, user_id, status_code, response_time_ms, message
        FROM logs
        ORDER BY id DESC
        LIMIT %s
        """,
        (limit,),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows