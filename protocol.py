import math
from config import (
    IP_DEFAULT_TTL, IP_PROTO_UDP, ETHER_TYPE_IPV4,
    UDP_SRC_PORT, UDP_DST_PORT, UDP_HEADER_SIZE,
    L4_TYPE_DATA, L4_TYPE_ACK, UDP_MAX_DATA
)

##### HEADER CLASSES #####

class UDPSegment:
    def __init__(self, src_port, dst_port, seg_type, seq, payload=b""):
        self.src_port = src_port # source port
        self.dst_port = dst_port # destination port
        self.length = len(payload) + UDP_HEADER_SIZE # total segment length
        self.type = seg_type # segment type (DATA or ACK)
        self.seq = seq # sequence number (0 or 1)
        self.payload = payload # payload in bytes
        self.checksum = self.compute_checksum() # checksum
        
    def compute_checksum(self) -> int:
        """Compute a 16-bit checksum by summing all bytes mod 65536."""
        # includes both header fields and the payload
        checksum = self.src_port + self.dst_port + self.length + self.type + self.seq
        for byte in self.payload:
            checksum += byte
        # 16-bit words -> mod 65536 = 2^16
        return checksum % 65536


    def __repr__(self):
        return (f"UDPSegment(type={'DATA' if self.type == 0 else 'ACK'}, "
                f"seq={self.seq}, len={self.length}, checksum={self.checksum})")


class IPPacket:
    def __init__(self, src_ip, dst_ip, payload):
        self.src_ip = src_ip # source IP address
        self.dst_ip = dst_ip # destination IP address
        self.payload = payload # payload is a UDPSegment
        self.ttl = IP_DEFAULT_TTL # time-to-live (decremented by 1 at each hop)
        self.protocol = IP_PROTO_UDP # protocol field indicating UDP payload
        self.total_length = 12 + payload.length # total packet length

    def __repr__(self):
        return (f"IPPacket(src={self.src_ip}, dst={self.dst_ip}, "
                f"TTL={self.ttl}, len={self.total_length})")


class EthernetFrame:
    def __init__(self, src_mac, dst_mac, payload):
        self.src_mac = src_mac # source MAC address
        self.dst_mac = dst_mac # destination MAC address
        self.type = ETHER_TYPE_IPV4 # EtherType indicating IPv4 payload
        self.payload = payload # payload is an IPPacket

    def __repr__(self):
        return (f"EthernetFrame(src={self.src_mac}, "
                f"dst={self.dst_mac}, type={self.type})")


##### LAYER CLASSES #####

class TransportLayer:
    def __init__(self, device):
        self.device = device  # reference to parent Host
        self.seq = 0
        self.curSegment = None
        
    def _send_above(self, segment: UDPSegment):
        # log delivery to application layer (not actually implemented as per spec)
        print(f"{self.device.name}: Layer 4: DATA segment delivered to Application Layer, Data size={len(segment.payload)}")
        
    def _send_below(self, segment: UDPSegment, dst_ip:str):
        # send segment down to network layer
        self.curSegment = segment
        print(f"{self.device.name}: Layer 4: Segment sent to Network Layer\n")
        self.device.network.receive_from_above(segment, dst_ip)
        
    def _verify_checksum(self, segment: UDPSegment):
        # check if actual checksum = computed checksum
        if segment.checksum == segment.compute_checksum():
            print(f"{self.device.name}: Layer 4: Checksum verified")
            return True
        else:
            print(f"{self.device.name}: Layer 4: Invalid checksum, segment discarded")
            return False
        
    def _encapsulate(self, payload: bytes, type: int, seq:int):
        segment = UDPSegment(UDP_SRC_PORT, UDP_DST_PORT, type, seq, payload)
        print(f"{self.device.name}: Layer 4: Checksum computed")
        print(f"{self.device.name}: Layer 4: Segment created by adding transport layer header ({'DATA' if type == L4_TYPE_DATA else 'ACK'}, seq={seq}) (encapsulation)")
        return segment
        
    def receive_from_above(self, size: int, dst_ip:str):
        """Called by the application layer to send data."""
        data = b"X" * size
        print(f"{self.device.name}: Layer 4: Data received from Application Layer. Data size={size}")
        
        if size > UDP_MAX_DATA:
            # if the data received from the application layer exceeds the maximum UDP payload size of 500 bytes,
            # it is segmented into mutliple UDP segments with maximum payload sizes of 500 bytes
            # due to the recursive nature of this code, waiting for _send_below() to return guarantees that segments are sent in order
            num_segments = math.ceil(size / UDP_MAX_DATA)
            for i in range(num_segments):
                chunk = data[i * UDP_MAX_DATA : (i + 1) * UDP_MAX_DATA]
                segment = self._encapsulate(chunk, L4_TYPE_DATA, self.seq)
                self._send_below(segment, dst_ip)
        else:
            segment = self._encapsulate(data, L4_TYPE_DATA, self.seq)
            self._send_below(segment, dst_ip)

    def receive_from_below(self, segment, src_ip):
        print(f"{self.device.name}: Layer 4: Segment received from Network Layer")
        
        # check if checksum is valid, if not; discard
        if not self._verify_checksum(segment):
            return
        
        # check if it's DATA or ACK
        if segment.type == L4_TYPE_DATA:
            
            self._send_above(segment)
            print(f"{self.device.name}: Layer 4: Segment created by adding transport layer header (ACK, seq={segment.seq})")
            
            ACKSegment = self._encapsulate(b'', L4_TYPE_ACK, segment.seq)
            
            self._send_below(ACKSegment, src_ip)
        
        else:  # it's an ACK
            if segment.seq != self.seq:
                print(f"{self.device.name}: Layer 4: Unexpected ACK sequence number, segment discarded")
                self.send_below(self.curSegment, src_ip)
                return
            
            print(f"{self.device.name}: Layer 4: ACK received: seq={segment.seq}")
            self.seq = 1 - self.seq
                

class NetworkLayer:
    def __init__(self, device, routing_table):
        self.device = device
        self.routing_table = routing_table

    #helper function to convert IP adresses to integers  
    def _ip_to_int(self, address):
        parts = address.split(".")
        int_parts = (int(parts[0]) << 24 | int(parts[1]) << 16 | int(parts[2]) << 8 | int(parts[3]))  
        return int_parts
        
    # helper function to lookup the routing table
    def _lookup_routing_table(self, dst_ip):

        # this convert dst_ip to an integer by shifting the values to their bitwise positions then summing all
        dst_ip_int = self._ip_to_int(dst_ip)

        for entry in self.routing_table:
            
            # convert entry["network"] to an integer
            network_int = self._ip_to_int(entry["network"])

            # create a standard mask for network comparison
            mask = (0xFFFFFFFF << (32 - entry["prefix"])) & 0xFFFFFFFF

            # check if the dst_ip matches the network in the table, if so, return
            if dst_ip_int & mask == network_int & mask:
                return entry
            
        return None
    
    def _send_above(self, segment, src_ip):
        print(f"{self.device.name}: Layer 3: Segment delivered to Transport Layer\n")
        
        # pass up to transport layer
        self.device.transport.receive_from_below(segment, src_ip)
        
    def _send_below(self, packet, next_hop, iface=None):
        print(f"{self.device.name}: Layer 3: Packet forwarded to Data Link Layer\n")  
        
        # pass down to DataLinkLayer
        self.device.datalink.receive_from_above(packet, next_hop, iface)
        
    def _encapsulate(self, segment, dst_ip):
        # print destination IP read
        print(f"{self.device.name}: Layer 3: Destination IP read: {dst_ip}")
        
        packet = IPPacket(self.device.ip, dst_ip, segment)
        return packet
        
    def _decapsulate(self, packet):
        segment = packet.payload
        return segment
    
    def receive_from_above(self, segment, dst_ip):
        print(f"{self.device.name}: Layer 3: Segment received from Transport Layer: SRC_IP={self.device.ip}, DST_IP={dst_ip}, TTL={IP_DEFAULT_TTL}")
        
        # create IPPacket
        packet = self._encapsulate(segment, dst_ip)
        
        # routing table lookup
        entry = self._lookup_routing_table(dst_ip)
        
        # discard packet if destination is unreachable
        if not entry:
            print(f"{self.device.name}: Layer 3: Routing table lookup unsuccessful, destination is unreachable")
            print(f"{self.device.name}: Layer 3: Discarding packet")
            return
        
        print(f"{self.device.name}: Layer 3: Routing table lookup performed")
        
        # determine next hop IP
        next_hop = entry["next_hop"] if entry["next_hop"] is not None else dst_ip
        print(f"{self.device.name}: Layer 3: Next-hop IP determined: {next_hop}")
        
        # determine outgoing interface
        iface = entry["iface"]
        print(f"{self.device.name}: Layer 3: Outgoing interface selected")
        
        self._send_below(packet, next_hop, iface)
       

    def receive_from_below(self, packet):
        print(f"{self.device.name}: Layer 3: Packet received from Data Link Layer: SRC_IP={packet.src_ip}, DST_IP={packet.dst_ip}, TTL={packet.ttl}")
        print(f"{self.device.name}: Layer 3: Destination IP read: {packet.dst_ip}")

        # handle both Host (single ip string) and Router (list of ips)
        device_ips = self.device.ip if isinstance(self.device.ip, list) else [self.device.ip]

        if packet.dst_ip in device_ips:
            print(f"{self.device.name}: Layer 3: Packet identified as local delivery")
            payload = self._decapsulate(packet)
            self._send_above(payload, packet.src_ip)

        else:
            #decrement TTL and check if expired
            packet.ttl -= 1
            if packet.ttl == 0:
                print(f"{self.device.name}: Layer 3: TTL expired, packet dropped")
                return
            print(f"{self.device.name}: Layer 3: TTL decremented: {packet.ttl + 1} → {packet.ttl}")
            
            entry = self._lookup_routing_table(packet.dst_ip)
            
            # discard packet if destination is unreachable
            if not entry:
                print(f"{self.device.name}: Layer 3: Routing table lookup unsuccessful, destination is unreachable")
                print(f"{self.device.name}: Layer 3: Discarding packet")
                return
            
            print(f"{self.device.name}: Layer 3: Routing table lookup performed")
            
            # determine next hop IP
            next_hop = entry["next_hop"] if entry["next_hop"] is not None else packet.dst_ip
            print(f"{self.device.name}: Layer 3: Next-hop IP determined: {next_hop}")
            
            # determine outgoing interface
            iface = entry["iface"]
            print(f"{self.device.name}: Layer 3: Outgoing interface selected ({iface})")
            
            self._send_below(packet, next_hop, iface)
            
            
class DataLinkLayer:
    def __init__(self, device):
        self.device = device
        self.neighbours = []
        self.mac_learning_table = {}
        
    def _send_above(self, packet):
        print(f"{self.device.name}: Layer 2: Packet delivered to Network Layer\n")
        self.device.network.receive_from_below(packet)
        
    def _send_below(self, frame, neighbour, iface=None):
        neighbour.datalink.receive_from_below(frame, iface)
        
    def _encapsulate(self, packet, dst_mac, src_mac):
        frame = EthernetFrame(src_mac, dst_mac, packet)
        print(f"{self.device.name}: Layer 2: Frame created: SRC_MAC={src_mac}, DST_MAC={dst_mac}")
        return frame
    
    def _decapsulate(self, frame):
        packet = frame.payload
        return packet

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
        frame = self._encapsulate(packet, dst_mac, src_mac)
        
        # determine log text — router says "forwarded", host says "sent"
        # determine log text — router says "forwarded", host says "sent"
        if hasattr(self.device, 'iface_mac') and iface:
            print(f"{self.device.name}: Layer 2: Frame forwarded on {iface}\n")
        else:
            print(f"{self.device.name}: Layer 2: Frame sent\n")
        
        # find the right neighbour and deliver the frame
        for neighbour in self.neighbours:
            if hasattr(neighbour, 'mac') and neighbour.mac == dst_mac:
                self._send_below(frame, neighbour, iface)
                return
            if hasattr(neighbour, 'iface_mac') and dst_mac in neighbour.iface_mac.values():
                # find which interface this corresponds to
                arriving_iface = next(k for k, v in neighbour.iface_mac.items() if v == dst_mac)
                self._send_below(frame, neighbour, arriving_iface)
                return
            
    def receive_from_below(self, frame, iface=None):
        is_router = hasattr(self.device, 'iface_mac')
        
        print(f"{self.device.name}: Layer 2: Frame received{' on ' + iface if is_router and iface else ''}")
        
        if self.mac_learning_table.get(frame.src_mac, None) == None:
            # learn the source MAC address from the received frame
            self.mac_learning_table[frame.src_mac] = iface
            print(f"{self.device.name}: Layer 2: Source MAC learned: {frame.src_mac}{' on ' + iface if is_router and iface else ''}")
        # else, mac is already learned so move on
        
        packet = self._decapsulate(frame)
        
        self._send_above(packet)