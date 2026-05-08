import logging
import os
from pathlib import Path

from dotenv import load_dotenv

from sdd_monitor import scheduler

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


def main() -> None:
    config_path = Path("config/devices.yaml")
    db_path = Path(os.getenv("DB_PATH", "data/metrics.db"))
    html_path = Path(os.getenv("HTML_PATH", "data/report.html"))
    interval = int(os.getenv("POLL_INTERVAL", "60"))

    scheduler.run(config_path, db_path, html_path, interval)


if __name__ == "__main__":
    main()
