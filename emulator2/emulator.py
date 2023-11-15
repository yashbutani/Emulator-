import argparse
import os
import socket
import struct
import time
from datetime import datetime
import random

class Packet:
    def __init__(self, priority, ip_src, src_port, ip_dest, dest_port, length):
        self.priority = priority
        self.ip_src = ip_src
        self.src_port = src_port
        self.ip_dest = ip_dest
        self.dest_port = dest_port
        self.length = length

class Forwarding:
    def __init__(self, ip_src, port_src, ip_dest, port_dest, next_hop_host, next_hop_port, delay, loss_prob):
        self.ip_src = ip_src
        self.port_src = port_src
        self.ip_dest = ip_dest
        self.port_dest = port_dest
        self.next_hop_host = next_hop_host
        self.next_hop_port = next_hop_port
        self.delay = delay
        self.loss_prob = loss_prob

class Emulator:
    def __init__(self, port, queue_sizes, forwarding_table, log_file):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        print(socket.gethostname())
        self.socket.bind(('localhost', port))
        self.queues = {1: [], 2: [], 3: []}  # Separate queue for each priority
        self.queue_sizes: int = queue_sizes  # Dict with queue sizes for each priority
        self.forwarding_table = forwarding_table
        self.log_file = log_file

    def unpack_data(self, packet):
        print(packet)
        unpacked_data = struct.unpack('!B4sH4sHI', packet[:17])
        priority = unpacked_data[0]

        # IP conversion
        ip_src = socket.inet_ntoa(unpacked_data[1])
        ip_dest = socket.inet_ntoa(unpacked_data[3])

        # int conversions
        src_port = socket.ntohs(unpacked_data[2])
        dest_port = socket.ntohs(unpacked_data[4])
        length = unpacked_data[5]
        print('length', length)

        packet = Packet(priority, ip_src, src_port, ip_dest, dest_port, length)
        return packet
    
    def pack_data(self, packet, bytes_packet):
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

    def log(self, message, data_packet=None):
        with open(self.log_file, 'a') as f:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            log_message = f"{timestamp} - {message}"
            if data_packet:
                log_message += (f" - Src: {data_packet.ip_src}:{data_packet.src_port}, "
                                f"Dst: {data_packet.ip_dest}:{data_packet.dest_port}, "
                                f"Priority: {data_packet.priority}, "
                                f"Length: {data_packet.length}\n")
            f.write(log_message)


    def queue_packet(self, packet, table):
        if len(self.queues[packet.priority]) < self.queue_sizes:
            self.queues[packet.priority].append((packet, table))
           # self.log(f"Packet queued", packet)
        else:
            self.log(f"PACKET DROPPPED: queue for priority {packet.priority} is full.", packet)

    def send_packet(self, packet, table, byte_packet):
        print('insde send packet')

        time.sleep((table.delay)/1000)  # emulator delays before sending

        loss_prob = (table.loss_prob)/100

        if random.uniform(0, 1) >= loss_prob:
            packed_packet = self.pack_data(packet,byte_packet)
            self.socket.sendto(packed_packet, (table.next_hop_host, table.next_hop_port))
        else: 
            # drop packet and event should be logged
            self.log("PACKET DROPPED: Lossy link probability realized", packet)


        # for entry in self.forwarding_table:
        #     print('inside for')
        #     ip_src = socket.gethostbyname(entry[0])
        #     port_src = int(entry[1])
        #     ip_dest = socket.gethostbyname(entry[2])
        #     port_dest = int(entry[3])

        #     if ip_src != src_addr and port_src != src_port: # ignore packets that don't corresponse to emulator's own hostname and port
        #         continue

        #     #if ip_dest == destination_ip and port_dest == destination_port: # indicates a match
        #     next_hop_host = socket.gethostbyname(entry[4])
        #     next_hop_port = int(entry[5])
        #     delay = int(entry[6])

        #     time.sleep(delay/1000)  # emulator delays before sending

        #     loss_prob = int(entry[7])/ 100
        #     if random.uniform(0, 1) >= loss_prob:
        #         packed_packet = self.pack_data(packet,byte_packet)
        #         print("next hop",next_hop_host,next_hop_port)
        #         self.socket.sendto(packed_packet, (next_hop_host, next_hop_port)) 
        #         print("Sending packet to the next hop")
        #     else: 
        #         # drop packet and event should be logged
        #         self.log("FAILURE: no forwarding entry found", packet)


    def forward_packets(self, packet, byte_packet):
        # TODO The destination of an incoming packet is compared with the destination in the forwarding table to find a match. 
        # If a match is found, the packet is queued for forwarding to the next hop. If a match is not found, the packet is dropped and the event should be logged (see logging function below).

        src_addr, src_port = self.socket.getsockname()
        match = False

        destination_ip = packet.ip_dest
        destination_port = packet.dest_port

        # look for match in forwarding table
        for entry in self.forwarding_table:
            print(entry)
            table = Forwarding(socket.gethostbyname(entry[0]), int(entry[1]), socket.gethostbyname(entry[2]), int(entry[3]), socket.gethostbyname(entry[4]), int(entry[5]), int(entry[6]), int(entry[7]))
            print(table.ip_dest)
            print(destination_ip)

            if table.ip_src != src_addr and table.port_src != src_port:
                continue

            if table.ip_dest == destination_ip and table.port_dest == destination_port:
                print('valid')
                self.queue_packet(packet, table)
                match = True

        if not match: # drop packet bc not dest not aligned
            self.log('PACKET DROPPED: Destination not found in forwarding table', packet)
            return -1
            

        for priority in sorted(self.queues.keys()):
            print(priority)
            while self.queues[priority]:
                packet, table = self.queues[priority].pop(0)
                self.send_packet(packet, table, byte_packet)


        # exit(1)
        # self.queue_packet(packet)

        # # Forward packets from the queues based on priority
        # for priority in sorted(self.queues.keys()):
        #     while self.queues[priority]:
        #         packet = self.queues[priority].pop(0)
        #         print(packet)
        #         self.send_packet(packet, byte_packet)

    def run(self):
        while True:
            try:
                bytes_packet, addr = self.socket.recvfrom(1024)
                arrival_time = datetime.now()
                packet = self.unpack_data(bytes_packet) # convert packet
            except socket.error:
                pass  # Non-blocking call, proceed if no packet is received
            finally:
                self.forward_packets(packet, bytes_packet) # TODO what if it returns -1 -> means packet was dropped

                # If a packet is currently being delayed and the delay has not expired, goto Step 1.??

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', type=int, required=True, help='Port of the emulator.')
    parser.add_argument('-q', type=int, required=True, help='The sizes of the three queues for each priority.')
    parser.add_argument('-f', type=str, required=True, help='The name of the file containing the static forwarding table.')
    parser.add_argument('-l', type=str, required=True, help='The name of the log file.')
    args = parser.parse_args()

    queue_size = int(args.q)

    os.chdir('..') # change to parent dir to get file
    file_path = os.path.join(os.getcwd(), args.f)

    forwarding_table = []
    with open(file_path, 'r') as file:
        for line in file:
            content = line.split()
            entry_names = []
            for word in content:
                entry_names.append(word)
            forwarding_table.append(entry_names)


    # # Read the forwarding table from the specified file
    # forwarding_table = {}
    # with open(args.f, 'r') as f:
    #     for line in f:
    #         parts = line.strip().split()
    #         if len(parts) == 6:
    #             dest_ip, dest_port, next_hop_ip, next_hop_port, delay, loss_prob = parts
    #             forwarding_table[(dest_ip, int(dest_port))] = ((next_hop_ip, int(next_hop_port)), int(delay), float(loss_prob))

    # Set the queue sizes for each priority
    #queue_sizes = {1: args.q, 2: args.q, 3: args.q}
    
    # Initialize the emulator with the loaded forwarding table and log file
    emulator = Emulator(args.p, queue_size, forwarding_table, args.l)
    emulator.run()
