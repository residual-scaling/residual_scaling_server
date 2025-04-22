from rsserver import RSServer
from config import single_host_parameter

server = RSServer(single_host_parameter["host"], single_host_parameter["port"])
server.run()
