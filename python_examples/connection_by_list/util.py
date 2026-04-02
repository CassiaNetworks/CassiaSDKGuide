from datetime import datetime


def get_timestamp():
    """UTC Timestamp(Second)"""
    return datetime.now().timestamp()


def get_timestamp_str():
    """20250323152730"""
    now = datetime.now()
    return now.strftime("%Y%m%d%H%M%S")
