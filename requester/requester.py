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
        


def write_to_file(file_name, sorted_buffer, writen_seq):
    with open(file_name, 'a') as file:
        for seq_num, payload in sorted_buffer:
            file.write(payload.decode())
            writen_seq.append(seq_num)
    return writen_seq


def send_requests(trackers, s, args):    
    # get destination from trackers
    for tracker in trackers:            # TODO important -> what will happen if there are multiple trakers!!!
        packet_type = b'R'
        seq_num = 0
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

    # for tracker in trackers:
    #     if args.file == tracker.filename:
    #         sock.sendto(packet, (tracker.hostname, tracker.port))
    #         # Handling responses
    #         handle_packets(sock, args)


def handle_packets(sock, args, ack_em_header):
    sender_stats = {}
    data_buffer = {}
    writen_seq = []
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    next_window = 0
    while True:
        #print("hello")
        data, addr = sock.recvfrom(65535)  # Maximum UDP packet size
        
        print(data)
       # try:
        packet_type, seq_num, length = struct.unpack("!cII", data[17:26])
        print(packet_type)
        # except:
        #     packet_type, seq_num = struct.unpack("!cI", data[:5])
        #     print(packet_type)


        #seq_num = socket.ntohl(seq_num)  # Convert seq_num from network byte order to host byte order
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
            # Print details for the data packet
            # TODO suppress data pack info
            # print(f"\nDATA Packet")
            # print(f"recv time:\t{current_time}")
            # print(f"sender addr:\t{sender_addr}")
            # print(f"Sequence num:\t{seq_num}")
            # print(f"length:\t\t{len(payload)}")
            # print(f"payload:\t{payload.decode('utf-8', 'ignore')}")  # Print only first few bytes of the payload
           
            # Update stats for the sender
            sender_stats[key]["total_packets"] += 1
            sender_stats[key]["total_bytes"] += len(payload)



            if seq_num not in writen_seq:
            # build an ack packet of priority 1
                ack_packet = struct.pack("!cI", b'A', seq_num)
                ack = ack_em_header + ack_packet
                sock.sendto(ack, (args.e_hostname, args.e_port))
                print(seq_num)
                data_buffer[seq_num] = payload

            # create data buffer
                # data_buffer.append((seq_num, payload))

            if len(data_buffer) == args.window:
                sorted_buffer = {}
                sorted_buffer = sorted(data_buffer.items(), key=lambda x: x[0])
                # with open('log', 'a') as f:
                #    # f.write("\nSorted Buffer:\n")
                #     f.write(str(sorted_buffer))
                # print('data_buffer', sorted_buffer)
              #  next_window += args.window
                writen_seq = write_to_file(args.file, sorted_buffer, writen_seq) 
                data_buffer = {}
                
            # saves the data to the file in the order of the packets' sequence numbers


            # build new emulator header



           #if data_end != True:
            # Here you would handle the data, e.g., writing it to a file
            # write_to_file(args.file, payload)



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
        parser.add_argument("-f", "--e_hostname", type=str, required=True, help="The host name of the emulator.")
        parser.add_argument("-e", "--e_port", type=int, required=True, help="The port of the emulator.")
        parser.add_argument("-w", "--window", type=int, required=True, help="The requester's window size.")
        args = parser.parse_args()


        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.bind(('localhost', args.port))
            
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





# import argparse
# import socket
# import struct
# from datetime import datetime
# class Tracker:
#     def __init__(self, filename, seq_no, hostname, port):
#         self.filename = filename
#         self.seq_no = seq_no
#         self.hostname = hostname
#         self.port = port


# def write_to_file(file_name, data):
#     """ Append data to the file. """
#     with open(file_name, 'ab') as file:
#         file.write(data)

# def send_ack(sock, seq_num, emulator_addr):
#     """ Send an ACK packet for the given sequence number to the emulator address. """
#     ack_packet = struct.pack("!cI", b'A', socket.htonl(seq_num))  # Pack the ACK packet with the sequence number
#     sock.sendto(ack_packet, emulator_addr)

# def write_to_file(file_name, payload):
#     with open(file_name, 'a') as file:
#         # if payload == "end":
#         #     file.write("\n")
#       #  else:
#         file.write(payload.decode())

# def handle_packets(sock, file_name, emulator_addr):
#     expected_seq_num = 1  # The expected sequence number of the next packet
#     received_packets = {}  # Buffer for storing out-of-sequence packets

#     while True:
#         packet, sender_addr = sock.recvfrom(65535)  # Maximum UDP packet size
#         current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
#         packet_type, seq_num, length = struct.unpack("!cII", packet[:9])
#         seq_num = socket.ntohl(seq_num)  # Convert sequence number to host byte order

#         # Send ACK for every packet, including the end packet
#         send_ack(sock, seq_num, emulator_addr)

#         if packet_type == b'D':
#             if seq_num == expected_seq_num:
#                 # Write data to file and increment the expected sequence number
#                 write_to_file(file_name, packet[9:])
#                 expected_seq_num += 1

#                 # Check if the next expected packet is already in the buffer
#                 while expected_seq_num in received_packets:
#                     write_to_file(file_name, received_packets.pop(expected_seq_num))
#                     expected_seq_num += 1

#             elif seq_num > expected_seq_num:
#                 # Buffer the out-of-sequence packet
#                 received_packets[seq_num] = packet[9:]

#         elif packet_type == b'E':
#             # End of transmission
#             break

#         # Print packet information
#         print(f"Received time: {current_time}, Sender's address: {sender_addr[0]}:{sender_addr[1]}, "
#               f"Packet sequence number: {seq_num}, Payload's length: {length}, "
#               f"First 4 bytes of the payload: {packet[9:13].decode('utf-8', 'ignore')}")

# def send_requests(trackers, s, args):
#     print('inside send requests')
#     # setup new packet (priority always 1 w requester)
#     priority = 0x01
#     packet_type = b'R'
#     seq_num = socket.htonl(0)
#     length = socket.htonl(args.window)
    
#     src_addr, src_port = s.getsockname()
#     packed_ip_src = socket.inet_aton(src_addr)
#     src_port = socket.htons(src_port)

#     # Send a request to each tracker for the requested file
#     for tracker in trackers:
#         print('inside loop')
#         if args.file == tracker.filename:
#             print('inside if statement')
#             # Prepare the request packet
#             request_packet = struct.pack("!cII", packet_type, seq_num, length) + args.file.encode()

#             # Get the destination address and port from the tracker info
#             dest_addr = socket.gethostbyname(tracker.hostname)
#             dest_port = tracker.port

#             # Convert destination address and port to network byte order
#             packed_ip_dest = socket.inet_aton(dest_addr)
#             dest_port = socket.htons(dest_port)

#             # Create the final packet with both old and new headers
#             packet_len = len(request_packet)
#             packed_data = struct.pack('!B4sH4sHI', priority, packed_ip_src, src_port, packed_ip_dest, dest_port, packet_len)
#             final_packet = packed_data + request_packet

#             # Send the final packet to the emulator's address and port
#             emulator_addr = (args.hostname, args.e_port)
#             s.sendto(final_packet, emulator_addr)

#             # Handle incoming packets after sending the request
#             handle_packets(s, args.file, emulator_addr)
#             break  # Assuming we stop after handling the first matching tracker

#     # packet_type = b'R'
#     # seq_num = socket.htonl(0)
#     # length = socket.htonl(args.window)
#     # old_packet = struct.pack("!cII", packet_type, seq_num, length) + args.file.encode()

#     # src_addr, src_port = s.getsockname()

#     # # setup new packet (priority always 1 w requester)
#     # priority = 0x01

#     # # Convert IP addresses to network byte order
#     # packed_ip_src = socket.inet_aton(src_addr)

#     # # 16-bit
#     # src_port = socket.htons(src_port)
    
#     # # get destination from trackers
#     # for tracker in trackers:            # TODO important -> what will happen if there are multiple trakers!!!
#     #     ip_addr = socket.gethostbyname(tracker.hostname)
#     #     packed_ip_dest = socket.inet_aton(ip_addr)
#     #     dest_port = socket.htons(tracker.port)
    
#     # # len of new packet == length of old
#     # packet_len = len(old_packet)

#     # # create new packet
#     # packed_data = struct.pack('!B4sH4sHI', priority, packed_ip_src, src_port, packed_ip_dest, dest_port, packet_len)

#     # # combine w previous
#     # final_packet = packed_data + old_packet

#     # s.sendto(final_packet, (args.hostname, args.e_port))

#     # handle_packets(s, args, (args.hostname, args.e_port))

#     # # for tracker in trackers:
#     # #     if args.file == tracker.filename:
#     # #         sock.sendto(packet, (tracker.hostname, tracker.port))
#     # #         # Handling responses
#     # #         handle_packets(sock, args)


# def main():
#     tracker_arr = []
#     parser = argparse.ArgumentParser(description="UDP File Requester")
#     parser.add_argument("-p", "--port", type=int, required=True, help="Port to bind to")
#     parser.add_argument("-o", "--file", type=str, required=True, help="File to request")
#     parser.add_argument("-f", "--hostname", type=str, required=True, help="The hostname of the emulator")
#     parser.add_argument("-e", "--e_port", type=int, required=True, help="The port of the emulator")
#     parser.add_argument("-w", "--window", type=int, required=True, help="The window size")
#     args = parser.parse_args()

#     emulator_addr = (args.hostname, args.e_port)  # Address of the emulator for sending ACKs

#     with open('tracker.txt', 'r') as file: #you have to request from one sender at a time and then move on to the next
#         content = file.readlines()
#         content = [line.strip() for line in content if line.strip()]  # Avoid empty lines
#         content.sort(key=lambda content: content[1])
#         for i in content:
#             filename, seq_no, hostname, port = i.split()
#             tracker_arr.append(Tracker(filename, int(seq_no), hostname, int(port)))

#     with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
#         s.bind(('', args.port))  # Bind to the requester's port
#         print(f"Requester bound to {socket.gethostname()} on port {args.port}")
#         print('entering send requests')
#         send_requests(tracker_arr, s, args)
#         # Handle incoming packets and send ACKs
#         handle_packets(s, args.file, emulator_addr)

# if __name__ == "__main__":
#     main()
