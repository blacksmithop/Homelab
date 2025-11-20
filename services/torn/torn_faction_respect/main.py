
from contextlib import asynccontextmanager
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
import pandas as pd
from typing import Optional
import os
from dotenv import load_dotenv

from utils.database import DatabaseManager
from utils.graph import build_time_range, generate_plot_buffer, send_to_discord
from utils.poller import TornPoller

load_dotenv()

# Global poller instance
poller = TornPoller()

# Database manager
db = DatabaseManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage background tasks on startup and shutdown"""
    # Startup: Start poller
    poller.start()
    
    yield  # App runs here
    
    # Shutdown: Stop poller
    poller.stop()

app = FastAPI(
    title="Torn Faction Respect → Discord (UTC)",
    version="2.0",
    description="Combined API server with background data polling",
    lifespan=lifespan
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
        "message": "Torn Faction Respect Monitor (UTC)",
        "endpoints": {
            "/": "This info",
            "/plot": "Send plot to Discord",
            "/graph": "Get plot as PNG image",
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
            "PostgreSQL data storage"
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)