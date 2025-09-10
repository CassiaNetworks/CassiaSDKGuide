class Error:
    OK = "OK"
    EMPTY = "Empty"
    TASK_TIMEOUT_BY_SCHEDULER = "TaskTimeoutByScheduler"
    MODEL_NOT_SUPPORT = "ModelNotSupport"

    GATEWAY_PARAMETER_INVALID = "GatewayParameterInvalid"
    GATEWAY_SERVICE_NOT_FOUND = "GatewayServiceNotFound"
    GATEWAY_PLEASE_SET_BYPASS_PARAMS_FIRST = "GatewayPleaseSetBypassParamsFirst"
    GATEWAY_TYPE_NOT_SUPPORTED = "GatewayTypeNotSupported"
    GATEWAY_OPERATION_NOT_SUPPORTED = "GatewayOperationNotSupported"
    GATEWAY_MEMORY_ALLOC_ERROR = "GatewayMemoryAllocError"
    GATEWAY_NO_RESOURCES = "GatewayNoResources"
    GATEWAY_AUTHENTICATE_MISS_KEY = "GatewayAuthenticateMisskey"
    GATEWAY_NEED_PAIR_OPERATION = "GatewayNeedPairOperation"
    GATEWAY_PAIR_IN_PROCESS = "GatewayPairInProcess"
    GATEWAY_ATT_INSUFFICIENT_AUTHENTICATION = "GatewayAttInsufficientAuthorication"
    GATEWAY_ATT_INSUFFICIENT_AUTHORIZATION = "GatewayAttInsufficientAuthorization"
    GATEWAY_ATT_INSUFFICIENT_ENCRYPTION = "GatewayAttInsufficientEncryption"
    GATEWAY_CHIP_IS_NOT_READY = "GatewayChipIsNotReady"
    GATEWAY_INCORRECT_MODE = "GatewayIncorrectMode"
    GATEWAY_CHIP_IS_BUSY = "GatewayChipIsBusy"
    GATEWAY_DEVICE_NOT_FOUND = "GatewayDeviceNotFound"
    GATEWAY_DEVICE_NOT_SCAN = "GatewayDeviceNotScan"
    GATEWAY_DEVICE_DISCONNECTING = "GatewayDeviceDisconnecting"
    GATEWAY_DEVICE_CAN_NOT_SCAN = "GatewayDeviceCanNotScan"
    GATEWAY_DEVICE_DISCONNECT = "GatewayDeviceDisconnect"
    GATEWAY_HOST_DISCONNECT = "GatewayHostDisconnect"
    GATEWAY_CONNECT_FAILED = "GatewayConnectFailed"
    GATEWAY_FAILURE = "GatewayFailure"
    GATEWAY_OPERATION_TIMEOUT = "GatewayOperationTimeout"

    ERROR_MAP = {
        "parameter invalid": GATEWAY_PARAMETER_INVALID,
        "Service not found": GATEWAY_SERVICE_NOT_FOUND,
        "please set bypass params first": GATEWAY_PLEASE_SET_BYPASS_PARAMS_FIRST,
        "type not supported": GATEWAY_TYPE_NOT_SUPPORTED,
        "operation not supported": GATEWAY_OPERATION_NOT_SUPPORTED,
        "memory alloc error": GATEWAY_MEMORY_ALLOC_ERROR,
        "no resources": GATEWAY_NO_RESOURCES,
        "authenticate miss key": GATEWAY_AUTHENTICATE_MISS_KEY,
        "need pair operation": GATEWAY_NEED_PAIR_OPERATION,
        "pair in process": GATEWAY_PAIR_IN_PROCESS,
        "ATT insufficient Authentication": GATEWAY_ATT_INSUFFICIENT_AUTHENTICATION,
        "ATT insufficient Authorization": GATEWAY_ATT_INSUFFICIENT_AUTHORIZATION,
        "ATT insufficient Encryption": GATEWAY_ATT_INSUFFICIENT_ENCRYPTION,
        "chip is not ready": GATEWAY_CHIP_IS_NOT_READY,
        "incorrect mode": GATEWAY_INCORRECT_MODE,
        "chip is busy": GATEWAY_CHIP_IS_BUSY,
        "device not found": GATEWAY_DEVICE_NOT_FOUND,
        "device not scan": GATEWAY_DEVICE_NOT_SCAN,
        "device disconnecting": GATEWAY_DEVICE_DISCONNECTING,
        "device can not scan": GATEWAY_DEVICE_CAN_NOT_SCAN,
        "device disconnect": GATEWAY_DEVICE_DISCONNECT,
        "host disconnect": GATEWAY_HOST_DISCONNECT,
        "connect failed": GATEWAY_CONNECT_FAILED,
        "failure": GATEWAY_FAILURE,
        "operation timeout": GATEWAY_OPERATION_TIMEOUT,
    }

    @staticmethod
    def from_cassiablue_ret(ret: str) -> str:
        return Error.ERROR_MAP.get(ret, ret)
