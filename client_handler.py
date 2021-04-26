# imports
from logger import log


class Handler:
    def __init__(self, thread_id, socket):
        self.thread_id = thread_id
        self.s = socket

    def auth(self):
        self.msg('Auth Init')

    def msg(self, message):
        log('TID:{} - {}'.format(self.thread_id, message))


def client_handler(thread_id, client_socket):
    handler = Handler(thread_id, client_socket)
    handler.auth()
