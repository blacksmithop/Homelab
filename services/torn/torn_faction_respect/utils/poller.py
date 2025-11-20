import time
import threading
import requests
import os
from datetime import datetime, timezone, timedelta
from .database import DatabaseManager

class TornPoller:
    def __init__(self):
        self.db = DatabaseManager()
        self.running = False
        self.thread = None
        
        # Poller configuration
        self.API_URL = "https://api.torn.com/v2/faction/basic"
        self.POLL_INTERVAL = 3600  # 1 hour
        self.MIN_AGE = timedelta(hours=1)

    def last_entry_age(self):
        return self.db.get_last_entry_age()

    def fetch_and_save(self):
        """Poller function to fetch data from Torn API and save to database"""
        api_key = os.getenv("TORN_API_KEY")
        if not api_key:
            print("ERROR: TORN_API_KEY missing")
            return

        # Skip if last entry < 1h old
        age = self.last_entry_age()
        if age is not None and age < self.MIN_AGE:
            remaining = int(self.MIN_AGE.total_seconds() - age.total_seconds())
            now_ist = datetime.now(timezone(timedelta(hours=5, minutes=30))).strftime("%I:%M %p IST")
            print(f"[{now_ist}] Last entry {int(age.total_seconds())}s ago — skipping ({remaining}s left)")
            return

        # Fetch from Torn API
        try:
            resp = requests.get(self.API_URL, headers={"Authorization": f"ApiKey {api_key}"}, timeout=10)
            data = resp.json() if resp.ok else {"error": resp.text}
        except Exception as e:
            data = {"error": str(e)}

        basic = data.get("basic", {})
        rank = basic.get("rank", {})

        # Prepare data for insertion
        ts = datetime.now(timezone.utc)
        faction_data = {
            'ts': ts,
            'respect': basic.get("respect"),
            'members': basic.get("members"),
            'capacity': basic.get("capacity"),
            'best_chain': basic.get("best_chain"),
            'days_old': basic.get("days_old"),
            'rank_level': rank.get("level"),
            'rank_name': rank.get("name"),
            'tag': basic.get("tag"),
            'name': basic.get("name")
        }

        # Insert data
        self.db.insert_faction_data(faction_data)

        ist = ts.astimezone(timezone(timedelta(hours=5, minutes=30))).strftime("%b %d, %I:%M %p IST")
        print(f"[{ist}] Saved | Respect: {basic.get('respect', 'N/A'):,} | Members: {basic.get('members')}")

    def _worker(self):
        """Background worker that runs the poller"""
        print("Torn → Postgres poller starting...")
        self.db.init_db()
        print("DB ready. Writing only if ≥1h since last entry.")

        while self.running:
            try:
                self.fetch_and_save()
            except Exception as e:
                print(f"Error in poller: {e}")
            
            # Sleep for POLL_INTERVAL, but check periodically if we should stop
            for _ in range(self.POLL_INTERVAL):
                if not self.running:
                    break
                time.sleep(1)

    def start(self):
        """Start the background poller"""
        if self.running:
            print("Poller is already running")
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()
        print("Background poller started")

    def stop(self):
        """Stop the background poller"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5.0)
            print("Background poller stopped")

    def get_status(self):
        """Get poller status"""
        return {
            "running": self.running,
            "last_entry_age": str(self.last_entry_age()) if self.last_entry_age() else "No entries",
            "poll_interval_seconds": self.POLL_INTERVAL
        }