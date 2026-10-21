"""
ML Anomaly Detector — Week 5 deliverable.

Replaces the fixed if/else rules with a real ML model (Isolation Forest)
that learns what "normal" looks like from your actual data, instead of
you hardcoding thresholds.

Run it in its own terminal, alongside everything else:
    python ml_anomaly_detector.py

It trains once on startup using existing logs, then continuously scores
new rows as they arrive. Stop with Ctrl+C.
"""

import time
import os

import pandas as pd
import psycopg2
import psycopg2.extras
from sklearn.ensemble import IsolationForest

MODEL_RULE_NAME = "ml_isolation_forest"
LATENCY_SENTINEL = 9999  # stand-in value when response_time_ms is missing
POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "localhost")


def get_connection():
    conn = psycopg2.connect(
        host=POSTGRES_HOST,
        port=5432,
        dbname="incident_db",
        user="incident_user",
        password="incident_pass",
        cursor_factory=psycopg2.extras.RealDictCursor,
    )
    conn.autocommit = True
    return conn


def ensure_ml_columns():
    """Anomalies table already exists (from log_analyzer.py) — nothing new needed,
    we just insert rows with rule_matched = 'ml_isolation_forest'."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS anomalies (
            id SERIAL PRIMARY KEY,
            log_id INTEGER,
            timestamp TIMESTAMPTZ,
            template TEXT,
            rule_matched TEXT,
            route TEXT,
            status_code INTEGER,
            response_time_ms INTEGER,
            message TEXT
        );
        """
    )
    conn.commit()
    cur.close()
    conn.close()


def build_features(df):
    """Turn raw log columns into numbers the model can learn from."""
    features = pd.DataFrame()
    features["response_time_ms"] = df["response_time_ms"].fillna(LATENCY_SENTINEL)
    features["status_code"] = df["status_code"].fillna(0)
    features["is_missing_latency"] = df["response_time_ms"].isna().astype(int)
    return features


def train_model():
    """Train on whatever logs already exist in Postgres."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, response_time_ms, status_code FROM logs ORDER BY id DESC LIMIT 3000;"
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    df = pd.DataFrame(rows)
    if len(df) < 50:
        print("Not enough data to train yet (need at least 50 logs). Waiting...")
        return None

    features = build_features(df)

    # contamination = the rough % of data we expect to be anomalous.
    # 0.05 is more realistic now that the generator produces far fewer anomalies overall.
    model = IsolationForest(contamination=0.05, random_state=42)
    model.fit(features)

    print(f"Model trained on {len(df)} logs.\n")
    return model


def get_last_processed_id():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT COALESCE(MAX(log_id), 0) as max_id FROM anomalies WHERE rule_matched = %s;",
        (MODEL_RULE_NAME,),
    )
    result = cur.fetchone()["max_id"]
    cur.close()
    conn.close()
    return result


def score_new_rows(model, last_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, timestamp, route, status_code, response_time_ms, message
        FROM logs
        WHERE id > %s
        ORDER BY id ASC
        """,
        (last_id,),
    )
    rows = cur.fetchall()

    if not rows:
        cur.close()
        conn.close()
        return last_id

    df = pd.DataFrame(rows)
    features = build_features(df)

    # -1 means the model thinks this row is an outlier, 1 means normal
    predictions = model.predict(features)

    for row, prediction in zip(rows, predictions):
        if prediction == -1:
            cur.execute(
                """
                INSERT INTO anomalies (log_id, timestamp, template, rule_matched, route, status_code, response_time_ms, message)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    row["id"],
                    row["timestamp"],
                    None,
                    MODEL_RULE_NAME,
                    row["route"],
                    row["status_code"],
                    row["response_time_ms"],
                    row["message"],
                ),
            )
            print(f"[ML FLAGGED] {row['message']} | status={row['status_code']} latency={row['response_time_ms']}")

        last_id = row["id"]

    conn.commit()
    cur.close()
    conn.close()
    return last_id


def run():
    ensure_ml_columns()

    model = None
    while model is None:
        model = train_model()
        if model is None:
            time.sleep(5)

    last_id = get_last_processed_id()
    print(f"Starting from log id {last_id}. Scoring new logs with the ML model...\n")

    rows_seen_since_retrain = 0
    while True:
        last_id = score_new_rows(model, last_id)
        time.sleep(3)


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        print("\nStopped.")