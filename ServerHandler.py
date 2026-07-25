from ReportGenerator import Report_Generator
from server_logs import Logs
from ServerFunctions import Server_Functions

import datetime
import socket
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
        
                
    def verify_connection(self, user_conn, user_data, session=None): # Edit it
        try:
            # Bound blocking recv() calls so a slow/malicious client cannot stall
            # the server forever (the single-threaded accept loop is vulnerable).
            if user_conn.gettimeout() is None:
                user_conn.settimeout(30)

            # Step 1: Receive the initial 3-byte user request
            # recv_exact() loops until all 3 bytes arrive so a partial TCP read
            # on a real network is not mistaken for an invalid request.
            try:
                first_request = self.recv_exact(user_conn, 3)
            except (ConnectionError, socket.timeout, OSError) as e:
                self.Logger_server_UserHandler.LogsMessages(
                    f"[!] Failed to read initial request from {user_data[0]}:{user_data[1]}: {e}",
                    message_type="warning", verbose=self.verbose
                )
                self.disconnect_user(user_conn, user_data)
                return False
    
            self.Logger_server_UserHandler.LogsMessages(
                f"[+] Valid request length. Received {len(first_request)} bytes.",
                message_type="info", verbose=self.verbose
            )
    
            command, user_type_init_request, first_user_status = struct.unpack("BBB", first_request)


            # Step 2: Retrieve the user ID (null-terminated, length-capped)
            user_id = b""
            while True:
                byte = user_conn.recv(1)
                if not byte:  # Socket closed by peer before null terminator
                    self.Logger_server_UserHandler.LogsMessages(
                        f"[!] Connection closed while reading User ID, from {user_data[0]}:{user_data[1]}",
                        message_type="warning", verbose=self.verbose
                    )
                    self.disconnect_user(user_conn, user_data)
                    return False
                if byte == b'\x00':  # Null terminator
                    break
                user_id += byte
                if len(user_id) > 256:  # Reject unbounded/oversized IDs
                    self.Logger_server_UserHandler.LogsMessages(
                        f"[!] User ID exceeded 256 bytes, from {user_data[0]}:{user_data[1]}",
                        message_type="warning", verbose=self.verbose
                    )
                    self.disconnect_user(user_conn, user_data)
                    return False
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
            try:
                second_request = self.recv_exact(user_conn, 3)
            except (ConnectionError, socket.timeout, OSError) as e:
                self.Logger_server_UserHandler.LogsMessages(
                    f"[!] Failed to read second request from {user_data[0]}:{user_data[1]}: {e}",
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
            # Echo back the *application* code the client requested (not the
            # user-type byte); the client validates that this matches its request.
            app_confirmation = struct.pack(
                "BBB",
                self.find_key_by_value(self.user_status_code, "accepted"),
                self.find_key_by_value(self.user_status_code, "server"),
                user_applications
            )
            if not self.send_request(user_conn, user_data, app_confirmation):
                self.disconnect_user(user_conn, user_data)
                return False
    
            self.Logger_server_UserHandler.LogsMessages(
                f"[+] Connection application validated: {self.user_status_code[_user_type_application]} - {user_data[0]}:{user_data[1]}",
                message_type="info", verbose=self.verbose
            )
    
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')


            # Step 8: Process connection details and store them.
            # Build the record in a LOCAL variable (never on self, which is shared
            # across handler threads) and do the duplicate check + append together
            # under the lock so two threads cannot both pass the check and append.
            conn_info = {
                # User Information
                "User No.": None,  # assigned under the lock below
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

            is_duplicate = None
            with self._conn_lock:
                for client in self.ConnClient:
                    if client.get("User ID") == user_id:
                        is_duplicate = client
                        break
                if is_duplicate is None:
                    self.order += 1
                    conn_info["User No."] = self.order
                    self.ConnClient.append(conn_info)

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
                # Reject the duplicate connection instead of silently accepting it.
                self.disconnect_user(user_conn, user_data)
                return False

            self.Logger_server_UserHandler.LogsMessages(conn_info, message_type="info", verbose=self.verbose)

            # Expose the negotiated session details to the caller (thread-safe:
            # the caller passes its own dict) so it can drive the file transfer.
            if session is not None:
                session["user_id"] = user_id
                session["command"] = command
                session["user_type"] = user_type_init_request
                session["app_code"] = user_applications
                session["application"] = self.user_status_code[user_applications]
                # Hand the caller our ConnClient record so it can remove it on
                # teardown (prevents the unbounded-growth / permanent-duplicate bug).
                session["_conn_record"] = conn_info

            return True
    
        except Exception as e:
            self.Logger_server_UserHandler.LogsMessages(
                f"[!] Error verifying connection: {e}",
                message_type="error", verbose=self.verbose
            )
            self.disconnect_user(user_conn, user_data)
            return False
       







       