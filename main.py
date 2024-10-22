# imports
import socket
import uuid
import traceback
import threading

from logger import log, Severity, init_log
from client_handler import client_handler

# global settings
HOST = '192.168.58.1'
PORT = 61222
CLIENT_SOCKET_TIMEOUT = 1
STAGES = {
    'server_init': 'Server Init',
    'server_run': 'Server Run',
    'server_shutdown': 'Server Shutdown'
}
DEFAULT_IDLE_TIMEOUT = 300


# control variables
SERVER = None
ACTIVE_STAGE_NAME = ''
ERROR = False
SHUTDOWN_IN_PROGRESS = False


# implementation
def stage_start(stage_name):
    global ACTIVE_STAGE_NAME
    ACTIVE_STAGE_NAME = stage_name
    log('{} Start.'.format(STAGES[stage_name]))


def stage_done(severity: object = Severity.OK):
    log('{} Done.'.format(STAGES[ACTIVE_STAGE_NAME]), severity)


if __name__ == '__main__':
    init_log()

    try:
        stage_start('server_init')
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((HOST, PORT))
        server.settimeout(DEFAULT_IDLE_TIMEOUT)
        server.listen(1)
        SERVER = server
        stage_done()

        stage_start('server_run')
        while not SHUTDOWN_IN_PROGRESS:
            try:
                (client_socket, address) = server.accept()
                thread_id = str(uuid.uuid4())[:4]
                client_socket.settimeout(CLIENT_SOCKET_TIMEOUT)
                threading.Thread(target=client_handler, args=(thread_id, client_socket)).start()
            except socket.timeout:
                SHUTDOWN_IN_PROGRESS = True
                log('Timeout. Shutdown initiated.')
            # does not work on Windows machines
            except KeyboardInterrupt:
                print('Interrupt')
                SHUTDOWN_IN_PROGRESS = True

        if SHUTDOWN_IN_PROGRESS:
            stage_done()
        else:
            stage_done(Severity.ERR)

        # shutdown
        stage_start('server_shutdown')
        server.close()
        stage_done()
    except Exception as e:
        log('Critical error occurred - {}. Exiting...'.format(e), Severity.ERR)
        traceback.print_exc()
