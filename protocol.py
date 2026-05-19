



##### HELPER FUNCTIONS #####

# Checksum the data for errors
def compute_checksum(data: bytes) -> int:
    checksum = 0

    for byte in data:
        checksum += byte

    return checksum % 65536 # Due to 65526 ciombinations in a 16-bit value 


class UDPSegment:
        def __init__(self, src_port, dst_port, seg_type, seq, data=b""):
            self.src_port = src_port
            self.dst_port = dst_port 
            self.length = len(data) + 10
            self.checksum = compute_checksum(data)
            self.type = seg_type
            self.seq = seq
            self.data = data

