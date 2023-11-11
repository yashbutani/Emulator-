import argparse
import socket
import struct
import time
import os

def send_packet(sock, packet, dest_addr):
    """Send a packet to the emulator."""
    sock.sendto(packet, dest_addr)

def create_packet(seq_no, data, packet_type, dest_addr, priority):
    """Create a packet with the given data and sequence number."""
    # Packet header structure: type (1 byte), seq_no (4 bytes), length (4 bytes)
    header = struct.pack('!cII', packet_type, socket.htonl(seq_no), socket.htonl(len(data)))
    packet = header + data
    return packet

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

def send_data(sock, file_path, dest_addr, rate, length, priority, timeout):
    """Read from the file and send data packets."""
    try:
        with open(file_path, 'rb') as file:
            seq_no = 1
            total_packets = 0
            retransmissions = 0

            while True:
                data = file.read(length)
                if not data:
                    break  # End of file reached

                packet = create_packet(seq_no, data, b'D', dest_addr, priority)
                while not receive_ack(sock, seq_no, timeout):
                    send_packet(sock, packet, dest_addr)
                    retransmissions += 1
                    if retransmissions >= 5:
                        print(f"Gave up on packet with sequence number {seq_no}")
                        break

                total_packets += 1
                seq_no += 1
                time.sleep(1 / rate)  # Enforce the sending rate

            # Send END packet
            end_packet = create_packet(seq_no, b'', b'E', dest_addr, priority)
            send_packet(sock, end_packet, dest_addr)

            # Print the packet loss rate
            loss_rate = retransmissions / total_packets if total_packets > 0 else 0
            print(f"Packet loss rate: {loss_rate:.2f}")

    except FileNotFoundError:
        print(f"File {file_path} not found.")

def main():
    parser = argparse.ArgumentParser(description="UDP Sender")
    parser.add_argument('-p', type=int, required=True, help='Port for the sender to listen on.')
    parser.add_argument('-g', type=int, required=True, help='Port for the requester.')
    parser.add_argument('-r', type=float, required=True, help='Rate of sending packets per second.')
    parser.add_argument('-l', type=int, required=True, help='Length of the payload in bytes.')
    parser.add_argument('-f', type=str, required=True, help='The host name of the emulator.')
    parser.add_argument('-e', type=int, required=True, help='The port of the emulator.')
    parser.add_argument('-i', type=int, required=True, help='The priority of the sent packets.')
    parser.add_argument('-t', type=float, required=True, help='Timeout in seconds for ACKs.')
    parser.add_argument('-q', type=float, required=True, help='Sequence Number')
    args = parser.parse_args()
    args.q = 1 

    if not (2049 < args.p < 65536):
        print("Error: Port number must be in the range 2050 to 65535.")
        exit(1)

    # Setup the UDP socket
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind(('', args.p))
        print('Sender is running...')

        while True:
            print("Waiting for incoming requests...")
            data, addr = sock.recvfrom(1024)
            packet_type, _, _ = struct.unpack('!cII', data[:9])
            if packet_type == b'R':
                requested_file = data[9:].decode()
                dest_addr = (args.f, args.e)
                send_data(sock, requested_file, dest_addr, args.r, args.l, args.i, args.t)

if __name__ == '__main__':
    main()
