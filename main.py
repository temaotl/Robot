import socket
import sys
import threading

PORT = 3999

MESSAGE_SUFFIX = b'\a\b'

# SERVER MASSAGE #
SERVER_MOVE = "102 MOVE".encode() + MESSAGE_SUFFIX
SERVER_TURN_LEFT = "103 TURN LEFT".encode() + MESSAGE_SUFFIX
SERVER_TURN_RIGHT = "104 TURN RIGHT".encode() + MESSAGE_SUFFIX
SERVER_PICK_UP = "105 GET MESSAGE".encode() + MESSAGE_SUFFIX
SERVER_LOGOUT = "106 LOGOUT".encode() + MESSAGE_SUFFIX
SERVER_KEY_REQUEST = "107 KEY REQUEST".encode() + MESSAGE_SUFFIX
SERVER_OK = "200 OK".encode() + MESSAGE_SUFFIX
SERVER_LOGIN_FAILED = "300 LOGIN FAILED".encode() + MESSAGE_SUFFIX
SERVER_SYNTAX_ERROR = "301 SYNTAX ERROR".encode() + MESSAGE_SUFFIX
SERVER_LOGIC_ERROR = "302 LOGIC ERROR".encode() + MESSAGE_SUFFIX
SERVER_KEY_OUT_OF_RANGE_ERROR = "303 KEY OUT OF RANGE".encode() + MESSAGE_SUFFIX
# END OF SERVER MASSAGE  #

# TIMEOUT #
TIMEOUT = 1
TIMEOUT_RECHARGING = 5
# END TIMEOUT #

# CLIENT MESSAGE #
CLIENT_FULL_POWER = "FULL POWER".encode()
CLIENT_RECHARGING = "RECHARGING".encode()
# END OF CLIENT MESSAGE #

# CLIENT  LIMIT BLOCK #
CLIENT_USERNAME_LENGTH = 20 - 2
CLIENT_CONFIRMATION_LENGTH = 7 - 2
CLIENT_OK_LENGTH = 12 - 2
CLIENT_MESSAGE_LENGTH = 100 - 2
# END OF CLIENT LIMIT #

# ARRAY OF KEY
SERVER_USER_KEY = [[23019, 32037],
                   [32037, 29295],
                   [18789, 13603],
                   [16443, 29533],
                   [18189, 21952]]


# start socket #
def open_Socket(server_port):
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, proto=0)
    my_socket.bind(("", server_port))
    my_socket.listen()
    return my_socket


def recharging_confirmation(con: socket.socket):
    con.settimeout(TIMEOUT_RECHARGING)
    last_len = 0
    tmp_message_text = b''
    try:
        while True:
            tmp_message_text += con.recv(1)
            new_len = len(tmp_message_text)
            if new_len == 1:
                continue
            if new_len > 12:
                print("err2")
                return send_response_to_client(con, SERVER_LOGIC_ERROR)
            for i in range(last_len, new_len):
                if tmp_message_text[i:(i + 2)] == MESSAGE_SUFFIX:
                    print(tmp_message_text)
                    return tmp_message_text[:i]
                elif new_len == 12:
                    print("err3")
                    return send_response_to_client(con, SERVER_LOGIC_ERROR)
            last_len = new_len - 1
    except ConnectionResetError:
        print("reset")
        return None
    except socket.timeout:
        print("timeOut")
        close_Socket(con)
        return None


def read_message(con: socket.socket, count_s: int):
    con.settimeout(TIMEOUT)
    last_len = 0
    tmp_message_text = b''
    try:
        while True:
            tmp_message_text += con.recv(1)
            new_len = len(tmp_message_text)
            if new_len == 1:
                continue
            if new_len > count_s:
                print("err0")
                return send_response_to_client(con, SERVER_SYNTAX_ERROR)
            for i in range(last_len, new_len):
                if tmp_message_text[i:(i + 2)] == MESSAGE_SUFFIX:

                    if tmp_message_text[:i] == CLIENT_RECHARGING:

                        if recharging_confirmation(con) == CLIENT_FULL_POWER:
                            return read_message(con, count_s)
                        else:
                            return send_response_to_client(con, SERVER_LOGIC_ERROR)

                    elif tmp_message_text[:i] == CLIENT_FULL_POWER:
                        return send_response_to_client(con, SERVER_LOGIC_ERROR)

                    return tmp_message_text[:i]
                elif new_len == count_s:
                    print("err1")
                    if count_s < 12 and tmp_message_text == (CLIENT_RECHARGING + MESSAGE_SUFFIX)[:count_s]:
                        recharging_str = tmp_message_text + read_message(con, 12 - count_s)
                        if recharging_str == CLIENT_RECHARGING:
                            if recharging_confirmation(con) == CLIENT_FULL_POWER:
                                return read_message(con, count_s)
                            else:
                                return send_response_to_client(con, SERVER_LOGIC_ERROR)
                        if recharging_str == CLIENT_FULL_POWER:
                            return send_response_to_client(con, SERVER_LOGIC_ERROR)
                    return send_response_to_client(con, SERVER_SYNTAX_ERROR)
            last_len = new_len - 1
    except ConnectionResetError:
        print("reset")
        return None
    except socket.timeout:
        print("timeOut")
        close_Socket(con)
        return None


def close_Socket(server_socket: socket.socket):
    server_socket.close()
    sys.exit()


def create_hash(name):
    return (sum(name) * 1000) % 65536


def send_response_to_client(con: socket.socket, message):
    con.sendall(message)
    close_Socket(con)
    return None


def get_quarter(x: int, y: int):
    if x > 0 and y > 0:
        return 0
    if x < 0 < y:
        return 1
    if x < 0 and y < 0:
        return 2
    if x > 0 > y:
        return 3
    if y == 0:
        if x > 0:
            return 0
        if x < 0:
            return 1
    if x == 0:
        if y > 0:
            return 0
        if y < 0:
            return 3


def give_coordinate(con: socket.socket, connected_str: bytes):
    splited = connected_str.decode().split()
    if connected_str[-1:] == b' ':
        return send_response_to_client(con, SERVER_SYNTAX_ERROR)
    if len(splited) != 3 or splited[0] != 'OK':
        return send_response_to_client(con, SERVER_SYNTAX_ERROR)
    try:
        int(splited[1])
        int(splited[2])
        return int(splited[1]), int(splited[2])
    except ValueError:
        return send_response_to_client(con, SERVER_SYNTAX_ERROR)


def check_coordinate(con: socket.socket, x, y):
    if x == 0 and y == 0:
        con.sendall(SERVER_PICK_UP)
        read_message(con, 100)
        return send_response_to_client(con, SERVER_LOGOUT)


def server_action(con: socket.socket, action):
    con.sendall(action)
    x, y = give_coordinate(con, read_message(con, 12))
    check_coordinate(con, x, y)
    return x, y


def change_compas(con: socket.socket):
    server_action(con, SERVER_TURN_LEFT)
    server_action(con, SERVER_TURN_LEFT)


def evade_block_full(con: socket.socket):
    server_action(con, SERVER_TURN_LEFT)
    server_action(con, SERVER_MOVE)
    server_action(con, SERVER_TURN_RIGHT)
    server_action(con, SERVER_MOVE)
    server_action(con, SERVER_MOVE)
    server_action(con, SERVER_TURN_RIGHT)
    x, y = server_action(con, SERVER_MOVE)
    server_action(con, SERVER_TURN_LEFT)
    return x, y


def evade_block_part_Left(con: socket.socket):
    server_action(con, SERVER_TURN_LEFT)
    x1, y1 = server_action(con, SERVER_MOVE)
    if x1 != 0:
        server_action(con, SERVER_TURN_RIGHT)
        x, y = server_action(con, SERVER_MOVE)
        vector_x = x1 - x  # West-> (>0) East-> (<0)
        vector_y = y1 - y  # North-> (<0)  South-> (>0)
        return x, y, vector_x, vector_y
    else:
        return x1, y1, 1, 1


def evade_block_part_Right(con: socket.socket):
    server_action(con, SERVER_TURN_RIGHT)
    x1, y1 = server_action(con, SERVER_MOVE)
    if x1 != 0:
        server_action(con, SERVER_TURN_LEFT)
        x, y = server_action(con, SERVER_MOVE)
        vector_x = x1 - x  # West-> (>0) East-> (<0)
        vector_y = y1 - y  # North-> (<0)  South-> (>0)
        return x, y, vector_x, vector_y
    else:
        return x1, y1, 1, 1


def right_direction_x(con: socket.socket, vector_x, vector_y, quarter):
    if vector_x == 0:
        if vector_y < 0:
            if quarter == 0 or quarter == 3:
                server_action(con, SERVER_TURN_LEFT)
            if quarter == 1 or quarter == 2:
                server_action(con, SERVER_TURN_RIGHT)
        if vector_y > 0:
            if quarter == 0 or quarter == 3:
                server_action(con, SERVER_TURN_RIGHT)
            if quarter == 1 or quarter == 2:
                server_action(con, SERVER_TURN_LEFT)

    if vector_x > 0 and (quarter == 1 or quarter == 2):
        change_compas(con)

    if vector_x < 0 and (quarter == 0 or quarter == 3):
        change_compas(con)


def find_a_right_way(con: socket.socket):
    print("__START__")
    x, y = server_action(con, SERVER_MOVE)  # look aside
    quarter = get_quarter(x, y)
    x1, y1 = server_action(con, SERVER_MOVE)
    vector_x = x - x1  # West-> (>0) East-> (<0)
    vector_y = y - y1  # North-> (<0)  South-> (>0)
    if vector_x == 0 and vector_y == 0:
        print("pregrada 0")
        server_action(con, SERVER_TURN_LEFT)
        x, y, = server_action(con, SERVER_MOVE)
        vector_x = x1 - x
        vector_y = y1 - y
        if x != 0:
            quarter1 = get_quarter(x, y)
            if quarter1 != quarter and (quarter1 is not None):
                quarter = quarter1
            right_direction_x(con, vector_x, vector_y, quarter)

    else:
        x = x1
        y = y1
        quarter1 = get_quarter(x, y)
        if quarter1 != quarter and (quarter1 is not None):
            quarter = quarter1
        right_direction_x(con, vector_x, vector_y, quarter)
    while x != 0:
        x1, y1 = server_action(con, SERVER_MOVE)
        vector_x = x - x1  # West-> (>0) East-> (<0)
        vector_y = y - y1  # North-> (<0)  South-> (>0)
        if vector_x == 0 and vector_y == 0:
            print("pregrada 1")
            if quarter == 0 or quarter == 2:
                x, y, vector_x, vector_y = evade_block_part_Left(con)
            if quarter == 1 or quarter == 3:
                x, y, vector_x, vector_y = evade_block_part_Right(con)

            if x != 0:
                quarter1 = get_quarter(x, y)
                if quarter1 != quarter and (quarter1 is not None):
                    quarter = quarter1
                    right_direction_x(con, vector_x, vector_y, quarter)
            else:
                continue
        else:
            x = x1
            y = y1

    if quarter == 0 or quarter == 2:
        server_action(con, SERVER_TURN_LEFT)
    if quarter == 1 or quarter == 3:
        server_action(con, SERVER_TURN_RIGHT)

    while y != 0:
        x1, y1 = server_action(con, SERVER_MOVE)
        vector_x = x - x1  # West-> (>0) East-> (<0)
        vector_y = y - y1  # North-> (<0)  South-> (>0)
        if abs(y1) - abs(y) > 0:
            change_compas(con)
        if vector_x == 0 and vector_y == 0:
            print("pregrada 2")
            x, y = evade_block_full(con)
            if (y1 > 0 > y) or (y1 < 0 < y):
                change_compas(con)
        else:
            x = x1
            y = y1
    con.sendall(SERVER_PICK_UP)
    read_message(con, 100)
    return send_response_to_client(con, SERVER_LOGOUT)

    # TODO check recharge and wrong sequence


def checkWhiteSpace(con: socket.socket, str1):
    if b' ' in str1:
        return send_response_to_client(con, SERVER_SYNTAX_ERROR)
    else:
        return None


def auf(con: socket.socket, art):  # authentication
    usr_name = read_message(con, 20)
    con.sendall(SERVER_KEY_REQUEST)
    key_id = read_message(con, 5)
    checkWhiteSpace(con, key_id)
    try:
        key_id_num = int(key_id.decode())
    except ValueError:
        return send_response_to_client(con, SERVER_SYNTAX_ERROR)

    if key_id_num > 4 or key_id_num < 0:
        return send_response_to_client(con, SERVER_KEY_OUT_OF_RANGE_ERROR)

    usr_hash = create_hash(usr_name)
    server_confirmation = bytearray(str((usr_hash + SERVER_USER_KEY[key_id_num][0]) % 65536).encode() + MESSAGE_SUFFIX)
    con.sendall(server_confirmation)
    client_confirmation = read_message(con, 7)
    checkWhiteSpace(con, client_confirmation)
    client_key_hash_my_compare = (usr_hash + SERVER_USER_KEY[key_id_num][1]) % 65536
    client_key_hash_client_compare = int(client_confirmation.decode())

    if client_key_hash_my_compare == client_key_hash_client_compare:
        con.sendall(SERVER_OK)
        return find_a_right_way(con)
    else:
        return send_response_to_client(con, SERVER_LOGIN_FAILED)


#  end of socket  #

if __name__ == '__main__':
    serverSocket = open_Socket(PORT)
    robot_counter = 0
    while True:
        (clientConnection, clientAddress) = serverSocket.accept()
        tredka = threading.Thread(target=auf, args=(clientConnection, robot_counter))
        tredka.start()
        robot_counter += 1

