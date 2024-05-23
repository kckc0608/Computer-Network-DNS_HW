from dns import Dns
from message import Message

class RecursiveDns(Dns):
    def __init__(self, port, cache_file_name, server_name):
        super().__init__(port, cache_file_name, server_name)
        self.recursive_flag = False

    def process_command(self, cmd):
        if cmd[0] == "exit":
            exit(0)

        elif cmd[0] == "cache":
            self.load_cache()
            for key, item in self.dns_cache.items():
                for record_type, record_value in item.items():
                    self.print_data(f"{key} : {record_value} ({record_type})")

        elif cmd[0] == "recursiveFlag":
            if len(cmd) != 2:
                self.print_data("명령어 형식이 잘못되었습니다.", print_type='error')
            elif len(cmd) == 1:
                self.print_data("명령어 형식이 잘못되었습니다. recursiveFlag [on|off]", print_type='error')

            if cmd[1] == "on":
                self.recursive_flag = True
                print("recursive processing : ON")
            elif cmd[1] == "off":
                self.recursive_flag = False
                print("recursive processing : OFF")
            else:
                self.print_data("명령어 형식이 잘못되었습니다. recursiveFlag [on|off]", print_type='error')

        else:
            self.print_data("존재하지 않는 명령어 입니다.", print_type='error')

    def process_reply(self, recv_message: Message, addr):
        super().process_reply(recv_message, addr)
        self.dns_socket.sendto(recv_message.encode(), self.msg_id_table[recv_message.message_id])
        self.print_data(f"{self.msg_id_table[recv_message.message_id]}에 응답을 보냈습니다.")

    def send_empty_reply(self, recv_message: Message, addr):
        reply_message = Message(
            message_id=recv_message.message_id,
            query_flag=False,
            questions=recv_message.questions,
            recursive_desired=recv_message.recursive_desired,
            recursive_available=self.recursive_flag,
            answers=tuple(recv_message.answers),
            authority=tuple(recv_message.authority),
            path=tuple(recv_message.path)
        )
        self.dns_socket.sendto(reply_message.encode(), addr)
