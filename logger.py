# imports
from enum import Enum


class Severity(Enum):
    OK = 'OK'
    ERR = 'ERR'
    INFO = 'INFO'


def log(message, severity: object = Severity.INFO):
    print('[*][{}] {}'.format(severity.value, message))

