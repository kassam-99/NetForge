import logging
import os
from datetime import datetime


class Logs:
    
    
    def __init__(self, default_log_level=logging.DEBUG, main_log_file="main.log"):
        self.default_log_level = default_log_level
        self.log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        self.mainloggerfile = self.resolve_log_path(main_log_file)
        self.logger = None

        # Initialize the main logger
        self.main_logger = logging.getLogger("MainLogger")
        self.main_logger.setLevel(self.default_log_level)

        if self.main_logger.hasHandlers():
            self.main_logger.handlers.clear()

        os.makedirs(os.path.dirname(self.mainloggerfile), exist_ok=True)
        main_handler = logging.FileHandler(self.mainloggerfile)
        main_handler.setFormatter(logging.Formatter(self.log_format))
        main_handler.setLevel(self.default_log_level)
        self.main_logger.addHandler(main_handler)


    def resolve_log_path(self, path):
        """Resolve relative or absolute path to absolute, ensuring it ends with `.log`."""
        if not path.lower().endswith(".log"):
            path += ".log"

        if not os.path.isabs(path):
            path = os.path.join(os.path.dirname(__file__), path)

        os.makedirs(os.path.dirname(path), exist_ok=True)
        return os.path.abspath(path)


    def construct_path(self, folder_name, file_name):
        """Construct full path from folder and file, respecting relative or absolute paths."""
        if not file_name.lower().endswith(".log"):
            file_name += ".log"

        if os.path.isabs(folder_name):
            full_path = os.path.join(folder_name, file_name)
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            full_path = os.path.join(base_dir, folder_name, file_name)

        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        return os.path.abspath(full_path)


    def log_to_file(self, message, TypeLog):
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL
        }
        log_level = level_map.get(TypeLog.upper(), logging.WARNING)
        self.main_logger.log(log_level, message)


    def LogEngine(self, folder_name, log_name):
        """Set up a named logger and resolve the file path correctly."""
        full_path = self.construct_path(folder_name, f"{log_name}.log")
    
        self.logger = logging.getLogger(log_name)
        self.logger.setLevel(self.default_log_level)
    
        for handler in self.logger.handlers[:]:
            if isinstance(handler, logging.FileHandler):
                self.logger.removeHandler(handler)
    
        handler = logging.FileHandler(full_path)
        handler.setFormatter(logging.Formatter(self.log_format))
        handler.setLevel(self.default_log_level)
        self.logger.addHandler(handler)
    

    def LogsMessages(self, message, message_type="info", folder_name=None, file_name=None):
        if folder_name and file_name:
            full_path = self.construct_path(folder_name, file_name)

            temp_logger = logging.getLogger(f"{folder_name}_{file_name}")
            temp_logger.setLevel(self.default_log_level)

            if not any(isinstance(h, logging.FileHandler) and h.baseFilename == full_path
                       for h in temp_logger.handlers):
                handler = logging.FileHandler(full_path)
                handler.setFormatter(logging.Formatter(self.log_format))
                temp_logger.addHandler(handler)

            getattr(temp_logger, message_type.lower(), temp_logger.warning)(message)
        elif self.logger:
            log_method = getattr(self.logger, message_type.lower(), self.logger.warning)
            log_method(message)
        else:
            self.log_to_file(message, message_type.upper())


    def print_and_log(self, message, message_type="info", folder_name=None, file_name=None):
        self.LogsMessages(message, message_type, folder_name, file_name)
        print(message)








# ==============================
# Usage Example
# ==============================
if __name__ == "__main__":
    logger = Logs()
    logger.LogEngine("ExxxxampleLogger", "ExampleLogger.log")
    logger.LogsMessages("This is a hidden message")
    logger.print_and_log("This is a test message.", message_type="info")

    # You can also directly specify folder and file for a log message
    logger.print_and_log("Direct log to folder", message_type="info", folder_name="CustomLogs", file_name="event.log")

