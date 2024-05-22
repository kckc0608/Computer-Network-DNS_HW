"""
가상의 root DNS 서버 dns.rootDNSservice.com에서 root DNS 서버 역할을 하는 실행 프로그램을
root DNS 서버 프로세스라 한다. Root DNS 서버 프로세스는 실행 후 config.txt 파일에 저장된 .com
TLD DNS 서버의 <네임, IP 주소> 및 port 번호를 읽어오고, port 번호를 통해 .com TLD DNS 서버와
통신한다. root DNS 서버가 recursive 처리를 수락 또는 거부하는 것은 명령어에 주어진 상태 값(flag:
on 또는 off)으로 결정된다.
"""
import os
import sys
from recursive_dns import RecursiveDns
from message import Message

os.system("")


class RootDnsServer(RecursiveDns):

    def process_query(self, recv_message, addr):
        super().process_query(recv_message, addr)

        cached_for, cached_record, cached_type = self.find_question_in_cache(recv_message.questions)
        self.print_data("캐시 검색 결과")
        self.print_data((cached_for, cached_record, cached_type))
        if cached_for:
            if cached_for == recv_message.questions:
                reply_message = Message(
                    message_id=recv_message.message_id,
                    query_flag=False,
                    questions=recv_message.questions,
                    recursive_desired=False,
                    recursive_available=self.recursive_flag,
                    answers=tuple(recv_message.answers) + ((cached_for, cached_record, cached_type),),
                    authority=tuple(recv_message.authority),
                    path=tuple(recv_message.path)
                )
                self.dns_socket.sendto(reply_message.encode(), addr)
            else:
                if recv_message.recursive_desired and self.recursive_flag:
                    self.print_data("recursive 방식으로서 authority에 대신 쿼리를 보냅니다.")
                    query_message = Message(
                        message_id=recv_message.message_id,
                        query_flag=True,
                        questions=recv_message.questions,
                        recursive_desired=True,
                        recursive_available=self.recursive_flag,
                        answers=tuple(recv_message.answers),
                        authority=tuple(recv_message.authority),
                        path=tuple(recv_message.path)
                    )

                    while cached_type and cached_type != 'A':
                        cached_for, cached_record, cached_type = self.find_question_in_cache(cached_record)

                    if cached_record not in self.ip_to_port:
                        self.print_data(self.ip_to_port)
                        raise Exception(f"IP 주소 {cached_record} 에 대한 포트 정보가 없습니다.")

                    authority_port = self.ip_to_port[cached_record]
                    self.print_data(f"authority server({authority_port})에 요청을 보냅니다.")
                    self.dns_socket.sendto(query_message.encode(), (self.host, authority_port))
                else:
                    self.print_data("iterative 방식으로서 authority 를 응답합니다.")
                    reply_message = Message(
                        message_id=recv_message.message_id,
                        query_flag=False,
                        questions=recv_message.questions,
                        recursive_desired=False,
                        recursive_available=self.recursive_flag,
                        answers=tuple(recv_message.answers),
                        authority=tuple(recv_message.authority) + ((cached_for, cached_record, cached_type),),
                        path=tuple(recv_message.path)
                    )
                    while cached_type != 'A':
                        cached_for, cached_record, cached_type = self.find_question_in_cache(cached_record)
                        reply_message.authority += ((cached_for, cached_record, cached_type),)
                    self.dns_socket.sendto(reply_message.encode(), addr)
        else:
            self.print_data(f"cache에 {recv_message.questions}이 없습니다.")
            self.print_data(f"캐시에 정보가 없으므로 recursive, iterative 모두 할 수 없습니다.")

            "사실 TLD 정보는 캐시에 들어있기 때문에, 진작 보낼 수 있었어야 한다."
            reply_message = Message(
                message_id=recv_message.message_id,
                query_flag=False,
                questions=recv_message.questions,
                recursive_desired=False,
                recursive_available=self.recursive_flag,
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

port = int(sys.argv[1])
# 포트 번호 범위 체크 필요?

root_dns_server = RootDnsServer(port, cache_file_name="root_dns_cache.txt", server_name="root dns server")
root_dns_server.start()