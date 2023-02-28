def MessageRequest(id, recipient, logical_time):
    opcode = 0
    return f"{opcode}||{id}||{recipient}||{logical_time}".encode("ascii")

def MessageReply(error_code):
    opcode = 0
    return f"{opcode}||{error_code}".encode("ascii")

def RefreshRequest(id):
    opcode = 1
    return f"{opcode}||{id}".encode("ascii")

def RefreshReply(id, logical_time, queue_length, error_code):
    opcode = 1
    return f"{opcode}||{id}||{logical_time}||{queue_length}||{error_code}".encode("ascii")