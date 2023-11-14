import argparse
import socket
import struct
import time
from datetime import datetime
import random

# class Packet:
#     def __init__(self, priority, data, src_addr, dest_addr, length, arrival_time):
#         self.priority = priority
#         self.data = data
#         self.src_addr = src_addr
#         self.dest_addr = dest_addr
#         self.length = length
#         self.arrival_time = arrival_time

class Packet:
    def __init__(self, priority, ip_src, src_port, ip_dest, dest_port, length):
        self.priority = priority
        self.ip_src = ip_src
        self.src_port = src_port
        self.ip_dest = ip_dest
        self.dest_port = dest_port
        self.length = length

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

    # def unpack_data(self, packet):
    #     priority, ip_src, src_port, ip_dest, dest_port, length = struct.unpack('!B4sH4sHI', packet[:17])
    #     data = packet[17:]
    #     return priority, socket.inet_ntoa(ip_src), socket.ntohs(src_port), socket.inet_ntoa(ip_dest), socket.ntohs(dest_port), length, data

    def queue_packet(self, packet):
        # print(type(len(self.queues[packet.priority])))
        # print(type(self.queue_sizes))
        if len(self.queues[packet.priority]) < self.queue_sizes:
            self.queues[packet.priority].append(packet)
            self.log(f"Packet queued", packet)
        else:
            self.log(f"Packet dropped: queue for priority {packet.priority} is full.", packet)

    def send_packet(self, packet, byte_packet):
        print('insde send packet')
        src_addr, src_port = self.socket.getsockname()

        destination_ip = packet.ip_dest
        destination_port = packet.dest_port

        for entry in self.forwarding_table:
            print('inside for')
            ip_src = socket.gethostbyname(entry[0])
            port_src = int(entry[1])
            ip_dest = socket.gethostbyname(entry[2])
            port_dest = int(entry[3])

            if ip_src != src_addr and port_src != src_port: # ignore packets that don't corresponse to its own hostname and porpt
                print(ip_src)
                print(src_addr)
                print(port_src)
                print(src_port)
                continue

            #if ip_dest == destination_ip and port_dest == destination_port: # indicates a match
            next_hop_host = socket.gethostbyname(entry[4])
            next_hop_port = int(entry[5])
            delay = int(entry[6])
            time.sleep(delay/1000)
            loss_prob = int(entry[7])/ 100
            print(loss_prob)
            if random.uniform(0, 1) >= loss_prob:
                packed_packet = self.pack_data(packet,byte_packet)
                print("next hop",next_hop_host,next_hop_port)
                self.socket.sendto(packed_packet, (next_hop_host, next_hop_port)) 
            else: 
                #drop packet and event should be logged
                self.log("FAILURE: no forwarding entry found", packet)

            

            # packet = self.pack_data(packet, byte_packet)
            # destination = [ip_dest, port_dest]

            # self.queueing(packet.priority, packet, destination)
            print("Will send packet to the next hop")
            # else:
            #     # drop packet and event should be logged
            #     self.log("FAILURE: no forwarding entry found", packet)


        # next_hop_info = self.forwarding_table.get((packet.dest_addr, packet.dest_port))
        # if next_hop_info:
        #     next_hop, delay, loss_prob = next_hop_info
        #     # Simulate delay
        #     time.sleep(delay / 1000.0)  # Delay is in milliseconds
        #     # Simulate packet loss
        #     if random.uniform(0, 1) >= loss_prob:
        #         next_table = ()
        #         if()
        #         next_hop_ip, next_hop_port = next_hop
        #         self.socket.sendto(packet.data, (next_hop_ip, next_hop_port))
        #         self.log(f"Packet forwarded to {next_hop_ip}:{next_hop_port}", packet)
        #     else:
        #         self.log(f"Packet lost due to simulated network loss", packet)
        # else:
        #     self.log(f"No forwarding entry found for packet", packet)

    def forward_packets(self, byte_packet):
        # Forward packets from the queues based on priority
        for priority in sorted(self.queues.keys()):
            while self.queues[priority]:
                packet = self.queues[priority].pop(0)
                print(packet)
                self.send_packet(packet, byte_packet)

    def run(self):
        while True:
            try:
                bytes_packet, addr = self.socket.recvfrom(1024)
                arrival_time = datetime.now()
                packet = self.unpack_data(bytes_packet) # convert packet
               # priority, src_addr, src_port, dest_addr, dest_port, length, data = self.unpack_data(bytes_packet)
               # packet = Packet(priority, data, src_addr, dest_addr, length, arrival_time)
                self.queue_packet(packet)
            except socket.error:
                pass  # Non-blocking call, proceed if no packet is received
            finally:         
                self.forward_packets(bytes_packet)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', type=int, required=True, help='Port of the emulator.')
    parser.add_argument('-q', type=int, required=True, help='The sizes of the three queues for each priority.')
    parser.add_argument('-f', type=str, required=True, help='The name of the file containing the static forwarding table.')
    parser.add_argument('-l', type=str, required=True, help='The name of the log file.')
    args = parser.parse_args()

    queue_size = int(args.q)

    forwarding_table = []
    with open(args.f, 'r') as file:
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
