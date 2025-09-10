import time
import sys

EPOCH_DIFF = 946684800  # 1970-2000


def unix_localtime(secs=None):
    """修正micropython time.localtime时间偏差"""
    if secs is None:
        secs = time.time()
    return time.gmtime(secs - EPOCH_DIFF)


def log_ts():
    ns = time.time_ns()
    s, ns_remain = divmod(ns, 1_000_000_000)
    ms = ns_remain // 1_000_000

    if sys.platform == "esp32":
        t = unix_localtime(s)
        return "{:04d}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}.{:03d}".format(*t[:6], ms)
    else:
        t = time.localtime()
        return "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}.{:03d}".format(*t[:6], ms)
