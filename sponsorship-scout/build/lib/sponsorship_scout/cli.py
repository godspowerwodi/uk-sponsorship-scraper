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
    abs_config = os.path.abspath(config)
    cfg = load_config(abs_config)
    asyncio.run(run_engine(cfg))

def run_job(config_path: str):
    print("Running scheduled scrape...")
    cfg = load_config(os.path.abspath(config_path))
    asyncio.run(run_engine(cfg))

@app.command()
def start_schedule(config: str = "config.yaml", hours: int = 24):
    """Run the scraper on a continuous schedule."""
    abs_config = os.path.abspath(config)
    print(f"Starting scheduler. Will run every {hours} hours using config {abs_config}.")
    schedule.every(hours).hours.do(run_job, config_path=abs_config)
    while True:
        schedule.run_pending()
        time.sleep(60)

@app.command()
def ui(config: str = "config.yaml", port: int = 8501):
    """Launch the Streamlit web dashboard."""
    ui_path = os.path.join(os.path.dirname(__file__), "ui", "app.py")
    # Pass absolute config path as an environment variable to streamlit
    os.environ['SPONSOR_SCOUT_CONFIG'] = os.path.abspath(config)
    subprocess.run([sys.executable, "-m", "streamlit", "run", ui_path, "--server.port", str(port)])

if __name__ == "__main__":
    app()
