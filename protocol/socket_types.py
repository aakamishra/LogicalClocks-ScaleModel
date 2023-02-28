ERROR_BYTES_INVALID = "ERROR bytes not decodable."
ERROR_ARGS_LENGTH = "ERROR Incorrect number of arguments provided."
ERROR_ARG_TYPE = "ERROR Argument provided is not valid for opcode."

class SocketMessage:
    def __init__(self, fields, raw_bytes):
        self.generated_error_code = None
        self.fields = fields
        for field in fields.keys():
            assert field not in self.__dict__
            setattr(self, field, None)
        self.decode(raw_bytes)
    
    def decode(self, raw_bytes):
        args = None
        try:
            args = raw_bytes.decode("UTF-8").split("||")[1:]
        except UnicodeDecodeError:
            self.generated_error_code = ERROR_BYTES_INVALID
            return
        if len(args) != len(self.fields):
            self.generated_error_code = ERROR_ARGS_LENGTH
            return
        
        for (field, cls), val in zip(self.fields.items(), args):
            try:
                setattr(self, field, cls(val))
            except ValueError:
                self.generated_error_code = ERROR_ARG_TYPE
                return

class MessageRequest(SocketMessage):
    def __init__(self, raw_bytes):
        fields = {
            "id": str,
            "recipient": str,
            "logical_time": str
        }
        super().__init__(fields, raw_bytes)

class MessageReply(SocketMessage):
    def __init__(self, raw_bytes):
        fields = {
            "error_code": str
        }
        super().__init__(fields, raw_bytes)

class RefreshRequest(SocketMessage):
    def __init__(self, raw_bytes):
        fields = {
            "id": str
        }
        super().__init__(fields, raw_bytes)

class RefreshReply(SocketMessage):
    def __init__(self, raw_bytes):
        fields = {
            "id": str,
            "logical_time": str,
            "queue_length": str,
            "error_code": str
        }
        super().__init__(fields, raw_bytes)