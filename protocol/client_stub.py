import socket
from . import socket_types

class ServerStub:

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sck = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.sck.connect((host,port))
    
    def SendMessage(self, message_request):
        self.sck.send(message_request)
        message_reply_bytes = self.sck.recv(1024)
        return socket_types.MessageReply(message_reply_bytes)

    def DeliverMessages(self, refresh_request):
        self.sck.send(refresh_request)
        refresh_reply_bytes = self.sck.recv(1024)
        return socket_types.RefreshReply(refresh_reply_bytes)