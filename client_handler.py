# imports
import socket
from enum import Enum

from logger import log
from logger import Severity


# global settings
DEBUG = True
KEYS = {
    0: [ 23019, 32037 ],
    1: [ 32037, 29295 ],
    2: [ 18789, 13603 ],
    3: [ 16443, 29533 ],
    4: [ 18189, 21952 ]
}

class MessageType(Enum):
    CLIENT_USERNAME = 100,
    CLIENT_KEY_ID = 101,
    CLIENT_CONFIRMATION = 102

    UNDEF = 900


class Message:
    def __init__(self):
        self.msg_list = bytes()
        self.type = MessageType.UNDEF

    def get_type(self):
        return self.type

    def set_type(self, new_type):
        self.type = new_type

    def get_str(self):
        return (self.msg_list[:-2]).decode()

    def raw(self):
        return self.msg_list

    def append_char(self, char):
        self.msg_list += char

    def is_valid(self):
        return len(self.msg_list) >= 2 and self.msg_list[-2] is ord('\a') and self.msg_list[-1] is ord('\b')

    @staticmethod
    def parse_key(msg):
        try:
            return int(msg.get_str())
        except ValueError:
            return None


class Handler:
    def __init__(self, thread_id, socket):
        self.thread_id = thread_id
        self.sock = socket

    @staticmethod
    def get_hashes(text, key_pair):
        h = 0
        for s in text:
            h += ord(s)
        h *= 1000
        h %= 65536
        server_hash = (h + key_pair[0]) % 65536
        client_hash = (h + key_pair[1]) % 65536
        return server_hash, client_hash

    def msg(self, message, severity: object = Severity.INFO):
        log('TID:{} - {}'.format(self.thread_id, message), severity)

    def succ(self, msg):
        self.msg(msg, Severity.OK)

    def info(self, msg):
        self.msg(msg, Severity.INFO)

    def err(self, msg):
        self.msg(msg, Severity.ERR)

    def debug(self, msg, severity: object = Severity.INFO):
        if DEBUG:
            self.msg(msg, severity)

    def send(self, msg):
        self.sock.send(msg.encode() + bytes(b'\a\b'))

    def recv(self):
        msg = Message()
        try:
            while not msg.is_valid():
                c = self.sock.recv(1)
                if c is None or len(c) == 0 or c[0] is ord('\0'):
                    self.info('Last accepted char is None')
                    break
                else:
                    msg.append_char(c)
        except socket.timeout:
            self.info('Connection timeout')

        if msg.is_valid():
            self.debug('Accepted Message: {}'.format(msg.get_str()))
        else:
            self.debug('Accepted message was not valid. {}'.format(msg.raw()))

        return msg

    def send_key_request(self):
        self.send("107 KEY REQUEST")

    def send_server_ok(self):
        self.send("200 OK")

    def send_login_failed(self):
        self.send("300 LOGIN FAILED")

    def auth(self):
        self.msg('Auth Init')

        msg = self.recv()
        if msg.is_valid():
            self.succ('Accepted Robot `{}`'.format(msg.get_str()))
        robot_name = msg.get_str()

        self.send_key_request()
        msg = self.recv()
        if not msg.is_valid():
            self.err('Key message syntax error.')
            return False

        key_id = Message.parse_key(msg)
        if key_id is None or key_id not in KEYS:
            self.err('KeyID message contains bad value.')
            return False
        self.succ('Client KeyID is `{}` - {}'.format(key_id, KEYS[key_id]))

        server_hash, client_hash = Handler.get_hashes(robot_name, KEYS[key_id])
        self.send(str(server_hash))

        log('ServerHash: {}, ClientHash: {}'.format(server_hash, client_hash))

        msg = self.recv()
        if not msg.is_valid():
            self.err('Client hash message contains bad value.')
            return False
        client_control_hash = Message.parse_key(msg)
        if client_control_hash is None or client_control_hash != client_hash:
            self.err('Client hash message contains incorrect value.')
            self.send_login_failed()
            return False
        self.send_server_ok()

        return True

    def handle(self):
        if not self.auth():
            self.err('Auth Fail')
            return False

        # get robot to the target [0,0]


def client_handler(thread_id, client_socket):
    handler = Handler(thread_id, client_socket)
    handler.handle()
