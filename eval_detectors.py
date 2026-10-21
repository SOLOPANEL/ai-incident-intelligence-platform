"""
Detector Evaluation — measures each anomaly detector against real ground truth.

Uses ground_truth.jsonl (the actual injected-anomaly windows from the generator)
as the answer key, and checks how well each detector (error_status_code,
latency_spike, ml_isolation_forest) actually did.

Run it once, any time, after your pipeline has been running a while:
    python eval_detectors.py

This is a one-shot report, not a continuous service — run it whenever you
want a fresh scorecard.
"""

import json

import pandas as pd
import psycopg2
import psycopg2.extras


def get_connection():
    return psycopg2.connect(
        host="localhost",
        port=5432,
        dbname="incident_db",
        user="incident_user",
        password="incident_pass",
        cursor_factory=psycopg2.extras.RealDictCursor,
    )


def load_ground_truth_windows(path="ground_truth.jsonl"):
    """Pair up anomaly_start/anomaly_end events into (start, end) time windows."""
    events = []
    with open(path) as f:
        for line in f:
            events.append(json.loads(line))

    windows = []
    open_start = None
    for event in events:
        if event["event"] == "anomaly_start":
            open_start = pd.to_datetime(event["timestamp"])
        elif event["event"] == "anomaly_end" and open_start is not None:
            end = pd.to_datetime(event["timestamp"])
            windows.append((open_start, end))
            open_start = None

    return windows


def label_is_truly_anomalous(timestamp, windows):
    for start, end in windows:
        if start <= timestamp <= end:
            return True
    return False


def load_all_logs():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, timestamp FROM logs ORDER BY id ASC;")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    df = pd.DataFrame(rows)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


def load_flagged_ids_by_rule():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT rule_matched, log_id FROM anomalies;")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    flagged = {}
    for row in rows:
        flagged.setdefault(row["rule_matched"], set()).add(row["log_id"])
    return flagged


def compute_metrics(true_labels, predicted_labels):
    tp = sum(1 for t, p in zip(true_labels, predicted_labels) if t and p)
    fp = sum(1 for t, p in zip(true_labels, predicted_labels) if not t and p)
    fn = sum(1 for t, p in zip(true_labels, predicted_labels) if t and not p)
    tn = sum(1 for t, p in zip(true_labels, predicted_labels) if not t and not p)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    return {
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "true_negatives": tn,
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1_score": round(f1, 3),
    }


def run():
    print("Loading ground truth windows...")
    windows = load_ground_truth_windows()
    print(f"Found {len(windows)} labeled anomaly windows.\n")

    print("Loading all logs...")
    logs_df = load_all_logs()
    print(f"Loaded {len(logs_df)} logs.\n")

    print("Labeling each log as truly anomalous or not, using ground truth...")
    logs_df["true_label"] = logs_df["timestamp"].apply(lambda t: label_is_truly_anomalous(t, windows))
    print(f"{logs_df['true_label'].sum()} logs fall inside a real injected anomaly window.\n")

    flagged_by_rule = load_flagged_ids_by_rule()

    print("=" * 60)
    print("EVALUATION RESULTS — each detector vs. ground truth")
    print("=" * 60)

    for rule_name, flagged_ids in flagged_by_rule.items():
        logs_df["predicted_label"] = logs_df["id"].isin(flagged_ids)
        metrics = compute_metrics(logs_df["true_label"], logs_df["predicted_label"])

        print(f"\n--- {rule_name} ---")
        print(f"  Precision: {metrics['precision']}  (of what it flagged, how much was real)")
        print(f"  Recall:    {metrics['recall']}  (of all real anomalies, how many it caught)")
        print(f"  F1 score:  {metrics['f1_score']}  (balance of both)")
        print(f"  True positives:  {metrics['true_positives']}")
        print(f"  False positives: {metrics['false_positives']}")
        print(f"  False negatives: {metrics['false_negatives']}")

    print("\n" + "=" * 60)
    print("Done. Higher precision = fewer false alarms. Higher recall = fewer missed incidents.")


if __name__ == "__main__":
    run()