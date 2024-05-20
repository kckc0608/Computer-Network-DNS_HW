"""
특정 .com authoritative DNS 서버 프로세스는 실행 후 commad-line argument로 주어지는 파일로부터
해당 DNS 서버가 관할하는 다수의 도메인 이름 각각의 IP 주소 또는 real name(CNAME)을 읽어와 RR 형태로 cache 저장한다.
이 프로세스는 다른 DNS 서버(local DNS 서버 또는 .com TLD DNS 서버)가 보낸 query에 대하여
네임 resolution에 필요한 RR 정보를 찾아 이(들)를 응답으로 제공한다.
"""

import os
import socket
import sys
import threading
from re import findall
from common import print_data
from message import Message
import json
os.system("")


def get_dns_cache(raw_data):
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

        dns_cache[server_name.strip()] = (host_info, port_info)


def process_query():

    with socket.socket(type=socket.SOCK_DGRAM) as local_dns_socket:
        local_dns_socket.bind((host, port))

        while True:
            data, addr = local_dns_socket.recvfrom(1024)
            data = json.loads(data.decode())
            recv_message = Message(**data)

            if not recv_message.query_flag:
                # reply는 무시한다.
                continue

            if recv_message.questions in dns_cache:
                if 'A' in dns_cache[data]:
                    local_dns_socket.sendto((dns_cache[data]['A'] + " from server").encode(), addr)
                elif 'CNAME' in dns_cache[data]:
                    local_dns_socket.sendto((dns_cache[data]['CNAME'] + " from server").encode(), addr)
                else:
                    # 이상한 타입이 들어있다는 의미
                    pass
            else:
                local_dns_socket.sendto((data+" from server").encode(), addr)


try:
    host = '127.0.0.1'
    if len(sys.argv) < 3:
        print("포트 정보가 필요합니다.")
        exit()
    elif len(sys.argv) > 3:
        print("인자가 너무 많습니다.")
        exit()

    if not sys.argv[1].isnumeric():
        print("포트 번호는 숫자입니다.")
        exit()

    # 포트 번호 범위 체크 필요?
    port = int(sys.argv[1])
    domain_info_file_name = sys.argv[2]
    if not domain_info_file_name:
        raise Exception("도메인 파일 이름이 없습니다.")
    if domain_info_file_name[0] == '<':
        domain_info_file_name = domain_info_file_name[1:]
    if domain_info_file_name[-1] == '>':
        domain_info_file_name = domain_info_file_name[:-1]

    dns_cache = dict()

    with open(domain_info_file_name, encoding="utf-8") as f:
        read_data = f.read()
        get_dns_cache(read_data)
        print(dns_cache)

    input_thread = threading.Thread(target=process_query)
    input_thread.daemon = True
    input_thread.start()

    while True:
        cmd = input(">> ")
        print(cmd)

        if cmd == "exit":
            exit(0)

        elif cmd == "cache":
            pass

except Exception as ex:
    print(ex)
    input("계속하려면 아무 키나 누르십시오...")
