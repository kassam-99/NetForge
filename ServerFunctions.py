from ReportGenerator import Report_Generator
from server_logs import Logs
from ServerSettings import Server

import socket
import struct



class Server_Functions(Server):
    
    
    def __init__(self, ServerIP=None, ServerPort=None, maxHostgroup=10, verbose=False):
        super().__init__(ServerIP, ServerPort, maxHostgroup, verbose)
        self.Reporter = Report_Generator()
        self.Logger_server_Functions = Logs()
        self.Logger_server_Functions.LogEngine("FileServer", "Server_Functions")

            
    def check_for_port(self, host='localhost', p1=8000, p2=65535):
        self.Logger_server_Functions.LogsMessages(f"[*] Scanning ports on host {host} from {p1} to {p2}.", message_type="info", verbose=self.verbose)
        for port in range(p1, p2 + 1):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.settimeout(1)
                    if sock.connect_ex((host, port)) != 0:  # Port is available
                        self.Logger_server_Functions.LogsMessages(f"[+] Found available port: {port}", message_type="info", verbose=self.verbose)
                        return port
                    
            except Exception as e:
                self.Logger_server_Functions.LogsMessages(f"[!] Error while checking port {port} on {host}: {e}", message_type="error", verbose=self.verbose)
    
        raise Exception(f"[!] Couldn't find open port on {host} in range {p1}-{p2}.")
    

    def find_key_by_value(self, dict, value):
        for key, val in dict.items():
            if val == value:
                return key
        return None


    def send_request(self, user_conn, user_data, message, username=None, user_id=None, user_type=None, message_type=None):
        
        try:
            
            user_conn.send(message)
            log_message = (
                f"[*] The message was sent successfully:"
                f"\n    - User IP: {user_data[0]}"
                f"\n    - User Port: {user_data[1]}"
                f"\n    - Message: {message}"
            )
                
            if username:
                log_message += f"\n    - Username: {username}"
            if user_id:
                log_message += f"\n    - User ID: {user_id}"
            if user_type:
                log_message += f"\n    - User Type: {user_type}"
            if message_type:
                log_message += f"\n    - Message Type: {message_type}"
                
            self.Logger_server_Functions.LogsMessages(log_message, message_type="info", verbose=self.verbose)
            return True
        
        except Exception as e:
    
            error_message = (
                f"[!] The message failed to send:"
                f"\n    - User IP: {user_data[0]}"
                f"\n    - User Port: {user_data[1]}"
                f"\n    - Message: {message}"
            )
                
            if username:
                error_message += f"\n    - Username: {username}"
            if user_id:
                error_message += f"\n    - User ID: {user_id}"
            if user_type:
                error_message += f"\n    - User Type: {user_type}"
            if message_type:
                error_message += f"\n    - Message Type: {message_type}"
                
            error_message += f"\n    - Error: {e}"
            
            self.Logger_server_Functions.LogsMessages(error_message, message_type="error", verbose=self.verbose)
            return False

    
    def disconnect_user(self, user_conn, user_data, username=None, user_id=None, user_type=None):
        """Disconnect a user safely, log the event, and update connection lists."""
        
        try:
            
            # Log the disconnection attempt
            log_message = (
                f"[*] Attempting to disconnect user:"
                f"\n    - User IP: {user_data[0]}"
                f"\n    - User Port: {user_data[1]}"
            )
            if username:
                log_message += f"\n    - Username: {username}"
            if user_id:
                log_message += f"\n    - User ID: {user_id}"
            if user_type:
                log_message += f"\n    - User Type: {user_type}"
                
            self.Logger_server_Functions.LogsMessages(log_message, message_type="info", verbose=self.verbose)
    
            # Send a disconnect command to the user
            disconnect_message = struct.pack(
                "BBB",
                self.find_key_by_value(self.user_status_code, "disconnect"),
                self.find_key_by_value(self.user_status_code, "server"),
                0xFF  # Padding byte
            )
            
            if self.send_request(user_conn, user_data, disconnect_message, username, user_id, user_type, "Disconnect"):
                log_message = (
                    f"[*] Disconnect message sent to user:"
                    f"\n    - User IP: {user_data[0]}"
                    f"\n    - User Port: {user_data[1]}"
                )
                if username:
                    log_message += f"\n    - Username: {username}"
                if user_id:
                    log_message += f"\n    - User ID: {user_id}"
                if user_type:
                    log_message += f"\n    - User Type: {user_type}"
                self.Logger_server_Functions.LogsMessages(log_message, message_type="info", verbose=self.verbose)    
            
            else:
                log_message = (
                    f"[*] [!] Failed to send disconnect message to user:"
                    f"\n    - User IP: {user_data[0]}"
                    f"\n    - User Port: {user_data[1]}"
                )
                if username:
                    log_message += f"\n    - Username: {username}"
                if user_id:
                    log_message += f"\n    - User ID: {user_id}"
                if user_type:
                    log_message += f"\n    - User Type: {user_type}"
                self.Logger_server_Functions.LogsMessages(log_message, message_type="warning", verbose=self.verbose)   
    
            # Close the connection
            user_conn.close()
            log_message = (
                f"[*] User disconnected successfully:"
                f"\n    - User IP: {user_data[0]}"
                f"\n    - User Port: {user_data[1]}"
            )
            if username:
                log_message += f"\n    - Username: {username}"
            if user_id:
                log_message += f"\n    - User ID: {user_id}"
            if user_type:
                log_message += f"\n    - User Type: {user_type}"
            self.Logger_server_Functions.LogsMessages(log_message, message_type="info", verbose=self.verbose)    
    
            # Remove from connection lists
            if (username and user_id and user_type) is not None:
                
                if (user_type == "admin") and (user_id or username):
                    for admin in self.ConnAdmin:
                        if admin.get("User ID") == user_id and admin.get("Username") == username:
                            self.ConnAdmin.remove(admin)
                            
                            self.Logger_server_Functions.LogsMessages(
                                f"[+] User ID {user_id} removed from ConnAdmin.",
                                message_type="info", verbose=self.verbose
                            )
                            break  
                        
                elif (user_type == "client") and (user_id or username):
                    for client in self.ConnClient:
                        if client.get("User ID") == user_id and client.get("Username") == username:
                            self.ConnClient.remove(client)
                            
                            self.Logger_server_Functions.LogsMessages(
                                f"[+] User ID {user_id} removed from ConnClient.",
                                message_type="info", verbose=self.verbose
                            )
                            break  
                        
                    
            if user_type is not None:
                pass
            
            
             
            
        except Exception as e:
            error_message = (
                f"[!] Error disconnecting user:"
                f"\n    - User IP: {user_data[0]}"
                f"\n    - User Port: {user_data[1]}"
            )
            if username:
                error_message += f"\n    - Username: {username}"
            if user_id:
                error_message += f"\n    - User ID: {user_id}"
            if user_type:
                error_message += f"\n    - User Type: {user_type}"
            error_message += f"\n    - Error: {e}"
            
            self.Logger_server_Functions.LogsMessages(error_message, message_type="error", verbose=self.verbose)
            
                                
                    
