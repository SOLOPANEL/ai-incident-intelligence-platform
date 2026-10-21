"""
Fake Log Generator — Week 1 deliverable, now Week 2 upgraded.

Simulates a running app emitting logs. Most of the time it behaves normally.
Occasionally it switches into a "broken" mode on purpose, so you have
labeled ground truth to test your anomaly detector against later.

Run it:
    python fake_log_generator.py

Output:
    - Prints each log line as JSON to the console
    - Appends the same lines to logs.jsonl (kept as a backup/local record)
    - Pushes each log line into a Redis Stream called "logs_stream"
    - Appends injected-anomaly windows to ground_truth.jsonl
      (so you can later check: did my detector actually catch this?)
"""

import json
import os
import random
import time
from datetime import datetime, timezone

import redis

LOG_FILE = "logs.jsonl"
GROUND_TRUTH_FILE = "ground_truth.jsonl"
REDIS_STREAM_NAME = "logs_stream"
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")

# Connect to the Redis container we started with docker compose
r = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)


ROUTES = ["/login", "/products", "/checkout", "/payment", "/profile", "/search"]
USERS = list(range(1000, 1050))

# Three kinds of "broken" behavior we can simulate
ANOMALY_TYPES = ["latency_spike", "error_storm", "crash_loop"]


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def normal_event():
    """A believable, healthy log line."""
    return {
        "timestamp": now_iso(),
        "route": random.choice(ROUTES),
        "user_id": random.choice(USERS),
        "status_code": 200,
        "response_time_ms": random.randint(30, 150),
        "message": "request handled successfully",
    }


def anomaly_event(anomaly_type):
    """A log line that looks like something is broken."""
    if anomaly_type == "latency_spike":
        return {
            "timestamp": now_iso(),
            "route": random.choice(ROUTES),
            "user_id": random.choice(USERS),
            "status_code": 200,
            "response_time_ms": random.randint(3000, 8000),  # very slow
            "message": "request handled successfully",
        }
    elif anomaly_type == "error_storm":
        return {
            "timestamp": now_iso(),
            "route": random.choice(ROUTES),
            "user_id": random.choice(USERS),
            "status_code": random.choice([500, 502, 503]),
            "response_time_ms": random.randint(50, 400),
            "message": "internal server error",
        }
    elif anomaly_type == "crash_loop":
        return {
            "timestamp": now_iso(),
            "route": "/payment",
            "user_id": None,
            "status_code": 500,
            "response_time_ms": None,
            "message": "connection pool exhausted: could not acquire connection",
        }


def write_line(filepath, data):
    with open(filepath, "a") as f:
        f.write(json.dumps(data) + "\n")


def push_to_redis(data):
    """Push one log event into the Redis stream, as a flat string dict."""
    # Redis Streams need flat string values, so we serialize the whole event as one JSON string
    r.xadd(REDIS_STREAM_NAME, {"data": json.dumps(data)})


def run(duration_seconds=300, anomaly_chance_per_tick=0.01):
    """
    Runs the generator for `duration_seconds`.
    Each tick, there's a small chance an anomaly window starts.
    Once started, an anomaly window lasts 10-20 ticks before returning to normal.
    """
    print(f"Starting fake log generator for {duration_seconds} seconds...")
    print(f"Writing logs to {LOG_FILE}, ground truth to {GROUND_TRUTH_FILE}\n")

    end_time = time.time() + duration_seconds
    in_anomaly = False
    anomaly_type = None
    anomaly_ticks_left = 0

    while time.time() < end_time:
        if not in_anomaly and random.random() < anomaly_chance_per_tick:
            # Start a new anomaly window
            in_anomaly = True
            anomaly_type = random.choice(ANOMALY_TYPES)
            anomaly_ticks_left = random.randint(10, 20)
            start_record = {
                "event": "anomaly_start",
                "type": anomaly_type,
                "timestamp": now_iso(),
            }
            write_line(GROUND_TRUTH_FILE, start_record)
            print(f"\n>>> INJECTING ANOMALY: {anomaly_type} <<<\n")

        if in_anomaly:
            event = anomaly_event(anomaly_type)
            anomaly_ticks_left -= 1
            if anomaly_ticks_left <= 0:
                in_anomaly = False
                end_record = {
                    "event": "anomaly_end",
                    "type": anomaly_type,
                    "timestamp": now_iso(),
                }
                write_line(GROUND_TRUTH_FILE, end_record)
                print(f"\n>>> ANOMALY ENDED: {anomaly_type} <<<\n")
        else:
            event = normal_event()

        print(json.dumps(event))
        write_line(LOG_FILE, event)
        push_to_redis(event)

        time.sleep(1.5)  # ~1 log every 1.5 seconds — realistic demo volume, not load-testing

    print("\nDone. Check logs.jsonl and ground_truth.jsonl")


if __name__ == "__main__":
    run(duration_seconds=300)