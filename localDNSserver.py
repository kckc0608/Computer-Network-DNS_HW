"""
가상의 dreamnet.com 회사의 네임 서버 dns.dreamnet.com에서 네임 resolution 처리를 위한 실행되는 프로그램을
local DNS 서버 프로세스라 한다. Local DNS 서버 프로세스는 실행 후 config.txt 파일에 저장된
root DNS 서버의 <네임, IP 주소> 및 port 번호를 읽어오고 port 번호를 통해 root DNS 서버와 통신한다.

- 클라이언트로부터 수신한 query는 즉각 응답(자신의 cache에 query의 답이 있는 경우)하거나,
또는 reply를 얻는 과정을 통해 답을 얻고 이를 클라이언트에게 전달한다.

- 다른 DNS 서버에 query를 보낼 때 local DNS 서버는 항상 recursive 처리를 요청하며,
상대 DNS 서버가 recursive 처리를 수락하지 않으면 iterative 처리를 통해 답을 얻는 과정을 진행한다.
대응하는 서버는 recursive 처리 수락을 독자적으로 결정하지만, root DNS 서버가 recursive 처리를 수락하면 하부의 .com TLD DNS 서
버는 반드시 recursive 처리를 수락해야 한다(이때 설정값이 거부(off)로 되어 있더라도 수락해야 함).

- 따라서 local DNS 서버가 root DNS 서버에 먼저 접근한 경우, root DNS 서버가 recursive 처리를 거부
하면 하부의 .com TLD DNS 서버는 recursive 처리 거부 또는 수락 중 하나를 독자 선택(현재 설정값에 따라 정해짐)할 수 있다.

- 답을 구하는 과정에서 얻은 정보는 새로운 정보이면 cache에 추가한다.
Query에 대한 reply를 클라이언트에게 전달하면서 local DNS 서버는 이를 얻기까지 접근한 서버(들)를 그 접근 순서대로 적절한 형태로 전달한다
(실제로는 클라이언트가 경로까지 알 필요가 없지만, 이 프로젝트에서는 어떤 경로를 통해 답을 얻었는지 확인하는 기능을 제공하려 함).
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
        print(f"\u001B[s\u001B[A\u001B[999D\u001B[S\u001B[L", end="", flush=True)
        print(COLOR["GREEN"], "[info] ", COLOR["ENDC"], end='', flush=True)
        print(f"{_data}\u001B[u", end='', flush=True)

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
                    local_dns_socket.sendto((data+" from server").encode(), addr)


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

while True:
    cmd = input(">> ")
    print(cmd)

    if cmd == "exit":
        exit(0)

