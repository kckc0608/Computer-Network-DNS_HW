"""
특정 .com authoritative DNS 서버 프로세스는 실행 후 commad-line argument로 주어지는 파일로부터
해당 DNS 서버가 관할하는 다수의 도메인 이름 각각의 IP 주소 또는 real name(CNAME)을 읽어와 RR 형태로 cache 저장한다.
이 프로세스는 다른 DNS 서버(local DNS 서버 또는 .com TLD DNS 서버)가 보낸 query에 대하여
네임 resolution에 필요한 RR 정보를 찾아 이(들)를 응답으로 제공한다.
"""

import os
import sys
from message import Message
from dns import Dns
os.system("")


class CompanyDns(Dns):

    def process_query(self, recv_message, addr):
        super().process_query(recv_message, addr)
        reply = Message(
            message_id=recv_message.message_id,
            questions=recv_message.questions,
            query_flag=False,
            recursive_desired=recv_message.recursive_desired,
            recursive_available=False,
            answers=tuple(recv_message.answers),
            authority=tuple(recv_message.authority),
            path=tuple(recv_message.path)
        )
        if reply.questions in self.dns_cache:
            self.print_data(f"{reply.questions}을 캐시에서 찾았습니다.")
            if 'A' in self.dns_cache[reply.questions]:
                reply.answers += ((reply.questions, self.dns_cache[reply.questions]['A'], 'A'),)
            else:
                question = reply.questions
                while 'A' not in self.dns_cache[question]:
                    if 'CNAME' in self.dns_cache[question]:
                        question = self.dns_cache[question]['CNAME']
                    elif 'NS' in self.dns_cache[question]:
                        question = self.dns_cache[question]['NS']
                    if question not in self.dns_cache:
                        self.print_data("A 레코드 정보를 찾지 못했습니다.")
                        question = None
                        break

                if question:
                    reply.answers += ((reply.questions, self.dns_cache[question]['A'], 'A'),)

            self.dns_socket.sendto(reply.encode(), addr)

        else:
            self.dns_socket.sendto(reply.encode(), addr)


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

    company_dns_server = CompanyDns(port, server_name=company_name, cache_file_name=domain_info_file_name)
    company_dns_server.start()

except Exception as ex:
    print(ex)
    input("계속하려면 아무 키나 누르십시오...")
