import json
import os
import socket
import threading

from re import findall
from message import Message

os.system("")


class Dns:
    host = '127.0.0.1'

    def __init__(self, port, cache_file_name, server_name):
        self.port = port
        self.cache_file_name = cache_file_name
        self.server_name = server_name
        self.dns_info = dict()
        self.dns_cache = dict()
        self.ip_to_port = dict()
        self.msg_id_table = dict()
        self.dns_socket: socket.socket

        self.clear_cache()
        self.load_config()
        self.load_cache()

    def start(self):
        try:
            network_thread = threading.Thread(target=self.process_message)
            network_thread.daemon = True
            network_thread.start()

            while True:
                try:
                    cmd = tuple(map(lambda x: x.strip(), input(">> ").strip().split()))
                    if not cmd:
                        continue

                    self.process_command(cmd)

                except Exception as ex:
                    print("예외가 발생했습니다.")
                    print(ex)

        except Exception as ex:
            print(ex)
            input("계속하려면 아무 키나 누르십시오...")

    def load_config(self, find=None, exclude=None):
        with open('config.txt', encoding="utf-8") as f:
            raw_data = f.read()
            for line in raw_data.split('\n'):
                if not line:
                    continue

                if line[0] in '# \n':
                    # 주석, 공백, 개행은 무시한다.
                    continue

                server_name, info = line.split('=')
                host_info = findall(r'\[.*\]', info)
                port_info = findall(r'\] [0-9]{1,5}', info)
                if not host_info or not port_info:
                    raise Exception("config.txt 파일 내용이 잘못되었습니다.")

                host_info = tuple(map(lambda x: x.strip(), host_info[0][1:-1].split(',')))
                port_info = int(port_info[0][2:])

                self.ip_to_port[host_info[1]] = port_info

                if exclude and server_name.strip() in exclude:
                    continue

                server_name = server_name.strip()
                if find:
                    if server_name in find:
                        if server_name not in self.dns_info:
                            self.dns_info[server_name] = (host_info, port_info)
                            self.save_record_into_cache((host_info[0], host_info[1], 'A'))
                else:
                    if server_name not in self.dns_info:
                        self.dns_info[server_name] = (host_info, port_info)
                        self.save_record_into_cache((host_info[0], host_info[1], 'A'))

    def load_cache(self):
        self.print_data("캐시를 로드합니다.")
        with open(self.cache_file_name, encoding="utf-8") as cache_file:
            raw_data = cache_file.read()
            for line in raw_data.split('\n'):
                if not line:
                    continue

                if line[0] in '# \n':
                    # 주석, 공백, 개행은 무시한다.
                    continue

                data = line.split(',')
                if len(data) != 3:
                    print("cache.txt 형식이 잘못되었습니다.")
                    continue

                record_host, record_target, record_type = map(lambda x: x.strip(), data)

                if record_host not in self.dns_cache:
                    self.dns_cache[record_host] = dict()

                self.dns_cache[record_host][record_type] = record_target

    def process_command(self, cmd):
        if cmd[0] == "exit":
            exit(0)

        elif cmd[0] == "cache":
            self.load_cache()
            for key, item in self.dns_cache.items():
                for record_type, record_value in item.items():
                    print(f"{key} : {record_value} ({record_type})")
        else:
            print("존재하지 않는 명령어 입니다.")

    def find_question_in_cache(self, question):
        self.load_cache()

        tokens = question.split('.')
        for i in range(len(tokens)):
            sub_question = ".".join(tokens[i:])
            # 일단 RR 타입은 생각하지 말고, host name 만 생각해보자.
            if sub_question in self.dns_cache:
                self.print_data(f"{sub_question}을 캐시에서 찾았습니다.")
                if 'A' in self.dns_cache[sub_question]:
                    return sub_question, self.dns_cache[sub_question]['A'], 'A'
                elif 'CNAME' in self.dns_cache[sub_question]:
                    return sub_question, self.dns_cache[sub_question]['CNAME'], 'CANME'
                elif 'NS' in self.dns_cache[sub_question]:
                    return sub_question, self.dns_cache[sub_question]['NS'], 'NS'

        return None, None, None

    def process_message(self):
        with socket.socket(type=socket.SOCK_DGRAM) as dns_socket:
            self.dns_socket = dns_socket
            self.dns_socket.bind((self.host, self.port))

            while True:
                recv_data, addr = dns_socket.recvfrom(1024)
                message_data = json.loads(recv_data.decode())
                recv_message = Message(**message_data)
                recv_message.path = tuple(recv_message.path) + (self.server_name,)

                if recv_message.message_id not in self.msg_id_table:
                    self.msg_id_table[recv_message.message_id] = addr

                if recv_message.query_flag:
                    self.process_query(recv_message, addr)
                else:
                    self.process_reply(recv_message, addr)

    def process_query(self, recv_message, addr):
        self.print_data("쿼리를 수신했습니다.")
        self.print_data(recv_message)

    def process_reply(self, recv_message, addr):
        self.print_data("reply 를 받았습니다.")
        self.print_data(recv_message)

        # Caching
        for auth_for, auth_record, auth_type in recv_message.answers:
            self.save_record_into_cache((auth_for, auth_record, auth_type))

        for auth_for, auth_record, auth_type in recv_message.authority:
            self.save_record_into_cache((auth_for, auth_record, auth_type))

    def send_empty_reply(self, recv_message: Message, addr):
        reply_message = Message(
            message_id=recv_message.message_id,
            query_flag=False,
            questions=recv_message.questions,
            recursive_desired=recv_message.recursive_desired,
            recursive_available=False,
            answers=tuple(recv_message.answers),
            authority=tuple(recv_message.authority),
            path=tuple(recv_message.path)
        )
        self.dns_socket.sendto(reply_message.encode(), addr)

    def save_record_into_cache(self, record):
        record_data = ' , '.join(record) + '\n'
        with open(self.cache_file_name, 'a', encoding="utf-8") as cache_file:
            cache_file.write(record_data)

    def print_data(self, _data, print_type='info'):

        # 과제 제출용은 디버깅 출력을 하지 않음
        return

        COLOR = {
            "HEADER": "\033[95m",
            "BLUE": "\033[94m",
            "GREEN": "\033[92m",
            "RED": "\033[91m",
            "ENDC": "\033[0m",
        }
        print(f"\u001B[999D\u001B[K", end="", flush=True)
        match print_type:
            case 'error':
                print(COLOR["RED"], "[error] ", COLOR["ENDC"], end='', flush=True)
            case _:
                print(COLOR["GREEN"], "[info] ", COLOR["ENDC"], end='', flush=True)

        print(f"{_data}\n", end='', flush=True)
        print(">> ", end='', flush=True)

    def clear_cache(self):
        open(self.cache_file_name, 'w')