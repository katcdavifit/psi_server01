# imports
import socket
from enum import Enum
import re

from logger import log
from logger import Severity
from navigation import get_direction, get_target_direction, rotate_right, direction_to_str

# global settings
DEBUG = False
KEYS = {
    0: [23019, 32037],
    1: [32037, 29295],
    2: [18789, 13603],
    3: [16443, 29533],
    4: [18189, 21952]
}


class MessageDescription(Enum):
    CLIENT_USERNAME = [
        20,
        '^.*$'
    ]

    CLIENT_KEY_ID = [
        5,
        '^\d{1,3}$'
    ]

    CLIENT_CONFIRMATION = [
        7,
        '^\d{1,5}$'
    ]

    CLIENT_OK = [
        12,
        '^OK [-]?\d+ [-]?\d+$'
    ]

    CLIENT_RECHARGING = [
        12,
        '^RECHARGING$'
    ]

    CLIENT_FULL_POWER = [
        12,
        '^FULL POWER$'
    ]

    CLIENT_MESSAGE = [
        100,
        '^.*$'
    ]


class Message:
    def __init__(self):
        self.msg_list = bytes()

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

    def len(self):
        return len(self.msg_list)

    def get_coords(self):
        try:
            form = re.search('OK [-]?\d+ [-]?\d+', self.get_str())
            if form is None:
                return []
            nums = re.findall('[-]?\d+', self.get_str())
            return [int(nums[0]), int(nums[1])]
        except IndexError:
            return None

    def is_valid2(self, message_description):
        try:
            type = message_description.value
            result = len(self.msg_list) >= 2
            result = result and len(self.msg_list) <= type[0]
            re_result = re.search(type[1], self.get_str())
            result = result and re_result is not None
            result = result and self.msg_list[-2] is ord('\a')
            result = result and self.msg_list[-1] is ord('\b')
            return result
        except Exception as err:
            print(err)

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

    def recv(self, expected):
        msg = Message()
        try:
            while not msg.is_valid():
                c = self.sock.recv(1)
                if c is None or len(c) == 0:
                    if DEBUG:
                        self.info('Last accepted char is None')
                    break
                else:
                    msg.append_char(c)

                if msg.is_valid():
                    if DEBUG:
                        self.info('Msg is valid. Stop recv now.')
                    break

                if msg.len() >= expected:
                    if DEBUG:
                        self.info('Msg too long. Stop recv now.')
                    break
        except socket.timeout:
            self.info('Connection timeout')
            self.sock.close()

        if msg.is_valid():
            if DEBUG:
                self.debug('Accepted Message: {}'.format(msg.get_str()))
        else:
            if DEBUG:
                self.debug('Accepted message was not valid. {}'.format(msg.raw()))

        return msg

    def send_key_request(self):
        self.send("107 KEY REQUEST")

    def send_server_ok(self):
        self.send("200 OK")

    def send_login_failed(self):
        self.send("300 LOGIN FAILED")

    def send_rotate_right(self):
        self.send("104 TURN RIGHT")

    def send_rotate_left(self):
        self.send("103 TURN LEFT")

    def send_get_message(self):
        self.send("105 GET MESSAGE")

    def send_logout(self):
        self.send("106 LOGOUT")

    def send_syntax_error(self):
        self.send("301 SYNTAX ERROR")

    def send_key_out_of_range(self):
        self.send("303 KEY OUT OF RANGE")

    def send_logic_error(self):
        self.send("302 LOGIC ERROR")

    def accept_msg(self, expected):
        msg = self.recv(expected)

        if msg is False:
            self.send_syntax_error()
            self.sock.close()
            return False

        if msg.is_valid2(MessageDescription.CLIENT_RECHARGING):
            if DEBUG:
                self.info('Processing recharge...')
            self.sock.settimeout(5)
            msg = self.recv(MessageDescription.CLIENT_RECHARGING.value[0])

            if msg.is_valid2(MessageDescription.CLIENT_FULL_POWER):
                self.sock.settimeout(1)
                return self.recv(expected)
            else:
                self.send_logic_error()
                self.sock.close()
                return False
        elif msg.is_valid2(MessageDescription.CLIENT_FULL_POWER):
            self.send_logic_error()
            self.sock.close()
            return False
        elif msg.is_valid2(MessageDescription.CLIENT_OK) or msg.is_valid2(MessageDescription.CLIENT_MESSAGE):
            return msg
        else:
            self.send_syntax_error()
            self.sock.close()
            return False

    def auth(self):
        self.msg('Auth Init')

        msg = self.accept_msg(MessageDescription.CLIENT_USERNAME.value[0])
        if msg is False or not msg.is_valid2(MessageDescription.CLIENT_USERNAME):
            self.send_syntax_error()
            return False
        else:
            self.succ('Accepted Robot `{}`'.format(msg.get_str()))
        robot_name = msg.get_str()

        self.send_key_request()
        msg = self.accept_msg(MessageDescription.CLIENT_RECHARGING.value[0])
        if not msg.is_valid2(MessageDescription.CLIENT_KEY_ID):
            self.err('Key message syntax error.')
            self.send_syntax_error()
            return False

        key_id = Message.parse_key(msg)
        if key_id is None or key_id not in KEYS:
            self.err('KeyID message contains bad value.')
            self.send_key_out_of_range()
            return False
        if DEBUG:
            self.succ('Client KeyID is `{}` - {}'.format(key_id, KEYS[key_id]))

        server_hash, client_hash = Handler.get_hashes(robot_name, KEYS[key_id])
        self.send(str(server_hash))

        log('ServerHash: {}, ClientHash: {}'.format(server_hash, client_hash))

        msg = self.accept_msg(MessageDescription.CLIENT_RECHARGING.value[0])
        if not msg.is_valid2(MessageDescription.CLIENT_CONFIRMATION):
            self.err('Client hash message contains bad value.')
            self.send_syntax_error()
            return False
        client_control_hash = Message.parse_key(msg)
        if client_control_hash is None or client_control_hash != client_hash:
            self.err('Client hash message contains incorrect value.')
            self.send_login_failed()
            return False
        self.send_server_ok()

        return True

    def send_server_move(self):
        self.send("102 MOVE")

    def check(self, msg):
        if msg is False:
            self.send_syntax_error()
            self.sock.close()
            return False
        return True

    def evade(self):
        self.send_rotate_right()
        msg = self.accept_msg(MessageDescription.CLIENT_OK.value[0])
        if not self.check(msg):
            return False

        self.send_server_move()
        msg = self.accept_msg(MessageDescription.CLIENT_OK.value[0])
        if not self.check(msg):
            return False

        self.send_rotate_left()
        msg = self.accept_msg(MessageDescription.CLIENT_OK.value[0])
        if not self.check(msg):
            return False

        self.send_server_move()
        msg = self.accept_msg(MessageDescription.CLIENT_OK.value[0])
        if not self.check(msg):
            return False

        self.send_rotate_left()
        msg = self.accept_msg(MessageDescription.CLIENT_OK.value[0])
        if not self.check(msg):
            return False

        self.send_server_move()
        msg = self.accept_msg(MessageDescription.CLIENT_OK.value[0])
        if not self.check(msg):
            return False

        self.send_rotate_right()
        msg = self.accept_msg(MessageDescription.CLIENT_OK.value[0])
        if not self.check(msg):
            return False

        return msg.get_coords()

    def handle(self):
        # auth
        if not self.auth():
            self.err('Auth Fail')
            self.sock.close()
            return False

        # get robot to the target [0,0]
        self.send_server_move()
        coords_msg_1 = self.accept_msg(MessageDescription.CLIENT_RECHARGING.value[0])

        if coords_msg_1 is False or not coords_msg_1.is_valid2(MessageDescription.CLIENT_OK):
            self.send_syntax_error()
            self.sock.close()
            return False

        coords1 = coords_msg_1.get_coords()
        self.info('[{} ; {}]'.format(coords1[0], coords1[1]))

        while True:
            self.send_server_move()
            new_coords_msg = self.accept_msg(MessageDescription.CLIENT_RECHARGING.value[0])

            if new_coords_msg is False or not new_coords_msg.is_valid2(MessageDescription.CLIENT_OK):
                self.sock.close()
                return False

            new_coords = new_coords_msg.get_coords()

            if new_coords[0] == 0 and new_coords[1] == 0:
                coords1 = new_coords
                break

            if new_coords[0] == coords1[0] and new_coords[1] == coords1[1]:
                coords = self.evade()
                if coords is False:
                    if DEBUG:
                        self.err('coords after evade() are false')
                    return False
                new_coords = coords

            my_direction = get_direction(coords1, new_coords)
            target_direction = get_target_direction(new_coords)

            if DEBUG:
                self.info('Robot is on [{} ; {}] facing {}, need to go {}'.format(new_coords[0], new_coords[1],
                                                                              direction_to_str(my_direction),
                                                                              direction_to_str(target_direction)))

            while my_direction != target_direction:
                self.send_rotate_right()
                my_direction = rotate_right(my_direction)
                dummy_msg = self.accept_msg(MessageDescription.CLIENT_RECHARGING.value[0])

            coords1 = new_coords

        self.info('Robot is on [{} ; {}]'.format(coords1[0], coords1[1]))
        self.send_get_message()

        final_msg = self.accept_msg(MessageDescription.CLIENT_MESSAGE.value[0])
        if final_msg is False:
            self.sock.close()
            return False
        if not final_msg.is_valid2(MessageDescription.CLIENT_MESSAGE):
            self.sock.close()
            return False
        else:
            self.send_logout()

        self.succ('Robot logged out. Picked up message: `{}`'.format(final_msg.get_str()))
        self.sock.close()


def client_handler(thread_id, client_socket):
    try:
        handler = Handler(thread_id, client_socket)
        handler.handle()
    except Exception as err:
        print('[ERROR]', err)
        return
