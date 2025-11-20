"""
Graph utilities for Torn Faction data visualization
"""

import io
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter
from datetime import datetime, timedelta
from fastapi import HTTPException
from typing import Optional
import requests
import os


WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
if not WEBHOOK_URL:
    raise RuntimeError("DISCORD_WEBHOOK_URL not set in .env")

__all__ = [
    "build_time_range",
    "generate_plot_buffer",
    "send_to_discord",
]

def build_time_range(
    days: Optional[int] = None,
    weeks: Optional[int] = None,
    months: Optional[int] = None,
    years: Optional[int] = None,
) -> tuple[datetime, datetime, str]:
    """
    Returns (start_utc, end_utc, human_description)
    If no params → All Time
    """
    import dateutil.relativedelta
    
    now_utc = datetime.utcnow()  # Naive UTC

    if not any([days, weeks, months, years]):
        return None, None, "All Time"

    delta = dateutil.relativedelta.relativedelta(
        days=days or 0,
        weeks=weeks or 0,
        months=months or 0,
        years=years or 0,
    )
    start_utc = now_utc - delta

    parts = []
    if days: parts.append(f"{days} day" if days == 1 else f"{days} days")
    if weeks: parts.append(f"{weeks} week" if weeks == 1 else f"{weeks} weeks")
    if months: parts.append(f"{months} month" if months == 1 else f"{months} months")
    if years: parts.append(f"{years} year" if years == 1 else f"{years} years")
    desc = ", ".join(parts)

    return start_utc, now_utc, desc


def format_yaxis_commas(ax):
    """Format y-axis labels with commas"""
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{int(x):,}"))


def configure_xaxis(ax, time_diff: timedelta):
    """Configure x-axis based on time range"""
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
    """Generate PNG plot buffer from DataFrame"""
    if df.empty:
        raise HTTPException(status_code=404, detail="No data in selected time range.")

    sns.set_style("whitegrid")
    plt.figure(figsize=(12, 6))
    ax = sns.lineplot(
        data=df, x="ts_utc", y="respect",
        marker="o", linewidth=2.5, markersize=6, color="#1f77b4"
    )

    title = "Faction Respect Over Time (UTC)"
    if time_desc != "All Time":
        title += f" — {time_desc}"
    ax.set_title(title, fontsize=16, pad=20)
    ax.set_xlabel("Date & Time (UTC)", fontsize=12)
    ax.set_ylabel("Respect", fontsize=12)

    format_yaxis_commas(ax)
    time_diff = df["ts_utc"].max() - df["ts_utc"].min()
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
    """Send plot to Discord webhook"""
    today = datetime.utcnow().strftime("%Y-%m-%d")
    content = f"**Respect Report (UTC) - {today}** | {time_desc}"

    files = {"file": ("respect_plot_utc.png", image_buffer, "image/png")}
    payload = {
        "content": content,
        "username": "Torn Informant",
        "avatar_url": "https://i.ibb.co/vxydcJCc/image.png",
    }
    response = requests.post(WEBHOOK_URL, data=payload, files=files)
    return response


def generate_simple_plot(db, days: int = 7) -> io.BytesIO:
    """Generate a simple plot for integration with poller"""
    start_utc = datetime.utcnow() - timedelta(days=days)
    rows = db.fetch_respect_data(start_utc, datetime.utcnow())
    
    if not rows:
        raise ValueError("No data available for plotting")
    
    df = pd.DataFrame(rows, columns=['ts_utc', 'respect'])
    df["ts_utc"] = pd.to_datetime(df["ts_utc"], utc=True)
    
    # Generate simplified plot
    sns.set_style("whitegrid")
    plt.figure(figsize=(10, 5))
    ax = sns.lineplot(
        data=df, x="ts_utc", y="respect",
        marker="o", linewidth=2, markersize=4, color="#1f77b4"
    )
    
    ax.set_title(f"Faction Respect - Last {days} Days", fontsize=14)
    ax.set_xlabel("Date (UTC)", fontsize=10)
    ax.set_ylabel("Respect", fontsize=10)
    
    # Format axes
    format_yaxis_commas(ax)
    time_diff = df["ts_utc"].max() - df["ts_utc"].min()
    configure_xaxis(ax, time_diff)
    
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    buf.seek(0)
    plt.close()
    return buf