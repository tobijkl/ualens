"""Logging configuration: file + queue for TUI display."""

import logging
import queue
from pathlib import Path

try:
    import platformdirs
    _LOG_DIR = Path(platformdirs.user_log_dir("ualens", "ualens"))
except ImportError:
    _LOG_DIR = Path.home() / ".local" / "share" / "ualens" / "logs"

# Queue for log records to be displayed in TUI (thread-safe)
log_queue: queue.Queue[str] = queue.Queue()


class QueueLogHandler(logging.Handler):
    """Handler that puts log records into a queue for TUI display."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            log_queue.put_nowait(msg)
        except Exception:
            self.handleError(record)


def configure_logging() -> None:
    """Configure logging: file + queue for TUI."""
    _LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = _LOG_DIR / "app.log"
    fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    formatter = logging.Formatter(fmt)
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    queue_handler = QueueLogHandler()
    queue_handler.setFormatter(formatter)
    logging.basicConfig(level=logging.INFO, format=fmt, handlers=[file_handler, queue_handler])
    # asyncua is very chatty at INFO level; only surface warnings and errors in the TUI.
    logging.getLogger("asyncua").setLevel(logging.WARNING)
