from dns import Dns

class RecursiveDns(Dns):
    def __init__(self, port, cache_file_name, server_name):
        super().__init__(port, cache_file_name, server_name)
        self.recursive_flag = False

    def process_command(self, cmd):
        if cmd[0] == "exit":
            exit(0)

        elif cmd[0] == "cache":
            self.load_cache()
            for item in self.dns_cache.items():
                self.print_data(item)

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

