import argparse
import socket
import struct
import os

# Chunk size used for streaming file bytes over the socket.
FILE_CHUNK_SIZE = 65536


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
    

    def _recv_exact(self, num_bytes):
        """Receive exactly num_bytes from the server socket or raise ConnectionError."""
        data = bytearray()
        while len(data) < num_bytes:
            chunk = self.client_socket.recv(min(FILE_CHUNK_SIZE, num_bytes - len(data)))
            if not chunk:
                raise ConnectionError(f"Socket closed after {len(data)}/{num_bytes} bytes")
            data.extend(chunk)
        return bytes(data)


    def send_file(self, filepath):
        """Upload a file to the server (used after a 'sender' handshake).

        Sends the length-prefixed frame (name length, name, size, bytes) then
        reads the 1-byte server status (0x09 success / 0x10 failed).
        """
        filename = os.path.basename(filepath)
        name_bytes = filename.encode("utf-8")
        filesize = os.path.getsize(filepath)
        self.client_socket.sendall(struct.pack("!Q", len(name_bytes)))
        self.client_socket.sendall(name_bytes)
        self.client_socket.sendall(struct.pack("!Q", filesize))
        with open(filepath, "rb") as f:
            while True:
                chunk = f.read(FILE_CHUNK_SIZE)
                if not chunk:
                    break
                self.client_socket.sendall(chunk)
        status = struct.unpack("!B", self._recv_exact(1))[0]
        if status == 0x09:
            self.log_info(f"[+] File '{filename}' uploaded successfully ({filesize} bytes)")
            return True
        self.log_info(f"[!] Server reported file transfer failed (status 0x{status:02X})")
        return False


    def request_file(self, requested_name, dest_dir="."):
        """Download a file from the server by name (used after a 'receiver' handshake)."""
        name_bytes = requested_name.encode("utf-8")
        self.client_socket.sendall(struct.pack("!Q", len(name_bytes)))
        self.client_socket.sendall(name_bytes)
        status = struct.unpack("!B", self._recv_exact(1))[0]
        if status != 0x09:
            self.log_info(f"[!] Server could not provide '{requested_name}' (status 0x{status:02X})")
            return None
        name_len = struct.unpack("!Q", self._recv_exact(8))[0]
        filename = self._recv_exact(name_len).decode("utf-8")
        filesize = struct.unpack("!Q", self._recv_exact(8))[0]
        os.makedirs(dest_dir, exist_ok=True)
        dest_path = os.path.join(dest_dir, os.path.basename(filename))
        with open(dest_path, "wb") as f:
            remaining = filesize
            while remaining > 0:
                chunk = self.client_socket.recv(min(FILE_CHUNK_SIZE, remaining))
                if not chunk:
                    raise ConnectionError("Socket closed during file download")
                f.write(chunk)
                remaining -= len(chunk)
        self.log_info(f"[+] File '{filename}' downloaded to {dest_path} ({filesize} bytes)")
        return dest_path


    def ConnToServer(self, user_id, user_applications, filepath=None, dest_dir="."):
        try:
            # Step 1: Establish a connection to the server
            self.client_socket.connect((self.server_ip, self.server_port))
            self.log_info(f"[*] Connecting to the server at {self.server_ip}:{self.server_port}")
    
    
            # Step 2: Transmit the initial 3-byte user request
            # Command: Connect (0xAA), User Type: Client (0x2A), Status: Request (0x3C)
            init_request = struct.pack("BBB", 0xAA, 0x2A, 0x3C)
            self.client_socket.sendall(init_request)


            # Step 3: Transmit the user ID
            # Append a null terminator (b'\x00') to signify the end of the user ID
            self.client_socket.sendall(user_id.encode('utf-8') + b'\x00')


            # Step 4: Receive the server's response for the user request
            # recv_exact() loops until all 3 bytes arrive (partial-read safe).
            server_response = self._recv_exact(3)
    
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
            self.client_socket.sendall(init_request)


            # Step 7: Receive the server's response for the user application
            server_response = self._recv_exact(3)
    
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


            # Step 9: Drive the file transfer according to the negotiated
            # application and propagate its outcome to the caller so a failed
            # upload/download is not reported as success.
            transfer_ok = True
            if user_applications == 0x3B:   # sender -> upload a file to the server
                if filepath:
                    transfer_ok = self.send_file(filepath)
                else:
                    self.log_info("[!] Sender application selected but no filepath provided")
                    transfer_ok = False
            elif user_applications == 0x2B:  # receiver -> download a file from the server
                if filepath:
                    transfer_ok = self.request_file(filepath, dest_dir) is not None
                else:
                    self.log_info("[!] Receiver application selected but no filename requested")
                    transfer_ok = False

            return bool(transfer_ok)

        except Exception as e:
            self.log_info(f"[!] Error: {e}")
            self.client_socket.close()
            return False
            
      












def _parse_args(argv=None):
    parser = argparse.ArgumentParser(description="NetForge reference client")
    parser.add_argument("--host", default="127.0.0.1", help="Server IP (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Server port (default: 8000)")
    parser.add_argument("--user-id", default="my_user", help="User ID sent during the handshake")
    parser.add_argument("--app", choices=["sender", "receiver"], default="receiver",
                        help="Application role: 'sender' uploads a file, 'receiver' downloads one")
    parser.add_argument("--file", default=None,
                        help="For --app sender: path to upload. For --app receiver: filename to fetch")
    parser.add_argument("--dest-dir", default=".", help="Directory to save downloaded files (receiver)")
    parser.add_argument("--quiet", action="store_true", help="Suppress log output")
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = _parse_args()
    app_code = 0x3B if args.app == "sender" else 0x2B

    client = General_User(args.host, args.port, user_id=args.user_id, verbose=not args.quiet)
    client.ConnToServer(args.user_id, app_code, filepath=args.file, dest_dir=args.dest_dir)
