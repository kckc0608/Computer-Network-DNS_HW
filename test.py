from message import Message
import json
message = Message(1, "q", False, False)
print(message.encode())

x = tuple()
x += (1, 2, 3)
x += (2, 3, 4)
print(x)