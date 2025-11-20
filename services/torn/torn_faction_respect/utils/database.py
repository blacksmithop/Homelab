"""
Database manager for Torn Faction data
"""

import os
import psycopg2
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Tuple, Any


class DatabaseManager:
    def __init__(self):
        self.db_config = {
            "host": os.getenv("POSTGRES_HOST", "postgres"),
            "database": os.getenv("POSTGRES_DB"),
            "user": os.getenv("POSTGRES_USER"),
            "password": os.getenv("POSTGRES_PASSWORD"),
            "port": int(os.getenv("POSTGRES_PORT", 5432)),
        }

    def get_connection(self):
        """Get a new database connection"""
        return psycopg2.connect(**self.db_config)

    def execute_query(self, query: str, params: Tuple[Any, ...] = None, fetch: bool = False) -> Optional[List[Tuple]]:
        """
        Execute a database query with optional parameters and fetch results
        
        Args:
            query: SQL query string
            params: Query parameters
            fetch: Whether to fetch and return results
            
        Returns:
            List of tuples if fetch=True, None otherwise
        """
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            cur.execute(query, params)
            
            if fetch:
                result = cur.fetchall()
                conn.commit()
                return result
            else:
                conn.commit()
                return None
                
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cur.close()
            conn.close()

    def init_db(self):
        """Initialize database tables"""
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute(
            """
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
        """
        )
        conn.commit()
        cur.close()
        conn.close()

    def get_last_entry_age(self) -> Optional[timedelta]:
        """Get the age of the last entry"""
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT ts FROM faction_log ORDER BY id DESC LIMIT 1")
        row = cur.fetchone()
        cur.close()
        conn.close()

        if not row:
            return None
        return datetime.now(timezone.utc) - row[0]

    def insert_faction_data(self, data: dict):
        """Insert faction data into the database"""
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO faction_log (
                ts, respect, members, capacity, best_chain, days_old,
                rank_level, rank_name, tag, name
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
            (
                data["ts"],
                data.get("respect"),
                data.get("members"),
                data.get("capacity"),
                data.get("best_chain"),
                data.get("days_old"),
                data.get("rank_level"),
                data.get("rank_name"),
                data.get("tag"),
                data.get("name"),
            ),
        )
        conn.commit()
        cur.close()
        conn.close()

    def fetch_respect_data(self, start_utc=None, end_utc=None) -> list:
        """Fetch respect data for plotting"""
        conn = self.get_connection()
        query = """
            SELECT ts AS ts_utc, respect
            FROM faction_log
            WHERE (%s IS NULL OR ts >= %s)
              AND (%s IS NULL OR ts <= %s)
            ORDER BY ts
        """
        cur = conn.cursor()
        cur.execute(query, (start_utc, start_utc, end_utc, end_utc))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows