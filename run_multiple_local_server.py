from rsserver import RSServer
from config import local_host_ports
import threading

for port in local_host_ports["ports"]:
    server = RSServer("127.0.0.1", port)
    server.run()

# Lists to keep track of servers and threads
servers = []
threads = []

def start_servers():
    """Start servers on ports 4001-4003 in non-blocking threads"""
    for port in range(4001, 4004):
        # Create server instance
        server = HTTPServer(('localhost', port), SimpleHTTPRequestHandler)
        servers.append(server)
        
        # Create and start thread
        thread = threading.Thread(target=server.serve_forever)
        threads.append(thread)
        thread.start()
        
        print(f"Server started on port {port}")

def stop_servers():
    """Gracefully shutdown all servers and clean up threads"""
    for server in servers:
        server.shutdown()  # Stop the serve_forever loop
    for thread in threads:
        thread.join()      # Wait for threads to exit
    
    print("\nAll servers stopped")

if __name__ == "__main__":
    start_servers()
    
    try:
        # Keep main thread alive until user input
        input("Press Enter to stop servers...\n")
    except KeyboardInterrupt:
        print("\nShutdown signal received")
    finally:
        stop_servers()
