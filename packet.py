class Packet: 
     def __init__(self, priority, src_ip, source_port, dest_ip, dest_port, length, filename, seq_no, hostname, port):
        self.filename = filename
        self.seq_no = seq_no
        self.hostname = hostname
        self.port = port
        self.priority = priority
        self.src_ip = src_ip
        self.source_port = source_port
        self.dest_ip = dest_ip
        self.dest_port = dest_port
        self.length = length
        self.filename = filename 