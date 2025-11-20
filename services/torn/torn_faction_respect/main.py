from contextlib import asynccontextmanager
from fastapi import FastAPI, Query, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
import pandas as pd
from dotenv import load_dotenv
from typing import Optional, Dict, Any
from utils.database import DatabaseManager
from utils.graph import build_time_range, generate_plot_buffer, send_to_discord
from utils.poller import TornPoller
from utils.crime_pass_rate import CPRManager

load_dotenv()

# Global instances
poller = TornPoller()
db = DatabaseManager()
cpr_manager = CPRManager()

async def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")):
    """Verify API key for CPR endpoints"""
    if not await cpr_manager.validate_api_key(x_api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage background tasks on startup and shutdown"""
    # Startup: Initialize databases and start poller
    db.init_db()
    cpr_manager.init_db()
    poller.start()
    
    yield  # App runs here
    
    # Shutdown: Stop poller
    poller.stop()

app = FastAPI(
    title="Torn Faction Respect → Discord (UTC)",
    version="2.0",
    description="Combined API server with background data polling and Crime Pass Rate tracking",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://oc.tornrevive.page", "http://localhost:3000"],
    allow_methods=["OPTIONS", "HEAD", "GET", "POST"],
    allow_headers=["*"],
)

def fetch_data(start_utc=None, end_utc=None):
    """Fetch data using DatabaseManager and convert to DataFrame"""
    rows = db.fetch_respect_data(start_utc, end_utc)

    if not rows:
        return pd.DataFrame(columns=["ts_utc", "respect"])

    df = pd.DataFrame(rows, columns=["ts_utc", "respect"])
    df["ts_utc"] = pd.to_datetime(df["ts_utc"], utc=True)
    return df


@app.get("/plot")
async def plot_respect(
    days: Optional[int] = Query(None, ge=0),
    weeks: Optional[int] = Query(None, ge=0),
    months: Optional[int] = Query(None, ge=0),
    years: Optional[int] = Query(None, ge=0),
):
    """Send plot to Discord webhook"""
    start_utc, end_utc, time_desc = build_time_range(days, weeks, months, years)
    df = fetch_data(start_utc, end_utc)
    img_buf = generate_plot_buffer(df, time_desc)

    resp = send_to_discord(img_buf, time_desc)

    if resp.status_code == 204:
        return JSONResponse(
            {
                "status": "success",
                "message": f"Plot sent to Discord: {time_desc}",
                "range": time_desc,
                "timezone": "UTC",
            }
        )
    else:
        raise HTTPException(
            status_code=500, detail=f"Discord error: {resp.status_code} {resp.text}"
        )


@app.get("/graph")
async def graph_respect(
    days: Optional[int] = Query(None, ge=0),
    weeks: Optional[int] = Query(None, ge=0),
    months: Optional[int] = Query(None, ge=0),
    years: Optional[int] = Query(None, ge=0),
):
    """Return PNG image directly"""
    start_utc, end_utc, time_desc = build_time_range(days, weeks, months, years)
    df = fetch_data(start_utc, end_utc)
    img_buf = generate_plot_buffer(df, time_desc)

    return StreamingResponse(
        img_buf,
        media_type="image/png",
        headers={
            "Cache-Control": "no-cache",
            "Content-Disposition": f'inline; filename="respect_{time_desc.lower().replace(" ", "_")}.png"',
        },
    )


# Crime Pass Rate Endpoints
@app.post("/cpr/submit")
async def submit_cpr_data(
    checkpoint_pass_rates: Dict[str, Any],
    api_key: str = Depends(verify_api_key)
):
    """Submit crime pass rate data"""
    success = await cpr_manager.store_cpr_data(api_key, checkpoint_pass_rates)
    
    if success:
        return {
            "status": "success",
            "message": "CPR data stored successfully"
        }
    else:
        raise HTTPException(
            status_code=500, 
            detail="Failed to store CPR data"
        )

@app.get("/cpr/user")
async def get_user_cpr_data(
    scenario_name: Optional[str] = None,
    api_key: str = Depends(verify_api_key)
):
    """Get CPR data for a specific user"""
    try:
        data = await cpr_manager.get_cpr_data(api_key, scenario_name)
        return {
            "status": "success",
            "api_key": api_key,
            "scenario_filter": scenario_name,
            "data": data
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error retrieving CPR data: {str(e)}"
        )


@app.get("/cpr/faction/{faction_id}")
async def get_faction_cpr_data(
    faction_id: int,
    api_key: str = Depends(verify_api_key)
):
    """Get aggregated CPR data for a faction"""
    try:
        # First verify the API key belongs to someone in this faction
        verify_query = """
            SELECT faction_id FROM cpr_users WHERE api_key = %s
        """
        result = cpr_manager.execute_query(verify_query, (api_key,), fetch=True)
        
        if not result or result[0][0] != faction_id:
            raise HTTPException(
                status_code=403, 
                detail="Access denied: API key not associated with this faction"
            )
        
        data = await cpr_manager.get_faction_cpr_data(faction_id)
        return {
            "status": "success",
            "faction_id": faction_id,
            "data": data
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error retrieving faction CPR data: {str(e)}"
        )


@app.get("/cpr/faction/{faction_id}/members")
async def get_faction_cpr_members_format(
    faction_id: int,
    api_key: str = Depends(verify_api_key)
):
    """Get faction CPR data in member-based format"""
    try:
        # First verify the API key belongs to someone in this faction
        verify_query = """
            SELECT faction_id FROM cpr_users WHERE api_key = %s
        """
        result = cpr_manager.execute_query(verify_query, (api_key,), fetch=True)
        
        if not result or result[0][0] != faction_id:
            raise HTTPException(
                status_code=403, 
                detail="Access denied: API key not associated with this faction"
            )
        
        data = await cpr_manager.get_faction_cpr_members_format(faction_id)
        return data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error retrieving faction CPR members data: {str(e)}"
        )


# Poller Endpoints
@app.get("/poller/status")
async def get_poller_status():
    """Get the status of the background poller"""
    return poller.get_status()


@app.post("/poller/trigger")
async def trigger_poller():
    """Manually trigger a poller run"""
    try:
        poller.fetch_and_save()
        return {"status": "success", "message": "Poller executed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Poller error: {str(e)}")


@app.post("/poller/start")
async def start_poller():
    """Start the background poller"""
    poller.start()
    return {"status": "success", "message": "Poller started"}


@app.post("/poller/stop")
async def stop_poller():
    """Stop the background poller"""
    poller.stop()
    return {"status": "success", "message": "Poller stopped"}


@app.get("/")
def root():
    return {
        "message": "Torn Faction Respect Monitor (UTC) with Crime Pass Rate Tracking",
        "endpoints": {
            "/": "This info",
            "/plot": "Send plot to Discord",
            "/graph": "Get plot as PNG image",
            "/cpr/submit": "Submit crime pass rate data",
            "/cpr/user": "Get user CPR data",
            "/cpr/faction/{faction_id}": "Get faction CPR data",
            "/poller/status": "Check poller status",
            "/poller/trigger": "Manually trigger data fetch",
            "/poller/start": "Start background poller",
            "/poller/stop": "Stop background poller",
            "/docs": "Interactive API docs",
        },
        "version": "2.0",
        "features": [
            "Background data polling (every 1 hour)",
            "Discord webhook integration",
            "Real-time graphing",
            "PostgreSQL data storage",
            "Crime Pass Rate tracking"
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)