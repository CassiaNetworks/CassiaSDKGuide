import logging
import sys
import asyncio
import os

LOG_LEVEL = {
    "CRITICAL": logging.CRITICAL,
    "FATAL": logging.FATAL,
    "ERROR": logging.ERROR,
    "WARNING": logging.WARNING,
    "WARN": logging.WARN,
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
    "NOTSET": logging.NOTSET,
}

log_level = LOG_LEVEL.get(os.getenv("LOG_LEVEL")) or logging.INFO


class AsyncioTaskFilter(logging.Filter):
    def filter(self, record):
        record.task_name = "main"

        try:
            current_task = asyncio.current_task()
            record.task_name = current_task.get_name()
        except Exception as ex:
            pass
        return True


class AppLogger:
    def __init__(self, name="app"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(log_level)

        if self.logger.handlers:
            return

        formatter = logging.Formatter(
            "[%(asctime)s] [%(name)s] [%(levelname)s] [%(task_name)s] %(message)s"
        )
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.addFilter(AsyncioTaskFilter())
        self.logger.addHandler(console_handler)

    def get_logger(self):
        return self.logger


logger = AppLogger().get_logger()
