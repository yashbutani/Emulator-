## I updated the emulator to be a class that is constantly running and listens to requester/sender data

## Emulator receives sender/requester data:
MAKE SURE YOUR ARE IN CORRECRT DIRECTORIES

1. First thing we need to do is to get your local host:
execute: 
```python3 emulator.py -p 3000 -q 100 -f test1/table1 -l log01```
the first print statement will have your localhost. Change Jacks-MacBook-Air.local in **tracker.txt** to your localhost

2. Start sender: -> make sure to change to your localhost found previously
```python3 sender.py -p 5000 -g 4000 -r 100 -q 1 -l 10 -f Jacks-MacBook-Air.local -e 3000 -i 3 -t 1000```

3. Run requester -> make sure to change to your localhost found previously
```python3 requester.py -p 4000 -f Jacks-MacBook-Air.local -e 3000 -o file.txt -w 10```

## You will see
Sender:
- data packets being chunked and sent
- final packet to be sent to the emulator
Emulator:
- first data packet from the requester
- final data which include:  new_packed_data_header(priority, src_ip, etc) + (prev_header + prev_data) -> last project

# TODO
- Use window value to know how many packets to wait for an ack: "The sender will send a full "window" of packets and wait for ACKs of each packet before sending more packets"
  - Based on given window value wait for all packets to be sent in given time frame.
  - the requester sends ack packets.
- Have forwarding table determine when the packets should be sent
  - Packets get forwarded from sender to the requester or inverse through correct emulators according to the forwarding table.
- Add to a queue
- Send the data based on the priority queue

