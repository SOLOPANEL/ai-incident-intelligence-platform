"""
Incident Explainer — Week 8 deliverable.

The full RAG + LLM loop, running live:
  1. Watch the 'anomalies' table for new, unexplained rows
  2. Embed each anomaly's message
  3. Search the vector database for the most similar past incident
  4. Hand both to a local LLM (via Ollama) and ask for a plain-English explanation
  5. Save the explanation back into the anomalies table

Run it in its own terminal, alongside everything else:
    python incident_explainer.py

Requires Ollama running in the background (ollama pull llama3.2 first).
"""

import time
import os

import psycopg2
import psycopg2.extras
import requests
from pgvector.psycopg2 import register_vector
from sentence_transformers import SentenceTransformer

POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "localhost")
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "localhost")
OLLAMA_URL = f"http://{OLLAMA_HOST}:11434/api/generate"
OLLAMA_MODEL = "llama3.2"


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


def ensure_explanation_columns():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("ALTER TABLE anomalies ADD COLUMN IF NOT EXISTS explanation TEXT;")
    cur.execute("ALTER TABLE anomalies ADD COLUMN IF NOT EXISTS matched_incident TEXT;")
    conn.commit()
    cur.close()
    conn.close()
    print("Columns 'explanation' and 'matched_incident' are ready on the anomalies table.")


def find_similar_incident(conn, model, anomaly_message):
    """Returns the single most similar past incident, or None if the table is empty."""
    cur = conn.cursor()
    query_embedding = model.encode(anomaly_message or "unknown error").tolist()

    cur.execute(
        """
        SELECT title, description, fix, embedding <=> %s::vector AS distance
        FROM incidents
        ORDER BY distance ASC
        LIMIT 1
        """,
        (query_embedding,),
    )
    result = cur.fetchone()
    cur.close()
    return result


def ask_llm_for_explanation(anomaly, similar_incident):
    """Builds a grounded prompt and asks the local LLM for a plain-English explanation."""

    if similar_incident:
        context = f"""A similar past incident was found:
Title: {similar_incident['title']}
What happened: {similar_incident['description']}
How it was fixed: {similar_incident['fix']}
(Similarity to current issue: {(1 - similar_incident['distance']) * 100:.0f}%)"""
    else:
        context = "No similar past incident was found in the database."

    prompt = f"""You are an SRE assistant. Explain a flagged anomaly in EXACTLY 2-3 sentences, no more.

New anomaly:
- Route: {anomaly['route']}
- Status code: {anomaly['status_code']}
- Response time: {anomaly['response_time_ms']}ms
- Message: {anomaly['message']}
- Detected by: {anomaly['rule_matched']}

{context}

Rules:
- Output ONLY the explanation. No greetings, no "Hey team", no meta-commentary about what you're doing.
- State the likely cause first, then the fix, referencing the past incident only if one was found.
- If no similar incident was found, say so briefly and suggest a general next step.
- Never repeat the raw data fields back verbatim."""

    response = requests.post(
        OLLAMA_URL,
        json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
        timeout=60,
    )
    response.raise_for_status()
    return response.json()["response"].strip()


def process_unexplained_anomalies(conn, model):
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, route, status_code, response_time_ms, message, rule_matched
        FROM anomalies
        WHERE explanation IS NULL
        ORDER BY id DESC
        LIMIT 20
        """
    )
    rows = cur.fetchall()

    for anomaly in rows:
        similar_incident = find_similar_incident(conn, model, anomaly["message"])

        try:
            explanation = ask_llm_for_explanation(anomaly, similar_incident)
        except requests.exceptions.ConnectionError:
            print("Could not reach Ollama. Is it running? Skipping for now.")
            return

        matched_title = similar_incident["title"] if similar_incident else None

        cur.execute(
            "UPDATE anomalies SET explanation = %s, matched_incident = %s WHERE id = %s",
            (explanation, matched_title, anomaly["id"]),
        )
        conn.commit()

        print(f"\n--- Anomaly #{anomaly['id']} ({anomaly['rule_matched']}) ---")
        print(f"Matched: {matched_title or 'nothing similar found'}")
        print(f"Explanation: {explanation}\n")

    cur.close()


def run():
    ensure_explanation_columns()
    print("Loading embedding model...")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    conn = get_connection()

    print(f"Watching for unexplained anomalies. Using Ollama model: {OLLAMA_MODEL}\n")

    while True:
        process_unexplained_anomalies(conn, model)
        time.sleep(2)


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        print("\nStopped.")