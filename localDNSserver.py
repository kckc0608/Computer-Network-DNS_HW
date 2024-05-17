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
import json
from re import findall
from message import Message
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
    print("root DNS 서버의 정보를 가져왔습니다.")
    print(dns_info)


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

    def find_question_in_cache(question):
        with open('local_dns_cache.txt', encoding="utf-8") as cache_file:
            cache_info = dict()
            cache_data = cache_file.read()
            get_cache_info(cache_info, cache_data)
            print_data(cache_info)

            if question in cache_info:
                # iterate 방식
                if 'A' in cache_info[question]:
                    return cache_info[question]['A']
                elif 'CNAME' in cache_info[question]:
                    return cache_info[question]['CNAME']
                else:
                    # 이상한 타입이 들어있다는 의미
                    pass

            return None

    with socket.socket(type=socket.SOCK_DGRAM) as local_dns_socket:
        local_dns_socket.bind((host, port))

        while True:
            data, addr = local_dns_socket.recvfrom(1024)
            print_data("데이터를 수신했습니다.")

            json_data = json.loads(data.decode())
            print_data(json_data)
            recv_message = Message(**json_data)

            # reply 인 경우
            if not recv_message.query_flag:
                print_data("reply 를 수신했습니다.")
                if addr[1] == root_dns_port:
                    if recv_message.answers:
                        print_data("answers 가 들어있는 응답을 받았습니다.")
                        print_data(f"client port : {client_port}")
                        print_data(f"{recv_message}")
                        local_dns_socket.sendto(recv_message.encode(), (host, client_port))
                    elif recv_message.authority:
                        print_data("authority 가 들어있는 응답을 받았습니다.")
                        print_data(recv_message.authority)

                        print_data("authority server에 요청을 보냅니다.")
                        authority_port = recv_message.authority.pop()[1]
                        print_data(f"authority port : {authority_port}")

                        query = recv_message
                        query.query_flag = True

                        local_dns_socket.sendto(recv_message.encode(), (host, authority_port))
                    else:
                        print_data("호스트에 대한 IP주소를 찾지 못했습니다.")
                else: # 다른 서버로부터 reply를 받은 상황
                    if recv_message.answers:
                        print_data("answers 가 들어있는 응답을 받았습니다.")
                        print_data(f"client port : {client_port}")
                        print_data(f"{recv_message}")
                        local_dns_socket.sendto(recv_message.encode(), (host, client_port))

            # query 인 경우
            else:
                print_data("query를 수신했습니다.")
                client_port = addr[1]
                """
                1. xyz.com dns server 정보가 캐시에 있는지 확인
                2. .com dns sever 정보가 캐시에 있는지 확인
                3. root server에 쿼리 전송
                """

                cached_answer = find_question_in_cache(recv_message.questions)
                if cached_answer:
                    reply_message = Message(
                        message_id=query.message_id,
                        query_flag=False,
                        questions=query.questions,
                        recursive_flag=False,
                        answers=query.answers + (cached_answer,),
                        authority=query.authority
                    )
                    local_dns_socket.sendto(reply_message.encode(), addr)

                # 3. root dns 서버에 요청 보내기
                else:
                    # recv_query 에서 recursion_desired 만 확실하게 True 로 바꿔서 root dns server 에 그대로 전송
                    query = recv_message
                    query.recursive_flag = True  # local DNS server는 항상 recursive 처리를 요청한다.

                    print_data(f"{query.questions} 도메인 정보가 캐시에 없습니다. root에 쿼리를 보냅니다.")
                    local_dns_socket.sendto(query.encode(), (host, root_dns_port))


try:
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

    host = '127.0.0.1'
    client_port = None

    # root DNS 서버의 정보 가져오기 (TODO : 지금은 모든 정보를 다 가져옴)
    with open('config.txt', encoding="utf-8") as f:
        read_data = f.read()
        get_dns_info(read_data)

    if 'root_dns_server' not in dns_info:
        raise Exception("root dns server 정보가 없습니다.")
    root_dns_host, root_dns_port = dns_info.get('root_dns_server')

    input_thread = threading.Thread(target=process_query)
    input_thread.daemon = True
    input_thread.start()

    while True:
        cmd = input(">> ").strip()
        if not cmd:
            continue

        if cmd == "exit":
            exit(0)
        elif cmd == "cache":
            # print cache (TODO)
            pass
        else:
            print("존재하지 않는 명령어 입니다.")


except Exception as ex:
    print("예상치 못한 오류가 발생했습니다.")
    print(ex)
