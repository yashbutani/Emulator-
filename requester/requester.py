import argparse
import socket
import time
import struct
import threading
from datetime import datetime


class Tracker:
    def __init__(self, filename, seq_no, hostname, port):
        self.filename = filename
        self.seq_no = seq_no
        self.hostname = hostname
        self.port = port
        


def write_to_file(file_name, sorted_buffer):
    with open(file_name, 'a') as file:
        for seq_num, payload in sorted_buffer:
            file.write(payload.decode())
    return


def send_requests(trackers, s, args):    
    # get destination from trackers
    for tracker in trackers:            # TODO important -> what will happen if there are multiple trakers!!!
        packet_type = b'R'
        seq_num = tracker.seq_no
        window = args.window
        old_packet = struct.pack("!cII", packet_type, seq_num, window) + args.file.encode()

        src_addr, src_port = s.getsockname()

        # setup new packet (priority always 1 w requester)
        priority = 0x01

        # Convert IP addresses to network byte order
        packed_ip_src = socket.inet_aton(src_addr)

        # 16-bit
        src_port = socket.htons(src_port)

        ip_addr = socket.gethostbyname(tracker.hostname)
        packed_ip_dest = socket.inet_aton(ip_addr)
        dest_port = socket.htons(tracker.port)
    
        # len of new packet == length of old
        packet_len = len(old_packet)

        # create new packet
        emulator_header = struct.pack('!B4sH4sHI', priority, packed_ip_src, src_port, packed_ip_dest, dest_port, packet_len)

        # combine w previous
        final_packet = emulator_header + old_packet

        s.sendto(final_packet, (args.e_hostname, args.e_port))

        # create ack emulator header
        packet_len = 5
        ack_em_header = struct.pack('!B4sH4sHI', priority, packed_ip_src, src_port, packed_ip_dest, dest_port, packet_len)
        handle_packets(s, args, ack_em_header)


def handle_packets(sock, args, ack_em_header):
    sender_stats = {}
    data_buffer = {}
    writen_seq = []
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    next_window = 0
    while True:
        data, addr = sock.recvfrom(65535)  # Maximum UDP packet size
        packet_type, seq_num, length = struct.unpack("!cII", data[17:26])
        payload = data[26:]


        sender_addr = f"{addr[0]}:{addr[1]}"
        key = sender_addr


        if key not in sender_stats:
            sender_stats[key] = {
                "total_packets": 0,
                "total_bytes": 0,
                "start_time": current_time,
                "sender": sender_addr,
            }


        if packet_type == b'D':           
            # Update stats for the sender
            sender_stats[key]["total_packets"] += 1
            sender_stats[key]["total_bytes"] += len(payload)

            # add if not in data_buffer
            if seq_num not in data_buffer and seq_num > next_window:
                ack_packet = struct.pack("!cI", b'A', seq_num)
                ack = ack_em_header + ack_packet
                sock.sendto(ack, (args.e_hostname, args.e_port))
                data_buffer[seq_num] = payload
    
            # write to file
            if len(data_buffer) == args.window:# or length != args.window:
                sorted_buffer = {}
                sorted_buffer = sorted(data_buffer.items(), key=lambda x: x[0])
                with open('log', 'a') as f:
                   # f.write("\nSorted Buffer:\n")
                    f.write('\n' + str(sorted_buffer))
                #print('data_buffer', sorted_buffer)
                next_window += args.window
                write_to_file(args.file, sorted_buffer)
                data_buffer = {}
                

        elif packet_type == b'E':
            # write last data to file
            sorted_buffer = {}
            sorted_buffer = sorted(data_buffer.items(), key=lambda x: x[0])
            write_to_file(args.file, sorted_buffer)

            # Calculate and print summary statistics here
            stats = sender_stats[key]
            end_time = time.time()
            duration = end_time - time.mktime(datetime.strptime(stats["start_time"], '%Y-%m-%d %H:%M:%S.%f').timetuple())
            packets_per_second = stats["total_packets"] / duration if duration > 0 else 0

            print(f"\nSummary for {sender_addr}")
            print(f"Total Data packets: {stats['total_packets']}")
            print(f"Total Data bytes: {stats['total_bytes']}")
            print(f"Data packets/second: {packets_per_second:.2f}")
            print(f"Duration of the test: {duration:.2f} seconds\n")
            break


def main():
    tracker_arr = [] #filename,id,hostname,port sender is recieving requests on 
    with open('tracker.txt', 'r') as file: #you have to request from one sender at a time and then move on to the next
        content = file.readlines()
        content = [line.strip() for line in content if line.strip()]  # Avoid empty lines
        content.sort(key=lambda line: int(line.split()[1]))
        for i in content:
            filename, seq_no, hostname, port = i.split()
            tracker_arr.append(Tracker(filename, int(seq_no), hostname, int(port)))
            
        print('----------------------------')
        print("Requester’s print information:")

        parser = argparse.ArgumentParser(description="UDP File Requester")
        parser.add_argument("-p", "--port", type=int, required=True, help="Port to bind to")
        parser.add_argument("-o", "--file", type=str, required=True, help="File to request")
        parser.add_argument("-f", "--e_hostname", type=str, required=True, help="The host name of the emulator.")
        parser.add_argument("-e", "--e_port", type=int, required=True, help="The port of the emulator.")
        parser.add_argument("-w", "--window", type=int, required=True, help="The requester's window size.")
        args = parser.parse_args()


        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.bind(('localhost', args.port))
            
            # requester will advertise a window size to the sender
            # it is willing to accept 10 packets at once before sending an ACK
            send_requests(tracker_arr, s, args)



if __name__ == "__main__":
    main()
