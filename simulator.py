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


        
def update(logger, id, event_type, clock, desc, queue_length=None):    
    info_str = str(id) + "," + str(time.time_ns()) + "," + str(clock.counter) + "," + str(event_type) + "," + str(desc) + "," + str(queue_length)  
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
    
    initalized = f"(pid: {pid}), (speed: {speed}), (recp: {recp}), (id: {id})"
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
    
    start_time = last_time = time.time()
    clock = LogicalClock()
    update(lgr, id, "CREATE", clock, initalized)
    
    
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
            queue_length = int(msg.queue_length)
            
            # update logical clock (time is negative if queue is empty = no update)
            clock.update(int(msg.logical_time))
            if queue_length < 0:
                # random decision process
                random_value = random.randint(1, 10)
                
                # check if we are to message a single process
                if random_value in [1,2]:
                    msg = message_creator.MessageRequest(id=id, 
                                                        recipient=recp[random_value-1], 
                                                        logical_time=clock.counter)
                    rsp = client_stub.SendMessage(msg)
                    if len(rsp.error_code) > 0:
                        print(f"[error] message not delivered {rsp.error_code}")
                    else:
                        sent = f"{id}->{recp[random_value-1]}"
                        #print("S " + sent)
                        update(lgr, id, "SEND", clock, sent)
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
                            sent = f"{id}->{r}"
                            #print("S "+sent)
                            update(lgr, id, "SEND", clock, sent)
                else:
                    internal = f"{id},{random_value}"
                    #print(f"I " + internal)
                    update(lgr, id, "INTERNAL", clock, internal)
            else:
                received = f"{msg.id}->{id}"
                #print("R " + received)
                update(lgr, id, "RECEIVED", clock, received, queue_length=queue_length)
                    
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
    
    
