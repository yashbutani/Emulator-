import argparse
import socket
import time
import struct
import os
from datetime import datetime

def send_file(s, filename, dest_addr, rate, seq_no, length):
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
    parser.add_argument('-p', type=int, required=True, help='Port of the emulator.')
    parser.add_argument('-q', type=int, required=True, help='The size of each of the three queues.')
    parser.add_argument('-f', type=int, required=True, help='The name of the file containing the static forwarding table.')
    parser.add_argument('-l', type=int, required=True, help='The name of the log file.')
    args = parser.parse_args()

    # Check port range validity
    if not (2049 < args.p < 65536) or not (2049 < args.g < 65536):
        print("Error: Port number must be in the range 2050 to 65535.")
        exit(1)

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind((socket.gethostname(), args.p))
        print('----------------------------')
        print("emualtor's print information:")

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
