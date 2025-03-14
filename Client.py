import socket
import struct
import os


class General_User:
    def __init__(self, server_ip, server_port, destination_ip=None, destination_port=None, user_id="user", verbose=True):
        self.server_ip = server_ip
        self.server_port = server_port
        self.destination_ip = destination_ip
        self.destination_port = destination_port
        self.user_id = user_id
        self.verbose = verbose
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        self.client_control_codes = {

            # Connection Commands
            0xAA: "connect",
            0xFF: "disconnect",
            
            # User Types
            0x0A: "server",
            0x2A: "client",
            
            # User Applications
            0x2B: "receiver", 
            0x3B: "sender", 
            
            # User Statuses
            0x0C: "authorized access",  
            0x1C: "unauthorized access",
            0x2C: "blocked User",
            0x3C: "request",
            0x4C: "approved",
            0x5C: "rejected",
            0x6C: "accepted", 
            
            # Connection Statuses
            0x0D: "Connection established",
            0x1D: "Connection lost",
            0x2D: "Network unreachable",
            0x3D: "Connection refused by server",
            0x4D: "Protocol error",
            0x5D: "Server disconnected",
            0x7D: "Client disconnected",
            0x8D: "Connection timeout",
            0x9D: "Network error",
            
            # Network Statuses
            0x0E: "Server not responding",
            0x2E: "Client not responding",
            0x3E: "Connection reset",
            0x4E: "Connection closed",
            0x5E: "Connection failed",
            0x6E: "Connection refused",

            # Server File Operations         
            0x05: "File saved",
            0x06: "File not saved",
            0x07: "File updated",
            0x08: "File not updated",
            0x09: "File transfer successful",
            0x10: "File transfer failed",
  
            # File Errors
            0x20: "Invalid file type",
            0x21: "Insufficient storage space",
            0x22: "File already exists",

        }
        
        

    def log_info(self, message):
        if self.verbose:
            print(message)
          

    def find_key_by_value(self, dict, value):
        for key, val in dict.items():
            if val == value:
                return key
        return None
    
    
    def find_value_by_key(self, dict, key):
        for k, value in dict.items():
            if k == key:
                return value
        return None
    

    def ConnToServer(self, user_id, user_applications):
        try:
            # Step 1: Establish a connection to the server
            self.client_socket.connect((self.server_ip, self.server_port))
            self.log_info(f"[*] Connecting to the server at {self.server_ip}:{self.server_port}")
    
    
            # Step 2: Transmit the initial 3-byte user request
            # Command: Connect (0xAA), User Type: Client (0x2A), Status: Request (0x3C)
            init_request = struct.pack("BBB", 0xAA, 0x2A, 0x3C)
            self.client_socket.send(init_request)
                
            
            # Step 3: Transmit the user ID
            # Append a null terminator (b'\x00') to signify the end of the user ID
            self.client_socket.send(user_id.encode('utf-8') + b'\x00')
        
        
            # Step 4: Receive the server's response for the user request
            server_response = self.client_socket.recv(3)
            if len(server_response) < 3:
                self.log_info(f"[!] Invalid response length. Received {len(server_response)} bytes.")
                self.client_socket.close()
                return
    
            user_status, server_type, client_type = struct.unpack("BBB", server_response)
    
    
            # Step 5: Validate the server's response for the user request (Step 4)
            if user_status == 0x6C and server_type == 0x0A and client_type == 0x2A:  # Accepted
                self.log_info("[+] Connection accepted")
            else:
                # Handle invalid or unexpected server responses
                self.log_info(f"[!] Unexpected response: User Status: {user_status}, Server Type: {server_type}, Client Type: {client_type}")
                self.client_socket.close()
                return
                
            
            # Step 6: Transmit the initial 3-byte user application
            # Command: Status: Request (0x3C), User Type: Client (0x2A), User application either 0x2B or 0x3B
            init_request = struct.pack("BBB", 0x3C, 0x2A, user_applications)
            self.client_socket.send(init_request)
                      
            
            # Step 7: Receive the server's response for the user application
            server_response = self.client_socket.recv(3)
            if len(server_response) < 3:
                self.log_info(f"[!] Invalid response length. Received {len(server_response)} bytes.")
                self.client_socket.close()
                return
    
            user_status, server_type, _user_applications = struct.unpack("BBB", server_response)
            
            
            # Step 8: Validate the server's response for the user application (Step 7)
            if user_status == 0x6C and server_type == 0x0A and _user_applications == user_applications:  # Accepted
                self.log_info("[+] Applications accepted")
            else:
                # Handle invalid or unexpected server responses
                self.log_info(f"[!] Unexpected response: User Status: {user_status}, Server Type: {server_type}, Application Type: {_user_applications}")
                self.client_socket.close()
                return
    
            self.log_info("[*] Connection process completed successfully")           
            
            
        except Exception as e:
            self.log_info(f"[!] Error: {e}")
            self.client_socket.close()
            
      












if __name__ == "__main__":
    # Parameters for the client
    server_ip = '192.168.0.101'  # Server IP
    server_port = 8000       # Server Port
    destination_ip = '127.0.0.1'  # Destination IP (could be client B)
    destination_port = 1000      # Destination Port
    user_id = "my_user"  # SOCKS4 User ID

    client = General_User(server_ip, server_port, destination_ip, destination_port, user_id=user_id)
    client.ConnToServer("testing", 0x2B)  # Establish the connection before sending the file
