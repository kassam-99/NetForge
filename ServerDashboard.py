import socket

from ReportGenerator import Report_Generator
from server_logs import Logs
from ServerHandler import UserHandler





class Server_Dashboard(UserHandler):
    
    
    def __init__(self, ServerIP=None, ServerPort=None, maxHostgroup=10, verbose=False):
        super().__init__(ServerIP, ServerPort, maxHostgroup, verbose)
        self.verbose = verbose

        self.Reporter = Report_Generator()
        self.Logger_server_Dashboard = Logs()
        self.Logger_server_Dashboard.LogEngine("FileServer", "Server_Dashboard")
        
        
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
        try:
            # ClientConn: <socket.socket fd=6, family=2, type=1, proto=0, laddr=('192.168.1.121', 8000), raddr=('192.168.1.121', 42952)>
            # ClientInfo: ('192.168.1.121', 42952)
            
            if self.verify_connection(ClientConn, ClientInfo) == True:
                self.Logger_server_Dashboard.LogsMessages(f"[+] Connection Established with {ClientInfo}", message_type="info", verbose=self.verbose)

            



        except Exception as e:
            self.Logger_server_Dashboard.LogsMessages(f"[!] Error in Handling a server - ServerHandler: {e}", message_type="error", verbose=self.verbose)


    def StartServer(self):
        try:
            while True:
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
                        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Allow address reuse
                        server.bind((self.ServerIP, self.ServerPort))
                        server.listen(5)
                        self.Logger_server_Dashboard.LogsMessages(f"[*] Listening on {self.ServerIP}:{self.ServerPort}", message_type="info", verbose=self.verbose)
    
                        while True:
                            client_socket, addr = server.accept()
                            self.Logger_server_Dashboard.LogsMessages(f"[+] Accepted connection from {addr}", message_type="info", verbose=self.verbose)
                            self.ServerHandler(client_socket, addr)
                    break  # Successfully started the server, exit the loop
                except OSError as bind_error:
                    if bind_error.errno == 98:  # Address already in use
                        self.Logger_server_Dashboard.LogsMessages(f"[!] Port {self.ServerPort} in use. Trying next available port.", message_type="warning", verbose=self.verbose)
                        self.ServerPort = self.check_for_port(self.ServerIP, self.ServerPort + 1, 8500)
                    else:
                        raise
        except Exception as e:
            self.Logger_server_Dashboard.LogsMessages(f"[!] Error in Starting a Server - StartServer: {e}", message_type="error", verbose=self.verbose)














if __name__ == "__main__":
    # Server IP and Port Configuration
    server_ip = '127.0.0.1'  # Localhost for testing
    server_port = 8080       # Port for server to listen on
    
    
    # Verbosity option
    verbose = True
    
    # Initialize the Server Dashboard
    server_dashboard = Server_Dashboard(
        #ServerIP=server_ip, 
        #ServerPort=server_port, 
        verbose=verbose
    )
    
    # Display server details (hostname, IP, and port)
    server_dashboard.server_details()

    # Start the server to listen for file transfer requests
    server_dashboard.StartServer()
