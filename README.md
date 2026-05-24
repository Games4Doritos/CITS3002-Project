# CITS3002-Project

| Student Name   | Student Number |
|----------------|----------------|
| Tom Nylund     | 22708177 |
| Evan Miocevich | 24147733 |

This is the implementation for the Computer Networks (CITS3002) Project: Mini Internet Protocol Stack Simulator (Python).

It simulates a simplified network stack consisting of the Data Link Layer (2), the Network Layer (3) and the Transport Layer (4), in the network topology below:
    
    A--------R1--------B
        L1        L2

    (A and B are Hosts, R1 is a Router, L1 and L2 are the physical links/interfaces)

## How to run
Dependencies:
- Python

Single command to run:

```
 python main.py [size]
```
```[size]``` is the single command line argument, an integer size of the message to send in bytes, e.g 100 for 100-byte message

## Project Structure
```
.
|
├─── config.py
|
├─── devices.py
|
├─── main.py
|
├─── protocol.py
|
├─── README.md (this)
|
```
## Source Code Explanation
config.py -> contains all constants and constraints for the simulation, e.g. MAC and IP addresses, routing tables, arp tables

protocol.py -> defines the UDPSegment, IPPacket, EthernetFrame, TransportLayer, NetworkLayer and DataLinkLayer classes, which represent the headers for the three different layers and those layers respectively

devices.py -> defines the Host and Router classes, which implement the TransportLayer, NetworkLayer and DataLinkLayer classes to form fully functioning devices

main.py -> runs the simulation by taking a command line argument and setting up and connecting all devices in the topology

