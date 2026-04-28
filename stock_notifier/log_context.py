from __future__ import annotations

import contextvars
import logging

job_log_id: contextvars.ContextVar[str] = contextvars.ContextVar("job_log_id", default="-")


def set_job_log_id(value: str) -> contextvars.Token[str]:
    return job_log_id.set(value)


def reset_job_log_id(token: contextvars.Token[str]) -> None:
    job_log_id.reset(token)


class JobContextFilter(logging.Filter):
    """Injects job_log_id into every log record for text or JSON formatters."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.job_id = job_log_id.get()
        return True
