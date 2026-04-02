from enum import IntEnum


class TaskPriority(IntEnum):
    """Device Task Priority"""

    HIGH = 3
    MEDIUM = 2
    LOW = 1


class DeviceType(IntEnum):
    """Device Type"""

    SENSOR = 50
    GATEWAY = 100


class TaskState(IntEnum):
    INIT = 0
    CONNECT_START = 1
    CONNECTED = 2
    EXECUTING = 3
    FAILED = 4
    SUCCESS = 5


class ChipId(IntEnum):
    NOP = -1
    H0 = 0
    H1 = 1
