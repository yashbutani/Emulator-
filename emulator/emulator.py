import argparse
import socket
import struct
import time
from datetime import datetime
import random

class Packet:
    def __init__(self, priority, data, src_addr, dest_addr, arrival_time):
        self.priority = priority
        self.data = data
        self.src_addr = src_addr
        self.dest_addr = dest_addr
        self.arrival_time = arrival_time

class Emulator:
    def __init__(self, port, queue_sizes, forwarding_table, log_file):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('', port))
        self.queues = {1: [], 2: [], 3: []}  # Queues for each priority
        self.queue_sizes = queue_sizes
        self.forwarding_table = forwarding_table
        self.log_file = log_file

    def log(self, message):
        with open(self.log_file, 'a') as f:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            f.write(f"{timestamp} - {message}\n")

    def unpack_data(self, packet):
        priority, ip_src, src_port, ip_dest, dest_port, length = struct.unpack('!B4sH4sHI', packet[:17])
        data = packet[17:]
        return priority, socket.inet_ntoa(ip_src), src_port, socket.inet_ntoa(ip_dest), dest_port, length, data

        # IP conversion
        ip_src = socket.inet_ntoa(unpacked_data[1])
        ip_dest = socket.inet_ntoa(unpacked_data[3])

        # int conversions
        src_port = socket.ntohs(unpacked_data[2])
        dest_port = socket.ntohs(unpacked_data[4])
        length = socket.ntohl(unpacked_data[5])

        data = Data(priority, ip_src, src_port, ip_dest, dest_port, length)
        return data

    def pack_data(self,packet, bytes_packet):
      #  priority, ip_src, src_port, ip_dest, dest_port, length
        priority = packet.priority

        packed_ip_src = socket.inet_aton(packet.ip_src)
        packed_ip_dest = socket.inet_aton(packet.ip_dest)

        # 16-bit
        src_port = socket.htons(packet.src_port)
        dest_port = socket.htons(packet.dest_port)

        packet_len = packet.length

        packed_data = struct.pack('!B4sH4sHI', priority, packed_ip_src, src_port, packed_ip_dest, dest_port, packet_len)

        final_packet = packed_data + bytes_packet[17:]

        return final_packet


    def log(self, message, data_packet):
# Logging function:
    # The logging function is integral to all functions of the emulator. A packet may be dropped in the emulator in the routing function,
    # the queueing function, or in the send function. Any and all packet drop events must be logged to a file. Loss events must provide a
    # textual reason for the loss (e.g., "no forwarding entry found", "priority queue 1 was full'', "loss event occurred.") Each log event
    # must include the source hostname and port, the intended destination host name and port, the time of loss (to millisecond resolution),
    # the priority level of the packet, and the size of the payload.

        print(message)
        print(f"Source Host and Port: {data_packet.ip_src}:{data_packet.src_port}")
        print(f"Destination Host and Port: {data_packet.ip_dest}:{data_packet.dest_port}")
        # TODO time of loss
        print(f"Priority: {data_packet.priority}")
        print(f"Payload size: {data_packet.length}\n")

    def route_packet(self, bytes_packet, data_packet):
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
        destination_port = data_packet.dest_port

        src_addr, src_port = self.socket.getsockname() 
        for entry in self.forwarding_table:
            ip_src = socket.gethostbyname(entry[0])
            port_src = entry[1]
            ip_dest = socket.gethostbyname(entry[2])
            port_dest = int(entry[3])

            if ip_src != src_addr and port_src != src_port: # ignore packets that don't corresponse to its own hostname and porpt
                continue

            if ip_dest == destination_ip and port_dest == destination_port: # indicates a match
                packet = self.pack_data(data_packet, bytes_packet)
                destination = [ip_dest, port_dest]
                self.queueing(data_packet.priority, packet, destination)
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
        self.socket.sendto(packet, (destination[0], destination[1]))


    def queueing(self, priority, packet, destination):
        self.queue[priority-1].append([packet, destination])
# Queueing function:

    # The queueing function should examine the priority field on the packet and place the packet in an appropriate queue. 
    # All the three queues are of fixed size. This queue size is specified on the command line of the emulator startup. 
    # If a queue is full, the packet is dropped and this event is logged (see logging function below).

    
        pass

    def run(self):
        while True:
            try:
                bytes_packet, addr = self.socket.recvfrom(1024)
                data_packet = self.unpack_data(bytes_packet) # convert packet
                self.route_packet(bytes_packet, data_packet)
            except socket.error:
                pass  # Non-blocking call, proceed if no packet is received

                # If no packet is currently being delayed, select the packet at the front of the queue with highest priority, 
                # remove that packet from the queue and delay it

                # When the delay expires, randomly determine whether to drop the packet
                # Otherwise, send the packet to the proper next hop.

                # Continue listening
                pass

            for priority_queue in self.queue:
                if priority_queue:
                    packet, destination = priority_queue.pop(0)
                    self.send_packet(packet, destination)
                    time.sleep(0.01)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', type=int, required=True, help='Port of the emulator.')
    parser.add_argument('-q', type=int, nargs=3, required=True, help='The sizes of the three queues for each priority.')
    parser.add_argument('-f', type=str, required=True, help='The name of the file containing the static forwarding table.')
    parser.add_argument('-l', type=str, required=True, help='The name of the log file.')
    args = parser.parse_args()

    forwarding_table = {}
    with open(args.f, 'r') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) == 6:
                dest_ip, dest_port, next_hop_ip, next_hop_port, delay, loss_prob = parts
                forwarding_table[(dest_ip, int(dest_port))] = ((next_hop_ip, int(next_hop_port)), int(delay), float(loss_prob))

    emulator = Emulator(args.p, args.q, forwarding_table, args.l)
    emulator.run()
