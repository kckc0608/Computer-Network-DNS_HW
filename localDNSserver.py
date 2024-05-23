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
import sys
from dns import Dns
from message import Message
os.system("")


class LocalDns(Dns):

    def __init__(self, port, cache_file_name, server_name):
        super().__init__(port, cache_file_name, server_name)
        self.root_dns_port = self.dns_info.get('root_dns_server')[1]

    def load_config(self, find=None, exclude=None):
        return super().load_config(['root_dns_server'], exclude)

    def process_query(self, recv_message: Message, addr):
        super().process_query(recv_message, addr)

        cached_for, cached_record, cached_type = self.find_question_in_cache(recv_message.questions)
        self.print_data((cached_for, cached_record, cached_type))

        if cached_for:
            if recv_message.questions == cached_for:
                self.print_data("캐싱된 answer를 전송합니다.")
                reply_message = Message(
                    message_id=recv_message.message_id,
                    query_flag=False,
                    questions=recv_message.questions,
                    recursive_desired=recv_message.recursive_desired,
                    recursive_available=False,
                    answers=tuple(recv_message.answers),
                    authority=tuple(recv_message.authority),
                    path=tuple(recv_message.path)
                )

                while cached_type and cached_type != 'A':
                    reply_message.answers += ((cached_for, cached_record, cached_type),)
                    cached_for, cached_record, cached_type = self.find_question_in_cache(cached_record)

                reply_message.answers += ((cached_for, cached_record, cached_type),)
                self.print_data(reply_message)
                self.dns_socket.sendto(reply_message.encode(), self.msg_id_table[recv_message.message_id])
            else:
                self.print_data("캐싱된 authority에 쿼리를 재전송합니다.")
                query = recv_message
                query.recursive_desired = True  # local DNS server는 항상 recursive 처리를 요청한다.
                while cached_type != 'A':
                    cached_for, cached_record, cached_type = self.find_question_in_cache(cached_record)
                authority_port = self.ip_to_port[cached_record]
                self.print_data(f"authority port: {authority_port}")
                self.dns_socket.sendto(query.encode(), (self.host, authority_port))
        # 3. root dns 서버에 요청 보내기
        else:
            query = recv_message
            query.recursive_desired = True  # local DNS server는 항상 recursive 처리를 요청한다.
            self.print_data(f"{query.questions} 도메인 정보가 캐시에 없습니다. root에 쿼리를 보냅니다.")
            self.dns_socket.sendto(query.encode(), (self.host, self.root_dns_port))

    def process_reply(self, recv_message: Message, addr):
        super().process_reply(recv_message, addr)

        cached_for, cached_record, cached_type = self.find_question_in_cache(recv_message.questions)
        while cached_for and cached_type != 'A':
            cached_for, cached_record, cached_type = self.find_question_in_cache(cached_record)

        if recv_message.answers:
            self.print_data("answers 가 들어있는 응답을 받았습니다.")
            self.print_data(f"client port : {self.msg_id_table[recv_message.message_id]}")
            self.print_data(f"{recv_message}")

            # Caching
            for answer_for, answer_record, answer_record_type in recv_message.answers:
                self.save_record_into_cache((answer_for, answer_record, answer_record_type))

            self.dns_socket.sendto(recv_message.encode(), self.msg_id_table[recv_message.message_id])
        elif recv_message.authority:
            self.print_data("authority 가 들어있는 응답을 받았습니다.")
            self.print_data(recv_message.authority)

            # Caching
            for auth_for, auth_record, auth_type in recv_message.authority:
                self.save_record_into_cache((auth_for, auth_record, auth_type))

            auth_for, auth_record, auth_type = self.find_question_in_cache(recv_message.questions)
            while auth_type != 'A':
                auth_for, auth_record, auth_type = self.find_question_in_cache(auth_record)

            # 이 과정을 거치면 auth_type = A 인 레코드를 얻을 수 있다고 가정함.
            self.print_data("authority server에 요청을 보냅니다.")
            if auth_record not in self.ip_to_port:
                self.print_data(self.ip_to_port)
                raise Exception(f"IP 주소 {auth_record} 에 대한 포트 정보가 없습니다.")

            authority_port = self.ip_to_port[auth_record]
            query = recv_message
            query.authority = tuple()
            query.query_flag = True
            self.dns_socket.sendto(recv_message.encode(), (self.host, authority_port))
        else:
            self.print_data("호스트 이름에 대한 IP주소를 찾지 못했습니다.")
            reply_message = Message(
                message_id=recv_message.message_id,
                query_flag=False,
                questions=recv_message.questions,
                recursive_desired=False,
                recursive_available=False,
                answers=tuple(recv_message.answers),
                authority=tuple(recv_message.authority),
                path=tuple(recv_message.path)
            )
            self.dns_socket.sendto(reply_message.encode(), self.msg_id_table[recv_message.message_id])


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

    # 포트 번호 범위 체크 필요?
    local_dns_port = int(sys.argv[1])

    local_dns_server = LocalDns(local_dns_port, server_name='local_dns_server', cache_file_name='local_dns_cache.txt')
    local_dns_server.start()

except Exception as ex:
    print("예상치 못한 오류가 발생했습니다.")
    print(ex)
    input("계속하려면 아무 키나 누르십시오...")
