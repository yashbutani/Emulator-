import argparse
import socket
import struct
import time
from datetime import datetime
import random

class Packet:
    def __init__(self, priority, data, src_addr, dest_addr, length, arrival_time):
        self.priority = priority
        self.data = data
        self.src_addr = src_addr
        self.dest_addr = dest_addr
        self.length = length
        self.arrival_time = arrival_time

class Emulator:
    def __init__(self, port, queue_sizes, forwarding_table, log_file):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('', port))
        self.queues = {1: [], 2: [], 3: []}  # Separate queue for each priority
        self.queue_sizes = queue_sizes  # Dict with queue sizes for each priority
        self.forwarding_table = forwarding_table
        self.log_file = log_file

    def log(self, message, data_packet=None):
        with open(self.log_file, 'a') as f:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            log_message = f"{timestamp} - {message}"
            if data_packet:
                log_message += (f" - Src: {data_packet.src_addr}:{data_packet.src_port}, "
                                f"Dst: {data_packet.dest_addr}:{data_packet.dest_port}, "
                                f"Priority: {data_packet.priority}, "
                                f"Length: {data_packet.length}\n")
            f.write(log_message)

    def unpack_data(self, packet):
        priority, ip_src, src_port, ip_dest, dest_port, length = struct.unpack('!B4sH4sHI', packet[:17])
        data = packet[17:]
        return priority, socket.inet_ntoa(ip_src), socket.ntohs(src_port), socket.inet_ntoa(ip_dest), socket.ntohs(dest_port), length, data

    def queue_packet(self, packet):
        if len(self.queues[packet.priority]) < self.queue_sizes[packet.priority - 1]:
            self.queues[packet.priority].append(packet)
            self.log(f"Packet queued", packet)
        else:
            self.log(f"Packet dropped: queue for priority {packet.priority} is full.", packet)

    def send_packet(self, packet):
        next_hop_info = self.forwarding_table.get((packet.dest_addr, packet.dest_port))
        if next_hop_info:
            next_hop, delay, loss_prob = next_hop_info
            # Simulate delay
            time.sleep(delay / 1000.0)  # Delay is in milliseconds
            # Simulate packet loss
            if random.uniform(0, 1) >= loss_prob:
                next_hop_ip, next_hop_port = next_hop
                self.socket.sendto(packet.data, (next_hop_ip, next_hop_port))
                self.log(f"Packet forwarded to {next_hop_ip}:{next_hop_port}", packet)
            else:
                self.log(f"Packet lost due to simulated network loss", packet)
        else:
            self.log(f"No forwarding entry found for packet", packet)

    def forward_packets(self):
        # Forward packets from the queues based on priority
        for priority in sorted(self.queues.keys()):
            while self.queues[priority]:
                packet = self.queues[priority].pop(0)
                self.send_packet(packet)

    def run(self):
        while True:
            try:
                bytes_packet, addr = self.socket.recvfrom(1024)
                arrival_time = datetime.now()
                priority, src_addr, src_port, dest_addr, dest_port, length, data = self.unpack_data(bytes_packet)
                packet = Packet(priority, data, src_addr, dest_addr, length, arrival_time)
                self.queue_packet(packet)
            except socket.error:
                pass  # Non-blocking call, proceed if no packet is received

            self.forward_packets()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', type=int, required=True, help='Port of the emulator.')
    parser.add_argument('-q', type=int, nargs=1, required=True, help='The sizes of the three queues for each priority.')
    parser.add_argument('-f', type=str, required=True, help='The name of the file containing the static forwarding table.')
    parser.add_argument('-l', type=str, required=True, help='The name of the log file.')
    args = parser.parse_args()

    queue_size = args.q

    # Read the forwarding table from the specified file
    forwarding_table = {}
    with open(args.f, 'r') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) == 6:
                dest_ip, dest_port, next_hop_ip, next_hop_port, delay, loss_prob = parts
                forwarding_table[(dest_ip, int(dest_port))] = ((next_hop_ip, int(next_hop_port)), int(delay), float(loss_prob))

    # Set the queue sizes for each priority
    queue_sizes = {1: args.q, 2: args.q, 3: args.q}
    
    # Initialize the emulator with the loaded forwarding table and log file
    emulator = Emulator(args.p, queue_sizes, forwarding_table, args.l)
    emulator.run()
