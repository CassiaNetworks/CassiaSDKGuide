def gateway_type():
    return "M2000"


def gateway_mac():
    return "00:00:00:00:00:00"


def gateway_ver():
    return ""


USER_CONFIG = ""


def save_user_config(content):
    global USER_CONFIG
    USER_CONFIG = content


def read_user_config():
    global USER_CONFIG
    return USER_CONFIG
