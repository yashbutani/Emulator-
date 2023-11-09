import argparse
import socket
import struct
from datetime import datetime

def write_to_file(file_name, data):
    """ Append data to the file. """
    with open(file_name, 'ab') as file:
        file.write(data)

def send_ack(sock, seq_num, emulator_addr):
    """ Send an ACK packet for the given sequence number to the emulator address. """
    ack_packet = struct.pack("!cI", b'A', socket.htonl(seq_num))  # Pack the ACK packet with the sequence number
    sock.sendto(ack_packet, emulator_addr)

def handle_packets(sock, file_name, emulator_addr):
    expected_seq_num = 1  # The expected sequence number of the next packet
    received_packets = {}  # Buffer for storing out-of-sequence packets

    while True:
        packet, sender_addr = sock.recvfrom(65535)  # Maximum UDP packet size
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        packet_type, seq_num, length = struct.unpack("!cII", packet[:9])
        seq_num = socket.ntohl(seq_num)  # Convert sequence number to host byte order

        # Send ACK for every packet, including the end packet
        send_ack(sock, seq_num, emulator_addr)

        if packet_type == b'D':
            if seq_num == expected_seq_num:
                # Write data to file and increment the expected sequence number
                write_to_file(file_name, packet[9:])
                expected_seq_num += 1

                # Check if the next expected packet is already in the buffer
                while expected_seq_num in received_packets:
                    write_to_file(file_name, received_packets.pop(expected_seq_num))
                    expected_seq_num += 1

            elif seq_num > expected_seq_num:
                # Buffer the out-of-sequence packet
                received_packets[seq_num] = packet[9:]

        elif packet_type == b'E':
            # End of transmission
            break

        # Print packet information
        print(f"Received time: {current_time}, Sender's address: {sender_addr[0]}:{sender_addr[1]}, "
              f"Packet sequence number: {seq_num}, Payload's length: {length}, "
              f"First 4 bytes of the payload: {packet[9:13].decode('utf-8', 'ignore')}")

def main():
    parser = argparse.ArgumentParser(description="UDP File Requester")
    parser.add_argument("-p", "--port", type=int, required=True, help="Port to bind to")
    parser.add_argument("-o", "--file", type=str, required=True, help="File to request")
    parser.add_argument("-f", "--hostname", type=str, required=True, help="The hostname of the emulator")
    parser.add_argument("-e", "--e_port", type=int, required=True, help="The port of the emulator")
    args = parser.parse_args()

    emulator_addr = (args.hostname, args.e_port)  # Address of the emulator for sending ACKs

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind(('', args.port))  # Bind to the requester's port
        print(f"Requester bound to {socket.gethostname()} on port {args.port}")

        # Handle incoming packets and send ACKs
        handle_packets(s, args.file, emulator_addr)

if __name__ == "__main__":
    main()
