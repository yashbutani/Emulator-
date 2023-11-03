import argparse
import socket
import time
import struct
import os
from datetime import datetime
from queue import PriorityQueue

class Emulator:
    def __init__(self, port, queue_size, forwarding_table, log_file):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((socket.gethostname(), port))
        print(socket.gethostname())
        self.socket.setblocking(False) # TODO may need blocking? not sure 
        self.queue = [[] for _ in range(3)]  # TODO fix inital priority queue PriorityQueue(maxsize=queue_size)#
        self.queue_size = queue_size
        self.forwarding_table = forwarding_table
        self.log_file = log_file

    def log(self, message):
        # Log events to a file
        # ...
        pass

    def route_packet(self, packet):
        # compare destination of incoming packet to forwarding table
        destination = -1 # get destination from sender
        for entry in self.forwarding_table:
            if entry[1] == destination:
                print("Queue packet for forwarding to the next hop")
            else:
            # drop packet and event should be logged
                self.log("FAILURE")
        # Decide packet forwarding based on the static table
        # ...
        pass

    def send_packet(self, packet, destination):
        # TODO get sender info from forwarding table -> not hardcoded
        #data, addr = self.socket.recvfrom(4096)
        packet_type, _, _ = struct.unpack('!cII', packet[:9])
        if packet_type == b'R': # means it was a request packet so need to call sender from the emulator
            requested_file = packet[9:].decode()
            print('file',requested_file)

            self.socket.sendto(packet, ('Jacks-MacBook-Air.local', 5000))

        # Simulate network conditions and send packet
        # ...
        pass

    def run(self):
        print(self.forwarding_table)
        print(self.queue_size)
        print(self.log_file)
        while True:
            try:
                packet, addr = self.socket.recvfrom(1024)
                print(packet)
                self.send_packet(packet, 1) # TODO will be moved in the for loop on the bottom; testing right now
                self.route_packet(packet) # TODO will either route a sender or receiver
            except socket.error:
                pass

            for priority_queue in self.queue:
                if priority_queue:
                    print("test")
                    packet = priority_queue.pop(0)
                    # ... send_packet() ...
                    time.sleep(0.01)



# Routing function:
# The routing function is based on the static forwarding table that you provide to your program 
# through the file described above. The destination of an incoming packet is compared with the
# destination in the forwarding table to find a match. If a match is found, the packet is queued for forwarding to the next hop.
# If a match is not found, the packet is dropped and the event should be logged (see logging function below).

# The emulator reads this file once it starts running and then only refers to its version of the file in memory 
# for every packet. The emulator ignores lines in the table that do not correspond to its own hostname and port. 
# Note that emulator, sender, and requester are all uniquely identified with a "<Host name, Port>" pair and thus 
# multiple of them can run on the same host.

def queueing():
    pass
# Queueing function:

# The queueing function should examine the priority field on the packet and place the packet in an appropriate queue. 
# All the three queues are of fixed size. This queue size is specified on the command line of the emulator startup. 
# If a queue is full, the packet is dropped and this event is logged (see logging function below).

def send():
    pass
# Send function:

# The send function accepts packets from the three queues defined above and simulates network link conditions for each destination. 
# Packets bound for a destination are first delayed to simulate link bandwidth. The delay is defined in the forwarding table and is 
# specified in milliseconds. After a packet has been delayed, it may be dropped to simulate a lossy link based on the loss probability 
# provided in the forwarding table, and the event is logged (see logging function below). If a packet is not dropped, it is then sent to 
# the network

def logging():
    pass
# Logging function:

# The logging function is integral to all functions of the emulator. A packet may be dropped in the emulator in the routing function,
# the queueing function, or in the send function. Any and all packet drop events must be logged to a file. Loss events must provide a
# textual reason for the loss (e.g., "no forwarding entry found", "priority queue 1 was full'', "loss event occurred.") Each log event
# must include the source hostname and port, the intended destination host name and port, the time of loss (to millisecond resolution),
# the priority level of the packet, and the size of the payload.
    

# def send_file(s, filename, dest_addr, rate, seq_no, length):
#     address = f"{dest_addr[0]}:{dest_addr[1]}"

#     if not os.path.exists(filename):
#         print(f"File {filename} not found!")
#         return

#     with open(filename, 'rb') as file:
#         while True:
#             data = file.read(length)
#             if not data:
#                 print("\nEND Packet")
#                 # Sending the END packet
#                 header = struct.pack('!cII', b'E', socket.htonl(seq_no), 0)
#                 s.sendto(header, dest_addr)
#                 current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
#                 print(f"send time:\t{current_time}\nrequester addr:\t{address}\nSequence num::\t{seq_no}\nlength:\t\t0\npayload:\t\n")
#                 break
            
#             header = struct.pack('!cII', b'D', socket.htonl(seq_no), len(data))
#             packet = header + data
#             s.sendto(packet, dest_addr)
#             current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]

#             # Print the sender's log
#             print("\nDATA Packet")
#             print(f"send time:\t{current_time}\nrequester addr:\t{address}\nSequence num::\t{seq_no}\nlength:\t\t{len(data)}\npayload:\t{data[:4].decode('utf-8', 'ignore')}")
            
#             seq_no += len(data)
#             time.sleep(1.0/rate)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', type=int, required=True, help='Port of the emulator.')
    parser.add_argument('-q', type=int, required=True, help='The size of each of the three queues.')
    parser.add_argument('-f', type=str, required=True, help='The name of the file containing the static forwarding table.')
    parser.add_argument('-l', type=str, required=True, help='The name of the log file.')
    args = parser.parse_args()

    # Check port range validity
    if not (2049 < args.p < 65536):
        print("Error: Port number must be in the range 2050 to 65535.")
        exit(1)

    # read forwarding table file
    forwarding_table = []
    with open(args.f, 'r') as file:
        for line in file:
            content = line.split()
            entry_names = []
            for word in content:
                entry_names.append(word)
            forwarding_table.append(entry_names)

    # initialize and create emulator
    emulator = Emulator(args.p, args.q, forwarding_table, args.l)
    emulator.run() # constantly running in the background


    # with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
    #     s.bind((socket.gethostname(), args.p))
    #     print('----------------------------')
    #     print("emualtor's print information:")
    #     rounting(args.f)

    #     try:
    #         while True:
    #             # Listen for incoming request packets
    #             data, addr = s.recvfrom(4096)
    #             packet_type, _, _ = struct.unpack('!cII', data[:9])
    #             rounting(args.f)

    #             if packet_type == b'R':
    #                 requested_file = data[9:].decode()
    #                 print('file',requested_file)

    #                 #send_file(s, requested_file, (addr[0], args.g), args.r, args.q, args.l)

    #     except KeyboardInterrupt:
    #         print("\nShutting down sender...")
    #     finally:
    #         s.close()
