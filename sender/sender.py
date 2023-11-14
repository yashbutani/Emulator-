import argparse
import socket
import time
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

# class Packet:
#     def __init__(self, priority, ip_src, src_port, ip_dest, dest_port, length):
#         self.priority = priority
#         self.ip_src = ip_src
#         self.src_port = src_port
#         self.ip_dest = ip_dest
#         self.dest_port = dest_port
#         self.length = length

# def unpack_data(packet):
#     unpacked_data = struct.unpack('!B4sH4sHI', packet[:17])
#     priority = unpacked_data[0]

#     # IP conversion
#     ip_src = socket.inet_ntoa(unpacked_data[1])
#     ip_dest = socket.inet_ntoa(unpacked_data[3])

#     # int conversions
#     src_port = socket.ntohs(unpacked_data[2])
#     dest_port = socket.ntohs(unpacked_data[4])
#     length = unpacked_data[5]

#     packet = Packet(priority, ip_src, src_port, ip_dest, dest_port, length)
#     return packet

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

def send_packets(s, filename, sender_info):
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

    total_length = 0
    final_size = 0

    # TODO calculate sequence number
    with open(filename, 'rb') as file:
        while True:
            data = file.read(sender_info.length)
            if not data:
                print("\nEND Packet")
                # Sending the END packet
                sender_header = struct.pack('!cII', b'E', socket.htonl(sender_info.seq_no), 0)
                # final_size = total_length + len(header)
                # # s.sendto(header, dest_addr) wait
                # current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                # print(f"send time:\t{current_time}\nrequester addr:\t{'hit'}\nSequence num::\t{seq_no}\nlength:\t\t0\npayload:\t\n")
            else:
                # Send data Packet
                sender_header = struct.pack('!cII', b'D', socket.htonl(sender_info.seq_no), len(data)) # header for file payload
            
            payload_length = len(sender_header) + len(data)
            src_addr, src_port = s.getsockname()

            # Convert IP addresses to network byte order
            packed_ip_src = socket.inet_aton(src_addr)
            packed_ip_dest = socket.inet_aton(sender_info.req_host)

            # Pack 16-bit ints, 32-bit integers don't need to be converted
            src_port = socket.htons(src_port)
            dest_port = socket.htons(sender_info.req_port)

            emulator_header = struct.pack('!B4sH4sHI', sender_info.priority, packed_ip_src, src_port, packed_ip_dest, dest_port, payload_length)

            # combime both packet headers and payload data
            packet = emulator_header + sender_header + data
            
            #total_length += len(packet)

            # emulator header completed now add data from the file and construct the packet_buffer
            packet_buffer = {} #mapping of seq_no -> ack {seq_no : ACK }
            packet_seq = {} #mapping of sequence num to packet {seq_no : final packet }


            while not all_data_sent:
                if len(packet_buffer) < sender_info.window:
                    packet_buffer[sender_info.seq_no] = packet
                    packet_seq[sender_info.seq_no] = packet
                    time.sleep(0.01)  # Wait for 0.01 seconds before sending the next packet
                    send_to_emulator(s, packet, sender_info.em_host, sender_info.em_port)



                # Check for ACKs
                readable, writable, exceptional = s.select([s], [], [], sender_info.timeout)
                for sock in readable:
                    ack_packet = s.recv(1024)
                    # Extract ACK number and remove from packet_buffer

                # Check if all packets have been sent and all ACKs received
                all_data_sent = check_all_data_sent_and_acked()



        #     bps = file_packet_size + 17 
        #     packets_per_window = bps/window

        #     data_rate = rate * length

        #     milliseconds = 10^3
        #     packets_per_milli = (10^3)/rate

        #     for i in range(packets_per_milli):

        #         pass
        #     # send one packet every 
        #     # Since a second has 1000 milliseconds, and you need to send 100 packets in that time, you should aim to send one packet every 10 milliseconds.

        #     print('file_data_length',len(data))
        #     header = struct.pack('!cII', b'D', socket.htonl(seq_no), len(data))
        #     packet = header + data
        #     total_length += len(packet)

        #   #  s.sendto(packet, dest_addr) # wait to send... i think -> send to emulator which determines order
        #     current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]

        #     # Print the sender's log
        #     print("\nDATA Packet")
        #     print(f"send time:\t{current_time}\nrequester addr:\t{address}\nSequence num::\t{seq_no}\nlength:\t\t{len(data)}\npayload:\t{data[:4].decode('utf-8', 'ignore')}")
            
        #     seq_no += 1
        #     time.sleep(1.0/rate)




   # unpacked_ip_src = struct.unpack('!I', packed_ip_src)[0]
   # unpacked_ip_dest = struct.unpack('!I', packed_ip_dest)[0]
    # final_packet = packed_data + header + data
    # print(final_packet)
    # return final_packet,seq_no
    

class Sender():
    def __init__(self,rate, seq_no, pload_len, em_host_name, em_port_name, priority, timeout):
        self.rate = rate
        self.seq_no = seq_no
        self.pload_len = pload_len
        self.em_host_name = em_host_name
        self.em_port_name = em_port_name
        self.priority = priority
        self.timeout = timeout

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
                print(data)
                file_packet_size, packet_type, seq_no, window = struct.unpack('!IcII', data[13:26])
                if packet_type == b'R':
                    requested_file = data[26:].decode()
                    send_packets(s, requested_file, sender_info)
                if packet_type == b'A':
                    pass


                    # window = socket.ntohl(window) 
                    # seq_no = socket.ntohl(seq_no)
                    # bytes_per_packet = file_packet_size + 17 
                    # packets_per_window = bytes_per_packet/window
                    # print('window',window)
                    # print('file',requested_file)
                    # print('file_packet_size',packets_per_window)
                    # get_packet(s, requested_file, (addr[0], args.g), args.r, args.q, args.l, args.i, file_packet_size)
                  #  exit(1)
                    packet_buffer = {} #mapping of seq_no -> ack {seq_no : ACK }
                    packet_seq = {} #mapping of sequence num to packet {seq_no : final packet }
                    for i in range(packets_per_window): 
                        final_packet,current_seq_no = get_packet(s, requested_file, (addr[0], args.g), args.r, args.q, args.l, args.i, window, args.t)
                        packet_buffer[current_seq_no] = False 
                        packet_seq[current_seq_no] = final_packet
                    while packet_buffer: # loop until all packets have been acked 
                        for seq_no in packet_buffer: 
                            if receive_ack(s,seq_no,args.t):
                                print('ACK Recieved')
                                del packet_buffer[seq_no]
                            else: 
                                while not receive_ack(s,seq_no,args.t):#while the ack is not recieved for the seq no
                                    print("ACK Not Recieved")
                                    retransmissions +=1
                                    send_to_emulator(s, final_packet, args.f, args.e)
                                    if retransmissions > 5: 
                                        print(f"Gave up on packet with sequence number {current_seq_no}")
                                        continue
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