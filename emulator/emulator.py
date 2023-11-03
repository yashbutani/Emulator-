import argparse
import socket
import sys
import time
import struct
import os
from datetime import datetime
from queue import PriorityQueue

class Data:
    def __init__(self, priority, ip_src, src_port, ip_dest, dest_port, length):
        self.priority = priority
        self.ip_src = ip_src
        self.src_port = src_port
        self.ip_dest = ip_dest
        self.dest_port = dest_port
        self.length = length

class Emulator:
    def __init__(self, port, queue_size, forwarding_table, log_file):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((socket.gethostname(), port))
        print(socket.gethostname() + '\n')
        self.socket.setblocking(False) # TODO may need blocking? not sure 
        self.queue = [[] for _ in range(3)]  # TODO fix inital priority queue PriorityQueue(maxsize=queue_size)#
        self.queue_size = queue_size
        self.forwarding_table = forwarding_table
        self.log_file = log_file

    def unpack_data(self, packet):
        unpacked_data = struct.unpack('!B4sH4sHI', packet[:17])
        priority = unpacked_data[0]

        # IP conversion
        ip_src = socket.inet_ntoa(unpacked_data[1])
        ip_dest = socket.inet_ntoa(unpacked_data[3])

        # int conversions
        src_port = socket.ntohs(unpacked_data[2])
        dest_port = socket.ntohs(unpacked_data[4])
        length = socket.ntohl(unpacked_data[5])

        data = Data(priority, ip_src, ip_dest, src_port, dest_port, length)
        return data

    def log(self, message, data_packet):
# Logging function:
    # The logging function is integral to all functions of the emulator. A packet may be dropped in the emulator in the routing function,
    # the queueing function, or in the send function. Any and all packet drop events must be logged to a file. Loss events must provide a
    # textual reason for the loss (e.g., "no forwarding entry found", "priority queue 1 was full'', "loss event occurred.") Each log event
    # must include the source hostname and port, the intended destination host name and port, the time of loss (to millisecond resolution),
    # the priority level of the packet, and the size of the payload.

        print(message)
        print(f"Source Host and Port: {data_packet.ip_src}: {data_packet.src_port}")
        print(f"Destination Host and Port: {data_packet.ip_dest}: {data_packet.dest_port}")
        # TODO time of loss
        print(f"Priority: {data_packet.priority}")
        print(f"Payload size: {data_packet.length}")

    def route_packet(self, data_packet):
# Routing function:
    # The routing function is based on the static forwarding table that you provide to your program 
    # through the file described above. The destination of an incoming packet is compared with the
    # destination in the forwarding table to find a match. If a match is found, the packet is queued for forwarding to the next hop.
    # If a match is not found, the packet is dropped and the event should be logged (see logging function below).

    # The emulator reads this file once it starts running and then only refers to its version of the file in memory 
    # for every packet. The emulator ignores lines in the table that do not correspond to its own hostname and port. 
    # Note that emulator, sender, and requester are all uniquely identified with a "<Host name, Port>" pair and thus 
    # multiple of them can run on the same host.

        # compare destination of incoming packet to forwarding table
        destination_ip = data_packet.ip_dest
        destination_port = data_packet.port_dest

        src_addr, src_port = self.socket.getsockname() 
        for entry in self.forwarding_table:
            if entry[0] != src_addr and entry[1] != src_port: # ignore packets that don't corresponse to its own hostname and porpt
                continue
            if entry[2] == destination_ip and entry[3] == destination_port: # indicates a match
                self.queueing()
                print("Queue packet for forwarding to the next hop")
            else:
                # drop packet and event should be logged
                self.log("FAILURE: no forwarding entry found", data_packet)

    def send_packet(self, packet, destination):
# Send function:

    # The send function accepts packets from the three queues defined above and simulates network link conditions for each destination. 
    # Packets bound for a destination are first delayed to simulate link bandwidth. The delay is defined in the forwarding table and is 
    # specified in milliseconds. After a packet has been delayed, it may be dropped to simulate a lossy link based on the loss probability 
    # provided in the forwarding table, and the event is logged (see logging function below). If a packet is not dropped, it is then sent to 
    # the network

        # TODO get sender info from forwarding table -> not hardcoded
        #data, addr = self.socket.recvfrom(4096)
        
        if destination == 1: # means it was a request packet so need to call sender from the emulator
            packet_type, seq_no, window = struct.unpack('!cII', packet[:9])
            seq_no = socket.ntohl(seq_no)
            window = socket.ntohl(window)
            print('Window:', window)
            requested_file = packet[9:].decode()
            print('File:',requested_file, '\n')

            self.socket.sendto(packet, ('Jacks-MacBook-Air.local', 5000))
        else:
            unpacked_data = struct.unpack('!B4sH4sHI', packet[:17])
            priority = unpacked_data[0]

            # IP conversion
            ip_src = socket.inet_ntoa(unpacked_data[1])
            ip_dest = socket.inet_ntoa(unpacked_data[3])

            # int conversions
            src_port = socket.ntohs(unpacked_data[2])
            dest_port = socket.ntohs(unpacked_data[4])
            length = socket.ntohl(unpacked_data[5])

            print("Priority:", priority)
            print("Source IP:", ip_src)
            print("Source Port:", src_port)
            print("Destination IP:", ip_dest)
            print("Destination Port:", dest_port)
            print("Length:", length)


        # Simulate network conditions and send packet
        # ...

    def queueing():
# Queueing function:

    # The queueing function should examine the priority field on the packet and place the packet in an appropriate queue. 
    # All the three queues are of fixed size. This queue size is specified on the command line of the emulator startup. 
    # If a queue is full, the packet is dropped and this event is logged (see logging function below).

    
        pass

    def run(self):
        while True:
            destination = 0
            try:
                packet, addr = self.socket.recvfrom(1024)
                data_packet = self.unpack_data(packet) # convert packet
                self.route_packet(data_packet)


                #self.route_packet(packet)


                # packet_type, seq_no, window = struct.unpack('!cII', packet[:9])
                # if packet_type == b'R':
                #     destination = 1
                # print(packet)
                # self.send_packet(packet, destination) # TODO will be moved in the for loop on the bottom; testing right now
                # self.route_packet(packet) # TODO will either route a sender or receiver
            except socket.error:
                # check if a packet is being delayed, if the delay hasn't expired go back to listening

                # If no packet is currently being delayed, select the packet at the front of the queue with highest priority, 
                # remove that packet from the queue and delay it

                # When the delay expires, randomly determine whether to drop the packet
                # Otherwise, send the packet to the proper next hop.

                # Continue listening
                pass

            for priority_queue in self.queue:
                if priority_queue:
                    print("test")
                    packet = priority_queue.pop(0)
                    # ... send_packet() ...
                    time.sleep(0.01)

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

    # read initial forwarding table file
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