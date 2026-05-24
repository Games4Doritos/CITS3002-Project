import math
from config import (
    IP_DEFAULT_TTL, IP_PROTO_UDP, ETHER_TYPE_IPV4,
    UDP_SRC_PORT, UDP_DST_PORT, UDP_HEADER_SIZE,
    L4_TYPE_DATA, L4_TYPE_ACK, UDP_MAX_DATA,
    IP_HOST_A, IP_HOST_B
)

##### HELPER FUNCTIONS #####

def compute_checksum(data: bytes) -> int:
    """Compute a 16-bit checksum by summing all bytes mod 65536."""
    checksum = 0
    for byte in data:
        checksum += byte
    return checksum % 65536


##### HEADER CLASSES #####

class UDPSegment:
    def __init__(self, src_port, dst_port, seg_type, seq, payload=b""):
        self.src_port = src_port
        self.dst_port = dst_port
        self.length = len(payload) + UDP_HEADER_SIZE
        self.checksum = compute_checksum(payload)
        self.type = seg_type
        self.seq = seq
        self.payload = payload

    def __repr__(self):
        return (f"UDPSegment(type={'DATA' if self.type == 0 else 'ACK'}, "
                f"seq={self.seq}, len={self.length}, checksum={self.checksum})")


class IPPacket:
    def __init__(self, src_ip, dst_ip, payload):
        self.src_ip = src_ip
        self.dst_ip = dst_ip
        self.payload = payload
        self.ttl = IP_DEFAULT_TTL
        self.protocol = IP_PROTO_UDP
        self.total_length = 12 + payload.length

    def __repr__(self):
        return (f"IPPacket(src={self.src_ip}, dst={self.dst_ip}, "
                f"TTL={self.ttl}, len={self.total_length})")


class EthernetFrame:
    def __init__(self, src_mac, dst_mac, payload):
        self.src_mac = src_mac
        self.dst_mac = dst_mac
        self.type = ETHER_TYPE_IPV4
        self.payload = payload

    def __repr__(self):
        return (f"EthernetFrame(src={self.src_mac}, "
                f"dst={self.dst_mac}, type={self.type})")


##### LAYER CLASSES #####

class TransportLayer:
    def __init__(self, device):
        self.device = device  # reference to parent Host
        self.seq = 0
        
    def _send_above(self, segment: UDPSegment):
        # log delivery to application layer (not actually implemented as per spec)
        print(f"{self.device.name}: Layer 4: DATA segment delivered to Application Layer, Data size={len(segment.payload)}")
        
    def _send_below(self, segment: UDPSegment, dst_ip:str):
        # send segment down to network layer
        print(f"{self.device.name}: Layer 4: Segment sent to network layer")
        self.device.network.receive_from_above(segment, dst_ip)
        self.seq = 1 - self.seq
        
    def _verify_checksum(self, segment: UDPSegment):
        # check if actual checksum = computed checksum
        if segment.checksum == compute_checksum(segment.payload):
            print(f"{self.device.name}: Layer 4: Checksum verified")
            return True
        else:
            print(f"{self.device.name}: Layer 4: Invalid checksum, segment has been discarded")
            return False

    def receive_from_above(self, size: int, dst_ip:str):
        """Called by the application layer to send data."""
        data = b"X" * size
        print(f"{self.device.name}: Layer 4: Data received from Application Layer. Data size={size}")

        if size > UDP_MAX_DATA:
            num_segments = math.ceil(size / UDP_MAX_DATA)
            for i in range(num_segments):
                chunk = data[i * UDP_MAX_DATA : (i + 1) * UDP_MAX_DATA]
                segment = UDPSegment(UDP_SRC_PORT, UDP_DST_PORT, L4_TYPE_DATA, self.seq, chunk)
                print(f"{self.device.name}: Layer 4: Checksum computed")
                print(f"{self.device.name}: Layer 4: Segment created by adding transport layer header ({'DATA' if segment.type == L4_TYPE_DATA else 'ACK'}, seq={self.seq}) (encapsulation)")
                self._send_below(segment, dst_ip)
        else:
            segment = UDPSegment(UDP_SRC_PORT, UDP_DST_PORT, L4_TYPE_DATA, self.seq, data)
            print(f"{self.device.name}: Layer 4: Checksum computed")
            print(f"{self.device.name}: Layer 4: Segment created by adding transport layer header ({'DATA' if segment.type == L4_TYPE_DATA else 'ACK'}, seq={self.seq}) (encapsulation)")
            self._send_below(segment, dst_ip)

    def receive_from_below(self, segment):
        print(f"{self.device.name}: Layer 4: Segment received from Network Layer")
        
        # check if checksum is valid, if not; discard
        if not self._verify_checksum(segment):
            return
        
        # check if it's DATA or ACK
        if segment.type == L4_TYPE_DATA:
            
            self._send_above(segment)
            print(f"{self.device.name}: Layer 4: Segment created by adding transport layer header (ACK, seq={segment.seq})")
            
            ACK = UDPSegment(UDP_DST_PORT, UDP_SRC_PORT, L4_TYPE_ACK, segment.seq)
            
            self._send_below(ACK, IP_HOST_A)
        
        else:  # it's an ACK
            print(f"{self.device.name}: Layer 4: ACK received: seq={segment.seq}")
            self.seq = 1 - self.seq
                

class NetworkLayer:
    def __init__(self, device):
        self.device = device

    #helper function to convert IP adresses to integers  
    def _ip_to_int(self, address):
        parts = address.split(".")
        int_parts = (int(parts[0]) << 24 | int(parts[1]) << 16 | int(parts[2]) << 8 | int(parts[3]))  
        return int_parts
        
    # helper function to lookup the routing table
    def _lookup_routing_table(self, dst_ip):

        # this convert dst_ip to an integer by shifting the values to their bitwise positions then summing all
        dst_ip_int = self._ip_to_int(dst_ip)

        for entry in self.device.routing_table:
            
            # convert entry["network"] to an integer
            network_int = self._ip_to_int(entry["network"])

            # create a standard mask for network comparison
            mask = (0xFFFFFFFF << (32 - entry["prefix"])) & 0xFFFFFFFF

            # check if the dst_ip matches the network in the table, if so, return
            if dst_ip_int & mask == network_int & mask:
                return entry
            
        return None
    
    def _send_above(self, segment):
        print(f"{self.device.name}: Layer 3: Segment delivered to Transport Layer")
        
        # pass up to transport layer
        self.device.transport.receive_from_below(segment)
        
    def _send_below(self, packet, next_hop, iface=None):
        print(f"{self.device.name}: Layer 3: Packet forwarded to Data Link Layer")  
        
        # pass down to DataLinkLayer
        self.device.datalink.receive_from_above(packet, next_hop, iface)
    
    def receive_from_above(self, segment, dst_ip):
        print(f"{self.device.name}: Layer 3: Segment received from Transport Layer: SRC_IP={self.device.ip}, DST_IP={dst_ip}, TTL={IP_DEFAULT_TTL}")
        
        # create IPPacket
        packet = IPPacket(self.device.ip, dst_ip, segment)
        
        # print destination IP read
        print(f"{self.device.name}: Layer 3: Destination IP read: {dst_ip}")
        
        # routing table lookup
        entry = self._lookup_routing_table(dst_ip)
        
        if not entry:
            print(f"{self.device.name}: Layer 3: No Next-hop IP available, discarding packet")
            return
        
        print(f"{self.device.name}: Layer 3: Routing table lookup performed")
        
        next_hop = entry["next_hop"] if entry["next_hop"] is not None else dst_ip
        
        # print routing decision 
        print(f"{self.device.name}: Layer 3: Next-hop IP determined: {next_hop}")
        print(f"{self.device.name}: Layer 3: Outgoing interface selected")
        
        iface = entry["iface"]
        self._send_below(packet, next_hop, iface)
       

    def receive_from_below(self, packet):
        print(f"{self.device.name}: Layer 3: Packet received from Data Link Layer: SRC_IP={packet.src_ip}, DST_IP={packet.dst_ip}, TTL={packet.ttl}")
        print(f"{self.device.name}: Layer 3: Destination IP read: {packet.dst_ip}")

        # handle both Host (single ip string) and Router (list of ips)
        device_ips = self.device.ip if isinstance(self.device.ip, list) else [self.device.ip]

        if packet.dst_ip in device_ips:
            print(f"{self.device.name}: Layer 3: Packet identified as local delivery")
            payload = packet.payload
            self._send_above(payload)

        else:
            packet.ttl -= 1
            if packet.ttl == 0:
                print(f"{self.device.name}: Layer 3: TTL expired, packet dropped")
                return
            entry = self._lookup_routing_table(packet.dst_ip)
            next_hop = entry["next_hop"] if entry["next_hop"] is not None else packet.dst_ip
            iface = entry["iface"]

            print(f"{self.device.name}: Layer 3: TTL decremented: {packet.ttl + 1} → {packet.ttl}")
            print(f"{self.device.name}: Layer 3: Routing table lookup performed")
            print(f"{self.device.name}: Layer 3: Next-hop IP determined: {next_hop}")
            print(f"{self.device.name}: Layer 3: Outgoing interface selected ({iface})")
            
            self._send_below(packet, next_hop, iface)
            
            
class DataLinkLayer:
    def __init__(self, device):
        self.device = device
        self.neighbours = []

    def receive_from_above(self, packet, next_hop, iface=None):
        print(f"{self.device.name}: Layer 2: Packet received from Network Layer")
        
        # look up destination MAC from ARP table using next_hop IP
        dst_mac = self.device.arp_table[next_hop]
        print(f"{self.device.name}: Layer 2: Destination MAC lookup for next-hop IP ({next_hop}) → {dst_mac}")
        
        # determine source MAC — router uses interface MAC, host uses its own MAC
        if hasattr(self.device, 'iface_mac') and iface:
            src_mac = self.device.iface_mac[iface]
        else:
            src_mac = self.device.mac
        
        # build the frame
        frame = EthernetFrame(src_mac, dst_mac, packet)
        print(f"{self.device.name}: Layer 2: Frame created: SRC_MAC={src_mac}, DST_MAC={dst_mac}")
        
        # determine log text — router says "forwarded", host says "sent"
        if iface:
            print(f"{self.device.name}: Layer 2: Frame forwarded on {iface}")
        else:
            print(f"{self.device.name}: Layer 2: Frame sent")
        
        # find the right neighbour and deliver the frame
        for neighbour in self.neighbours:
            if hasattr(neighbour, 'mac') and neighbour.mac == dst_mac:
                neighbour.datalink.receive_from_below(frame, iface)
                return
            if hasattr(neighbour, 'iface_mac') and dst_mac in neighbour.iface_mac.values():
                # find which interface this corresponds to
                arriving_iface = next(k for k, v in neighbour.iface_mac.items() if v == dst_mac)
                neighbour.datalink.receive_from_below(frame, arriving_iface)
                return
            
    def receive_from_below(self, frame, iface=None):
        print(f"{self.device.name}: Layer 2: Frame received{' on ' + iface if iface else ''}")
        
        # learn the source MAC
        print(f"{self.device.name}: Layer 2: Source MAC learned: {frame.src_mac}{' on ' + iface if iface else ''}")
        
        # deliver payload up to network layer
        print(f"{self.device.name}: Layer 2: Packet delivered to Network Layer")
        self.device.network.receive_from_below(frame.payload)