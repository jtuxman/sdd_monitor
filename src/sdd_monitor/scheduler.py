import logging
import signal
import threading
from pathlib import Path

from apscheduler.schedulers.blocking import BlockingScheduler

from sdd_monitor import collector, presentation, processor
from sdd_monitor.storage import Storage

logger = logging.getLogger(__name__)

_shutdown_event = threading.Event()


def _poll_cycle(devices: list[dict], storage: Storage) -> None:
    try:
        raw = collector.collect(devices)
        metrics = processor.process(raw)
        if metrics:
            storage.insert(metrics)
        presentation.render(metrics)
    except Exception as exc:
        logger.error("Error en ciclo de polling: %s", exc)


def run(config_path: str | Path, db_path: str | Path, interval: int) -> None:
    devices = collector.load_devices(config_path)

    storage = Storage(db_path)

    def handle_signal(signum: int, _frame: object) -> None:
        logger.info("Señal %s recibida, deteniendo scheduler...", signum)
        _shutdown_event.set()
        sched.shutdown(wait=False)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    sched = BlockingScheduler()
    sched.add_job(
        _poll_cycle,
        "interval",
        seconds=interval,
        args=[devices, storage],
        next_run_time=__import__("datetime").datetime.now(),
        max_instances=1,
        coalesce=True,
    )

    logger.info(
        "SDD Monitor iniciado — %d dispositivo(s), intervalo %ds",
        len(devices),
        interval,
    )
    try:
        sched.start()
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        storage.close()
        logger.info("SDD Monitor detenido.")
