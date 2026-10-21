"""
Redis -> Postgres Consumer — Week 2 deliverable.

Reads log events from the Redis stream (pushed by fake_log_generator.py)
and stores them into a Postgres table, permanently.

Run it in a SEPARATE terminal, at the same time fake_log_generator.py is running:
    python redis_to_postgres_consumer.py

It runs forever, picking up new logs as they arrive. Stop with Ctrl+C.
"""

import json
import os
import time

import psycopg2
import redis

REDIS_STREAM_NAME = "logs_stream"
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "localhost")

# Connect to Redis (same container as the generator uses)
r = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)

# Connect to Postgres (matches docker-compose.yml credentials)
conn = psycopg2.connect(
    host=POSTGRES_HOST,
    port=5432,
    dbname="incident_db",
    user="incident_user",
    password="incident_pass",
)
conn.autocommit = True
cur = conn.cursor()


def ensure_table_exists():
    """Create the logs table if it doesn't already exist."""
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS logs (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMPTZ,
            route TEXT,
            user_id INTEGER,
            status_code INTEGER,
            response_time_ms INTEGER,
            message TEXT,
            raw_json JSONB
        );
        """
    )
    print("Table 'logs' is ready.")


def insert_log(event):
    """Insert one log event into Postgres."""
    cur.execute(
        """
        INSERT INTO logs (timestamp, route, user_id, status_code, response_time_ms, message, raw_json)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (
            event.get("timestamp"),
            event.get("route"),
            event.get("user_id"),
            event.get("status_code"),
            event.get("response_time_ms"),
            event.get("message"),
            json.dumps(event),
        ),
    )


def run():
    ensure_table_exists()

    # "$" means: start reading only NEW messages from now on, not old history
    last_id = "$"
    print("Listening for new logs on Redis stream... (Ctrl+C to stop)\n")

    while True:
        # Blocks for up to 5 seconds waiting for new messages
        response = r.xread({REDIS_STREAM_NAME: last_id}, block=5000, count=10)

        if response:
            for stream_name, messages in response:
                for message_id, fields in messages:
                    event = json.loads(fields["data"])
                    insert_log(event)
                    print(f"Inserted: {event.get('message')} @ {event.get('timestamp')}")
                    last_id = message_id
        else:
            # No new messages in the last 5 seconds — just keep waiting
            pass


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        cur.close()
        conn.close()