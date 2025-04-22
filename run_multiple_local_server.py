from rsserver import RSServer
from config import local_host_ports

for port in local_host_ports["ports"]:
    server = RSServer("127.0.0.1", port)
    server.run()
