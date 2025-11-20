import os
import requests
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from fastapi import HTTPException
from .database import DatabaseManager


class CPRManager(DatabaseManager):
    def init_db(self):
        """Initialize CPR tables"""
        
        query1 = """
            CREATE TABLE IF NOT EXISTS cpr_users (
                api_key VARCHAR(64) PRIMARY KEY,
                user_id INTEGER,
                user_name VARCHAR(100),
                faction_id INTEGER,
                faction_name VARCHAR(100),
                created_at TIMESTAMPTZ DEFAULT NOW(),
                last_updated TIMESTAMPTZ DEFAULT NOW()
            )
        """
        self.execute_query(query1)

        query2 = """
            CREATE TABLE IF NOT EXISTS cpr_data (
                id SERIAL PRIMARY KEY,
                api_key VARCHAR(64) REFERENCES cpr_users(api_key),
                scenario_name VARCHAR(200) NOT NULL,
                slot_name VARCHAR(200) NOT NULL,
                success_chance DECIMAL(5,2) NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                UNIQUE(api_key, scenario_name, slot_name)
            )
        """
        self.execute_query(query2)

    async def validate_api_key(self, api_key: str) -> bool:
        """Validate Torn API key and store user info"""
        try:
            # Test API key with Torn API
            resp = requests.get(
                f"https://api.torn.com/user/?selections=profile,basic&key={api_key}",
                timeout=10,
            )

            if resp.status_code != 200:
                return False

            data = resp.json()

            if "error" in data:
                return False

            # Store/update user info
            query = """
                INSERT INTO cpr_users (api_key, user_id, user_name, faction_id, faction_name, last_updated)
                VALUES (%s, %s, %s, %s, %s, NOW())
                ON CONFLICT (api_key) 
                DO UPDATE SET 
                    user_name = EXCLUDED.user_name,
                    faction_id = EXCLUDED.faction_id,
                    faction_name = EXCLUDED.faction_name,
                    last_updated = NOW()
            """
            params = (
                api_key,
                data.get("player_id"),
                data.get("name"),
                data.get("faction", {}).get("faction_id"),
                data.get("faction", {}).get("faction_name"),
            )
            self.execute_query(query, params)

            return True

        except Exception as e:
            print(f"API key validation error: {e}")
            return False

    async def store_cpr_data(
        self, api_key: str, checkpoint_pass_rates: Dict[str, Any]
    ) -> bool:
        """Store checkpoint pass rates data"""
        if not await self.validate_api_key(api_key):
            raise HTTPException(status_code=400, detail="Invalid API key")

        try:
            for scenario_name, slots in checkpoint_pass_rates.items():
                for slot_name, success_chance in slots.items():
                    query = """
                        INSERT INTO cpr_data (api_key, scenario_name, slot_name, success_chance)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (api_key, scenario_name, slot_name) 
                        DO UPDATE SET 
                            success_chance = EXCLUDED.success_chance,
                            created_at = NOW()
                    """
                    params = (api_key, scenario_name, slot_name, float(success_chance))
                    self.execute_query(query, params)

            return True

        except Exception as e:
            print(f"Error storing CPR data: {e}")
            return False

    async def get_cpr_data(
        self, api_key: str, scenario_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get CPR data for user"""
        if scenario_name:
            query = """
                SELECT scenario_name, slot_name, success_chance, created_at
                FROM cpr_data 
                WHERE api_key = %s AND scenario_name = %s
                ORDER BY scenario_name, slot_name
            """
            params = (api_key, scenario_name)
        else:
            query = """
                SELECT scenario_name, slot_name, success_chance, created_at
                FROM cpr_data 
                WHERE api_key = %s
                ORDER BY scenario_name, slot_name
            """
            params = (api_key,)

        rows = self.execute_query(query, params, fetch=True)

        result = {}
        for scenario, slot, chance, created_at in rows:
            if scenario not in result:
                result[scenario] = {}
            result[scenario][slot] = {
                "success_chance": float(chance),
                "last_updated": created_at.isoformat(),
            }

        return result

    async def get_faction_cpr_data(self, faction_id: int) -> Dict[str, Any]:
        """Get aggregated CPR data for entire faction"""
        query = """
            SELECT cd.scenario_name, cd.slot_name, 
                   AVG(cd.success_chance) as avg_success,
                   COUNT(DISTINCT cu.api_key) as contributors,
                   MAX(cd.created_at) as last_updated
            FROM cpr_data cd
            JOIN cpr_users cu ON cd.api_key = cu.api_key
            WHERE cu.faction_id = %s
            GROUP BY cd.scenario_name, cd.slot_name
            ORDER BY cd.scenario_name, cd.slot_name
        """
        params = (faction_id,)

        rows = self.execute_query(query, params, fetch=True)

        result = {}
        for scenario, slot, avg_success, contributors, last_updated in rows:
            if scenario not in result:
                result[scenario] = {}
            result[scenario][slot] = {
                "average_success": float(avg_success),
                "contributors": contributors,
                "last_updated": last_updated.isoformat(),
            }

        return result
    
    async def get_faction_cpr_members_format(self, faction_id: int) -> Dict[str, Any]:
        """Get faction CPR data in member-based format"""
        try:
            # Query to get individual member contributions
            query = """
                SELECT cu.user_id, cd.scenario_name, cd.slot_name, cd.success_chance
                FROM cpr_data cd
                JOIN cpr_users cu ON cd.api_key = cu.api_key
                WHERE cu.faction_id = %s
                ORDER BY cu.user_id, cd.scenario_name, cd.slot_name
            """
            params = (faction_id,)
            rows = self.execute_query(query, params, fetch=True)
            
            # Transform data into the requested format
            members = {}
            for user_id, scenario_name, slot_name, success_chance in rows:
                user_id_str = str(user_id)
                
                if user_id_str not in members:
                    members[user_id_str] = {}
                
                if scenario_name not in members[user_id_str]:
                    members[user_id_str][scenario_name] = {}
                
                members[user_id_str][scenario_name][slot_name] = int(success_chance)
            
            return {
                "status": True,
                "message": "Fetching faction CPR results.",
                "members": members
            }
            
        except Exception as e:
            print(f"Error getting faction CPR members data: {e}")
            return {
                "status": False,
                "message": f"Error fetching data: {str(e)}",
                "members": {}
            }