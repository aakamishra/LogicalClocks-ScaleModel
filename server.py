import socket
import threading as mp

import protocol as wp

socket.setdefaulttimeout(60 * 60)


class Server:
    def __init__(self):
        super().__init__()
        self.id_inbox = {i: [] for i in range(1, 4)}
        print("Inbox Init: ", self.id_inbox)


    def ReceiveMessage(self, raw_bytes: str) -> wp.encode.MessageReply:
        """
        Receives a raw string buffer from the user
        and stores the message in the correct recipient's inbox.
        Args:
            raw_bytes (str): A string buffer representing a message sent by a user,
            containing the message content,
            recipient username, and authentication token.
        Returns:
            wp.encode.MessageReply: A message reply object containing
            a version number and error code, if applicable.
        """

        request = wp.socket_types.MessageRequest(raw_bytes)
        if request.generated_error_code:
            return wp.encode.MessageReply(error_code=request.generated_error_code, )
        
        recp_id = int(request.recipient)
        
        self.id_inbox[recp_id].append((request.id, request.logical_time))
        return wp.encode.MessageReply(error_code="")

    def DeliverMessages(self, raw_bytes: str) -> wp.encode.RefreshReply:
        """
        Given a raw string buffer user request,
        validate the request and deliver a set of messages to the user.
        Args:
            raw_bytes (str): A raw string buffer user request.
        Returns:
            wp.encode.RefreshReply: A RefreshReply object containing
            the messages and/or error code.
        """

        request = wp.socket_types.RefreshRequest(raw_bytes)
        if request.generated_error_code:
            return wp.encode.RefreshReply(pid=-1, 
                                          logical_time=-1, 
                                          queue_length=-1,
                                          error_code=request.generated_error_code)

        n = len(self.id_inbox[int(request.id)])
        if n > 0:
            msg = self.id_inbox[int(request.id)].pop(0)
            id = msg[0]
            logical_time = msg[1]
            return wp.encode.RefreshReply(id=id,
                                          logical_time=logical_time,
                                          queue_length=n-1, 
                                          error_code=""
                                         )
        else:
            return wp.encode.RefreshReply(id=-1,
                                          logical_time=-1,
                                          queue_length=-1,
                                          error_code=""
                                        )

    def HandleNewConnection(self, c: socket.socket, addr: tuple) -> None:
        """
        This method handles incoming connections and spins off new threads to handle requests.
        Args:
            c (socket.socket): The socket object used for communication with the client.
            addr (tuple): The IP address and port number of the client.
        Returns:
            None
        """

        while True:
            try:
                data = c.recv(2048)
            except Exception as e:
                print("Connection Disrupted:", e, " - softhandler resolved")
                c.close()
                return
            decoded = ""
            try:
                decoded = data.decode("UTF-8")
            except UnicodeDecodeError:
                print("Unable to decode the message")
                c.close()

            args = decoded.split("||")
            if len(args) == 0:
                c.close()
                return

            try:
                opcode = int(args[0])
            except ValueError:
                opcode = -1

            opcode_map = {
                0: self.ReceiveMessage,
                1: self.DeliverMessages
            }

            if opcode in opcode_map.keys():
                result = opcode_map[opcode](data)
                c.send(result)
            else:
                # Invalid opcodes are dropped immediately, invalid opcodes
                #  occur when a connection is being closed by the client,
                #  or when a malicious / corrupted message is being sent
                c.close()
                return


if __name__ == "__main__":

    chatServer = Server()

    host = "0.0.0.0"
    port = 50051

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, port))

    print("socket binded to port", port)

    # put the socket into listening mode
    s.listen(10)
    print("socket is listening")

    while True:
        # establish connection with client
        c, addr = s.accept()
        print('Connected to :', addr[0], ':', addr[1])

        # Start a new thread and return its identifier
        mp.Thread(target=chatServer.HandleNewConnection,
                  daemon=False, args=(c, addr)).start()