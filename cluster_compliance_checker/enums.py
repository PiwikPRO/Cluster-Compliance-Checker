from enum import Enum


class MonthlyTraffic(str, Enum):
    _10M = "10"
    _50M = "50"
    _100M = "100"
    _250M = "250"
    _500M = "500"


class MaintenanceType(str, Enum):
    REMOTE_ACCESS = "remote-access"
    SELF_SUPPORT = "self-support"


class LogLevel(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARN = "warn"
    ERROR = "error"


class Phase(str, Enum):
    PRE_CONTRACT = "pre-contract"
    PRE_INSTALL = "pre-install"
