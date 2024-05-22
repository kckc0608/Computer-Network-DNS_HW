import json


class Message:

    def __init__(self,
                 message_id,
                 questions,
                 query_flag,
                 recursive_desired,
                 recursive_available,
                 answers=tuple(),
                 authority=tuple(),
                 path=tuple()):
        self.message_id = message_id
        self.questions = questions
        self.query_flag = query_flag
        self.recursive_desired = recursive_desired
        self.recursive_available = recursive_available
        self.answers = answers
        self.authority = authority
        self.path = path

    def encode(self):
        return json.dumps(self.__dict__, ensure_ascii=False).encode()

    def __str__(self):
        return json.dumps(self.__dict__, ensure_ascii=False)