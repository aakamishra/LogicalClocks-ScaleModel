from multiprocessing import Process, Lock
import os
import socket
from _thread import *
import threading
import time
from threading import Thread
import random
import logging
import numpy as np

TOTAL_TIME = 60

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
    """
    Implementation of Lamport's Logicial Clock
    """
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
        self.op_code = (0, 0)
        
        # queue and the lock to protect it
        self.queue_lock = Lock()
        self.queue = []
        
        # pid and global state
        self.pid = None
        self.config = config
        
        # process value 
        self.p_val = config[2]
        self.speed = np.random.choice(np.arange(1,7), 1, p=[1/6, 1/6, 1/6, 1/6, 1/6, 1/6])[0]
        self.ports_list = config[1]
        
        # create logical clock for this machine
        self.clock = LogicalClock()
        self.last_time = 0
        
        
        
    def run(self, folder_id: int) -> None:
        """
        Run the main machine level thread and random simulation metrics.
        
        Args:
            folder_id (int): Folder id to put log files in
            
        Returns:
            None
        """
        
        # get pid of process for documenting reasons
        self.pid = os.getpid()
        
        # create logger
        self.lgr = logging.getLogger(f"{self.p_val}")
        self.lgr.setLevel(logging.DEBUG) # log all escalated at and above DEBUG
        # add a file handler
        fh = logging.FileHandler(f"logs/logs_{folder_id}/{self.p_val}.csv", mode='w')
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
        
        # localhost
        host= "127.0.0.1"

        # extensible to multiple producers
        sockets_dict = {}
        agent = 0
        for i in range(len(self.ports_list)):
            port = self.ports_list[i]
            if self.p_val != (i + 1):
                agent += 1
                port = int(port)
                s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                sockets_dict[agent] = (s, i + 1)
                try:
                    s.connect((host, port))
                except Exception as e:
                    print(e)
                

        start_time = self.last_time = time.time()
        
        while True:
            # update timing mechanism
            new_time = time.time()
            elapsed_time = new_time - self.last_time
            
            # if the experiment time is up close the connection
            if new_time - start_time > TOTAL_TIME + 5:
                for (conn, _) in sockets_dict.values():
                    conn.close()
                return 
            
            # do not do anything if the ticks per second have been exhausted
            if elapsed_time >= 1/self.speed:
                self.last_time = new_time
                
                self.op_code = (random.randint(1,10), self.clock.counter)
                val = -1
                n = -1
                
                # ensure thread saftey
                with self.queue_lock:
                    n = len(self.queue)
                    if n > 0:
                        # added log data, case for when queue is not empty
                        id, val = self.queue.pop(0)
                        LogData(
                            id=self.p_val,
                            clock_counter=self.clock.counter,
                            event_type="RECEIVED",
                            post_queue_length=n,
                            sender=id,
                            reciever=self.p_val,
                            description=self.op_code[0]
                        ).update(self.lgr)
                    elif self.op_code[0] >= 4:
                        # case for an internal event
                        
                        LogData(
                            id=self.p_val,
                            clock_counter=self.clock.counter,
                            event_type="INTERNAL",
                            post_queue_length=n,
                            description=self.op_code[0]
                        ).update(self.lgr)
                    elif self.op_code[0] in sockets_dict.keys():
                        # case for when we send a one off message
                        
                        s, id = sockets_dict[self.op_code[0]]
                        msg = f"{self.p_val},{self.clock.counter}"
                        try:
                            s.send(msg.encode('ascii'))
                        except BrokenPipeError:
                            pass
                        LogData(
                            id=self.p_val,
                            clock_counter=self.clock.counter,
                            event_type="SEND",
                            post_queue_length=n,
                            sender=self.p_val,
                            reciever=id,
                            description=self.op_code[0]
                        ).update(self.lgr)
                    else:
                        # case for when we message both of the other processes
                        for agent in sockets_dict.keys():
                            s, id = sockets_dict[agent]
                            msg = f"{self.p_val},{self.clock.counter}"
                            try:
                                s.send(msg.encode('ascii'))
                            except BrokenPipeError:
                                pass
                            LogData(
                                id=self.p_val,
                                clock_counter=self.clock.counter,
                                event_type="SEND",
                                post_queue_length=n,
                                sender=self.p_val,
                                reciever=id,
                                description=self.op_code[0]
                            ).update(self.lgr)

                self.clock.update(int(val))
            
    
    def init_machine(self) -> None:
        """
        Creates a new machine thread that monitors 
        and accepts new client connections and hands
        them off to a newly created consumer thread.
        
        Args:
            None
        
        Returns:
            None
        """
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
            id=self.p_val,
            clock_counter=self.clock.counter,
            event_type="CREATE",
            post_queue_length=None,
            description=initalized
        ).update(self.lgr)
        
        for _ in range(2):
            conn, addr = s.accept()
            start_new_thread(self.consumer, (conn,))
    
    def consumer(self, conn) -> None:
        """
        Consumes data from a network connection and adds it to a queue.

        Args:
            conn (socket.socket): The network connection to consume data from.

        Returns:
            None

        """
        # Record the start time so we know when to stop consuming.
        start_time = time.time()
        while True:
            # Check if we've been consuming for longer than the allowed time.
            if time.time() - start_time > TOTAL_TIME:
                # Close the connection and return to stop consuming.
                conn.close()
                return
            
            # Receive data from the connection.
            data = conn.recv(1024)

            # Split the received data into ID and value.
            data_value = data.decode('ascii').split(",")
            if len(data_value) > 1:
                id, val = data_value[0], data_value[1]
                
                # Add the ID and value to the shared queue, ensuring thread safety.
                with self.queue_lock:
                    self.queue.append((id, val))

        
# define localhost global address
localHost= "127.0.0.1"
 
if __name__ == '__main__':   
    
    jitter = random.randint(0, 500)

    # define ports for socket connections
    ports_list = [2056 + jitter, 3056 + jitter, 4056 + jitter]

    # create logging folder
    folder_id = random.randint(1, 10000)
    print(f"Folder ID: {folder_id}")
    os.mkdir(f"logs/logs_{folder_id}")
    
    # setup virtual machine 1, 2 and 3
    config1=[localHost, ports_list, 1,]
    machine1 = VirtualMachine(config1)
    p1 = Process(target=machine1.run, args=(folder_id,))
    
    config2=[localHost, ports_list, 2,]
    machine2 = VirtualMachine(config2)
    p2 = Process(target=machine2.run, args=(folder_id,))
    
    config3=[localHost, ports_list, 3,]
    machine3 = VirtualMachine(config3)
    p3 = Process(target=machine3.run, args=(folder_id,))
    
    # start all respective threads
    p1.start()
    p2.start()
    p3.start()
    

    p1.join()
    p2.join()
    p3.join()
 
 