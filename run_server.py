from rsserver import RSServer
from config import host_parameter

server = RSServer(host_parameter["host"], host_parameter["port"])
server.start()
