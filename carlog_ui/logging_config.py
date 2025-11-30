"""
Unified logging configuration for Car Log.
Routes all logs (including print) to MLflow span events.
"""
import sys
import logging
from typing import Optional
from opentelemetry import trace

logger = logging.getLogger("carlog")


class MLflowSpanHandler(logging.Handler):
    """
    Logging handler that attaches log messages to active MLflow span.
    Logs appear in MLflow trace UI under "Events" tab.
    """

    def emit(self, record):
        try:
            span = trace.get_current_span()
            if span and span.is_recording():
                span.add_event(
                    name=f"log.{record.levelname.lower()}",
                    attributes={
                        "message": record.getMessage(),
                        "logger": record.name,
                        "level": record.levelname,
                        "filename": record.filename,
                        "lineno": record.lineno,
                    }
                )
        except Exception:
            pass


class StdoutCapture:
    """Redirects stdout/stderr to logging."""

    def __init__(self, logger: logging.Logger, level: int = logging.INFO):
        self.logger = logger
        self.level = level
        self._original = None

    def write(self, message: str):
        if message.strip():
            self.logger.log(self.level, message.strip())

    def flush(self):
        pass

    def isatty(self):
        return self._original.isatty() if self._original else False

    def fileno(self):
        return self._original.fileno() if self._original else 1


def setup_logging(
    level: int = logging.INFO,
    capture_stdout: bool = True,
    mlflow_enabled: bool = True,
) -> logging.Logger:
    """Initialize unified logging for Car Log."""
    logging.basicConfig(
        level=level,
        format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    if mlflow_enabled:
        try:
            handler = MLflowSpanHandler()
            handler.setLevel(level)
            logging.getLogger().addHandler(handler)
            logger.info("MLflow span logging enabled")
        except Exception as e:
            logger.warning(f"MLflow span logging not available: {e}")

    if capture_stdout:
        stdout_capture = StdoutCapture(logging.getLogger("stdout"), logging.INFO)
        stdout_capture._original = sys.stdout
        sys.stdout = stdout_capture

        stderr_capture = StdoutCapture(logging.getLogger("stderr"), logging.ERROR)
        stderr_capture._original = sys.stderr
        sys.stderr = stderr_capture

        logger.info("stdout/stderr capture enabled")

    return logger


def wait_for_mlflow(url: str, timeout: int = 60, interval: int = 2) -> bool:
    """Wait for MLflow to be ready before initializing logging."""
    import time
    import requests

    start = time.time()
    while time.time() - start < timeout:
        try:
            response = requests.get(f"{url}/health", timeout=5)
            if response.status_code == 200:
                logger.info(f"MLflow ready at {url}")
                return True
        except Exception:
            pass

        logger.info(f"Waiting for MLflow at {url}...")
        time.sleep(interval)

    logger.warning(f"MLflow not ready after {timeout}s, continuing without MLflow logging")
    return False
