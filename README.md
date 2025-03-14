# NetForge
NetForge is an open-source Python framework designed for building networked applications with robust server-client communication, logging, and reporting capabilities. Whether you're creating a file transfer tool, a chat app, or an IoT management system, NetForge provides a modular foundation to forge your own solutions.

Let’s dive in and explore what makes this framework special!


## Features

Here’s what NetForge brings to the table:

- Socket-Based Networking: Reliable TCP communication between servers and clients using a custom protocol.
- User Management: Supports admin and client roles with connection validation and status tracking.
- Extensive Logging: Five log levels (DEBUG, INFO, <span style="color:orange">WARNING</span>, <span style="color:red">ERROR</span>, <span style="color:purple">CRITICAL</span>) with file-based storage.
- Reporting: Generate reports in CSV, TXT, and JSON formats for connection details and server activity.
- Modular Design: Easily extendable classes for custom applications.
- Cross-Platform: Runs on Windows, Linux, and macOS with Python 3.8+.

    “NetForge is like a blacksmith’s forge for networking—shape it to fit your needs!” — A happy developer

## Use Cases

NetForge can be adapted for:
### Unordered List of Possibilities

* File Transfer Applications: Securely share files between clients via a server.
* Chat Systems: Enable real-time messaging with broadcast capabilities.
* Remote Administration: Manage servers and users with admin privileges.
* IoT Device Control: Coordinate and monitor connected devices.
* Cybersecurity Tools: Monitor network traffic and test security protocols.


# Installation
## Prerequisites
* Python 3.8 or higher
* pip for dependency management

## Steps
1. Clone the Repository:

       git clone https://github.com/kassam-99/NetForge.git
       cd NetForge


2. Install Dependencies: Currently, NetForge uses only Python’s standard library. If additional dependencies are added, install them with:

       pip install -r requirements.txt


3. Run the Example: Test the framework with the included server and client scripts:


       python3 ServerDashboard.py 
       python3 Client.py 




  
