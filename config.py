# config.py
# ─────────────────────────────────────────────────────────────────────────────
# Central configuration for the Mini Internet Protocol Stack Simulator.
# All fixed network parameters live here: IP addresses, MAC addresses,
# routing tables, and ARP-like tables. Every other module imports from this
# file so that changing a value here propagates everywhere automatically.
# ─────────────────────────────────────────────────────────────────────────────


# ── IP Addresses

IP_HOST_A       = "10.0.1.10"   # Host A
IP_R1_IFACE1    = "10.0.1.1"    # Router R1, Interface 1 (faces Network 1)
IP_R1_IFACE2    = "10.0.2.1"    # Router R1, Interface 2 (faces Network 2)
IP_HOST_B       = "10.0.2.20"   # Host B


# ── MAC Addresses

MAC_HOST_A      = "AA:AA:AA:AA:AA:AA"   # Host A NIC
MAC_R1_IFACE1   = "BB:BB:BB:BB:BB:BB"   # Router R1, Interface 1
MAC_R1_IFACE2   = "CC:CC:CC:CC:CC:CC"   # Router R1, Interface 2
MAC_HOST_B      = "DD:DD:DD:DD:DD:DD"   # Host B NIC


# ── Ethernet / Layer-2 constants

ETHER_TYPE_IPV4 = 0x0800   # EtherType value that signals an IPv4 payload


# ── IP / Layer-3 constants 

IP_DEFAULT_TTL  = 100      # Starting TTL placed in every outgoing IP packet
IP_PROTO_UDP    = 17       # Protocol field value indicating a UDP-like payload


# ── UDP / Layer-4 constants

UDP_SRC_PORT    = 5000     # Source port used by the sending application
UDP_DST_PORT    = 80       # Destination port used by the receiving application
UDP_HEADER_SIZE = 10        # Bytes: src_port(2) + dst_port(2) + length(2)
                           #        + checksum(2) + type(1) + seq(1) = 10
                           # (sequence number is included in the fixed header)
UDP_MAX_DATA    = 500      # Maximum application bytes per segment

# Layer-4 segment type codes
L4_TYPE_DATA    = 0        # Segment carries application data
L4_TYPE_ACK     = 1        # Segment is an acknowledgement (no data)


# ── ARP-like tables: next-hop IP → destination MAC 
#
# In a real network these would be learned dynamically via ARP.  Here they are
# pre-populated because the topology is fixed.  Each node only needs entries
# for the neighbours it can reach directly on its local segment.
#
# Layout:  { next_hop_ip : mac_address }

ARP_TABLE_HOST_A = {
    IP_R1_IFACE1 : MAC_R1_IFACE1,   # Host A's only neighbour is R1 IF1
}

ARP_TABLE_HOST_B = {
    IP_R1_IFACE2 : MAC_R1_IFACE2,   # Host B's only neighbour is R1 IF2
}

# R1 has two interfaces so it needs entries on both segments.
ARP_TABLE_R1 = {
    IP_HOST_A    : MAC_HOST_A,       # Reachable via Interface 1
    IP_HOST_B    : MAC_HOST_B,       # Reachable via Interface 2
}


# ── Routing tables 
#
# Each entry maps a destination network (as a string prefix) to a dict with:
#   "next_hop"  – IP of the next router, or the destination itself if directly
#                 connected (used by Layer 3 to pass to Layer 2 for MAC lookup)
#   "iface"     – outgoing interface label (informational; used in log output)
#
# Hosts have a simple default route; R1 has two directly-connected routes.

ROUTING_TABLE_HOST_A = [
    # Destination network    next_hop          iface
    {"network": "10.0.1.0",  "prefix": 24, "next_hop": None,        "iface": "eth0"},
    # None means "destination is on this segment — use dst IP directly"
    {"network": "0.0.0.0",   "prefix": 0,  "next_hop": IP_R1_IFACE1, "iface": "eth0"},
    # Default route: send everything else to R1
]

ROUTING_TABLE_HOST_B = [
    {"network": "10.0.2.0",  "prefix": 24, "next_hop": None,        "iface": "eth0"},
    {"network": "0.0.0.0",   "prefix": 0,  "next_hop": IP_R1_IFACE2, "iface": "eth0"},
]

ROUTING_TABLE_R1 = [
    # Interface 1 side — Network 1
    {"network": "10.0.1.0",  "prefix": 24, "next_hop": None,        "iface": "Interface 1"},
    # Interface 2 side — Network 2
    {"network": "10.0.2.0",  "prefix": 24, "next_hop": None,        "iface": "Interface 2"},
]


# ── Interface → source MAC mapping for R1
#
# When R1 forwards a packet it needs to know which source MAC to stamp on the
# outgoing frame, depending on which interface it is sending from.

R1_IFACE_MAC = {
    "Interface 1": MAC_R1_IFACE1,
    "Interface 2": MAC_R1_IFACE2,
}

# Corresponding IP addresses for each interface (used for local-delivery check)
R1_IFACE_IP = {
    "Interface 1": IP_R1_IFACE1,
    "Interface 2": IP_R1_IFACE2,
}