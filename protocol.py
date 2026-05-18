import math

class TransportLayer:
    class TransportSegment:
        def __init__(self, size:int, type:int):
            self.sourcePort = 5000
            self.destPort = 5001
            self.length = 10 + size
            self.checksum = 0
            self.type = 0
            self.seq = 0
            self.data = size
    
    def __init__(self):
        self.seq = 0
        
        
    def _receiveAbove(self, size:int):
        print(f"Layer 4: Data received from the Application Layer, Data size = {size}")
        if size > 500:
            numSegments = math.ceil(size/500)
            print(f"Data size too large for a single UDP segment, dividing data into {numSegments} segments")
        else:
            newSegment = self.TransportSegment(size, 0)
    
    def _receiveBelow(self, packet):
        segment = packet.data
        print("Layer 4: Segment received from the Network Layer")
        if segment.seq == self.seq:
            if segment.type == 0:
                self._sendAbove(segment)
                newSegment = self.TransportSegment(0, 1)
                self._sendBelow(newSegment)
            else:
                print(f"Layer 4: ACK received, seq = {segment.seq}")
            self.seq = 1 - self.seq
                
        else:
            print('error lol')
    
    def _sendBelow(self, segment):
        print(f"Layer 4: Sending segment to Network Layer ({ "ACK" if segment.type else "DATA"}, size = {segment.size})")
    
    def _sendAbove(self, segment):
        print(f"DATA segment delivered to Application Layer, Data size = {segment.data}")
    
    def _verifyChecksum():
        print('Layer 4: Checksum Verified')
        
    def _computeChecksum():
        print('Layer 4: Checksum Computed')