#!/usr/bin/env python3
"""
FastAPI: /plot?days=3&weeks=1 → sends respect plot to Discord webhook
Returns JSON status
"""

from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter
from datetime import datetime, timedelta, timezone
import dateutil.relativedelta
import psycopg2
import io
import os
import requests
from dotenv import load_dotenv

load_dotenv()

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
if not WEBHOOK_URL:
    raise RuntimeError("DISCORD_WEBHOOK_URL not set in .env")
app = FastAPI(title="Torn Faction Respect → Discord", version="1.0")
DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "postgres"),
    "database": os.getenv("POSTGRES_DB"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "port": int(os.getenv("POSTGRES_PORT", 5432)),
}


def parse_time_range_from_params(
    days: int = 0, weeks: int = 0, months: int = 0, years: int = 0
):
    now_ist = datetime.now().astimezone(timezone(timedelta(hours=5, minutes=30)))
    delta = dateutil.relativedelta.relativedelta(
        days=days, weeks=weeks, months=months, years=years
    )
    return now_ist - delta, now_ist


def fetch_data_from_db(start_ist=None, end_ist=None):
    conn = psycopg2.connect(**DB_CONFIG)
    query = """
        SELECT ts AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata' AS ts_ist,
               respect
        FROM faction_log
        WHERE (%s IS NULL OR ts_ist >= %s)
          AND (%s IS NULL OR ts_ist <= %s)
        ORDER BY ts_ist
    """
    df = pd.read_sql(query, conn, params=(start_ist, start_ist, end_ist, end_ist))
    conn.close()
    return df


def format_yaxis_commas(ax):
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{int(x):,}"))


def configure_xaxis(ax, time_diff: timedelta):
    if time_diff <= timedelta(days=2):
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d\n%I %p"))
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=6))
    elif time_diff <= timedelta(days=14):
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
        ax.xaxis.set_major_locator(mdates.DayLocator())
    elif time_diff <= timedelta(days=90):
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=3))
    else:
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
        ax.xaxis.set_major_locator(mdates.MonthLocator())


def generate_plot_buffer(df: pd.DataFrame, time_desc: str) -> io.BytesIO:
    if df.empty:
        raise HTTPException(status_code=404, detail="No data in selected time range.")

    sns.set_style("whitegrid")
    plt.figure(figsize=(12, 6))
    ax = sns.lineplot(
        data=df,
        x="ts_ist",
        y="respect",
        marker="o",
        linewidth=2.5,
        markersize=6,
        color="#1f77b4",
    )

    title = "Faction Respect Over Time"
    if time_desc != "All Time":
        title += f" ({time_desc})"
    ax.set_title(title, fontsize=16, pad=20)
    ax.set_xlabel("Date & Time (IST)", fontsize=12)
    ax.set_ylabel("Respect", fontsize=12)

    format_yaxis_commas(ax)
    time_diff = df["ts_ist"].max() - df["ts_ist"].min()
    configure_xaxis(ax, time_diff)

    plt.xticks(rotation=0, ha="center")
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.15)

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=300, bbox_inches="tight")
    buf.seek(0)
    plt.close()
    return buf


def send_to_discord(image_buffer: io.BytesIO, time_desc: str):
    today = (
        datetime.now()
        .astimezone(timezone(timedelta(hours=5, minutes=30)))
        .strftime("%d-%m-%Y")
    )
    content = f"**Respect Report - {today}** | {time_desc}"

    files = {"file": ("respect_plot.png", image_buffer, "image/png")}
    payload = {
        "content": content,
        "username": "Torn Informant",
        "avatar_url": "https://i.ibb.co/vxydcJCc/image.png",
    }

    response = requests.post(WEBHOOK_URL, data=payload, files=files)
    return response


@app.get("/plot")
def plot_respect(
    days: Optional[int] = Query(None, ge=0, description="Number of days"),
    weeks: Optional[int] = Query(None, ge=0, description="Number of weeks"),
    months: Optional[int] = Query(None, ge=0, description="Number of months"),
    years: Optional[int] = Query(None, ge=0, description="Number of years"),
):
    """
    Generate respect plot and send to Discord webhook.
    Returns JSON status.
    """
    parts = []
    if days:
        parts.append(f"{days} day" if days == 1 else f"{days} days")
    if weeks:
        parts.append(f"{weeks} week" if weeks == 1 else f"{weeks} weeks")
    if months:
        parts.append(f"{months} month" if months == 1 else f"{months} months")
    if years:
        parts.append(f"{years} year" if years == 1 else f"{years} years")
    time_desc = ", ".join(parts) if parts else "All Time"

    start_ist = end_ist = None
    if any([days, weeks, months, years]):
        start_ist, end_ist = parse_time_range_from_params(
            days=days or 0, weeks=weeks or 0, months=months or 0, years=years or 0
        )

    df = fetch_data_from_db(start_ist, end_ist)
    img_buf = generate_plot_buffer(df, time_desc)

    resp = send_to_discord(img_buf, time_desc)

    if resp.status_code == 204:
        return JSONResponse(
            {
                "status": "success",
                "message": f"Plot sent to Discord: {time_desc}",
                "range": time_desc,
            }
        )
    else:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send to Discord: {resp.status_code} {resp.text}",
        )


@app.get("/")
def root():
    return {"message": "Torn → Discord Plotter", "docs": "/docs"}
