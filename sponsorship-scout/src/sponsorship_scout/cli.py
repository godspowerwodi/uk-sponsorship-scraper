import typer
import asyncio
import schedule
import time
import os
import subprocess
import sys

from .core.config import load_config
from .core.engine import run_engine

app = typer.Typer(help="Sponsorship Scout CLI")

@app.command()
def run(config: str = "config.yaml"):
    """Run the scraper once."""
    cfg = load_config(config)
    asyncio.run(run_engine(cfg))

def run_job(config_path: str):
    print("Running scheduled scrape...")
    cfg = load_config(config_path)
    asyncio.run(run_engine(cfg))

@app.command()
def start_schedule(config: str = "config.yaml", hours: int = 24):
    """Run the scraper on a continuous schedule."""
    print(f"Starting scheduler. Will run every {hours} hours using config {config}.")
    schedule.every(hours).hours.do(run_job, config_path=config)
    while True:
        schedule.run_pending()
        time.sleep(60)

@app.command()
def ui(config: str = "config.yaml"):
    """Launch the Streamlit web dashboard."""
    ui_path = os.path.join(os.path.dirname(__file__), "ui", "app.py")
    # Pass config path as an environment variable to streamlit
    os.environ['SPONSOR_SCOUT_CONFIG'] = config
    subprocess.run([sys.executable, "-m", "streamlit", "run", ui_path])

if __name__ == "__main__":
    app()
