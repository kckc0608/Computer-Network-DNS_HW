"""
가상의 root DNS 서버 dns.rootDNSservice.com에서 root DNS 서버 역할을 하는 실행 프로그램을
root DNS 서버 프로세스라 한다. Root DNS 서버 프로세스는 실행 후 config.txt 파일에 저장된 .com
TLD DNS 서버의 <네임, IP 주소> 및 port 번호를 읽어오고, port 번호를 통해 .com TLD DNS 서버와
통신한다. root DNS 서버가 recursive 처리를 수락 또는 거부하는 것은 명령어에 주어진 상태 값(flag:
on 또는 off)으로 결정된다.
"""

import os
import sys
from message import Message
from common import print_data
from recursive_dns import RecursiveDns
os.system("")


class ComTLDDns(RecursiveDns):

    def process_query(self, recv_message, addr):
        super().process_query(recv_message, addr)
        cached_for, cached_record, cached_type = self.find_question_in_cache(recv_message.questions)
        print_data("캐시 검색 결과")
        print_data((cached_for, cached_record, cached_type))

        if cached_for:
            if cached_for == recv_message.questions:
                reply_message = Message(
                    message_id=recv_message.message_id,
                    query_flag=False,
                    questions=recv_message.questions,
                    recursive_desired=False,
                    answers=tuple(recv_message.answers) + ((cached_for, cached_record, cached_type),),
                    authority=tuple(recv_message.authority),
                    path=tuple(recv_message.path)
                )
                self.dns_socket.sendto(reply_message.encode(), addr)
            else:
                if recv_message.recursive_desired and self.recursive_flag:
                    "recursive 하게 대신 알아오기"
                    pass
                else:
                    print_data("iterative 방식으로 authority 를 응답합니다.")
                    reply_message = Message(
                        message_id=recv_message.message_id,
                        query_flag=False,
                        questions=recv_message.questions,
                        recursive_desired=False,
                        answers=tuple(recv_message.answers),
                        authority=tuple(recv_message.authority) + ((cached_for, cached_record, cached_type),),
                        path=tuple(recv_message.path)
                    )
                    while cached_type != 'A':
                        cached_for, cached_record, cached_type = self.find_question_in_cache(cached_record)
                        reply_message.authority += ((cached_for, cached_record, cached_type),)
                    self.dns_socket.sendto(reply_message.encode(), addr)

        else:  # 쿼리와 관련되어 요청을 보내볼 만한 서버를 아무것도 찾지 못함.
            print_data(f"cache에 {recv_message.questions}이 없습니다.")
            print_data(f"com tld server 에 없는 쿼리는 처리할 수 없습니다.")
            reply_message = Message(
                message_id=recv_message.message_id,
                query_flag=False,
                questions=recv_message.questions,
                recursive_desired=False,
                answers=tuple(recv_message.answers),
                authority=tuple(recv_message.authority),
                path=tuple(recv_message.path)
            )
            self.dns_socket.sendto(reply_message.encode(), addr)


if len(sys.argv) < 2:
    print("포트 정보가 필요합니다.")
    exit()
elif len(sys.argv) > 2:
    print("인자가 너무 많습니다.")
    exit()

if not sys.argv[1].isnumeric():
    print("포트 번호는 숫자입니다.")
    exit()

# 포트 번호 범위 체크 필요?
port = int(sys.argv[1])

com_tld_dns_server = ComTLDDns(port, 'com_tld_dns_cache.txt', 'comTLD_dns_server')
com_tld_dns_server.start()