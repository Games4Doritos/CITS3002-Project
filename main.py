from devices import Host, Router
from config import (
    IP_HOST_A, IP_HOST_B, MAC_HOST_A, MAC_HOST_B,
    ARP_TABLE_HOST_A, ARP_TABLE_HOST_B, ARP_TABLE_R1,
    ROUTING_TABLE_HOST_A, ROUTING_TABLE_HOST_B, ROUTING_TABLE_R1,
    R1_IFACE_IP, R1_IFACE_MAC

)

import sys

def main():
    # validates CLI arguments
    args = sys.argv
    if len(args) != 2:
        raise RuntimeError("Error: A single argument for data size was not passed")
    dataSize = int(args[1])
    
    # initialises Host A in the topology
    hostA = Host(
        name="Host A",
        ip=IP_HOST_A,
        mac=MAC_HOST_A,
        routing_table=ROUTING_TABLE_HOST_A,
        arp_table=ARP_TABLE_HOST_A
    )
    
    # initialises Host B in the topology
    hostB = Host(
        name="Host B",
        ip=IP_HOST_B,
        mac=MAC_HOST_B,
        routing_table=ROUTING_TABLE_HOST_B,
        arp_table=ARP_TABLE_HOST_B
        
    )
    
    # initialises Router R1 in the topology
    router1 = Router(
        name="Router R1",
        routing_table=ROUTING_TABLE_R1,
        arp_table=ARP_TABLE_R1,
        iface_ip=R1_IFACE_IP,
        iface_mac=R1_IFACE_MAC
    )

    # connects the devices according to the topology
    hostA.connect(router1)
    router1.connect(hostA)
    router1.connect(hostB)
    hostB.connect(router1)
    
    # simulates Host A sending data to Host B by Host A initially receiving date from the application layer 
    # (not fully implemented as per spec, so a simple function call for Host A's transport layer)
    hostA.transport.receive_from_above(size=dataSize, dst_ip=IP_HOST_B)


if __name__ == "__main__":
    main()