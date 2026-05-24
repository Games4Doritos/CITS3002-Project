from protocol import TransportLayer, NetworkLayer, DataLinkLayer

class Host:
    def __init__(self, name, ip, mac, routing_table, arp_table):
        self.name = name
        self.ip = ip
        self.mac = mac
        self.arp_table = arp_table
        self.transport = TransportLayer(self)
        self.network = NetworkLayer(self, routing_table)
        self.datalink = DataLinkLayer(self)

    def connect(self, neighbour):
        self.datalink.neighbours.append(neighbour)

class Router:
    def __init__(self, name, routing_table, arp_table, iface_mac, iface_ip):
        self.name = name
        self.arp_table = arp_table
        self.iface_mac = iface_mac
        self.iface_ip = iface_ip
        self.network = NetworkLayer(self, routing_table)
        self.datalink = DataLinkLayer(self)

    @property
    def ip(self):
        return list(self.iface_ip.values())

    def connect(self, neighbour):
        self.datalink.neighbours.append(neighbour)