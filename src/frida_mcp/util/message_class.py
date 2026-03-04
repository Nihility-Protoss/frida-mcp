from collections import deque


class MessageLog:
    def __init__(self):
        self.messages: deque = deque(maxlen=5000)
        self.append_size: int = 0
        self.output_size: int = 0

    def append(self, message):
        self.messages.append(message)
        self.append_size += 1

    def get_messages(self, _size):
        if len(self.messages) == 0:
            return []
        self.output_size = self.append_size
        snapshot = list(self.messages)
        if _size > 0:
            snapshot = snapshot[-_size:]
        else:
            snapshot = []
        return snapshot

    def get_new_messages(self):
        return self.get_messages(self.append_size - self.output_size)
