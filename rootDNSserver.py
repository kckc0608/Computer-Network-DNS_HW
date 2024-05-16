"""
가상의 root DNS 서버 dns.rootDNSservice.com에서 root DNS 서버 역할을 하는 실행 프로그램을
root DNS 서버 프로세스라 한다. Root DNS 서버 프로세스는 실행 후 config.txt 파일에 저장된 .com
TLD DNS 서버의 <네임, IP 주소> 및 port 번호를 읽어오고, port 번호를 통해 .com TLD DNS 서버와
통신한다. root DNS 서버가 recursive 처리를 수락 또는 거부하는 것은 명령어에 주어진 상태 값(flag:
on 또는 off)으로 결정된다.
"""

import os
import socket
import sys
import threading
from re import findall
os.system("")

def get_dns_info(raw_data):
    for line in raw_data.split('\n'):
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

        dns_info[server_name.strip()] = (host_info, port_info)


def get_cache_info(cache_info, raw_data):
    for line in raw_data.split('\n'):
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


def process_query():
    def print_data(_data):
        COLOR = {
            "HEADER": "\033[95m",
            "BLUE": "\033[94m",
            "GREEN": "\033[92m",
            "RED": "\033[91m",
            "ENDC": "\033[0m",
        }
        #  print(f"\u001B[s\u001B[A\u001B[999D\u001B[S\u001B[L", end="", flush=True)
        print(f"\u001B[999D\u001B[K",end="", flush=True)
        print(COLOR["GREEN"], "[info] ", COLOR["ENDC"], end='', flush=True)
        #  print(f"{_data}\u001B[u", end='', flush=True)
        print(f"{_data}\n", end='', flush=True)
        print(">> ", end='', flush=True)

    with socket.socket(type=socket.SOCK_DGRAM) as local_dns_socket:
        local_dns_socket.bind((host, port))

        while True:
            data, addr = local_dns_socket.recvfrom(1024)
            data = data.decode()
            print_data(data)

            cache_info = dict()
            with open('local_dns_cache.txt', encoding="utf-8") as f:
                cache_data = f.read()
                get_cache_info(cache_info, cache_data)
                print_data(cache_info)

                if data in cache_info:
                    # iterate 방식
                    if 'A' in cache_info[data]:
                        local_dns_socket.sendto((cache_info[data]['A'] + " from server").encode(), addr)
                    elif 'CNAME' in cache_info[data]:
                        local_dns_socket.sendto((cache_info[data]['CNAME'] + " from server").encode(), addr)
                    else:
                        # 이상한 타입이 들어있다는 의미
                        pass
                else:
                    # recursive 든, iterator 든 알아내서 반환하기
                    # 일단은 그냥 반환
                    # 일단 그냥 에코 반환
                    local_dns_socket.sendto((data+" from root dns server").encode(), addr)


host = '127.0.0.1'
if len(sys.argv) < 2:
    print("포트 정보가 필요합니다.")
    exit()
elif len(sys.argv) > 2:
    print("인자가 너무 많습니다.")
    exit()

if not sys.argv[1].isnumeric():
    print("포트 번호는 숫자입니다.")
    exit()

port = int(sys.argv[1])
# 포트 번호 범위 체크 필요?
dns_info = dict()

with open('config.txt', encoding="utf-8") as f:
    read_data = f.read()
    get_dns_info(read_data)
    print(dns_info)

input_thread = threading.Thread(target=process_query)
input_thread.daemon = True
input_thread.start()

recursive_flag = False
while True:
    try:
        cmd = tuple(map(lambda x: x.strip(), input(">> ").strip().split()))

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

    except Exception as ex:
        print("예외가 발생했습니다.")
        print(ex)
