import json
import os
import socket
import threading

from re import findall
from message import Message

os.system("")


class Dns:
    host = '127.0.0.1'

    COLOR = {
        "HEADER": "\033[95m",
        "BLUE": "\033[94m",
        "GREEN": "\033[92m",
        "RED": "\033[91m",
        "ENDC": "\033[0m",
    }

    def __init__(self, port, cache_file_name, server_name):
        self.port = port
        self.cache_fine_name = cache_file_name
        self.server_name = server_name
        self.dns_info = dict()
        self.ip_to_port = dict()
        self.dns_socket = None

        self.load_config()

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

    def load_config(self):
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

                self.dns_info[server_name.strip()] = (host_info, port_info)
                self.ip_to_port[host_info[1]] = port_info

            self.print_data(self.dns_info)
            self.print_data(self.ip_to_port)

    def process_command(self, cmd):
        if cmd[0] == "exit":
            exit(0)

        elif cmd[0] == "cache":
            # TODO : Print Cache of Root
            pass

        elif cmd[0] == "recursiveFlag":
            if len(cmd) != 2:
                print("명령어 형식이 잘못되었습니다.")
            if cmd[1] == "on":
                recursive_flag = True
                print("recursive processing : ON")
            elif cmd[1] == "off":
                recursive_flag = False
                print("recursive processing : OFF")
            else:
                print("명령어 형식이 잘못되었습니다. on/off 중 하나를 입력하세요.")

        else:
            print("존재하지 않는 명령어 입니다.")

    def get_cache_info(self, cache_info, raw_data):
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

            if record_host not in cache_info:
                cache_info[record_host] = dict()

            cache_info[record_host][record_type] = record_target

    def find_question_in_cache(self, question):
        with open(self.cache_fine_name, encoding="utf-8") as cache_file:
            cache_info = dict()
            cache_data = cache_file.read()
            self.get_cache_info(cache_info, cache_data)
            self.print_data(cache_info)

            tokens = question.split('.')
            for i in range(len(tokens)):
                sub_question = ".".join(tokens[i:])
                # 일단 RR 타입은 생각하지 말고, host name 만 생각해보자.
                if sub_question in cache_info:
                    self.print_data(f"{sub_question}을 캐시에서 찾았습니다.")
                    if 'A' in cache_info[sub_question]:
                        return sub_question, cache_info[sub_question]['A'], 'A'
                    elif 'CNAME' in cache_info[sub_question]:
                        return sub_question, cache_info[sub_question]['CNAME'], 'CANME'
                    elif 'NS' in cache_info[sub_question]:
                        return sub_question, cache_info[sub_question]['NS'], 'NS'

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

    def print_data(self, _data):
        #  print(f"\u001B[s\u001B[A\u001B[999D\u001B[S\u001B[L", end="", flush=True)
        print(f"\u001B[999D\u001B[K", end="", flush=True)
        print(self.COLOR["GREEN"], "[info] ", self.COLOR["ENDC"], end='', flush=True)
        #  print(f"{_data}\u001B[u", end='', flush=True)
        print(f"{_data}\n", end='', flush=True)
        print(">> ", end='', flush=True)