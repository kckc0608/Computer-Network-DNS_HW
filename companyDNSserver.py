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


def get_cache_info(cache_info, raw_data):
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


def process_query():

    with socket.socket(type=socket.SOCK_DGRAM) as company_dns_socket:
        company_dns_socket.bind((host, port))

        while True:
            data, addr = company_dns_socket.recvfrom(1024)
            data = json.loads(data.decode())
            recv_message = Message(**data)

            recv_message.path = tuple(recv_message.path) + (f'{company_name}.com DNS server',)

            print_data("메세지를 수신했습니다.")
            print_data(recv_message)

            if not recv_message.query_flag:
                # company dns server는 최종 dns 서버 이므로 쿼리를 보낼 일이 없다.
                # 따라서 reply는 무시한다.
                continue

            reply = Message(
                message_id=recv_message.message_id,
                questions=recv_message.questions,
                query_flag=False,
                recursive_desired=recv_message.recursive_desired,
                answers=tuple(recv_message.answers),
                authority=tuple(recv_message.authority),
                path=tuple(recv_message.path)
            )
            if reply.questions in dns_cache:
                print_data(f"{reply.questions}을 캐시에서 찾았습니다.")
                if 'A' in dns_cache[reply.questions]:
                    reply.answers += ((reply.questions, dns_cache[reply.questions]['A'], 'A'),)
                else:
                    question = reply.questions
                    while 'A' not in dns_cache[question]:
                        if 'CNAME' in dns_cache[question]:
                            question = dns_cache[question]['CNAME']
                        elif 'NS' in dns_cache[question]:
                            question = dns_cache[question]['NS']
                        if question not in dns_cache:
                            print_data("A 레코드 정보를 찾지 못했습니다.")
                            question = None
                            break

                    if question:
                        reply.answers += ((reply.questions, dns_cache[question]['A'], 'A'),)

                company_dns_socket.sendto(reply.encode(), addr)

            else:
                # 일단 보내줄 데이터가 없으면 응답 X
                pass


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

    company_name = domain_info_file_name.split('.')[0]

    dns_cache = dict()

    with open(domain_info_file_name, encoding="utf-8") as f:
        read_data = f.read()
        get_cache_info(dns_cache, read_data)
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
