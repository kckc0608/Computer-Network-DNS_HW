"""
가상의 회사 dreamnet.com의 머신 swdpt0.dreamnet.com에서 실행되는 응용 프로그램을 클라이언트
프로세스라 하며, 이 클라이언트가 네임 resolution을 위한 query를 최초로 발생시키는 역할을 한다.
클라이언트 프로세스는 실행 후 config.txt 파일(접근 가능 지정된 위치 저장)에 저장된 local DNS 서버의
<네임, IP 주소> 및 port 번호를 읽어오고, 읽은 port 번호로 UDP segment를 보냄으로 local DNS 서
버에 query를 전달한다. Query 생성 및 resolution 과정은 클라이언트가 사용자의 키보드 입력을 통해
ipaddr <name> 명령어를 입력받고 이를 query로 만들어 local DNS 서버에 보냄으로써 시작된다.
Local DNS 서버는 이 query의 reply를 얻기까지 필요한 모든 절차를 클라이언트 대신 진행한 후, reply
및 이를 얻기 위해 접근한 서버(들) 정보를 클라이언트에게 제공한다.
"""


import socket
import sys
import json
from message import Message
from re import findall


def get_dns_info(raw_data):
    for line in raw_data.split('\n'):
        if not line or line[0] in '# \n':
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


if len(sys.argv) < 2:
    print("포트 정보가 필요합니다.")
    exit()
elif len(sys.argv) > 2:
    print("인자가 너무 많습니다.")
    exit()

if not sys.argv[1].isnumeric():
    print("포트 번호는 숫자입니다.")
    exit()

host = '127.0.0.1'
port = int(sys.argv[1])
# 포트 번호 범위 체크도 필요?
dns_info = dict()
try:
    with open('config.txt', encoding="utf-8") as f:
        read_data = f.read()
        get_dns_info(read_data)
        print(dns_info)
except:
    print("config.txt 파일에서 데이터를 가져오는 중 오류가 발생했습니다.")
    exit()

with socket.socket(type=socket.SOCK_DGRAM) as client_socket:
    client_socket.bind((host, port))
    while True:
        try:
            cmd = list(map(lambda x: x.strip(), input(">> ").split()))
            if len(cmd) == 2:
                if cmd[0] == 'ipaddr':
                    query_host = cmd[1]

                    query = Message(
                        message_id=1,
                        query_flag=True,
                        recursive_desired=False,
                        questions=query_host
                    )

                    dns_host, dns_port = dns_info["local_dns_server"]
                    client_socket.sendto(query.encode(), (host, dns_port))
                    print("쿼리를 전송했습니다.")

                    rcv_msg, server_addr = client_socket.recvfrom(2048)
                    print("reply를 받았습니다.")
                    print(rcv_msg.decode())
                else:
                    print("존재하지 않는 명령어입니다.")
            else:
                if not cmd:
                    continue

                if cmd[0] == 'ipaddr':  # 쿼리 발생
                    print("명령어의 형식이 잘못되었습니다.")
                else:
                    print("존재하지 않는 명령어입니다.")

        except Exception as ex:
            print("예상치 못한 오류가 발생했습니다.")
            print(ex)