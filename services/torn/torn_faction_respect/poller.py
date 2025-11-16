#!/usr/bin/env python3
import os
import time
import requests
from datetime import datetime, timezone, timedelta
import psycopg2

# === Config ===
API_URL = "https://api.torn.com/v2/faction/basic"
POLL_INTERVAL = 3600  # 1 hour
MIN_AGE = timedelta(hours=1)

DB_CONFIG = {
    "host": "postgres",
    "database": os.getenv("POSTGRES_DB"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "port": 5432
}

# === DB Setup: Columns Only ===
def init_db():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS faction_log (
            id SERIAL PRIMARY KEY,
            ts TIMESTAMPTZ NOT NULL,
            respect BIGINT,
            members SMALLINT,
            capacity SMALLINT,
            best_chain INTEGER,
            days_old INTEGER,
            rank_level SMALLINT,
            rank_name TEXT,
            tag TEXT,
            name TEXT
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

# === Helper: last entry age ===
def last_entry_age():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("SELECT ts FROM faction_log ORDER BY id DESC LIMIT 1")
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        return None
    return datetime.now(timezone.utc) - row[0]

# === Fetch & Save (Columns Only) ===
def fetch_and_save():
    api_key = os.getenv("TORN_API_KEY")
    if not api_key:
        print("ERROR: TORN_API_KEY missing")
        return

    # Skip if last entry < 1h old
    age = last_entry_age()
    if age is not None and age < MIN_AGE:
        remaining = int(MIN_AGE.total_seconds() - age.total_seconds())
        now_ist = datetime.now(timezone(timedelta(hours=5, minutes=30))).strftime("%I:%M %p IST")
        print(f"[{now_ist}] Last entry {int(age.total_seconds())}s ago — skipping ({remaining}s left)")
        return

    # Fetch
    try:
        resp = requests.get(API_URL, headers={"Authorization": f"ApiKey {api_key}"}, timeout=10)
        data = resp.json() if resp.ok else {"error": resp.text}
    except Exception as e:
        data = {"error": str(e)}

    basic = data.get("basic", {})
    rank = basic.get("rank", {})

    # Extract
    ts = datetime.now(timezone.utc)
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO faction_log (
            ts, respect, members, capacity, best_chain, days_old,
            rank_level, rank_name, tag, name
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        ts,
        basic.get("respect"),
        basic.get("members"),
        basic.get("capacity"),
        basic.get("best_chain"),
        basic.get("days_old"),
        rank.get("level"),
        rank.get("name"),
        basic.get("tag"),
        basic.get("name")
    ))
    conn.commit()
    cur.close()
    conn.close()

    ist = ts.astimezone(timezone(timedelta(hours=5, minutes=30))).strftime("%b %d, %I:%M %p IST")
    print(f"[{ist}] Saved | Respect: {basic.get('respect', 'N/A'):,} | Members: {basic.get('members')}")

# === Main ===
if __name__ == "__main__":
    print("Torn → Postgres (columns) poller starting...")
    init_db()
    print("DB ready. Writing only if ≥1h since last entry.")

    while True:
        fetch_and_save()
        time.sleep(POLL_INTERVAL)