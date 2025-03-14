# NetForge
NetForge is an open-source Python framework designed for building networked applications with robust server-client communication, logging, and reporting capabilities. Whether you're creating a file transfer tool, a chat app, or an IoT management system, NetForge provides a modular foundation to forge your own solutions.

Let’s dive in and explore what makes this framework special!


# Features

Here’s what NetForge brings to the table:

- Socket-Based Networking: Reliable TCP communication between servers and clients using a custom protocol.
- User Management: Supports admin and client roles with connection validation and status tracking.
- Extensive Logging: Five log levels (DEBUG, INFO, <span style="color:orange">WARNING</span>, <span style="color:red">ERROR</span>, <span style="color:purple">CRITICAL</span>) with file-based storage.
- Reporting: Generate reports in CSV, TXT, and JSON formats for connection details and server activity.
- Modular Design: Easily extendable classes for custom applications.
- Cross-Platform: Runs on Windows, Linux, and macOS with Python 3.8+.

    “NetForge is like a blacksmith’s forge for networking—shape it to fit your needs!” — A happy developer

# Use Cases

NetForge can be adapted for:
* File Transfer Applications: Securely share files between clients via a server.
* Chat Systems: Enable real-time messaging with broadcast capabilities.
* Remote Administration: Manage servers and users with admin privileges.
* IoT Device Control: Coordinate and monitor connected devices.
* Cybersecurity Tools: Monitor network traffic and test security protocols.

# Installation
### Prerequisites
* Python 3.8 or higher
* No external dependencies required; uses Python standard library only.

### Steps
1. Clone the Repository:

       git clone https://github.com/kassam-99/NetForge.git
       cd NetForge

2. Run the Example: Test the framework with the included server and client scripts:

       python3 ServerDashboard.py 
       python3 Client.py 


# Project Structure
      NetForge/
      ├── server_logs.py         # Logging system
      ├── ServerSettings.py      # Core server definitions
      ├── ReportGenerator.py     # Report generation in CSV/TXT/JSON
      ├── ServerFunctions.py     # Server utility functions
      ├── ServerHandler.py       # User connection handling
      ├── ServerDashboard.py    # Main server interface
      ├── Client.py        # Client implementation
      └── README.md              # Project documentation
  
# Libraries used in the provided files
1. server_logs.py:

       import logging (standard library)
       import os (standard library)
       from datetime import datetime (standard library)
       import traceback (standard library)
       No external libraries.

2. ServerSettings.py:

       import socket (standard library)
       No external libraries.

3. ReportGenerator.py:

       import csv (standard library)
       import datetime (standard library)
       import json (standard library)
       import os (standard library)
       No external libraries.

4. ServerFunctions.py:

       from ReportGenerator import Report_Generator (internal module)
       from server_logs import Logs (internal module)
       from ServerSettings import Server (internal module)
       import datetime (standard library)
       import socket (standard library)
       import struct (standard library)
       No external libraries.

5. ServerHandler.py:

       from ReportGenerator import Report_Generator (internal module)
       from server_logs import Logs (internal module)
       from ServerFunctions import Server_Functions (internal module)
       import datetime (standard library)
       import struct (standard library)
       No external libraries.

6. ServerDashboard.py:

       import socket (standard library)
       from ReportGenerator import Report_Generator (internal module)
       from server_logs import Logs (internal module)
       from ServerHandler import UserHandler (internal module)
       No external libraries.

7. Client.py:

       import socket (standard library)
       import struct (standard library)
       import os (standard library)
       No external libraries.
   

All the libraries used in the provided files (os, socket, datetime, logging, traceback, csv, json, struct) are part of Python’s standard library. There are no external dependencies (e.g., from PyPI) explicitly required based on the code you shared. Therefore, the requirements.txt file can technically be empty or simply indicate that no additional installations are needed beyond a compatible Python version.




---

# Customization

To adapt **NetForge** for your specific project, you only need to edit `ServerDashboard.py`. This file acts as the main control center, leveraging the robust foundation provided by `ServerSettings.py`. Here’s how to get started:

### Why `ServerDashboard.py`?
- **Flexible Configuration**: Set your `ServerIP`, `ServerPort`, and `maxHostgroup` in the `__main__` block or `__init__` method.
- **Custom Behavior**: Extend the `ServerHandler` method to implement your target functionality (e.g., file transfers, chat messaging) using the predefined `server_functions` like `broadcast` or `ban` from `ServerSettings.py`.
- **Keep It Simple**: No need to modify other files—`ServerSettings.py` already provides a socket setup, user roles (`admin`, `client`), and a rich set of commands and statuses.

### What Can You Edit?

- **Server Configuration**: Adjust `IP`, `port`, and `maximum connections` in `__init__` or `__main__`.
- **ServerHandler**: Define how the server interacts with clients (e.g., chat, file transfer).
- **Reporter**: Customize reporting with `self.Reporte`r to log connection data, chat history, or server metrics in `CSV`, `TXT`, or `JSON` formats.
- **Logging**: Modify `self.Logger_server_Dashboard` settings (e.g., log file name, verbosity) for detailed debugging or custom logs.
- **Server Details**: Enhance `server_details` to display additional info like connected clients or uptime.

    
### Example: File Transfer Server
Modify `ServerDashboard.py` to handle file transfers:

    def ServerHandler(self, ClientConn, ClientInfo):
        try:
            if self.verify_connection(ClientConn, ClientInfo):
                self.Logger_server_Dashboard.LogsMessages(f"[+] Connection Established with {ClientInfo}", message_type="info", verbose=self.verbose)
                # Add file transfer logic
                file_data = ClientConn.recv(1024)  # Receive file data
                with open("received_file.txt", "wb") as f:
                    f.write(file_data)
                self.Logger_server_Dashboard.LogsMessages(f"[+] File received from {ClientInfo}", message_type="info", verbose=self.verbose)
        except Exception as e:
            self.Logger_server_Dashboard.LogsMessages(f"[!] Error in ServerHandler: {e}", message_type="error", verbose=self.verbose)


### Example: Example: Chat Server

Turn `ServerDashboard.py` into a chat server by modifying the ServerHandler method to broadcast messages to all connected clients:


    def ServerHandler(self, ClientConn, ClientInfo):
        try:
            if self.verify_connection(ClientConn, ClientInfo):
                self.Logger_server_Dashboard.LogsMessages(f"[+] Connection Established with {ClientInfo}", message_type="info", verbose=self.verbose)
                # Store the client socket for broadcasting
                self.ConnClient.append({"socket": ClientConn, "info": ClientInfo})
                while True:
                    message = ClientConn.recv(1024).decode("utf-8")
                    if not message:
                        break
                    broadcast_msg = f"{ClientInfo[0]}:{ClientInfo[1]} says: {message}"
                    for client in self.ConnClient:
                        try:
                            client["socket"].send(broadcast_msg.encode("utf-8"))
                        except:
                            continue
                    self.Logger_server_Dashboard.LogsMessages(f"[+] Broadcasted message from {ClientInfo}: {message}", message_type="info", verbose=self.verbose)
        except Exception as e:
            self.Logger_server_Dashboard.LogsMessages(f"[!] Error in ServerHandler: {e}", message_type="error", verbose=self.verbose)
        finally:
            ClientConn.close()
            # Remove client from list on disconnect
            self.ConnClient = [c for c in self.ConnClient if c["socket"] != ClientConn]


### Notes on the Chat Server Example
* Loop: The while True loop keeps the connection open to receive multiple messages.
* Broadcasting: Messages are sent to all clients in `self.ConnClient`, using the client’s IP and port as an identifier.
* Error Handling: Skips unresponsive clients and closes the connection cleanly.

Tips
* Use `server_functions`: Check `ServerSettings.py` for commands like `0x2D: "broadcast"` or `0x16: "ban"` to enhance functionality (e.g., implement ban to block users).
* Leverage `user_status_code`: Utilize codes like `0x2B: "receiver"` or `0x3B: "sender"` for role-specific logic, such as distinguishing chat senders.
* Verbose Mode: Enable `verbose=True` for detailed logs during development to debug message flow.




Edit `ServerDashboard.py` under `__main__` to set your desired `IP` and `port`:

    if __name__ == "__main__":
        server_ip = "192.168.1.100"  # Your target IP
        server_port = 5000           # Your target port
        verbose = True               # Enable logging
        server_dashboard = Server_Dashboard(ServerIP=server_ip, ServerPort=server_port, verbose=verbose)
        server_dashboard.server_details()
        server_dashboard.StartServer()


---
## Using the Reporter

The `self.Reporter` object, initialized in `__init__` as `self.Reporter = Report_Generator()`, allows you to generate reports about server activity. Here’s how to use it effectively in ServerDashboard.py:

Available Methods
Assuming ReportGenerator.py provides:

* `CSV_GenerateReport(data, filename)`: Writes data as a CSV file.
* `TXT_GenerateReport(data, filename)`: Writes data as a plain text file.
* `JSON_GenerateReport(data, filename)`: Writes data as a JSON file.

How to Use It

1. Prepare Data: Create a dictionary with the information you want to report (e.g., client details, messages, timestamps).
2. Call a Method: Use `self.Reporter.<method>(data, filename)` to save the report.
3. Customize Output: Specify a unique filename to avoid overwriting, and choose the format that suits your needs.



### Example 1: Log Chat Messages in a Chat Server

Modify ServerHandler to record chat history:

    def ServerHandler(self, ClientConn, ClientInfo):
        try:
            if self.verify_connection(ClientConn, ClientInfo):
                self.Logger_server_Dashboard.LogsMessages(f"[+] Connection Established with {ClientInfo}", message_type="info", verbose=self.verbose)
                self.ConnClient.append({"socket": ClientConn, "info": ClientInfo})
                while True:
                    message = ClientConn.recv(1024).decode("utf-8")
                    if not message:
                        break
                    broadcast_msg = f"{ClientInfo[0]}:{ClientInfo[1]} says: {message}"
                    for client in self.ConnClient:
                        try:
                            client["socket"].send(broadcast_msg.encode("utf-8"))
                        except:
                            continue
                    self.Logger_server_Dashboard.LogsMessages(f"[+] Broadcasted message from {ClientInfo}: {message}", message_type="info", verbose=self.verbose)
                    # Use Reporter to log the message
                    report_data = {
                        "timestamp": str(datetime.datetime.now()),
                        "client": f"{ClientInfo[0]}:{ClientInfo[1]}",
                        "message": message
                    }
                    self.Reporter.CSV_GenerateReport(report_data, filename="chat_log.csv")
        except Exception as e:
            self.Logger_server_Dashboard.LogsMessages(f"[!] Error in ServerHandler: {e}", message_type="error", verbose=self.verbose)
        finally:
            ClientConn.close()
            self.ConnClient = [c for c in self.ConnClient if c["socket"] != ClientConn]
            self.Logger_server_Dashboard.LogsMessages(f"[-] Client {ClientInfo} disconnected", message_type="info", verbose=self.verbose)




Output (chat_log.csv):

    timestamp,client,message
    "2025-03-14 10:00:00","192.168.1.100:5000","Hello everyone!"
    "2025-03-14 10:00:05","192.168.1.101:5001","Hi there!"




### Example 2: Report Connected Clients in server_details

Enhance server_details to log all connected clients:

    def server_details(self):
        try:
            host_name = socket.gethostname()
            if self.ServerIP is None:
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                    sock.connect(('8.8.8.8', 80))
                    self.ServerIP = sock.getsockname()[0]
            if self.ServerPort is None:
                self.ServerPort = self.check_for_port('localhost', 8000, 8500)
            server_info = f"""
    --------------------------------------------------------------------
    [-] Hostname: {host_name} 
    [-] IP: {self.ServerIP}       
    [-] Port: {self.ServerPort}
    [-] Connected Clients: {len(self.ConnClient)}
    --------------------------------------------------------------------
    """
            self.Logger_server_Dashboard.LogsMessages(server_info, message_type="info", verbose=self.verbose)
            # Use Reporter to log connected clients
            client_data = {
                "server": f"{self.ServerIP}:{self.ServerPort}",
                "clients": [c["info"] for c in self.ConnClient]
            }
            self.Reporter.JSON_GenerateReport(client_data, filename="connected_clients.json")
        except Exception as e:
            self.Logger_server_Dashboard.LogsMessages(f"[!] Unable to get Hostname and IP: {str(e)}", message_type="critical", verbose=self.verbose)



Output (connected_clients.json):

    {
        "server": "192.168.1.100:5000",
        "clients": [
            ["192.168.1.100", 5001],
            ["192.168.1.101", 5002]
        ]
    }


### Example 3: Log Server Status in StartServer

Track server start events:

    def StartServer(self):
        try:
            while True:
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
                        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                        server.bind((self.ServerIP, self.ServerPort))
                        server.listen(5)
                        self.Logger_server_Dashboard.LogsMessages(f"[*] Listening on {self.ServerIP}:{self.ServerPort}", message_type="info", verbose=self.verbose)
                        # Report server start
                        self.Reporter.TXT_GenerateReport({"start_time": str(datetime.datetime.now()), "ip": self.ServerIP, "port": self.ServerPort}, filename="server_status.txt")
                        while True:
                            client_socket, addr = server.accept()
                            self.Logger_server_Dashboard.LogsMessages(f"[+] Accepted connection from {addr}", message_type="info", verbose=self.verbose)
                            self.ServerHandler(client_socket, addr)
                    break
                except OSError as bind_error:
                    if bind_error.errno == 98:
                        self.Logger_server_Dashboard.LogsMessages(f"[!] Port {self.ServerPort} in use. Trying next available port.", message_type="warning", verbose=self.verbose)
                        self.ServerPort = self.check_for_port(self.ServerIP, self.ServerPort + 1, 8500)
                    else:
                        raise
        except Exception as e:
            self.Logger_server_Dashboard.LogsMessages(f"[!] Error in Starting a Server - StartServer: {e}", message_type="error", verbose=self.verbose)

Output (server_status.txt):

    start_time: 2025-03-14 10:00:00
    ip: 192.168.1.100
    port: 5000



### Key Points on Using Reporter

* Initialization: self.Reporter is already set up in `__init__` with self.Reporter = Report_Generator(), so it’s ready to use throughout ServerDashboard.py.
* Data Structure: Pass a dictionary to the report methods—keys become headers in CSV or fields in `JSON/TXT`.
* Flexibility: Call self.Reporter in any method `(ServerHandler, server_details, StartServer)` to log specific events or states.
* Dynamic Filenames: Use timestamps or counters `(e.g., f"chat_log_{time.time()}.csv")` to avoid overwriting files if needed.





# Conclusion

**NetForge** is more than just a networking framework—it’s a versatile toolkit that empowers developers to craft tailored server-client applications with ease. From file transfers to real-time chat systems, its modular design, robust logging, and customizable reporting via `self.Reporter` make it a solid foundation for a wide range of projects. By editing only `ServerDashboard.py`, you can harness the power of `ServerSettings.py`’s predefined functions and statuses to build exactly what you need, whether it’s a secure IoT hub, a remote admin tool, or a cybersecurity monitor.  

As an open-source project, NetForge thrives on community input. Whether you’re tweaking it for a personal project or contributing to its growth, your creativity can shape its future. So, dive in, forge your solution, and let’s build the next generation of networked applications together! 🚀

---

## Extra Goodies

#### Table of Supported Platforms
| Platform  | Status       | Notes                 |
|-----------|--------------|-----------------------|
| Windows   | ✅ Supported | Tested on Win 10+     |
| Linux     | ✅ Supported | Ubuntu, Fedora, etc.  |
| macOS     | ✅ Supported | macOS 11+ compatible  |

#### Horizontal Rule
***  
Ready to forge your next app? Let’s go! 🚀  

---
