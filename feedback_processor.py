"""
Feedback Processor — Week 10 deliverable.

Watches for anomalies where feedback_correct = FALSE and a correction_note
was provided, then adds that correction as a NEW entry in the vector
database — so next time something similar happens, retrieval finds the
corrected answer instead of repeating the same mistake.

This is what makes the system "learn" over time, in a simple, explainable way.

Run it in its own terminal:
    python feedback_processor.py
"""

import time
import os

import psycopg2
import psycopg2.extras
from pgvector.psycopg2 import register_vector
from sentence_transformers import SentenceTransformer

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
    register_vector(conn)
    return conn


def ensure_processed_column():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("ALTER TABLE anomalies ADD COLUMN IF NOT EXISTS feedback_processed BOOLEAN DEFAULT FALSE;")
    conn.commit()
    cur.close()
    conn.close()


def process_corrections(conn, model):
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, route, status_code, response_time_ms, message, correction_note
        FROM anomalies
        WHERE feedback_correct = FALSE
          AND correction_note IS NOT NULL
          AND feedback_processed = FALSE
        """
    )
    rows = cur.fetchall()

    for row in rows:
        title = f"Correction: {row['message'] or 'unlabeled issue'} on {row['route']}"
        description = f"An anomaly was flagged (status {row['status_code']}, {row['response_time_ms']}ms) but the AI's first explanation was wrong. Corrected understanding: {row['correction_note']}"
        fix = row["correction_note"]

        text_to_embed = f"{title}. {description}"
        embedding = model.encode(text_to_embed).tolist()

        cur.execute(
            """
            INSERT INTO incidents (title, description, fix, embedding)
            VALUES (%s, %s, %s, %s)
            """,
            (title, description, fix, embedding),
        )
        cur.execute(
            "UPDATE anomalies SET feedback_processed = TRUE WHERE id = %s",
            (row["id"],),
        )
        conn.commit()
        print(f"Learned from anomaly #{row['id']}: added correction to the vector database.")

    cur.close()


def run():
    ensure_processed_column()
    print("Loading embedding model...")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    conn = get_connection()

    print("Watching for corrected feedback to learn from...\n")
    while True:
        process_corrections(conn, model)
        time.sleep(5)


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        print("\nStopped.")