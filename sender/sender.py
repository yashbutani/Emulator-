import argparse
import socket
import time
import struct
import os
from datetime import datetime

def send_file(s, filename, dest_addr, rate, seq_no, length):
# UPDATE SENDER SO IT CAN:
# 1. Always start at sequence number 1
# 2. Increment the sequence number by 1 for each packet sent, instead of by the packet length
# 3. Print out the observed percentage of packets lost. # The loss rate that the sender prints
# out is not necessarily the same as the loss rate that we identify in the forwarding table since the sender might miss some ACKs. 
# This loss rate is computed by (number of retransmissions / total number of transmissions), 
# where total number of transmissions including both normal transmissions and retransmissions.
# 3. The end packet is sent after ensuring that all data packets have been received by the receiver 
# (or if max number of retries have reached for sending all packets in the last window).
 
    address = f"{dest_addr[0]}:{dest_addr[1]}"

    if not os.path.exists(filename):
        print(f"File {filename} not found!")
        return

    with open(filename, 'rb') as file:
        while True:
            data = file.read(length)
            if not data:
                print("\nEND Packet")
                # Sending the END packet
                header = struct.pack('!cII', b'E', socket.htonl(seq_no), 0)
                s.sendto(header, dest_addr)
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                print(f"send time:\t{current_time}\nrequester addr:\t{address}\nSequence num::\t{seq_no}\nlength:\t\t0\npayload:\t\n")
                break
            
            header = struct.pack('!cII', b'D', socket.htonl(seq_no), len(data))
            packet = header + data
            s.sendto(packet, dest_addr)
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]

            # Print the sender's log
            print("\nDATA Packet")
            print(f"send time:\t{current_time}\nrequester addr:\t{address}\nSequence num::\t{seq_no}\nlength:\t\t{len(data)}\npayload:\t{data[:4].decode('utf-8', 'ignore')}")
            
            seq_no += len(data)
            time.sleep(1.0/rate)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', type=int, required=True, help='Port for the sender to listen on.')
    parser.add_argument('-g', type=int, required=True, help='Port for the requester.')
    parser.add_argument('-r', type=int, required=True, help='Rate of sending packets.')
    parser.add_argument('-q', type=int, required=True, help='Initial sequence number.')
    parser.add_argument('-l', type=int, required=True, help='Length of the payload in bytes.')
    parser.add_argument('-f', type=int, required=True, help='The host name of the emulator.')
    parser.add_argument('-e', type=int, required=True, help='The port of the emulator.')
    parser.add_argument('-i', type=int, required=True, help='The priority of the sent packets.')
    parser.add_argument('-t', type=int, required=True, help='The timeout for retransmission for lost packets in the unit of milliseconds.')
    args = parser.parse_args()

    # Check port range validity
    if not (2049 < args.p < 65536) or not (2049 < args.g < 65536):
        print("Error: Port number must be in the range 2050 to 65535.")
        exit(1)

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind((socket.gethostname(), args.p))
        print('----------------------------')
        print("sender1's print information:")

        try:
            while True:
                # Listen for incoming request packets
                data, addr = s.recvfrom(4096)
                packet_type, _, _ = struct.unpack('!cII', data[:9])
                if packet_type == b'R':
                    requested_file = data[9:].decode()
                    print('file',requested_file)
                    send_file(s, requested_file, (addr[0], args.g), args.r, args.q, args.l)

        except KeyboardInterrupt:
            print("\nShutting down sender...")
        finally:
            s.close()
