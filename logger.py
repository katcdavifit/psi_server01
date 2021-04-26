# imports
from enum import Enum
import time

# global settings
PROGRAM_START_STAMP = None
PREFIX = 3


class Severity(Enum):
    OK = 'SUCC'
    ERR = 'ERRO'
    INFO = 'INFO'


def init_log():
    global PROGRAM_START_STAMP
    PROGRAM_START_STAMP = time.time()


def format_time(t):
    st = '{:.3f}'.format(t)
    parts = st.split('.')
    return '{}.{}'.format(parts[0].zfill(PREFIX), parts[1])


def get_time():
    current = time.time()
    return format_time(current - PROGRAM_START_STAMP)


def log(message, severity: object = Severity.INFO):
    print('[*][{}][{}] {}'.format(severity.value, get_time(), message))
