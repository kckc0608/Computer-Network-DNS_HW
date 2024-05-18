"""
가상의 root DNS 서버 dns.rootDNSservice.com에서 root DNS 서버 역할을 하는 실행 프로그램을
root DNS 서버 프로세스라 한다. Root DNS 서버 프로세스는 실행 후 config.txt 파일에 저장된 .com
TLD DNS 서버의 <네임, IP 주소> 및 port 번호를 읽어오고, port 번호를 통해 .com TLD DNS 서버와
통신한다. root DNS 서버가 recursive 처리를 수락 또는 거부하는 것은 명령어에 주어진 상태 값(flag:
on 또는 off)으로 결정된다.
"""
import json
import os
import socket
import sys
import threading
from re import findall

from message import Message
from common import print_data

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

    with socket.socket(type=socket.SOCK_DGRAM) as root_dns_socket:
        root_dns_socket.bind((host, port))

        while True:
            recv_data, addr = root_dns_socket.recvfrom(1024)
            message_data = json.loads(recv_data.decode())
            message = Message(**message_data)

            if message.query_flag:
                print_data("쿼리를 수신했습니다.")
                query = message
                print_data(query)

                cached_answer = find_question_in_cache(message.questions)
                if cached_answer:
                    reply_message = Message(
                        message_id=query.message_id,
                        query_flag=False,
                        questions=query.questions,
                        recursive_flag=False,
                        answers=tuple(query.answers) + (cached_answer,),
                        authority=query.authority
                    )
                    root_dns_socket.sendto(reply_message.encode(), addr)
                else:
                    print_data(f"cache에 {message.questions}이 없습니다.")
                    if query.recursive_flag:  # recursive 요청 (사실 항상 이쪽으로 들어옴. local dns server는 항상 recursive 요청을 보냄)
                        if recursive_flag:  # recursive 수락
                            "recursive 과정으로 IP주소 알아오기"
                            pass
                        else:
                            "TLD 정보 보내주고 끝"
                            reply_message = Message(
                                message_id=query.message_id,
                                query_flag=False,
                                questions=query.questions,
                                recursive_flag=False,
                                answers=tuple(query.answers),
                                authority=tuple(query.authority) + (dns_info.get("comTLD_dns_server"),)
                            )
                            root_dns_socket.sendto(reply_message.encode(), addr)
                    else:
                        "TLD정보 보내주고 끝"


            else:
                pass  # root dns가 reply를 받는다는건 recursive 방식밖에 없음


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
        if not cmd:
            continue

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
