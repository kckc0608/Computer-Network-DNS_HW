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
                print("명령어 형식이 잘못되었습니다.")
            if cmd[1] == "on":
                self.recursive_flag = True
                print("recursive processing : ON")
            elif cmd[1] == "off":
                self.recursive_flag = False
                print("recursive processing : OFF")
            else:
                print("명령어 형식이 잘못되었습니다. on/off 중 하나를 입력하세요.")

        else:
            print("존재하지 않는 명령어 입니다.")

    def process_reply(self, recv_message: Message, addr):
        super().process_reply(recv_message, addr)
        # reply 를 받았다는 것 == com tld dns server 가 요청을 보냈었다는 것 == recursive 라는 이야기
        # 메세지 아이디에 적힌 것도 아니고, 그냥 자기한테 요청을 보냈던 addr 로 그냥 응답하면 될 것 같다.
        self.dns_socket.sendto(recv_message.encode(), self.msg_id_table[recv_message.message_id])
        self.print_data(f"{self.msg_id_table[recv_message.message_id]}에 응답을 보냈습니다.")



