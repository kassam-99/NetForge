from ReportGenerator import Report_Generator
from server_logs import Logs
from ServerFunctions import Server_Functions

import datetime
import struct



class UserHandler(Server_Functions):
    def __init__(self, ServerIP=None, ServerPort=None, maxHostgroup=10, verbose=False):
        super().__init__(ServerIP, ServerPort, maxHostgroup, verbose)
        self.Reporter = Report_Generator()
        self.Logger_server_UserHandler = Logs()
        self.Logger_server_UserHandler.LogEngine("FileServer", "UserHandler")


    def validate_initial_request(self, command, user_type_init_request, first_user_status, user_data):
        """Validate the initial 3-byte user request."""
        if command not in self.user_status_code or \
           user_type_init_request not in self.user_status_code or \
           first_user_status not in self.user_status_code:
            self.Logger_server_UserHandler.LogsMessages(f"[!] Invalid verification, from {user_data[0]}:{user_data[1]}", message_type="warning", verbose=self.verbose)
            return False

        if self.user_status_code[command] != "connect":
            self.Logger_server_UserHandler.LogsMessages(f"[!] Invalid Connection Command, from {user_data[0]}:{user_data[1]}", message_type="warning", verbose=self.verbose)
            return False

        if self.user_status_code[first_user_status] != "request":
            self.Logger_server_UserHandler.LogsMessages(f"[!] Invalid User status, from {user_data[0]}:{user_data[1]}", message_type="warning", verbose=self.verbose)
            return False

        return True
            
            
    def validate_user_type(self, user_type_init_request, user_data):
        """Validate the user type."""
        if self.user_status_code[user_type_init_request] == "admin":
            self.Logger_server_UserHandler.LogsMessages(f"[+] {self.user_status_code[user_type_init_request]} has full authorized access - {user_data[0]}:{user_data[1]}", message_type="info", verbose=self.verbose)
        elif self.user_status_code[user_type_init_request] == "client":
            self.Logger_server_UserHandler.LogsMessages(f"[+] {self.user_status_code[user_type_init_request]} connected with unauthorized access - {user_data[0]}:{user_data[1]}", message_type="info", verbose=self.verbose)
        else:
            self.Logger_server_UserHandler.LogsMessages(f"[!] Invalid User type, from {user_data[0]}:{user_data[1]}", message_type="warning", verbose=self.verbose)
            return False
        return True


    def validate_user_application(self, second_user_status, first_user_status, _user_type_application, user_applications, user_data):
        """Validate the second 3-byte user application."""
        if second_user_status != first_user_status:
            self.Logger_server_UserHandler.LogsMessages(f"[!] The user STATUS has been manipulated: expected user status - {self.user_status_code[first_user_status]}:{first_user_status} and new user status - {self.user_status_code[second_user_status]}:{second_user_status}, from {user_data[0]}:{user_data[1]}", message_type="warning", verbose=self.verbose)
            return False

        if self.user_status_code[user_applications] in ["function", "browser"]:
            if self.user_status_code[_user_type_application] == "admin":
                self.Logger_server_UserHandler.LogsMessages(f"[+] Admin authorized to use {self.user_status_code[user_applications]} application - {user_data[0]}:{user_data[1]}", message_type="info", verbose=self.verbose)
            else:
                self.Logger_server_UserHandler.LogsMessages(f"[!] Unauthorized application access attempt by non-admin for {self.user_status_code[user_applications]} - {user_data[0]}:{user_data[1]}", message_type="warning", verbose=self.verbose)
                return False

        elif self.user_status_code[user_applications] in ["receiver", "sender"]:
            if self.user_status_code[_user_type_application] in ["admin", "client"]:
                self.Logger_server_UserHandler.LogsMessages(f"[+] {self.user_status_code[_user_type_application].capitalize()} authorized to use {self.user_status_code[user_applications]} application - {user_data[0]}:{user_data[1]}", message_type="info", verbose=self.verbose)
            else:
                self.Logger_server_UserHandler.LogsMessages(f"[!] Unauthorized application access attempt by {self.user_status_code[_user_type_application]} for {self.user_status_code[user_applications]} - {user_data[0]}:{user_data[1]}", message_type="warning", verbose=self.verbose)
                return False
        else:
            self.Logger_server_UserHandler.LogsMessages(f"[!] Unknown application requested: {user_applications}, from {user_data[0]}:{user_data[1]}", message_type="warning", verbose=self.verbose)
            return False

        return True
        
                
    def verify_connection(self, user_conn, user_data): # Edit it 
        try:

            # Step 1: Receive the initial 3-byte user request
            first_request = user_conn.recv(3)
            if len(first_request) < 3:
                self.Logger_server_UserHandler.LogsMessages(
                    f"[!] Invalid request length. Received {len(first_request)} bytes.",
                    message_type="warning", verbose=self.verbose
                )
                self.Logger_server_UserHandler.LogsMessages(
                    f"[!] Connection request received from: {user_data[0]}:{user_data[1]} - Request: {first_request}",
                    message_type="warning", verbose=self.verbose
                )
                self.disconnect_user(user_conn, user_data)
                return False
    
            self.Logger_server_UserHandler.LogsMessages(
                f"[+] Valid request length. Received {len(first_request)} bytes.",
                message_type="info", verbose=self.verbose
            )
    
            command, user_type_init_request, first_user_status = struct.unpack("BBB", first_request)


            # Step 2: Retrieve the user ID
            user_id = b""
            while True:
                byte = user_conn.recv(1)
                if byte == b'\x00':  # Null terminator
                    break
                user_id += byte
            user_id = user_id.decode('utf-8')
    
            self.Logger_server_UserHandler.LogsMessages(
                f"[-] Reviewing connection request from {self.user_status_code[user_type_init_request]}: {user_data[0]}:{user_data[1]}",
                message_type="info", verbose=self.verbose
            )
            

            # Step 3: Validate the initial 3-byte user request
            if not self.validate_initial_request(command, user_type_init_request, first_user_status, user_data):
                self.disconnect_user(user_conn, user_data)
                return False

            if not self.validate_user_type(user_type_init_request, user_data):
                self.disconnect_user(user_conn, user_data)
                return False


            # Step 4: Confirm the user request
            init_confirmation = struct.pack(
                "BBB",
                self.find_key_by_value(self.user_status_code, "accepted"),
                self.find_key_by_value(self.user_status_code, "server"),
                user_type_init_request
            )
            if not self.send_request(user_conn, user_data, init_confirmation):
                self.disconnect_user(user_conn, user_data)
                return False
    
            self.Logger_server_UserHandler.LogsMessages(
                f"[+] Connection request validated: {self.user_status_code[user_type_init_request]} - {user_data[0]}:{user_data[1]}",
                message_type="info", verbose=self.verbose
            )


            # Step 5: Receive the second 3-byte user application
            second_request = user_conn.recv(3)
            if len(second_request) < 3:
                self.Logger_server_UserHandler.LogsMessages(
                    f"[!] Invalid second request length. Received {len(second_request)} bytes.",
                    message_type="warning", verbose=self.verbose
                )
                self.disconnect_user(user_conn, user_data)
                return False
    
            second_user_status, _user_type_application, user_applications = struct.unpack("BBB", second_request)


            # Step 6: Validate the second request
            if not self.validate_user_application(
                second_user_status, first_user_status, _user_type_application, user_applications, user_data
            ):
                self.disconnect_user(user_conn, user_data)
                return False


            # Step 7: Confirm the user application
            app_confirmation = struct.pack(
                "BBB",
                self.find_key_by_value(self.user_status_code, "accepted"),
                self.find_key_by_value(self.user_status_code, "server"),
                _user_type_application
            )
            if not self.send_request(user_conn, user_data, app_confirmation):
                self.disconnect_user(user_conn, user_data)
                return False
    
            self.Logger_server_UserHandler.LogsMessages(
                f"[+] Connection application validated: {self.user_status_code[_user_type_application]} - {user_data[0]}:{user_data[1]}",
                message_type="info", verbose=self.verbose
            )
    
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')


            # Step 8: Process connection details and store them
            is_duplicate = None
            for client in self.ConnClient:
                if client.get("User ID") == user_id:
                    is_duplicate = client
                    break
            
            if is_duplicate:
                self.Logger_server_UserHandler.LogsMessages(
                    f"[!] Duplicate user detected:"
                    f"\n[!] Existing data:"
                    f"\n    - User No.: {is_duplicate.get('User No.')}"
                    f"\n    - User ID: {is_duplicate.get('User ID')}"
                    f"\n    - User Type: {is_duplicate.get('User Type')}"
                    f"\n    - User Application: {is_duplicate.get('User Application')}"
                    f"\n    - User IP: {is_duplicate.get('User IP')}"
                    f"\n    - User Port: {is_duplicate.get('User Port')}"
                    f"\n    - Connected Time: {is_duplicate.get('Connected Time')}"
                    f"\n[!] New data (attempted connection):"
                    f"\n    - User ID: {user_id}"
                    f"\n    - User Type: {self.user_status_code[user_type_init_request]}"
                    f"\n    - User Application: {self.user_status_code[user_applications]}"
                    f"\n    - User IP: {user_data[0]}"
                    f"\n    - User Port: {user_data[1]}",
                    message_type="warning", verbose=self.verbose
                )
                
            else:
                self.order += 1
                self.ConnClientInfo = {
                    # User Information
                    "User No.": self.order,
                    "User Status": self.user_status_code[user_type_init_request], # e.g., "authorized access", "unauthorized access", "blocked User"
                    "User ID": user_id,
                    "Username": "user",
                    "User IP": user_data[0],
                    "User Port": user_data[1],
                    
                    # Connection Details
                    "Connected Time": timestamp,
                    "Connection Command": self.user_status_code[command],         # Values from user_status_code (e.g., "connect", "disconnect")
                    "User Type": self.user_status_code[user_type_init_request],   # e.g., "server", "admin", "client"
                    "User Application": self.user_status_code[user_applications], # e.g., "all", "browser", "receiver", "sender"
                     
                    # Connection and Network Status
                    "Connection Status": self.user_status_code[0x0D],             # Values from user_status_code connection statuses (e.g., "Connection established")
                }
                self.ConnClient.append(self.ConnClientInfo)
                self.Logger_server_UserHandler.LogsMessages(self.ConnClientInfo, message_type="info", verbose=self.verbose)
    
            return True
    
        except Exception as e:
            self.Logger_server_UserHandler.LogsMessages(
                f"[!] Error verifying connection: {e}",
                message_type="error", verbose=self.verbose
            )
            self.disconnect_user(user_conn, user_data)
            return False
       







       