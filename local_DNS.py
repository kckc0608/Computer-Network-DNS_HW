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
# 포트 번호 범위 체크 필요?
dns_info = dict()

with open('config.txt', encoding="utf-8") as f:
    read_data = f.read()
    get_dns_info(read_data)
    print(dns_info)

with socket.socket(type=socket.SOCK_DGRAM) as local_dns_socket:
    local_dns_socket.bind((host, port))
    while True:
        data, addr = local_dns_socket.recvfrom(1024)
        data = data.decode() + " from server"
        print(data)
        print(addr)

        local_dns_socket.sendto(data.encode(), addr)

        # cmd = input(">> ").split()
        #
        # if len(cmd) == 2:
        #     if cmd[0] == 'ipaddr':
        #         host = cmd[1]
        #         print(host)
        #         data, addr = local_dns_socket.recvfrom(1024)
        #         data = data.decode()
        #         print(data)
        #         print(addr)
        #     else:
        #         print("존재하지 않는 명령어입니다.")
        # else:
        #     if cmd[0] == 'ipaddr':
        #         print("명령어의 형식이 잘못되었습니다.")
        #     else:
        #         print("존재하지 않는 명령어입니다.")

