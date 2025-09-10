from cassia_time import log_ts


class Logger:
    LEVELS = {
        "DEBUG": 10,
        "INFO": 20,
        "WARN": 30,
        "ERROR": 40,
    }

    def __init__(self, name, level="INFO"):
        self.name = name
        self.level = self.LEVELS.get(level, self.LEVELS["INFO"])

    def _log(self, level_name, *args, **kw):
        if self.LEVELS[level_name] < self.level:
            return

        ts = log_ts()

        print(f"[{ts}] [{level_name}] [{self.name}]", *args, **kw)

    def debug(self, *a, **k):
        self._log("DEBUG", *a, **k)

    def info(self, *a, **k):
        self._log("INFO", *a, **k)

    def warn(self, *a, **k):
        self._log("WARN", *a, **k)

    def error(self, *a, **k):
        self._log("ERROR", *a, **k)


def get_logger(name: str, level="INFO") -> Logger:
    return Logger(name, level)
