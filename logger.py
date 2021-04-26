# imports
from enum import Enum
import time

PROGRAM_START_STAMP = None
ROUND_FACTOR = 4


class Severity(Enum):
    OK = 'SUCC'
    ERR = 'ERRO'
    INFO = 'INFO'


def init_log():
    global PROGRAM_START_STAMP
    PROGRAM_START_STAMP = time.time()


def get_time():
    current = time.time()
    return current - PROGRAM_START_STAMP


def log(message, severity: object = Severity.INFO):
    print('[*][{:.3f}][{}] {}'.format(get_time(), severity.value, message))

