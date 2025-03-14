import socket



class Server:
    
    
    def __init__(self, ServerIP = None, ServerPort = None, maxHostgroup = 10, verbose = False):
        self.ServerIP = ServerIP
        self.ServerPort = ServerPort
        self.maxHostgroup = maxHostgroup
        self.verbose = verbose
        
        self.ServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        self.order = 0
        self.ConnAdmin = []
        self.ConnClient = []
        self.ConnFile = []
        
        self.user_status_code = {
            # Connection Commands
            0xAA: "connect",
            0xFF: "disconnect",
            
            # User Types
            0x0A: "server",
            0x1A: "admin",
            0x2A: "client",
            
            # User Applications
            0x0B: "function", # Admin only is authorized => Control Server
            0x1B: "browser", # Admin only is authorized -> File Operations
            0x2B: "receiver", # Admin and Client
            0x3B: "sender", # Admin and Client
            
            # User Statuses
            0x0C: "authorized access",  
            0x1C: "unauthorized access",
            0x2C: "blocked User",
            0x3C: "request",
            0x4C: "approved",
            0x5C: "rejected",
            0x6C: "accepted",
            0x7C: "declined",
            0x8C: "waiting",
            0x9C: "done",
            
            # Connection Statuses
            0x0D: "Connection established",
            0x1D: "Connection lost",
            0x2D: "Network unreachable",
            0x3D: "Connection refused by server",
            0x4D: "Protocol error",
            0x5D: "Server disconnected",
            0x6D: "Admin disconnected",
            0x7D: "Client disconnected",
            0x8D: "Connection timeout",
            0x9D: "Network error",
            
            # Network Statuses
            0x0E: "Server not responding",
            0x1E: "Admin not responding",
            0x2E: "Client not responding",
            0x3E: "Connection reset",
            0x4E: "Connection closed",
            0x5E: "Connection failed",
            0x6E: "Connection refused",
        }            
            
    
        self.server_functions = {
            0x0F: "start",                          # Start the server
            0x10: "stop",                           # Stop the server
            0x11: "restart",                        # Restart the server
            0x12: "status",                         # Get server status
            0x13: "update",                         # Update the server
            0x14: "backup",                         # Backup server data
            0x15: "restore",                        # Restore server data
            0x16: "ban",                            # Ban a user
            0x17: "unban",                          # Unban a user
            0x18: "block",                          # Block a user
            0x19: "unblock",                        # Unblock a user
            0x20: "show_all_users",                 # List all users
            0x21: "show_all_admins",                # List all admins
            0x22: "show_all_banned_users",          # List all banned users
            0x23: "show_all_blocked_users",         # List all blocked users
            0x24: "show_all_active_admins",         # List all active admins
            0x25: "show_all_active_users",          # List all active users
            0x26: "show_all_inactive_admins",       # List all inactive admins
            0x27: "show_all_inactive_users",        # List all inactive users
            0x28: "add_user",                       # Add a new user
            0x29: "remove_user",                    # Remove a user
            0x2A: "promote_to_admin",               # Promote a user to admin
            0x2B: "demote_from_admin",              # Demote an admin to user
            0x2C: "send_message",                   # Send a message to users/admins
            0x2D: "broadcast",                      # Broadcast a message to all users
            0x2E: "view_logs",                      # View server logs
            0x2F: "clear_logs",                     # Clear server logs
            0x30: "set_server_config",              # Update server configuration
            0x31: "get_server_config",              # View server configuration
            0x32: "reset_password",                 # Reset a user's password
            0x33: "shutdown",                       # Shutdown the server
            0x34: "reboot",                         # Reboot the server
            0x35: "monitor_usage",                  # Monitor server resource usage
            0x36: "check_network",                  # Check server network status
            0x37: "assign_roles",                   # Assign roles to users
            0x38: "remove_roles",                   # Remove roles from users
            0x39: "create_backup_schedule",         # Create a backup schedule
            0x3A: "delete_backup_schedule",         # Delete a backup schedule
            0x3B: "view_backup_schedule",           # View backup schedule
            0x3C: "run_diagnostics",                # Run server diagnostics
            0x3D: "enable_maintenance_mode",        # Enable maintenance mode
            0x3E: "disable_maintenance_mode",       # Disable maintenance mode
            0x3F: "list_plugins",                   # List all installed plugins
            0x40: "install_plugin",                 # Install a new plugin
            0x41: "uninstall_plugin",               # Uninstall an existing plugin
            0x42: "update_plugin",                  # Update an installed plugin
            0x43: "enable_plugin",                  # Enable a plugin
            0x44: "disable_plugin",                 # Disable a plugin
            0x45: "view_server_uptime",             # View server uptime
            0x46: "set_user_quota",                 # Set data usage quota for a user
            0x47: "remove_user_quota",              # Remove data usage quota for a user
            0x48: "track_activity",                 # Track user activity
            0x49: "export_data",                    # Export server data
            0x4A: "import_data",                    # Import data to the server
        }
        
        self.ServerRunningInfo = {
            # General Server Information
            "Server Status": None,                 # Current status of the server (e.g., Running, Stopped)
            "Server IP": None,                     # IP address of the server
            "Server Port": None,                   # Port number the server is listening on
            "Server Name": None,                   # Human-readable name of the server
            "Server Version": None,                # Version of the server software
            "Server Type": None,                   # Type of server (e.g., Application, Database)
            
            # Client Statistics
            "Total Clients": None,                 # Total number of clients connected to the server
            "Active Clients": None,                # Number of currently active clients
            "Inactive Clients": None,              # Number of inactive or disconnected clients
            
            # Performance Metrics
            "Uptime": None,                        # Server uptime (e.g., in hours or days)
            "CPU Usage": None,                     # Percentage of CPU usage
            "Memory Usage": None,                  # Memory usage in MB or percentage
            "Network Throughput": None,            # Data transfer rate in Mbps
            
            # Security Information
            "Encryption Protocol": None,           # Encryption protocol used (e.g., TLS 1.3)
            "Authentication Method": None,         # Authentication method in use (e.g., OAuth, Basic Auth)
            
            # Logs and Events
            "Last Error": None,                    # Details of the last server error (if any)
            "Last Client Connected": None,         # Timestamp of the last client connection
            "Last Client Disconnected": None,      # Timestamp of the last client disconnection
            
            # Admin Information
            "Admin List": [],                      # List of admin names or IDs
            "Admin Roles": {},                     # Dictionary mapping admin names/IDs to their roles (e.g., Super Admin, Moderator)
            "Last Admin Login": None,              # Timestamp of the last admin login
            "Admin Login History": {},             # Dictionary mapping admin names/IDs to their login timestamps
            "Active Admins": [],                   # List of currently logged-in admins
            "Admin Contact Info": {},              # Dictionary mapping admin names/IDs to their contact details (e.g., email, phone)
            "Admin Actions Log": [],               # List of recent actions performed by admins (e.g., "Admin1 added a new client")
            "Admin Permissions": {},               # Dictionary mapping admin names/IDs to their specific permissions
        }


        self.ConnClientInfo = {
            # User Information
            "User No.": None,
            "User Status": None,
            "User ID": None,
            "Username": None,
            "User IP": None,
            "User Port": None,
            
            # Connection Details
            "Connected Time": None,
            "Connection Command": None,   # Values from user_status_code (e.g., "connect", "disconnect")
            "User Type": None,            # e.g., "server", "admin", "client"
            "User Application": None,     # e.g., "all", "browser", "receiver", "sender"
                        
            # Connection and Network Status
            "Connection Status": None,    # Values from user_status_code connection statuses (e.g., "Connection established")

        }












