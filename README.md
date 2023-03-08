# LogicalClocks-ScaleModel
CS262 Demo Day 2 Assignment, Visualization / Scale Model of Logical Clocks Scaling

## Experiment Descriptions and Results

Our [experiment report is here.](experiments.md)

## Engineering Notebook

Our [engineering notebook is here.](notebook.md)

## Model Design Document

Our [design document is here.](design.md)

## Usage

To run a single trial of the peer to peer connection logical clock simulator. 

```
python p2p_simulator.py
```

To run a single trial of the centralized server model.

```
python simulator.py
```

To run a full experiment (5 trials) and visualize them.

```
make
```

## Unit Tests

These tests check that the logical clock and log data classes are properly initialized, and that the virtual machine's run() method executes correctly. The setUp() method initializes a VirtualMachine object with the configuration [1, ['2000', '2001', '2002'], 1], and each test method uses this object to test the appropriate behavior. Note that in test_virtual_machine_run(), the run() method is tested using a mock for socket.socket, which allows us to test the code without actually attempting to create a network connection. We also check for the counter logic of the lamport logical clock and the formatting of the log strings as well. After the process mock finishes, we assert that the prcoess "communicates" by calling the appropriate thread functions and asserting that they were called. 

In order to run the unit tests, just type in the following command
```
python test.py
```