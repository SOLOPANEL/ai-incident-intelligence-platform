"""
Log Analyzer — Week 3 deliverable.

Reads new rows from Postgres (written by the consumer), runs each
message through Drain3 to get a structured "template", applies simple
rule-based anomaly detection, and stores flagged anomalies in a new table.

Run it in a THIRD terminal, while the generator and consumer are also running:
    python log_analyzer.py

It runs forever, checking for new rows every few seconds. Stop with Ctrl+C.
"""

import time
import os

import psycopg2
from drain3 import TemplateMiner

POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "localhost")

# Connect to Postgres (same credentials as the consumer)
conn = psycopg2.connect(
    host=POSTGRES_HOST,
    port=5432,
    dbname="incident_db",
    user="incident_user",
    password="incident_pass",
)
conn.autocommit = True
conn.autocommit = True
cur = conn.cursor()

# Drain3's template miner learns log patterns as it sees more data
template_miner = TemplateMiner()

# Simple thresholds — the "dumb rules" version, replaced by real ML next week
LATENCY_THRESHOLD_MS = 2000


def ensure_anomalies_table():
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
    print("Table 'anomalies' is ready.")


def get_last_processed_id():
    """Start from the highest existing anomaly's log_id, or 0 if none yet."""
    cur.execute("SELECT COALESCE(MAX(log_id), 0) FROM anomalies;")
    return cur.fetchone()[0]


def check_rules(row):
    """
    Very simple rule-based anomaly detection.
    Returns a rule name if something looks wrong, otherwise None.
    """
    log_id, timestamp, route, user_id, status_code, response_time_ms, message, raw_json = row

    if status_code is not None and status_code >= 500:
        return "error_status_code"

    if response_time_ms is not None and response_time_ms > LATENCY_THRESHOLD_MS:
        return "latency_spike"

    if response_time_ms is None:
        return "missing_response_time"

    if "exhausted" in (message or "") or "crash" in (message or "").lower():
        return "crash_pattern"

    return None


def process_new_rows(last_id):
    cur.execute(
        """
        SELECT id, timestamp, route, user_id, status_code, response_time_ms, message, raw_json
        FROM logs
        WHERE id > %s
        ORDER BY id ASC
        """,
        (last_id,),
    )
    rows = cur.fetchall()

    for row in rows:
        log_id, timestamp, route, user_id, status_code, response_time_ms, message, raw_json = row

        # Run through Drain3 to get a structured template
        result = template_miner.add_log_message(message or "")
        template = result["template_mined"]

        # Apply the simple rules
        rule_matched = check_rules(row)

        if rule_matched:
            cur.execute(
                """
                INSERT INTO anomalies (log_id, timestamp, template, rule_matched, route, status_code, response_time_ms, message)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (log_id, timestamp, template, rule_matched, route, status_code, response_time_ms, message),
            )
            print(f"[FLAGGED] {rule_matched} | {message} (template: {template})")

        last_id = log_id

    return last_id


def run():
    ensure_anomalies_table()
    last_id = get_last_processed_id()
    print(f"Starting from log id {last_id}. Watching for new logs...\n")

    while True:
        last_id = process_new_rows(last_id)
        time.sleep(3)


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        cur.close()
        conn.close()