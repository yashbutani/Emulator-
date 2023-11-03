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
        


def write_to_file(file_name, payload):
    with open(file_name, 'a') as file:
        # if payload == "end":
        #     file.write("\n")
      #  else:
        file.write(payload.decode())


def send_requests(trackers, s, args):
    packet_type = b'R'
    seq_num = socket.htonl(0)
    length = socket.htonl(args.window)
    old_packet = struct.pack("!cII", packet_type, seq_num, length) + args.file.encode()

    src_addr, src_port = s.getsockname()

    # setup new packet (priority always 1 w requester)
    priority = 0x01

    # Convert IP addresses to network byte order
    packed_ip_src = socket.inet_aton(src_addr)

    # 16-bit
    src_port = socket.htons(src_port)
    
    # get destination from trackers
    for tracker in trackers:            # TODO important -> what will happen if there are multiple trakers!!!
        ip_addr = socket.gethostbyname(tracker.hostname)
        packed_ip_dest = socket.inet_aton(ip_addr)
        dest_port = socket.htons(tracker.port)
    
    # len of new packet == length of old
    packet_len = len(old_packet)

    # create new packet
    packed_data = struct.pack('!B4sH4sHI', priority, packed_ip_src, src_port, packed_ip_dest, dest_port, packet_len)

    # combine w previous
    final_packet = packed_data + old_packet

    s.sendto(final_packet, (args.hostname, args.e_port))

    # for tracker in trackers:
    #     if args.file == tracker.filename:
    #         sock.sendto(packet, (tracker.hostname, tracker.port))
    #         # Handling responses
    #         handle_packets(sock, args)


def handle_packets(sock, args):
    sender_stats = {}


    while True:
        data, addr = sock.recvfrom(65535)  # Maximum UDP packet size
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        packet_type, seq_num, length = struct.unpack("!cII", data[:9])


        seq_num = socket.ntohl(seq_num)  # Convert seq_num from network byte order to host byte order
        payload = data[9:]


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
            # Print details for the data packet
            print(f"\nDATA Packet")
            print(f"recv time:\t{current_time}")
            print(f"sender addr:\t{sender_addr}")
            print(f"Sequence num:\t{seq_num}")
            print(f"length:\t\t{len(payload)}")
            print(f"payload:\t{payload[:4].decode('utf-8', 'ignore')}")  # Print only first few bytes of the payload
           
            # Update stats for the sender
            sender_stats[key]["total_packets"] += 1
            sender_stats[key]["total_bytes"] += len(payload)

           #if data_end != True:
            # Here you would handle the data, e.g., writing it to a file
            write_to_file(args.file, payload)


        elif packet_type == b'E':
            print("\nEND Packet")
            print(f"recv time:\t{current_time}")
            print(f"sender addr:\t{sender_addr}")
            print(f"Sequence num:\t{seq_num}")
            print(f"length:\t{length}")
            print(f"payload:\t{len(payload)}")


            # Calculate and print summary statistics here
            stats = sender_stats[key]
            end_time = time.time()
            duration = end_time - time.mktime(datetime.strptime(stats["start_time"], '%Y-%m-%d %H:%M:%S.%f').timetuple())
            packets_per_second = stats["total_packets"] / duration if duration > 0 else 0


            print(f"\nSummary for {sender_addr}")
            print(f"Total Data packets: {stats['total_packets']}")
            print(f"Total Data bytes: {stats['total_bytes']}")
            print(f"Start time: {stats['start_time']}")
            print(f"End time: {current_time}")
            print(f"Duration of the test: {duration:.2f} seconds")
            print(f"Data packets/second: {packets_per_second:.2f}\n")
            break


def main():
    tracker_arr = [] #filename,id,hostname,port sender is recieving requests on 
    with open('tracker.txt', 'r') as file: #you have to request from one sender at a time and then move on to the next
        content = file.readlines()
        content = [line.strip() for line in content if line.strip()]  # Avoid empty lines
        content.sort(key=lambda content: content[1])
        for i in content:
            filename, seq_no, hostname, port = i.split()
            tracker_arr.append(Tracker(filename, int(seq_no), hostname, int(port)))

        
        print('----------------------------')
        print("Requester’s print information:")

        parser = argparse.ArgumentParser(description="UDP File Requester")
        parser.add_argument("-p", "--port", type=int, required=True, help="Port to bind to")
        parser.add_argument("-o", "--file", type=str, required=True, help="File to request")
        parser.add_argument("-f", "--hostname", type=str, required=True, help="The host name of the emulator.")
        parser.add_argument("-e", "--e_port", type=int, required=True, help="The port of the emulator.")
        parser.add_argument("-w", "--window", type=int, required=True, help="The requester's window size.")
        args = parser.parse_args()


        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.bind((socket.gethostname(), args.port))
            print("test")

            # requester will advertise a window size to the sender
            # it is willing to accept 10 packets at once before sending an ACK
            send_requests(tracker_arr, s, args)


            # Send the request packet to the emulator
          
           # s.sendto(packet, (host, port))

            # send window to the sender

            # Send requests in the main thread
          #  send_requests(tracker_arr, s, args)


if __name__ == "__main__":
    main()



