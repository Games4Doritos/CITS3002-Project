from protocol import TransportLayer, NetworkLayer, DataLinkLayer

class Host:
    def __init__(self, name, ip, mac, routing_table, arp_table):
        self.name = name
        self.ip = ip
        self.mac = mac
        self.routing_table = routing_table
        self.arp_table = arp_table
        self.transport = TransportLayer(self)
        self.network = NetworkLayer(self)
        self.datalink = DataLinkLayer(self)

class Router:
    def __init__(self, name, routing_table, arp_table, iface_mac, iface_ip):
        self.name = name
        self.routing_table = routing_table
        self.arp_table = arp_table
        self.iface_mac = iface_mac
        self.iface_ip = iface_ip
        self.network = NetworkLayer(self)
        self.datalink = DataLinkLayer(self)