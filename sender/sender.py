import argparse
import socket
import time
import struct
import os
from datetime import datetime
import math 

def send_to_emulator(s, final_packet, dest_host, dest_port):
    s.sendto(final_packet, (dest_host, dest_port))

def receive_ack(sock, expected_seq_no, timeout):
    """Wait for an ACK packet."""
    try:
        sock.settimeout(timeout)
        while True:
            ack_packet, _ = sock.recvfrom(1024)
            ack_type, ack_seq_no = struct.unpack('!cI', ack_packet[:5])
            if ack_type == b'A' and ack_seq_no == expected_seq_no:
                return True  # ACK received
    except socket.timeout:
        return False  # ACK not received within the timeout

def get_packet(s, filename, dest_addr, rate, seq_no, length, priority, file_packet_size):
# UPDATE SENDER SO IT CAN:
# 3. Print out the observed percentage of packets lost. # The loss rate that the sender prints
# out is not necessarily the same as the loss rate that we identify in the forwarding table since the sender might miss some ACKs. 
# This loss rate is computed by (number of retransmissions / total number of transmissions), 
# where total number of transmissions including both normal transmissions and retransmissions.
# 3. The end packet is sent after ensuring that all data packets have been received by the receiver 
# (or if max number of retries have reached for sending all packets in the last window).
    address = f"{dest_addr[0]}:{dest_addr[1]}"
    seq_no = 1
    
    # creating header
     # below code creates the new packet with old appened
    length = file_packet_size
    src_addr, src_port = s.getsockname()

    # Convert IP addresses to network byte order
    packed_ip_src = socket.inet_aton(src_addr)
    packed_ip_dest = socket.inet_aton(dest_addr[0])

    # Pack 16-bit ints
    src_port = socket.htons(src_port)
    dest_port = socket.htons(dest_addr[1])

    # Pack 32-bit integers
    packet_len = length

    packed_data = struct.pack('!B4sH4sHI', priority, packed_ip_src, src_port, packed_ip_dest, dest_port, packet_len)

    if not os.path.exists(filename):
        print(f"File {filename} not found!")
        return

    total_length = 0
    final_size = 0
    with open(filename, 'rb') as file:
        while True:
            data = file.read(length)
            if not data:
                print("\nEND Packet")
                # Sending the END packet
                header = struct.pack('!cII', b'E', socket.htonl(seq_no), 0)
                final_size = total_length + len(header)
                # s.sendto(header, dest_addr) wait
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                print(f"send time:\t{current_time}\nrequester addr:\t{address}\nSequence num::\t{seq_no}\nlength:\t\t0\npayload:\t\n")
                break
            bps = file_packet_size + 17 
            packets_per_window = bps/window
            print('file_data_length',len(data))
            exit(1)
            header = struct.pack('!cII', b'D', socket.htonl(seq_no), len(data))
            packet = header + data
            total_length += len(packet)

          #  s.sendto(packet, dest_addr) # wait to send... i think -> send to emulator which determines order
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]

            # Print the sender's log
            print("\nDATA Packet")
            print(f"send time:\t{current_time}\nrequester addr:\t{address}\nSequence num::\t{seq_no}\nlength:\t\t{len(data)}\npayload:\t{data[:4].decode('utf-8', 'ignore')}")
            
            seq_no += 1
            time.sleep(1.0/rate)




   # unpacked_ip_src = struct.unpack('!I', packed_ip_src)[0]
   # unpacked_ip_dest = struct.unpack('!I', packed_ip_dest)[0]
    final_packet = packed_data + header + data
    print(final_packet)
    return final_packet,seq_no
    

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
        s.bind((socket.gethostname(), args.p))
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
                print(data)
                file_packet_size, packet_type, seq_no, window = struct.unpack('!IcII', data[13:26])
                # file_packet_size = struct.unpack('!I', data[13:17])[0]
                print(file_packet_size)
                if packet_type == b'R':
                    requested_file = data[26:].decode()
                    window = socket.ntohl(window) 
                    seq_no = socket.ntohl(seq_no)
                    bps = file_packet_size + 17 
                    packets_per_window = bps/window
                    print('window',window)
                    print('file',requested_file)
                    print('file_packet_size',packets_per_window)
                  #  exit(1)
                    packet_buffer = {}
                    final_packet,curent_seq_no = get_packet(s, requested_file, (addr[0], args.g), args.r, args.q, args.l, args.i, file_packet_size)
                    while not receive_ack(s,curent_seq_no,args.t):
                        retransmissions +=1
                        send_to_emulator(s, final_packet, args.f, args.e)
                        if retransmissions > 5: 
                            print(f"Gave up on packet with sequence number {curent_seq_no}")
                            break
                    #send_to_emulator(s, final_packet, args.f, args.e)

                #     # determine if a retransmission occur
                #     if (if no ack in timeout):
                #         retransmissions += 1
                #     transmissions += 1

        except KeyboardInterrupt:
            print("\nShutting down sender...")
        finally:
            s.close()

        print(retransmissions/transmissions)