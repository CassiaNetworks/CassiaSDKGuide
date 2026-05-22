import time
timestamp = int(time.time())
try:
    tm = (0, 0, 0, 0, 0, 0, 0, 0, -1)
    timestamp = int(time.mktime(tm))
    print(f"Success: {timestamp}")
except Exception as e:
    print(f"Exception: {e}")
