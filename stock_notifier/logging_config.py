from __future__ import annotations

import json
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path

from pytz import timezone as tz

from stock_notifier.log_context import JobContextFilter
from stock_notifier.models import AppConfig


class _IstTextFormatter(logging.Formatter):
    def formatTime(self, record: logging.LogRecord, datefmt: str | None = None) -> str:
        return datetime.now(tz("Asia/Kolkata")).strftime(datefmt or "%Y-%m-%d %H:%M:%S")


class _JsonFormatter(logging.Formatter):
    """One JSON object per line; suitable for log aggregators."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.now(tz("Asia/Kolkata")).isoformat(timespec="seconds"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "job_id": getattr(record, "job_id", "-"),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def setup_logging(app: AppConfig, root: Path) -> None:
    log_path = root / app.logs_dir
    log_path.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    if root_logger.handlers:
        return

    job_filter = JobContextFilter()

    text_tmpl = "%(asctime)s : %(levelname)s : %(name)s : %(job_id)s : %(message)s"
    file_fmt: logging.Formatter
    stream_fmt: logging.Formatter
    if app.log_json:
        file_fmt = _JsonFormatter()
        stream_fmt = _JsonFormatter()
    else:
        file_fmt = _IstTextFormatter(text_tmpl)
        stream_fmt = _IstTextFormatter(text_tmpl)

    file_handler = logging.handlers.RotatingFileHandler(
        log_path / "stock_notifier.log",
        maxBytes=app.log_max_bytes,
        backupCount=app.log_backup_count,
        encoding="utf-8",
    )
    file_handler.setFormatter(file_fmt)
    file_handler.addFilter(job_filter)

    stream = logging.StreamHandler()
    stream.setFormatter(stream_fmt)
    stream.addFilter(job_filter)

    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(stream)
