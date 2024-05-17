import json


class Message:

    def __init__(self,
                 message_id,
                 questions,
                 query_flag,
                 recursive_flag,
                 answers=tuple(),
                 authority=tuple()):
        self.message_id = message_id
        self.questions = questions
        self.query_flag = query_flag
        self.recursive_flag = recursive_flag
        self.answers = answers
        self.authority = authority

    def encode(self):
        return json.dumps(self.__dict__, ensure_ascii=False).encode()

    def __str__(self):
        return json.dumps(self.__dict__, ensure_ascii=False)