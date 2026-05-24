from protocol import TransportLayer, NetworkLayer, DataLinkLayer

class Host:
    def __init__(self, name, ip, mac, routing_table, arp_table):
        self.name = name
        self.ip = ip
        self.mac = mac
        self.arp_table = arp_table
        self.transport = TransportLayer(self) #embedded transport layer
        self.network = NetworkLayer(self, routing_table) #embedded network layer
        self.datalink = DataLinkLayer(self) #embedded data link layer

    def connect(self, neighbour):
        # connects this host to another device via a physical link
        self.datalink.neighbours.append(neighbour)

class Router:
    def __init__(self, name, routing_table, arp_table, iface_mac, iface_ip):
        self.name = name
        self.arp_table = arp_table
        self.iface_mac = iface_mac
        self.iface_ip = iface_ip
        self.network = NetworkLayer(self, routing_table) #embdedded network layer
        self.datalink = DataLinkLayer(self) #embedded data link layer
        # no transport layer is embedded as a router does not need that functionality for our constraints

    @property
    def ip(self):
        return list(self.iface_ip.values())

    def connect(self, neighbour):
        # connects this router to another device via a physical link
        self.datalink.neighbours.append(neighbour)