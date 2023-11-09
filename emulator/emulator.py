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

    def queue_packet(self, packet):
        queue = self.queues[packet.priority]
        if len(queue) < self.queue_sizes[packet.priority - 1]:
            queue.append(packet)
        else:
            self.log(f"Packet dropped: queue for priority {packet.priority} is full.")

    def forward_packets(self):
        for priority, queue in self.queues.items():
            while queue:
                packet = queue.pop(0)
                self.send_packet(packet)

    def send_packet(self, packet):
        # Find the forwarding information for the packet's destination
        dest = (packet.dest_addr[0], packet.dest_addr[1])
        if dest in self.forwarding_table:
            next_hop, delay, loss_prob = self.forwarding_table[dest]
            # Simulate delay
            time_elapsed = (datetime.now() - packet.arrival_time).total_seconds() * 1000
            if time_elapsed < delay:
                time.sleep((delay - time_elapsed) / 1000.0)
            # Simulate potential packet loss
            if random.random() > loss_prob:
                # Send the packet to the next hop
                self.socket.sendto(packet.data, next_hop)
            else:
                self.log(f"Packet lost: simulated loss for priority {packet.priority} packet.")
        else:
            self.log("No routing information found for packet.")

    def run(self):
        while True:
            try:
                packet_data, addr = self.socket.recvfrom(1024)
                priority, src_ip, src_port, dest_ip, dest_port, length, data = self.unpack_data(packet_data)
                arrival_time = datetime.now()
                packet = Packet(priority, data, (src_ip, src_port), (dest_ip, dest_port), arrival_time)
                self.queue_packet(packet)
            except socket.error:
                pass  # Non-blocking call, proceed if no packet is received

            self.forward_packets()  # Forward packets from the queues

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
