## Engineering Notebook

### Entry 3/1/2023

To design a logical clock modelling program that uses Python multiprocessing to model three processes that connect to a fourth process running a centralized server and use a Lamport clock implementation to synchronize using socket connections.

```python
class LogicalClock:
    def __init__(self):
        self.counter = 0
    
    def update(self, update_value=None):
        if update_value is None or self.counter >= update_value:
            # Calculate elapsed time since start
            self.counter += 1
        else:
            self.counter = update_value + 1
```

Define the message format: We need to define the format of the messages that will be exchanged between the processes. The message format should include a message ID, sender ID, receiver ID, and Lamport timestamp. We put our implementation for the message formatting in `protocol`.

Implement the Lamport clock: We need to implement the Lamport clock algorithm to keep track of the logical time in each process. The Lamport clock is a simple algorithm that increments the local time whenever a process sends or receives a message. The logical time is updated as the maximum of the local time and the timestamp of the received message plus one.

Implement the centralized server: We need to implement a centralized server that will receive messages from the processes and update the Lamport clocks accordingly. The server should maintain a queue of messages and process them in the order of their timestamps. We base our centralized server as a echo server that is implemented in `server.py`


#### Technical Plan for Centralized Server

Implement the processes: We need to implement the three processes that will exchange messages with each other and with the server. Each process should have a unique ID and a Lamport clock.

Use Python multiprocessing and sockets: We can use the Python multiprocessing library to create separate processes for each of the three processes and the server. We can use sockets to establish connections between the processes and the server and exchange messages.

Synchronize the processes: To synchronize the processes, each process should send a message to the server with its current Lamport timestamp whenever it sends or receives a message.

Handle concurrency: Since multiple processes can send messages to the server simultaneously, we need to handle concurrency issues. We can use locks to protect the message inbox of each client process. 

By following these steps, we can design a logical clock modelling program that uses Python multiprocessing to model three processes that connect to a fourth process running a centralized server and use a Lamport clock implementation to synchronize using socket connections.

**NOTE** We abandoned this idea, and moved on from p2p after noticing that we would eventually face scalability issues. 

### Entry 3/3/2023

When multiple processes tried to send messages to the server simultaneously, some of the messages were being lost, and the timestamps were not being updated correctly. I realized that I needed to handle concurrency issues to ensure that only one process could access the server queue at a time.

After some debugging we used the `mp.Lock` to protect our per-process queue. Lock object was used to synchronize access to shared resources. We modified the code to use locks to ensure that only one process could access the server queue at a time. 

### Entry 3/5/2023

After successfully fixing the concurrency bugs in our logical clock modeling program, we started working on implementing logging to record the events and messages exchanged between the processes. However, we realized that there were issues with the log files being empty. The issue was related to the nature of forking processes in Python. When a process forks, it creates a copy of itself, including the file descriptor for the log file. However, when the child process writes to the log file, it writes to the same file descriptor as the parent process, which can cause the log file to become empty. We made sure the a dupped version of the logging module in Python wrote the log messages to the new file descriptor in each child process, ensuring that the log files were not empty. This fixed our file descriptor inheritance problem. 

### Entry 3/6/2023

We decided to re-design the simulator to use peer-to-peer socket connections between each process using a producer and a consumer thread. This redesign eliminates the internal server latency issues and provides a more efficient and scalable solution.

In this new design, each process acts as both a producer and a consumer. When a process sends a message, it becomes a producer and adds the message to anothers message queue. A consumer thread that reads messages from the other processes' message queues and updates its Lamport clock accordingly. Each process maintains its own Lamport clock, which is updated based on the messages received from other processes.

The simulator now waits for 1/speed seconds before executing writes and reads (instead of sleeping here, we choose to sync with system time instead), where speed is a parameter that can be set by the user. This ensures that the simulation runs at a realistic pace and provides a more accurate representation of real-world distributed systems.

### Entry 3/7/2023

One of the main problems we encountered was running with a producer thread that simply looked at the randomly generated code value without checking for if a message was actually sent. In this case we see that we must somehow signal the producer thread to ensure that the message is send correctly and only when the actual queue is empty and the number is correct. In this case we first found a race condition with reading the queue's value length because at times the server accidentally commited a send and recieve at the same. Then we used locks, we ran into deadlock issues regarding sub functions that also use the `with lock` syntax. Finally, we saw that we still had a race condition aside from the locking and fixes that we implemented.

In the end we joined the producer logic to the main thread and sent messages conditional on the op code and the queue length all under lock such that the clock counter time access was atomic. This fixed all of logging issues. The last logging issue we faced was making sure to actually lock post the event rather than before the event. This way, we managed to eliminate the log coming in with the wrong counter time. 