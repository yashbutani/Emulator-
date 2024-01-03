This projects emulates a reliable file transfer via a TCP connection. 

- Reliable Transfer
To achieve the reliable transfer, the requester will advertise a window size to the sender with the request packet. The sender will send a full "window" of packets and wait for ACKs of each packet before sending more packets. After a certain timeout, the sender will retransmit the packets that it has not received an ack for. This implementation also implements a queue to determine packet sending order 


Run the project using the following syntax: 

python3 emulator.py -p <port> -q <queue_size> -f <filename> -l <log>
  port: the port of the emulator.
  queue_size: the size of each of the three queues.
  filename: the name of the file containing the static forwarding table in the format specified above.
  log: the name of the log file.

python3 sender.py -p <port> -g <requester port> -r <rate> -q <seq_no> -l <length> -f <f_hostname> -e <f_port> -i <priority> -t <timeout>
  f_hostname: the host name of the emulator.
  f_port: the port of the emulator.
  priority: the priority of the sent packets.
  timeout: the timeout for retransmission for lost packets in the unit of milliseconds.

python3 requester.py -p <port> -o <file option> -f <f_hostname> -e <f_port> -w <window>
  f_hostname: the host name of the emulator.
  f_port: the port of the emulator.
  window: the requester's window size.
