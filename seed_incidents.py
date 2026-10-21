"""
Seed Past Incidents — Week 6 deliverable.

Creates an "incidents" table with a vector column, then inserts a set of
realistic fake past incidents, each converted into an embedding.

This is the "memory" your RAG layer will search later — when a new
anomaly happens, we'll embed it too and find the most similar past
incidents here.

Run it once:
    python seed_incidents.py
"""

import psycopg2
from pgvector.psycopg2 import register_vector
from sentence_transformers import SentenceTransformer

# This model turns text into a 384-number embedding. Small, free, runs locally.
print("Loading embedding model (first run downloads it, ~90MB)...")
model = SentenceTransformer("all-MiniLM-L6-v2")

# Fake past incidents — written the way a real postmortem/incident log would be.
# Deliberately covers the same categories your generator injects, plus a few extra
# for realism (a RAG system should also correctly find "nothing similar" sometimes).
PAST_INCIDENTS = [
    {
        "title": "Payment service connection pool exhaustion",
        "description": "Payment endpoint started returning 500 errors with message 'connection pool exhausted: could not acquire connection'. Traced to a leaked connection in the retry logic that never released back to the pool under high load.",
        "fix": "Increased pool size from 10 to 30 as a stopgap, then fixed the retry logic to properly close connections in a finally block. Added a pool utilization alert at 80% capacity.",
    },
    {
        "title": "Checkout latency spike during flash sale",
        "description": "Response times on /checkout climbed from ~100ms to over 4000ms during a promotional traffic spike. Database CPU was pegged at 100%, caused by an unindexed query scanning the full orders table.",
        "fix": "Added a composite index on (user_id, created_at). Response times dropped back to under 150ms even under similar load in the next sale.",
    },
    {
        "title": "Login failures after auth provider outage",
        "description": "Users couldn't log in; /login returned 502 errors. Root cause was our third-party auth provider having an outage, and our service had no fallback or circuit breaker, so it just hung waiting on their API.",
        "fix": "Added a circuit breaker with a 3-second timeout and a cached-session fallback so existing sessions kept working even when the provider was down.",
    },
    {
        "title": "Search service memory leak",
        "description": "Search pods were restarting every few hours due to OOM kills. Memory usage climbed steadily over time rather than spiking suddenly.",
        "fix": "Found a cache that was never evicting old entries. Added a max size and TTL to the cache. Memory usage stabilized after deploy.",
    },
    {
        "title": "Product catalog 500 errors after deploy",
        "description": "Immediately after a deploy, /products started returning 500 errors for about 12% of requests. Correlated exactly with the deploy timestamp.",
        "fix": "A new required field was added to the product schema but old cached records didn't have it, causing a null pointer error. Rolled back, added a migration script, redeployed safely.",
    },
    {
        "title": "Disk space exhaustion on log server",
        "description": "Multiple services started failing writes with disk-full errors. Root cause was log rotation not being configured on one server, letting debug logs accumulate unchecked.",
        "fix": "Configured log rotation with a 7-day retention policy and added a disk usage alert at 85%.",
    },
    {
        "title": "Checkout errors from downstream inventory service timeout",
        "description": "Checkout requests were timing out and returning 503s. The inventory service they depend on was responding slowly (8-10 seconds instead of ~200ms) due to a slow downstream query, and our service had no timeout set, so it just waited.",
        "fix": "Added a 2-second timeout with graceful degradation (show 'checking availability' instead of failing outright). Separately fixed the slow query in the inventory service.",
    },
    {
        "title": "Profile page errors from a bad third-party image CDN",
        "description": "Profile pages were slow to load and occasionally erroring, tracked to a third-party avatar CDN having intermittent failures. Not our infrastructure, but our page had no fallback.",
        "fix": "Added a local default avatar fallback and stopped blocking page render on the CDN response.",
    },
    {
        "title": "Database replica lag causing stale reads",
        "description": "Users reported seeing outdated data right after making changes. Root cause was read replicas lagging behind the primary database by up to 30 seconds under heavy write load.",
        "fix": "Routed reads-immediately-after-write to the primary database instead of a replica for a short window after any write.",
    },
    {
        "title": "Redis cache stampede after cold restart",
        "description": "After a Redis restart, the cache was empty, and a burst of traffic all missed cache simultaneously, hammering the database with duplicate identical queries.",
        "fix": "Added request coalescing so only one request per cache key hits the database while others wait for that result, instead of all hitting the database independently.",
    },
    {
        "title": "Email service silently dropping messages",
        "description": "Password reset emails weren't arriving for some users. No errors were logged. Root cause was the email provider silently rate-limiting our account without returning a clear error.",
        "fix": "Added explicit logging of the provider's response codes and an alert if send success rate drops below 95%.",
    },
    {
        "title": "Checkout payment double-charging",
        "description": "A small number of users were charged twice for one order. Root cause was a retry on a network timeout that didn't check if the original request had actually succeeded server-side first.",
        "fix": "Added an idempotency key to payment requests so retries with the same key are recognized and only processed once.",
    },
]


def ensure_incidents_table(conn):
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS incidents (
            id SERIAL PRIMARY KEY,
            title TEXT,
            description TEXT,
            fix TEXT,
            embedding vector(384)
        );
        """
    )
    conn.commit()
    cur.close()
    print("Table 'incidents' is ready.")


def seed(conn):
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM incidents;")
    existing_count = cur.fetchone()[0]
    if existing_count > 0:
        print(f"'incidents' table already has {existing_count} rows. Skipping seed to avoid duplicates.")
        print("(If you want to reseed, run: DELETE FROM incidents; first.)")
        cur.close()
        return

    for incident in PAST_INCIDENTS:
        # We embed title + description together — that's what future anomalies
        # will be compared against when searching for similar past incidents.
        text_to_embed = f"{incident['title']}. {incident['description']}"
        embedding = model.encode(text_to_embed).tolist()

        cur.execute(
            """
            INSERT INTO incidents (title, description, fix, embedding)
            VALUES (%s, %s, %s, %s)
            """,
            (incident["title"], incident["description"], incident["fix"], embedding),
        )
        print(f"Seeded: {incident['title']}")

    conn.commit()
    cur.close()
    print(f"\nDone. Inserted {len(PAST_INCIDENTS)} past incidents with embeddings.")


def run():
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        dbname="incident_db",
        user="incident_user",
        password="incident_pass",
    )
    register_vector(conn)  # tells psycopg2 how to handle the vector type

    ensure_incidents_table(conn)
    seed(conn)

    conn.close()


if __name__ == "__main__":
    run()