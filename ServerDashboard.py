import argparse
import os
import socket
import struct
import threading

from ReportGenerator import Report_Generator
from server_logs import Logs
from ServerFunctions import MAX_NAME_LEN
from ServerHandler import UserHandler



class Server_Dashboard(UserHandler):
    
    
    def __init__(self, ServerIP=None, ServerPort=None, maxHostgroup=10, verbose=False):
        super().__init__(ServerIP, ServerPort, maxHostgroup, verbose)
        self.verbose = verbose

        self.Reporter = Report_Generator()
        self.Logger_server_Dashboard = Logs()
        self.Logger_server_Dashboard.LogEngine("FileServer", "Server_Dashboard")

        # Directory where uploaded files are stored and downloadable files live.
        self.storage_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "FileServer", "storage")
        self._shutdown = threading.Event()



    def server_details(self):
        """Fetches and logs server details such as hostname, IP, and port."""
        try:
            host_name = socket.gethostname()
            if self.ServerIP is None:
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                    sock.connect(('8.8.8.8', 80))  # Dummy IP to get the local IP
                    self.ServerIP = sock.getsockname()[0]

            if self.ServerPort is None:
                self.ServerPort = self.check_for_port('localhost', 8000, 8500)

            server_info = f"""
--------------------------------------------------------------------
[-] Hostname: {host_name} 
[-] IP: {self.ServerIP}       
[-] Port: {self.ServerPort}
[-] Share IP and port with the client
--------------------------------------------------------------------
"""
            self.Logger_server_Dashboard.LogsMessages(server_info, message_type="info", verbose=self.verbose)

        except Exception as e:
            self.Logger_server_Dashboard.LogsMessages(f"[!] Unable to get Hostname and IP: {str(e)}", message_type="critical", verbose=self.verbose)
     

    def ServerHandler(self, ClientConn, ClientInfo):
        """Handles the communication with the client and initiates file transfer."""
        # ClientConn: <socket.socket fd=6, family=2, type=1, proto=0, laddr=('192.168.1.121', 8000), raddr=('192.168.1.121', 42952)>
        # ClientInfo: ('192.168.1.121', 42952)
        session = {}
        try:
            ClientConn.settimeout(30)
            if self.verify_connection(ClientConn, ClientInfo, session) == True:
                self.Logger_server_Dashboard.LogsMessages(f"[+] Connection Established with {ClientInfo}", message_type="info", verbose=self.verbose)
                self.handle_file_transfer(ClientConn, ClientInfo, session)

        except Exception as e:
            self.Logger_server_Dashboard.LogsMessages(f"[!] Error in Handling a server - ServerHandler: {e}", message_type="error", verbose=self.verbose)
        finally:
            # Remove this client's ConnClient record so the list does not grow
            # without bound and the User ID is not permanently seen as a duplicate.
            record = session.get("_conn_record")
            if record is not None:
                with self._conn_lock:
                    try:
                        self.ConnClient.remove(record)
                    except ValueError:
                        pass
            try:
                ClientConn.close()
            except OSError:
                pass


    def handle_file_transfer(self, ClientConn, ClientInfo, session):
        """Drive the file transfer after a successful handshake.

        A 'sender' client uploads a file to the server (server receives and
        stores it); a 'receiver' client requests a file by name and the server
        sends it. In both cases the server reports a 1-byte status code:
            0x09 = File transfer successful, 0x10 = File transfer failed.
        """
        sender_code = self.find_key_by_value(self.user_status_code, "sender")
        receiver_code = self.find_key_by_value(self.user_status_code, "receiver")
        app_code = session.get("app_code")
        SUCCESS, FAILED = 0x09, 0x10
        try:
            if app_code == sender_code:
                dest_path, size = self.recv_file(ClientConn, self.storage_dir)
                ClientConn.sendall(struct.pack("!B", SUCCESS))
                self.Logger_server_Dashboard.LogsMessages(
                    f"[+] Received file from {ClientInfo}: {dest_path} ({size} bytes)",
                    message_type="info", verbose=self.verbose)

            elif app_code == receiver_code:
                name_len = struct.unpack("!Q", self.recv_exact(ClientConn, 8))[0]
                if name_len == 0 or name_len > MAX_NAME_LEN:
                    raise ValueError(f"Rejected requested-name length {name_len} (limit {MAX_NAME_LEN})")
                requested = self.recv_exact(ClientConn, name_len).decode("utf-8")
                path = os.path.join(self.storage_dir, os.path.basename(requested))
                if os.path.isfile(path):
                    ClientConn.sendall(struct.pack("!B", SUCCESS))
                    _, size = self.send_file(ClientConn, path)
                    self.Logger_server_Dashboard.LogsMessages(
                        f"[+] Sent file to {ClientInfo}: {path} ({size} bytes)",
                        message_type="info", verbose=self.verbose)
                else:
                    ClientConn.sendall(struct.pack("!B", FAILED))
                    self.Logger_server_Dashboard.LogsMessages(
                        f"[!] Requested file not found for {ClientInfo}: {requested}",
                        message_type="warning", verbose=self.verbose)
            else:
                self.Logger_server_Dashboard.LogsMessages(
                    f"[*] No file transfer for application '{session.get('application')}' from {ClientInfo}",
                    message_type="info", verbose=self.verbose)

        except Exception as e:
            self.Logger_server_Dashboard.LogsMessages(
                f"[!] Error during file transfer with {ClientInfo}: {e}",
                message_type="error", verbose=self.verbose)
            try:
                ClientConn.sendall(struct.pack("!B", FAILED))
            except OSError:
                pass


    def StartServer(self):
        """Bind, listen, and serve clients concurrently until shutdown."""
        server = None
        try:
            # Resolve a free port up front so binding cannot loop forever.
            while True:
                try:
                    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Allow address reuse
                    server.bind((self.ServerIP, self.ServerPort))
                    break
                except OSError as bind_error:
                    server.close()
                    if bind_error.errno == 98:  # Address already in use
                        self.Logger_server_Dashboard.LogsMessages(f"[!] Port {self.ServerPort} in use. Trying next available port.", message_type="warning", verbose=self.verbose)
                        self.ServerPort = self.check_for_port(self.ServerIP, self.ServerPort + 1, 8500)
                    else:
                        raise

            server.listen(5)
            server.settimeout(1.0)  # Wake periodically to honour the shutdown flag
            self.Logger_server_Dashboard.LogsMessages(f"[*] Listening on {self.ServerIP}:{self.ServerPort}", message_type="info", verbose=self.verbose)

            while not self._shutdown.is_set():
                try:
                    client_socket, addr = server.accept()
                except socket.timeout:
                    continue
                self.Logger_server_Dashboard.LogsMessages(f"[+] Accepted connection from {addr}", message_type="info", verbose=self.verbose)
                # Handle each client in its own thread so one slow client cannot
                # stall the others (and cannot DoS the accept loop).
                worker = threading.Thread(
                    target=self.ServerHandler, args=(client_socket, addr), daemon=True)
                worker.start()

        except KeyboardInterrupt:
            self.Logger_server_Dashboard.LogsMessages("[*] Shutdown requested (KeyboardInterrupt).", message_type="info", verbose=self.verbose)
        except Exception as e:
            self.Logger_server_Dashboard.LogsMessages(f"[!] Error in Starting a Server - StartServer: {e}", message_type="error", verbose=self.verbose)
        finally:
            self._shutdown.set()
            if server is not None:
                server.close()
            self.Logger_server_Dashboard.LogsMessages("[*] Server stopped.", message_type="info", verbose=self.verbose)

    def stop(self):
        """Signal the accept loop to stop."""
        self._shutdown.set()














def _parse_args(argv=None):
    parser = argparse.ArgumentParser(description="NetForge file-transfer server dashboard")
    parser.add_argument("--host", default=None,
                        help="IP to bind (default: auto-detect the local IP)")
    parser.add_argument("--port", type=int, default=None,
                        help="Port to bind (default: first free port in 8000-8500)")
    parser.add_argument("--verbose", action="store_true", help="Print log messages to stdout")
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = _parse_args()

    # Initialize the Server Dashboard
    server_dashboard = Server_Dashboard(
        ServerIP=args.host,
        ServerPort=args.port,
        verbose=args.verbose,
    )

    # Display server details (hostname, IP, and port)
    server_dashboard.server_details()

    # Start the server to listen for file transfer requests
    server_dashboard.StartServer()
