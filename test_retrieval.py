"""
Test Retrieval — Week 7 deliverable, part 1.

Given a description of a new problem, finds the most similar past incidents
from the vector database — the core "RAG" mechanism.

This is a TEST/DEMO script to prove retrieval works correctly before we
wire it into the live pipeline. Edit the QUERY_TEXT below and re-run it
with different problems to see how well it matches.

Run it:
    python test_retrieval.py
"""

import psycopg2
from pgvector.psycopg2 import register_vector
from sentence_transformers import SentenceTransformer

# Try changing this to different fake problems and see what it finds
QUERY_TEXT = "checkout page is throwing 500 errors, message says connection pool exhausted"


def run(query_text, top_k=3):
    print("Loading embedding model...")
    model = SentenceTransformer("all-MiniLM-L6-v2")

    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        dbname="incident_db",
        user="incident_user",
        password="incident_pass",
    )
    register_vector(conn)
    cur = conn.cursor()

    # Turn the query into the same kind of embedding we stored for past incidents
    query_embedding = model.encode(query_text).tolist()

    # <=> is pgvector's "cosine distance" operator — smaller number means more similar.
    # We order by it ascending and take the top few closest matches.
    cur.execute(
        """
        SELECT title, description, fix, embedding <=> %s::vector AS distance
        FROM incidents
        ORDER BY distance ASC
        LIMIT %s
        """,
        (query_embedding, top_k),
    )
    results = cur.fetchall()

    print(f"\nQuery: \"{query_text}\"\n")
    print(f"Top {top_k} most similar past incidents:\n")
    for i, (title, description, fix, distance) in enumerate(results, start=1):
        similarity_pct = (1 - distance) * 100  # rough, human-friendly conversion
        print(f"{i}. {title}  (similarity: {similarity_pct:.1f}%)")
        print(f"   What happened: {description}")
        print(f"   How it was fixed: {fix}\n")

    cur.close()
    conn.close()


if __name__ == "__main__":
    run(QUERY_TEXT)