import math
from config import (
    IP_DEFAULT_TTL, IP_PROTO_UDP, ETHER_TYPE_IPV4,
    UDP_SRC_PORT, UDP_DST_PORT, UDP_HEADER_SIZE,
    L4_TYPE_DATA, L4_TYPE_ACK, UDP_MAX_DATA
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
    def __init__(self, src_port, dst_port, seg_type, seq, data=b""):
        self.src_port = src_port
        self.dst_port = dst_port
        self.length = len(data) + UDP_HEADER_SIZE
        self.checksum = compute_checksum(data)
        self.type = seg_type
        self.seq = seq
        self.data = data

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

    def receive_from_above(self, size: int):
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
                print(f"{self.device.name}: Layer 4: Segment sent to the Network Layer")
                self.device.network.receive_from_above(segment)
                self.seq = 1 - self.seq
        else:
            segment = UDPSegment(UDP_SRC_PORT, UDP_DST_PORT, L4_TYPE_DATA, self.seq, data)
            print(f"{self.device.name}: Layer 4: Checksum computed")
            print(f"{self.device.name}: Layer 4: Segment created by adding transport layer header ({'DATA' if segment.type == L4_TYPE_DATA else 'ACK'}, seq={self.seq}) (encapsulation)")
            print(f"{self.device.name}: Layer 4: Segment sent to the Network Layer")
            self.device.network.receive_from_above(segment)
            self.seq = 1 - self.seq

    def receive_from_below(self, segment):
        print(f"{self.device.name}: Layer 4: Segment received from Network Layer")
        
        # check if checksum is valid, if not; discard
        if not self._verify_checksum(segment):
            print(f"{self.device.name}: Layer 4: Invalid checksum, segment has been discarded")
            return
        
        # check if it's DATA or ACK
        if segment.type == L4_TYPE_DATA:
            print(f"{self.device.name}: Layer 4: Checksum verified")
            print(f"{self.device.name}: Layer 4: DATA segment delivered to Application Layer, Data size={len(segment.data)}")
            print(f"{self.device.name}: Layer 4: Segment created by adding transport layer header (ACK, seq={segment.seq})")
            print(f"{self.device.name}: Layer 4: Segment sent to network layer")
            
            ACK = UDPSegment(UDP_DST_PORT, UDP_SRC_PORT, L4_TYPE_ACK, segment.seq)
            self.device.network.receive_from_above(ACK)
            
            self.seq = 1 - self.seq
        
        else:  # it's an ACK
            print(f"{self.device.name}: Layer 4: ACK received: seq={segment.seq}")
            self.seq = 1 - self.seq
                

    def _verify_checksum(self, segment):
        return segment.checksum == compute_checksum(segment.data):
    

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

    def receive_from_above(self, segment, dst_ip):
        print(f"{self.device.name}: Layer 3: Segment received from Transport Layer: SRC_IP={self.device.ip}, DST_IP={dst_ip}, TTL={IP_DEFAULT_TTL}")
        
        # create IPPacket
        packet = IPPacket(self.device.ip, dst_ip, segment)
        
        # print destination IP read
        print(f"{self.device.name}: Layer 3: Destination IP read: {dst_ip}")
        
        # routing table lookup
        entry = self._lookup_routing_table(dst_ip)
        next_hop = entry["next_hop"] if entry["next_hop"] is not None else dst_ip
        
        # print routing decision
        print(f"{self.device.name}: Layer 3: Routing table lookup performed")
        print(f"{self.device.name}: Layer 3: Next-hop IP determined: {next_hop}")
        print(f"{self.device.name}: Layer 3: Outgoing interface selected")
        print(f"{self.device.name}: Layer 3: Packet forwarded to Data Link Layer")        
        
        # pass down to DataLinkLayer
        self.device.datalink.receive_from_above(packet, next_hop)

    def receive_from_below(self, packet):
        print(f"{self.device.name}: Layer 3: Packet received from Data Link Layer: SRC_IP={packet.src_ip}, DST_IP={packet.dst_ip}, TTL={packet.ttl}")
        print(f"{self.device.name}: Layer 3: Destination IP read: {packet.dst_ip}")

        if packet.dst_ip == self.device.ip:
            print(f"{self.device.name}: Layer 3: Packet identified as local delivery")
            print(f"{self.device.name}: Layer 3: Segment delivered to Transport Layer")
            self.device.transport.receive_from_below(packet.payload)

        else:
            # decrement TTL
            packet.ttl -= 1
            # check if TTL == 0, drop if so
            if packet.ttl == 0:
                print(f"{self.device.name}: Layer 3: TTL expired, packet dropped")
                return
            # lookup routing table
            entry = self._lookup_routing_table(packet.dst_ip)
            next_hop = entry["next_hop"] if entry["next_hop"] is not None else packet.dst_ip
            iface = entry["iface"]

            print(f"{self.device.name}: Layer 3: TTL decremented: {packet.ttl + 1} → {packet.ttl}")
            print(f"{self.device.name}: Layer 3: Routing table lookup performed")
            print(f"{self.device.name}: Layer 3: Next-hop IP determined: {next_hop}")
            print(f"{self.device.name}: Layer 3: Outgoing interface selected ({iface})")
            print(f"{self.device.name}: Layer 3: Packet forwarded to Data Link Layer")

            # forward down to datalink 
            self.device.datalink.receive_from_above(packet, next_hop)
            
            
