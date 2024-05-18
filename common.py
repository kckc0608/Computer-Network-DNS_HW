COLOR = {
    "HEADER": "\033[95m",
    "BLUE": "\033[94m",
    "GREEN": "\033[92m",
    "RED": "\033[91m",
    "ENDC": "\033[0m",
}


def print_data(_data):
    #  print(f"\u001B[s\u001B[A\u001B[999D\u001B[S\u001B[L", end="", flush=True)
    print(f"\u001B[999D\u001B[K", end="", flush=True)
    print(COLOR["GREEN"], "[info] ", COLOR["ENDC"], end='', flush=True)
    #  print(f"{_data}\u001B[u", end='', flush=True)
    print(f"{_data}\n", end='', flush=True)
    print(">> ", end='', flush=True)