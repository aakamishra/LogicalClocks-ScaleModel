import multiprocessing as mp
import threading as th
import time 
import socket
from server import Server
import os
import protocol as wp
import random
import pandas as pd
import logging

class LogData:
    def __init__(
            self,
            id,
            clock_counter,
            event_type,
            post_queue_length,
            sender=None,
            reciever=None,
            description=None,
    ):
        self.id = id
        self.clock_counter = clock_counter
        self.event_type = event_type
        self.post_queue_length = post_queue_length
        self.sender = sender
        self.reciever = reciever
        self.description = description
    
    def get_log_string(self):
        return f"{self.id},{time.time_ns()},{self.clock_counter},{self.event_type}," + \
        f"{self.sender},{self.reciever},{self.description},{self.post_queue_length}"
        
    def update(self, logger):    
        info_str = self.get_log_string() 
        print(info_str)      
        logger.info(info_str)

class LogicalClock:
    def __init__(self):
        self.counter = 0
    
    def update(self, update_value=None):
        if update_value is None or self.counter >= update_value:
            # Calculate elapsed time since start
            self.counter += 1
        else:
            self.counter = update_value + 1
                
                
def run_server() -> None:
    server = Server()

    host = "localhost"
    port = 50051

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, port))

    print("socket binded to port", port)

    # put the socket into listening mode
    s.listen(10)
    print("socket is listening")

    start_time = time.time()
    thread_list = []

    while True:
        # establish connection with client
        c, addr = s.accept()
        print('Connected to :', addr[0], ':', addr[1])

        # Start a new thread and return its identifier
        t = th.Thread(target=server.HandleNewConnection,
                  daemon=False, args=(c, addr))
        t.start()
        thread_list.append(t)
        
        if time.time() - start_time > 80:
            print("server finished")
            for t in thread_list:
                t.join()
            return 
    

def run_client_process(id):
    
    time.sleep(1)
    # initalize recpient metadata
    recp = []
    if id == 1:
        recp = [2,3]
    elif id == 2:
        recp = [1,3]
    else: # value == 3
        recp = [1,2]
    
    # create object for sending messages
    message_creator = wp.encode
    client_stub = wp.client_stub.ServerStub("localhost", 50051)
    
    # get current process data
    pid = os.getpid()
    speed = random.randint(1, 6)
    
    initalized = f"(pid: {pid}) - (speed: {speed}) - (recp: {recp[0]};{recp[1]}) - (id: {id})"
    #print(initalized)
    
    # create logger
    lgr = logging.getLogger(f"client-{id}")
    lgr.setLevel(logging.DEBUG) # log all escalated at and above DEBUG
    # add a file handler
    fh = logging.FileHandler(f"logs/client-{id}.csv")
    fh.setLevel(logging.DEBUG) # ensure all messages are logged to file

    # create a formatter and set the formatter for the handler.
    frmt = logging.Formatter('%(message)s')
    fh.setFormatter(frmt)

    # add the Handler to the logger
    lgr.addHandler(fh)

    LogData(
        id="Process Id",
        clock_counter="Clock Counter",
        event_type="Event Type",
        post_queue_length="Queue Length",
        sender="Sender",
        reciever="Reciever",
        description="Description"
    ).update(lgr)
    
    start_time = last_time = time.time()
    clock = LogicalClock()
    LogData(
        id=id,
        clock_counter=clock.counter,
        event_type="CREATE",
        post_queue_length=None,
        description=initalized
    ).update(lgr)
    
    while True:
        new_time = time.time()
        elapsed_time = new_time - last_time

        if new_time - start_time > 65:
            client_stub.sck.close()
            print(f"finished: {id}")
            return 0
        # Check if the limit on a second has passed
        if elapsed_time >= 1/speed:
            last_time = new_time
            
            # run server update to check queue
            # note that the queue would fill up
            # regardless of whether the process checks 
            # or not on the server side
            query = message_creator.RefreshRequest(id=id)
            msg = client_stub.DeliverMessages(query)
            if len(msg.error_code) > 0:
                print(f"[error] (pid: {pid}) {msg.error_code}")
            
            # store queue value
            # TODO: Change queue_length to just be an int type in RefreshReply type
            queue_length = int(msg.queue_length)
            
            # update logical clock (time is negative if queue is empty = no update)
            # TODO: Same change for logical time as for queue_length
            clock.update(int(msg.logical_time))
            if queue_length < 0: # TODO: understand how can be queue_length be negative?
                # random decision process
                random_value = random.randint(1, 10)
                
                # check if we are to message a single process
                # TODO: move each case into separate functions
                if random_value in [1,2]:
                    msg = message_creator.MessageRequest(id=id, 
                                                        recipient=recp[random_value-1], 
                                                        logical_time=clock.counter)
                    rsp = client_stub.SendMessage(msg)
                    if len(rsp.error_code) > 0:
                        print(f"[error] message not delivered {rsp.error_code}")
                    else:
                        sent = f"{id}->{recp[random_value-1]}"
                        print(f"{id}: {queue_length}")
                        LogData(
                            id=id,
                            clock_counter=clock.counter,
                            event_type="SEND",
                            post_queue_length=queue_length,
                            sender=id,
                            reciever=recp[random_value-1],
                        ).update(lgr)
                elif random_value == 3:
                    # case for messaging both processes
                    
                    for r in recp:
                        msg = message_creator.MessageRequest(id=id, 
                                                            recipient=r, 
                                                            logical_time=clock.counter)
                        rsp = client_stub.SendMessage(msg)
                        
                        if len(rsp.error_code) > 0:
                            print(f"[error] message not delivered {rsp.error_code}")
                        else:
                            LogData(
                                id=id,
                                clock_counter=clock.counter,
                                event_type="SEND",
                                post_queue_length=queue_length,
                                sender=id,
                                reciever=r,
                            ).update(lgr)
                else:
                    LogData(
                        id=id,
                        clock_counter=clock.counter,
                        event_type="INTERNAL",
                        post_queue_length=queue_length,
                        description=random_value
                    ).update(lgr)
            else:
                LogData(
                    id=id,
                    clock_counter=clock.counter,
                    event_type="RECEIVED",
                    post_queue_length=queue_length,
                    sender=msg.id,
                    reciever=id
                ).update(lgr)
                    
        time.sleep(0.001)
    

if __name__ == "__main__":
    print("Hello!")

    proc1 = mp.Process(target=run_client_process, args=(1,))
    proc2 = mp.Process(target=run_client_process, args=(2,))
    proc3 = mp.Process(target=run_client_process, args=(3,))
    
    server_thread = mp.Process(target=run_server)
    server_thread.start()
    
    proc1.start()
    proc2.start()
    proc3.start()
    
    
    proc1.join()
    proc2.join()
    proc3.join()
    server_thread.join()
    
    
