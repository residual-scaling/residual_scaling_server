import socket
from config import db_hyperparameter
from db.db_loader import load_db
import threading
from rsprotocol.protocol import RSMetaMsg, RSMetaType, RSMsgDelimiter


class RSServer:
    def __init__(self, host, port):
        # server setting
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.host, self.port))
        self.socket.listen()
        # db setting
        self.db = load_db(db_hyperparameter["type"])
        self.lock = threading.Lock()

    def handle_client(self, conn):
        try:
            while True:
                data = conn.recv(RSMetaMsg.get_size())
                if not data:
                    break
                # process rsprotocol message
                meta_msg = RSMetaMsg.deserialize(data)
                if meta_msg.meta_type == RSMetaType.CLIENT_PUT:
                    # handle client put request
                    byte_data = conn.recv(meta_msg.meta_len)
                    info = byte_data.decode("utf-8")
                    with self.lock:
                        self.db.put(info)
                elif meta_msg.meta_type == RSMetaType.CLIENT_GET:
                    # handle client get request
                    byte_data = conn.recv(meta_msg.meta_len)
                    info = byte_data.decode("utf-8")
                    with self.lock:
                        result = self.db.get(info)
                    # send response back to client
                    response = RSMsgDelimiter.RSJOINBLOCK.join(result).encode("utf-8")
                    response_msg = RSMetaMsg(RSMetaType.SERVER_SEND, len(response))
                    conn.sendall(response_msg.serialize())
                    conn.sendall(response)
                else:
                    raise
        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            conn.close()

    def start(self):
        print(f"Server listening on {self.host}:{self.port}")
        try:
            while True:
                conn, addr = self.socket.accept()
                print(f"Connected by {addr}")
                threading.Thread(target=self.handle_client, args=(conn,)).start()
        except KeyboardInterrupt:
            print("\nServer shutting down caused by KeyboardInterrupt...")
        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            self.socket.close()

