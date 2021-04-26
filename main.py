# imports
import socket
from logger import log, Severity

# global settings
HOST = '127.0.0.1'
PORT = 61222

STAGES = {
    'server_init': 'Server Init',
    'server_run': 'Server Run',
    'server_shutdown': 'Server Shutdown'
}


# CONTROL VARS
ACTIVE_STAGE_NAME = ''
ERROR = False
SHUTDOWN_IN_PROGRESS = False


# implementation
def stage_start(stage_name):
    global ACTIVE_STAGE_NAME
    ACTIVE_STAGE_NAME = stage_name
    log('{} Start'.format(STAGES[stage_name]))


def stage_done(severity: object = Severity.OK):
    log('{} Done'.format(STAGES[ACTIVE_STAGE_NAME]), severity)


if __name__ == '__main__':
    try:
        stage_start('server_init')
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((HOST, PORT))
        server.listen()
        stage_done()

        stage_start('server_run')
        # listen
        stage_done()

        # shutdown
        stage_start('server_shutdown')
        server.close()
        stage_done()
    except Exception as e:
        log('Critical error occurred - {}. Exiting...'.format(e), Severity.ERR)
