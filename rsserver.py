import socket
from config import db_hyperparameter
from db.db_loader import load_db
import threading
from rsprotocol.protocol import RSMetaMsg, RSMetaType, RSMsgDelimiter
from util import log_flush


class RSServer:
    def __init__(self, host, port):
        # server setting
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.host, self.port))
        self.socket.listen()
        # set up logger
        self.fileIO = open(f'./log/server_{port}.log', 'a')
        # db setting, load db if exist
        self.db = load_db(db_hyperparameter["type"])
        self.write_lock = threading.Lock()
        if self.db.exist_backup():
            log_flush(self.fileIO, f"Loading db {self.port} from backup...")
            self.db.load()


    def handle_client(self, conn, addr):
        try:
            while True:
                data = conn.recv(RSMetaMsg.get_size())
                if not data:
                    break
                # process rsprotocol message
                meta_msg = RSMetaMsg.deserialize(data)
                if meta_msg.meta_type == RSMetaType.CLIENT_PUT:
                    log_flush(self.fileIO, f"[{addr}] Received put request")
                    # handle client put request
                    byte_data = conn.recv(meta_msg.meta_len)
                    info = byte_data.decode("utf-8")
                    with self.write_lock:
                        self.db.put(info)
                elif meta_msg.meta_type == RSMetaType.CLIENT_GET:
                    log_flush(self.fileIO, f"[{addr}] Received get request")
                    # handle client get request
                    byte_data = conn.recv(meta_msg.meta_len)
                    info = byte_data.decode("utf-8")
                    result = self.db.get(info)
                    # send response back to client
                    response = RSMsgDelimiter.RSJOINBLOCK.join(result).encode("utf-8")
                    response_msg = RSMetaMsg(RSMetaType.SERVER_SEND, len(response))
                    conn.sendall(response_msg.serialize())
                    conn.sendall(response)
                else:
                    raise
        except Exception as e:
            log_flush(self.fileIO, f"Error handling client: {e}")
        finally:
            conn.close()

    def close(self):
        log_flush(self.fileIO, f"Server on {self.host}:{self.port} closed")
        # save the db
        self.db.save()
        # close process
        self.fileIO.close()
        self.socket.close()

    def run(self):
        print(f"Server listening on {self.host}:{self.port}")
        log_flush(self.fileIO, "=================================================")
        log_flush(self.fileIO, f"Server listening on {self.host}:{self.port}")
        try:
            while True:
                conn, addr = self.socket.accept()
                log_flush(self.fileIO, f"Connected by {addr}")
                threading.Thread(target=self.handle_client, args=(conn, addr,)).start()
        except KeyboardInterrupt:
            log_flush(self.fileIO, "\nServer shutting down caused by KeyboardInterrupt...")
        except Exception as e:
            log_flush(self.fileIO, f"ERROR: Error handling client: {e}")
        finally:
            self.close()
