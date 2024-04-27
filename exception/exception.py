

class QuantException(Exception):

    def __init__(self, code=None, message=None):
        super().__init__(message)
        self.message = message
        self.code = code if code else -1
