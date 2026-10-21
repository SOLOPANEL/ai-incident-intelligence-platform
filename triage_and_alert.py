"""
Triage & Alert — Week 9 deliverable.

Watches for anomalies that already have an LLM explanation, assigns a
severity level, and sends a Slack alert — critical ones get pinged
immediately, low-severity ones are just logged quietly.

Requires SLACK_WEBHOOK_URL to be set as an environment variable first:
    $env:SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."

Run it in its own terminal, after incident_explainer.py has been running a bit:
    python triage_and_alert.py
"""

import os
import time

import psycopg2
import psycopg2.extras
import requests

SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")
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


def ensure_triage_columns():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("ALTER TABLE anomalies ADD COLUMN IF NOT EXISTS severity TEXT;")
    cur.execute("ALTER TABLE anomalies ADD COLUMN IF NOT EXISTS alerted BOOLEAN DEFAULT FALSE;")
    conn.commit()
    cur.close()
    conn.close()
    print("Columns 'severity' and 'alerted' are ready.")


def determine_severity(anomaly):
    """
    Simple, explainable severity rules — deliberately not a black box.
    Real teams want to know exactly why something was called critical.
    """
    status_code = anomaly["status_code"]
    response_time_ms = anomaly["response_time_ms"]
    rule = anomaly["rule_matched"]
    message = (anomaly["message"] or "").lower()

    if "exhausted" in message or "crash" in message:
        return "critical"
    if status_code is not None and status_code >= 500:
        return "critical"
    if response_time_ms is not None and response_time_ms > 4000:
        return "warning"
    if rule == "ml_isolation_forest":
        return "info"
    return "warning"


SEVERITY_EMOJI = {
    "critical": ":rotating_light:",
    "warning": ":warning:",
    "info": ":mag:",
}


def send_slack_alert(anomaly, severity):
    if not SLACK_WEBHOOK_URL:
        print("SLACK_WEBHOOK_URL not set — skipping Slack alert (severity still recorded).")
        return

    emoji = SEVERITY_EMOJI.get(severity, ":grey_question:")
    text = (
        f"{emoji} *{severity.upper()}* — anomaly on `{anomaly['route']}`\n"
        f"*Status:* {anomaly['status_code']}  *Latency:* {anomaly['response_time_ms']}ms\n"
        f"*Message:* {anomaly['message']}\n"
        f"*Explanation:* {anomaly['explanation']}\n"
    )
    if anomaly.get("matched_incident"):
        text += f"*Similar past incident:* {anomaly['matched_incident']}"

    try:
        requests.post(SLACK_WEBHOOK_URL, json={"text": text}, timeout=10)
    except requests.exceptions.RequestException as e:
        print(f"Failed to send Slack alert: {e}")


def process_pending(conn):
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, route, status_code, response_time_ms, message, rule_matched, explanation, matched_incident
        FROM anomalies
        WHERE explanation IS NOT NULL AND alerted = FALSE
        ORDER BY id ASC
        LIMIT 10
        """
    )
    rows = cur.fetchall()

    for anomaly in rows:
        severity = determine_severity(anomaly)
        send_slack_alert(anomaly, severity)

        cur.execute(
            "UPDATE anomalies SET severity = %s, alerted = TRUE WHERE id = %s",
            (severity, anomaly["id"]),
        )
        conn.commit()
        print(f"Anomaly #{anomaly['id']} -> severity: {severity}, alert sent: {bool(SLACK_WEBHOOK_URL)}")

    cur.close()


def run():
    ensure_triage_columns()
    if not SLACK_WEBHOOK_URL:
        print("\nWARNING: SLACK_WEBHOOK_URL is not set. Severity will still be recorded, but no Slack messages will send.\n")

    conn = get_connection()
    print("Watching for explained anomalies to triage and alert...\n")

    while True:
        process_pending(conn)
        time.sleep(5)


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        print("\nStopped.")