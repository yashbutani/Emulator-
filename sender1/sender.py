import argparse
import socket
import time
import math
import struct
import os
from datetime import datetime
import math 

class Sender():
    def __init__(self, req_host, req_port, rate, seq_no, pload_len, em_host, em_port, priority, timeout):
        self.req_host = req_host
        self.req_port = req_port
        self.rate = rate
        self.seq_no = seq_no
        self.pload_len = pload_len
        self.em_host = em_host
        self.em_port = em_port
        self.priority = priority
        self.timeout = timeout


def send_to_emulator(s, final_packet, dest_host, dest_port):
    s.sendto(final_packet, (dest_host, dest_port))

def receive_ack(sock, ack_tracker, timeout):
    try:
        sock.settimeout(timeout/1000)
        ack_packet, _ = sock.recvfrom(4096)
        ack_type, ack_seq_no = struct.unpack('!cI', ack_packet[17:22])

        if ack_type == b'A' and ack_seq_no in ack_tracker:
            ack_tracker[ack_seq_no] = True

    except socket.timeout:
        pass

    return ack_tracker

# Function to create data or end packet
def make_packet(sender_info, seq_no, file_data):
    if file_data is None:  # End packet
        packet_type = b'E'
        length = 0
    else:
        packet_type = b'D'
        length = len(file_data)

    sender_header = struct.pack('!cII', packet_type, seq_no, length)
    payload_length = len(sender_header) + length
    src_addr, src_port = s.getsockname()
    packed_ip_src = socket.inet_aton(src_addr)
    packed_ip_dest = socket.inet_aton(sender_info.req_host)
    src_port = socket.htons(src_port)
    dest_port = socket.htons(sender_info.req_port)
    emulator_header = struct.pack('!B4sH4sHI', sender_info.priority, packed_ip_src, src_port, packed_ip_dest, dest_port, payload_length)
    packet = emulator_header + sender_header + (file_data if file_data is not None else b'')
    return packet


def send_packets(s, filename, sender_info, window):
# UPDATE SENDER SO IT CAN:
# 3. Print out the observed percentage of packets lost. # The loss rate that the sender prints
# out is not necessarily the same as the loss rate that we identify in the forwarding table since the sender might miss some ACKs. 
# This loss rate is computed by (number of retransmissions / total number of transmissions), 
# where total number of transmissions including both normal transmissions and retransmissions.
# 3. The end packet is sent after ensuring that all data packets have been received by the receiver 
# (or if max number of retries have reached for sending all packets in the last window).

    if not os.path.exists(filename):
        print(f"File {filename} not found!")
        return

    seq_no = 1
    transmissions = 0
    total_retransmissions = 0

    with open(filename, 'rb') as file:
        while True:
            packet_buffer = {}
            ack_tracker = {}

            # iterate thru window to build packet_buffer with payloads and ack_tracker with default False values
            for _ in range(window):
                data = file.read(sender_info.pload_len)
                if not data and not packet_buffer:          # End of file and no packets to send
                    packet = make_packet(sender_info, seq_no, None)
                    send_to_emulator(s, packet, sender_info.em_host, sender_info.em_port)
                    transmissions += 1
                    percentage_dropped = total_retransmissions/transmissions
                    return (percentage_dropped * 100)
                elif data:
                    packet = make_packet(sender_info, seq_no, data)
                    packet_buffer[seq_no] = packet
                    ack_tracker[seq_no] = False
                    seq_no += 1

            # Send payload data from the apcket_buffer to the emulator and receive acks
            for _, packet in packet_buffer.items():
                send_to_emulator(s, packet, sender_info.em_host, sender_info.em_port)
                transmissions += 1
                time.sleep(sender_info.rate/1000)
                ack_tracker = receive_ack(s, ack_tracker, sender_info.timeout)

            # make sure all values in ack_tracker are true; if not retransmmit
            while not all(ack_tracker.values()):
                retransmissions = 0
                for num in ack_tracker:
                    if not ack_tracker[num]:
                        send_to_emulator(s, packet_buffer[num], sender_info.em_host, sender_info.em_port)
                        time.sleep(sender_info.rate/1000)
                        ack_tracker = receive_ack(s, ack_tracker, sender_info.timeout)

                        transmissions += 1
                        retransmissions += 1
                        total_retransmissions += 1
                        
                if retransmissions >= 5:
                    print(f"Gave up on packet with sequence number {num}")
                    return



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', type=int, required=True, help='Port for the sender to listen on.')
    parser.add_argument('-g', type=int, required=True, help='Port for the requester.')
    parser.add_argument('-r', type=int, required=True, help='Rate of sending packets.')
    parser.add_argument('-q', type=int, required=True, help='Initial sequence number.')
    parser.add_argument('-l', type=int, required=True, help='Length of the payload in bytes.')
    parser.add_argument('-f', type=str, required=True, help='The host name of the emulator.')
    parser.add_argument('-e', type=int, required=True, help='The port of the emulator.')
    parser.add_argument('-i', type=int, required=True, help='The priority of the sent packets.')
    parser.add_argument('-t', type=int, required=True, help='The timeout for retransmission for lost packets in the unit of milliseconds.')
    args = parser.parse_args()


    # Check port range validity
    if not (2049 < args.p < 65536) or not (2049 < args.g < 65536):
        print("Error: Port number must be in the range 2050 to 65535.")
        exit(1)

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind(('localhost', args.p))
        print('----------------------------')
        print("sender1's print information:")
        transmissions = 0
        retransmissions = 0
        try:
            

            # TODO for timeout using args.t
           # The sender keeps this set of data in a buffer, and keeps a timeout for each of the packets. 
           # If it does not receive an ack for a packet and its timeout expires, it will retransmit that packet. 
           # The timeout is fixed and is specified by one of the sender's parameters.

            while True:
                # Listen for incoming request packets
                data, addr = s.recvfrom(4096)
                sender_info = Sender(addr[0], args.g, args.r, args.q, args.l, args.f, args.e, args.i, args.t)
                packet_type, seq_no, window = struct.unpack('!cII', data[17:26])
                if packet_type == b'R':
                    requested_file = data[26:].decode()
                    percentage = send_packets(s, requested_file, sender_info, window)
                    print('Loss Rate:', percentage)
                    break

        except KeyboardInterrupt:
            print("\nShutting down sender...")
        finally:
            s.close()