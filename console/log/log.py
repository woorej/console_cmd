import os
from datetime import datetime
import logging
import logging.config
from copy import deepcopy
import inspect
import grpc
from lib import *
from lib import sample_pb2
from lib import sample_pb2_grpc

class grpcHandler(logging.Handler):
    """
    A logging handler that sends logs to a remote server via gRPC.
    """
    def __init__(self, ssl_cert_data, identifier):
        super().__init__()
        self.ssl_cert_data = ssl_cert_data
        self.db = {}
        self.identifier = identifier
    
    def valid_address(self, address):
        try:
            addr = address.split(':') # server address
            return addr
        except Exception as e:
            return None
    
    def append_address(self, grpc_address):
        addr = self.valid_address(grpc_address)
        if not addr:
            return "Invalid address Format"
        try:
            ip, port = addr[0], addr[1]
        except Exception as e:
            return "Invalid Input. Please enter <IP:PORT>"
      
        self.db[grpc_address] = conn_info(name="Netshell", ip=ip, port=port, ca_data=self.ssl_cert_data)
        return f"Successfully applied address: {self.db[grpc_address].addr}"
        
    def remove_address(self, grpc_address):
        if not self.valid_address(grpc_address):
            return "Invalid address Format"
        
        if grpc_address in self.db:
            del self.db[grpc_address]
            return f"Successfully removed address: {grpc_address}"
        else:
            return "Address not found in the database"
    
    def emit(self, record):
        """
        Emit a log record.

        Sends the log record to the remote server via gRPC.
        """
        try:
            if self.db:
                message = self.format(record)
                general_message = sample_pb2.GeneralMsg()
                general_message.id = self.identifier
                
                for _, receiver in self.db.items():    
                    general_message.msg = message
                
                    # Call the remote gRPC service
                    _ = receiver.stub.log(general_message)
            
        except Exception as e:
            pass
            #self.handleError(record)

        
def delete_handler(logger, handler_type=grpcHandler, address=''): # logging.FileHandler
    removed = False
    for handler in list(logger.handlers):  # Create a copy of the list to modify it while iterating
        if isinstance(handler, handler_type):
            if handler_type == grpcHandler and address and handler.netshell.addr != address:
                continue 
            logger.removeHandler(handler) # Remove and close the handler
            handler.close()
            removed = True

    return removed

def add_handler(logger, config, path, address, ssl_cert_data, print_console=False):    
    if 'handlers' in config:
        handlers_config = config['handlers']
        
        for handler_name, handler_config in handlers_config.items():
            if handler_config['class'] == 'logging.StreamHandler' and print_console: # stream handler가 설정에 있어도 print_console이 False이면 추가하지 않음
                handler = logging.StreamHandler()
                
            elif handler_config['class'] == 'logging.handlers.RotatingFileHandler' and path: # File handler가 설정에 있어도 경로를 넘겨주지 않으면 생성하지 않음
                handler = logging.handlers.RotatingFileHandler(
                    filename = path,
                    maxBytes=handler_config.get('maxBytes', 0),
                    backupCount=handler_config.get('backupCount', 0)
                )
            elif handler_config['class'] == 'grpcHandler' and address:
                # grpc_address = handler_config.get('grpc_address')
                if not address:
                    raise ValueError("Please insert your address")
                handler = grpcHandler(ssl_cert_data, address)
            else:
                continue
            
            formatter_config = config['formatters'][handler_config['formatter']]
            
            if 'datefmt' in formatter_config:
                datefmt = formatter_config['datefmt']
            else:
                datefmt = None
                
            formatter = logging.Formatter(
                fmt=formatter_config['format'],
                datefmt=datefmt
            )
        
            handler.setFormatter(formatter)
            handler.setLevel(handler_config['level'])
            logger.addHandler(handler)
            
    logger.setLevel(config['root']['level'])
    return "successfully added log handler"


def configure_logging(debug_mode: bool, log_filename: str, original_log_config: dict, use_timestamp=False) -> logging.Logger:
    log_directory = os.path.dirname(log_filename)
    log_name = os.path.basename(log_filename)
    logger = logging.getLogger(log_name)
    if not logger.hasHandlers():
        if log_directory == '':
            log_directory = os.path.join('logs', log_name)
        elif use_timestamp:
            date_time = datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
            log_directory = os.path.join(log_directory, f"{log_name}_{date_time}")
            
        log_name = f"{log_name}.log"
        os.makedirs(log_directory, exist_ok=True)
        full_log_path = os.path.join(log_directory, log_name)

        log_config = deepcopy(original_log_config)
        handlers_config = log_config['handlers']

        for handler_name, handler_config in handlers_config.items():
            # Only add FileHandler if debug_mode is False
            if handler_config['class'] == 'logging.StreamHandler' and debug_mode:
                handler = logging.StreamHandler()
            elif handler_config['class'] == 'logging.handlers.RotatingFileHandler':
                handler = logging.handlers.RotatingFileHandler(
                    filename=full_log_path,
                    maxBytes=handler_config.get('maxBytes', 0),
                    backupCount=handler_config.get('backupCount', 0)
                )
            else:
                continue  # Skip unsupported handlers

            # Set formatter and level
            formatter_config = log_config['formatters'][handler_config['formatter']]
            formatter = logging.Formatter(
                fmt=formatter_config['format'],
                datefmt=formatter_config['datefmt']
            )
            handler.setFormatter(formatter)
            handler.setLevel(handler_config['level'])
            
            logger.addHandler(handler)

        logger.setLevel(log_config['root']['level'])
            
    return logger

def log_generator(path, config, address='', ssl_cert_data=None, print_console: bool=False):
    name = os.path.basename(path)
    directory = os.path.dirname(path)
    logger = logging.getLogger(name)
    os.makedirs(directory, exist_ok=True)
    # def add_handler(logger, config, path='', ssl_cert_data=None, my_address='', print_console=False):

    if not logger.hasHandlers():
        add_handler(logger, config, path, address, ssl_cert_data, print_console=print_console)
    return logger

class Logcfg:
    log_cfg = {
        "version": 1,
        "formatters": {
            "nsh": {
                "format": "%(message)s",
            },
            "rev_full": {
                "format": "%(asctime)s - %(name)s - %(levelname)5s - %(message)s",
                "datefmt": "%Y%m%d %H:%M:%S.%f"
            },
            "rev_full2": {
                "format": "%(asctime)s:%(levelname)5s: %(filename)s:%(funcName)s:%(lineno)d: %(message)s",
                "datefmt": "%Y%m%d %H:%M:%S"
            },
            "rev_small1": {
                "format": "%(asctime)s - %(name)s - %(levelname)5s - %(message)s",
                "datefmt": "%H:%M:%S"
            },
            "rev_mini1": {
                "format": "%(asctime)s - %(message)s",
                "datefmt": "%H:%M"
            },
            "rev_mini2": {
                "format": "%(asctime)s:%(levelname)5s: %(filename)s:%(funcName)s:%(lineno)d: %(message)s",
                "datefmt": "%H:%M:%S.%f"
            },
            "rev_mini3": {
                "format": "%(asctime)s:%(levelname)5s: %(lineno)d: %(message)s",
                "datefmt": "%H:%M"
            },
            "rev_mini0": {
                "format": "%(lineno)3d: %(message)s",
                "datefmt": "%H:%M"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "DEBUG",
                "formatter": "rev_mini2",
                "stream": "ext://sys.stdout"
            },
            "info_file_handler": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "DEBUG",
                "formatter": "rev_full2",
                "filename": "logs/mem_control.log",
                "maxBytes": 500000000,
                "backupCount": 10
            },
            "grpc_handler": {
                "class": "grpcHandler",
                "level": "DEBUG",
                "formatter": "rev_full2",
            }
        },
        "root": {
            "level": "DEBUG",
            # "handlers": [
            #     "console",
            #     "info_file_handler"
            # ]
        }
    }
    