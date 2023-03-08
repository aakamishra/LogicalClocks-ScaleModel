from multiprocessing import Process, Lock
import os
import socket
from _thread import *
import threading
import time
from threading import Thread
import random
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
 
class VirtualMachine:
    def __init__(self, config):
        # set initial op-code
        self.op_code = 0
        
        # queue and the lock to protect it
        self.queue_lock = Lock()
        self.queue = []
        
        # pid and global state
        self.pid = None
        self.config = config
        
        # process value 
        self.p_val = config[2]
        self.speed = random.randint(1, 6)
        self.ports_list = config[1]
        
        # create logical clock for this machine
        self.clock = LogicalClock()
        
        
        
    def run(self):
        self.pid = os.getpid()
        
        # create logger
        self.lgr = logging.getLogger(f"{self.p_val}")
        self.lgr.setLevel(logging.DEBUG) # log all escalated at and above DEBUG
        # add a file handler
        fh = logging.FileHandler(f"logs/{self.p_val}.csv")
        fh.setLevel(logging.DEBUG) # ensure all messages are logged to file

        # create a formatter and set the formatter for the handler.
        frmt = logging.Formatter('%(message)s')
        fh.setFormatter(frmt)

        # add the Handler to the logger
        self.lgr.addHandler(fh)
        
        init_thread = Thread(target=self.init_machine)
        init_thread.start()
        #add delay to initialize the server-side logic on all processes
        
        
        time.sleep(3)
        
        # extensible to multiple producers
        prods = []
        agent = 0
        for i in range(len(self.ports_list)):
            port = self.ports_list[i]
            if self.p_val != (i + 1):
                agent += 1
                prod_thread = Thread(target=self.producer, args=(port, agent, i+1,))
                prods.append(prod_thread)
                prod_thread.start()

        start_time = last_time = time.time()
        
        while True:
            new_time = time.time()
            elapsed_time = new_time - last_time
            
            if new_time - start_time > 65:
                for t in prods:
                    t.join()
                return 
            
            if elapsed_time >= 1/self.speed:
                last_time = new_time
                
                self.op_code = random.randint(1,10)
                val = -1
                n = -1
                
                with self.queue_lock:
                    n = len(self.queue)
                    if n > 0:
                        id, val = self.queue.pop(0)
                        # received = f"{id}->{self.p_val}"
                        LogData(
                            id=self.p_val,
                            clock_counter=self.clock.counter,
                            event_type="RECEIVED",
                            post_queue_length=n,
                            sender=id,
                            reciever=self.p_val
                        ).update(self.lgr)
                    else:
                        internal = f"{self.p_val},{self.op_code}"
                        #print(f"I " + internal)
                        LogData(
                            id=self.p_val,
                            clock_counter=self.clock.counter,
                            event_type="INTERNAL",
                            post_queue_length=n,
                            description=self.op_code
                        ).update(self.lgr)
                self.clock.update(int(val))
            
    
    def init_machine(self):
        HOST = str(self.config[0])
        PORT = int(self.ports_list[self.p_val - 1])
        print(HOST, PORT, self.p_val)
        # create the socket port for listening
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # bind to the port number
        s.bind((HOST, PORT))
        
        # start listening on port
        s.listen()

        LogData(
            id="Process Id",
            clock_counter="Clock Counter",
            event_type="Event Type",
            post_queue_length="Queue Length",
            sender="Sender",
            reciever="Reciever",
            description="Description"
        ).update(self.lgr)
        
        initalized = f"(pid: {self.pid}) - (speed: {self.speed}) - (recp: {HOST};{PORT}) - (id: {self.p_val})"

        LogData(
            id=id,
            clock_counter=self.clock.counter,
            event_type="CREATE",
            post_queue_length=None,
            description=initalized
        ).update(self.lgr)
        
        while True:
            conn, addr = s.accept()
            start_new_thread(self.consumer, (conn,))
    
    def consumer(self, conn):
        start_time = time.time()
        while True:
            if time.time() - start_time > 60:
                return
            data = conn.recv(1024)
            data_value = data.decode('ascii').split(",")
            if len(data_value) > 1:
                id, val = data_value[0], data_value[1]
                with self.queue_lock:
                    self.queue.append((id, val))
    
    def producer(self, port, agent, recv_p_val):
        host= "127.0.0.1"
        port = int(port)
        s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        
        try:
            s.connect((host,port))
            
            start_time = last_time = time.time()
            while True:
                new_time = time.time()
                elapsed_time = new_time - last_time

                if time.time() - start_time > 65:
                    return 
                
                if elapsed_time < 1/self.speed:
                    continue

                last_time = new_time
                n = 0
                with self.queue_lock:
                    n = len(self.queue)
                
                if n == 0:
                    code_value = self.op_code

                    if agent == code_value or code_value == 3 and code_value != 0:
                        msg = f"{self.p_val},{self.clock.counter}"
                        # sent = f"{self.p_val}->{recv_p_val}"
                        # self.update(self.p_val, "SEND", sent)
                        queue_length = None
                        with self.queue_lock:
                            queue_length = len(self.queue)
                        LogData(
                            id=self.p_val,
                            clock_counter=self.clock.counter,
                            event_type="SEND",
                            post_queue_length=queue_length,
                            sender=self.p_val,
                            reciever=recv_p_val,
                        ).update(self.lgr)
                        s.send(msg.encode('ascii'))


        except socket.error as e:
            print ("Error connecting producer: %s" % e)
        
    # def update(self, id, event_type, desc, queue_length=None):    
    #     info_str = str(id) + "," + str(time.time_ns()) + "," + str(self.clock.counter) + "," + str(event_type) + "," + str(desc) + "," + str(queue_length)  
    #     print(info_str)      
    #     self.lgr.info(info_str)

localHost= "127.0.0.1"
 

if __name__ == '__main__':   
    
    ports_list = [2056, 3056, 4056]

    config1=[localHost, ports_list, 1,]
    machine1 = VirtualMachine(config1)
    p1 = Process(target=machine1.run)
    
    config2=[localHost, ports_list, 2,]
    machine2 = VirtualMachine(config2)
    p2 = Process(target=machine2.run)
    
    config3=[localHost, ports_list, 3,]
    machine3 = VirtualMachine(config3)
    p3 = Process(target=machine3.run)
    
    p1.start()
    p2.start()
    p3.start()
    

    p1.join()
    p2.join()
    p3.join()
 
 