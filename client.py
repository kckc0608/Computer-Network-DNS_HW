import socket, sys
from re import findall


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

try:
    with socket.socket(type=socket.SOCK_DGRAM) as client_socket:
        client_socket.bind((host, port))
        while True:
            cmd = input(">> ").split()
            if len(cmd) == 2:
                if cmd[0] == 'ipaddr':
                    query_host = cmd[1]
                    dns_host, dns_port = dns_info["local_dns_server"]
                    client_socket.sendto(query_host.encode(), (dns_host[1], dns_port))

                    rcv_msg, server_addr = client_socket.recvfrom(2048)
                    print(rcv_msg.decode())
                else:
                    print("존재하지 않는 명령어입니다.")
            else:
                if cmd[0] == 'ipaddr':
                    print("명령어의 형식이 잘못되었습니다.")
                else:
                    print("존재하지 않는 명령어입니다.")
except:
    print("예상치 못한 에러가 발생했습니다.")
    exit()