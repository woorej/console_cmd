import logging
from lib.conn import conn_info
from rev.prettyjson import prettyjson 
import traceback
from functools import wraps
import logging
from typing import Dict
import os
from pprint import pprint
import shutil
from functools import wraps
from zeroconf_client import *
from zeroconf_client import *
import json

# class Tee:
#     def __init__(self, name, mode):
#         self.file = open(name, mode)
#         self.stdout = sys.stdout  
#         self.stderr = sys.stderr  
#         #self.stdin = sys.stdin

#     def write(self, data):
#         self.file.write(data) 
#         self.stdout.write(data) 

#     def flush(self):
#         self.file.flush() 
#         self.stdout.flush()  

#     def close(self):
#         self.file.close()  

def clean_input(input_string):
    # 입력된 문자열이 "''" 또는 '""'일 경우 빈 문자열로 변환
    if input_string == "\"''\"" or input_string == "'\"\"'":
        return ''
    return input_string.strip('"').strip("'")
        
def _auto_input(prompt):
        return input(f"{prompt} ")
    
def process_input(parameters=[], hints=[]):
        basket = []
        
        for i in range(len(hints)):
            prompt = hints[i]
            current_value = parameters[i] if i < len(parameters) else None

            if not current_value:
                current_value = _auto_input(prompt)
                
            basket.append(current_value)
            
        # hints는 1개인데 hints에 관한 파라미터를 우선 순서로 담고 이후 1개이상의 변수를 담은경우
        for param in parameters[len(hints):]:
            basket.append(param)
            
        return basket
    
def process_hints(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        hints = kwargs.get('hints', [])
        total_param_count = kwargs.get('total_param')
        
        if not hints:
            return func(self, *args, **kwargs)
        
        parameters = process_input(hints=hints, parameters=args)
        
        if len(parameters) > total_param_count:
            print(f"Warning: Too many parameters provided. Expected {len(hints)}, got {len(parameters)}.")
            extra_params = parameters[len(hints):]
            kwargs.update({f"extra_param_{i}": param for i, param in enumerate(extra_params)})
            parameters = parameters[:len(hints)]
            
        return func(self, *parameters, **kwargs)
    return wrapper

class ShareData():
    def __init__(self):
        self.appended_svc_sessions = {}

def save_recent_return(value, command_handler):
    result = command_handler.variable_manager.set_variable("_$", repr(value))
    if 'set to' in result:
        result = f"{result[:result.index('set to')-1]} updated"
    print(result) 
    
def print_console_message(message, command_handler=None, **kwargs):
    if not message:
        return
    
    if isinstance(message, str):
        print(message)
        if command_handler:
            save_recent_return(message, command_handler)
        return

    ret = message.get('return', None)  
    whom = message.get('whom', "") 
    
    if ret is not None:
        if whom:
            print(f"response from: {whom}")
            
        if isinstance(ret, dict):
            print(prettyjson(ret))
            if command_handler:
                save_recent_return(message, ret)
        else:
            print(ret)
    else:
        if isinstance(message, dict):
            print(prettyjson(message))
            if command_handler:
                save_recent_return(message, command_handler)
            return
        else:
            print(message)
            if command_handler:
                save_recent_return(message, command_handler)
            return
        
        
def print_console_message_for_thread(output, command_handler):
    if not output:
        return
    
    if isinstance(output, str):
        print(output)
        save_recent_return(output, command_handler)
        return
    
    ret = output.get('return', None)
    whom = output.get('whom', "")

    if ret:
        if whom:
            print(f"response from: {whom}")
            
        if isinstance(ret, dict):
            print(f"\n{prettyjson(ret)}")
            save_recent_return(ret, command_handler)
        
        elif isinstance(ret, (list, str)):
            print(f"\n{ret}")
            save_recent_return(ret, command_handler)
       
    else:
        if isinstance(output, dict):
            print(prettyjson(output))
            save_recent_return(output, command_handler)
            return
        else:
            print(output)
            save_recent_return(output, command_handler)
            return
            
    print(f"{command_handler.get_current_context()[0]} > ", end='', flush=True)

def check_attribute(attr_name, attr_type):
    """
    A decorator factory that checks if a specific attribute exists within the instance and validates its type.

    :param attr_name: The name of the attribute to check.
    :param attr_type: The type the attribute should be.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if not hasattr(self.instance, attr_name):
                return f"Please set {attr_name} attribute before proceeding"
            elif not isinstance(getattr(self.instance, attr_name), attr_type):
                return f"{attr_name} attribute is invalid type, expected {attr_type.__name__}"
            else:
                return func(self, *args, **kwargs)
        return wrapper
    return decorator


def check_log_attr(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not hasattr(self.instance, "log"):
            return "Please set log attribute before proceeding"
        elif not isinstance(getattr(self.instance, "log"), logging):
            return "log attribute is invalid type"
        else:
            return func(self, *args, **kwargs)
    return wrapper

def check_my_name(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not hasattr(self.instance, "my_name"):
            return "Please set my_name attribute before proceeding"
        elif not isinstance(getattr(self.instance, "my_name"), str):
            return "my_name attribute is invalid type"
        else:
            return func(self, *args, **kwargs)
    return wrapper

class SessionTable():
    def __init__(self, idx: int, conn: conn_info, name: str):
        self._idx = idx
        self._svc = conn
        self._name = name
        self._prefix = f"{self._name[0]}{self.idx}"
    
    @property
    def idx(self):
        return self._idx
    
    @idx.setter
    def idx(self, value: str):
        if not isinstance(value, str):
            raise ValueError("value must be string")
        self._idx = value
    
    @property
    def svc(self):
        return self._svc
    
    @svc.setter
    def svc(self, value):
        if not isinstance(value, conn_info):
            raise ValueError("conn must be an instance of conn_info")
        self._svc = value
    
    @property
    def name(self):
        return self._name
    
    @name.setter
    def name(self, value):
        if not isinstance(value, str):
            raise ValueError("value must be string")
        self._name = value
        self._prefix = f"{self._name[0]}{self.idx}"

def update_formatter(logger, new_formatter_config):
    # Iterate through all handlers of the logger
    for handler in logger.handlers:
        new_formatter = logging.Formatter(
            fmt=new_formatter_config.get('format'),
            datefmt=new_formatter_config.get('datefmt', None)
        )
        # Update the handler's formatter
        handler.setFormatter(new_formatter)
        # logger.debug(f"Updated formatter of handler '{handler.__class__.__name__}'")
        
def console(command_handler):
    "For Local Console"
    while True:
        try:
            command = input(command_handler.tap_completer.prompt)
            output = command_handler.execute_command(command)
            print_console_message(output)
            
        except Exception as e:
            print_console_message(traceback.format_exc())
            


class FileManager:
    def __init__(self):
        self.path_options = {}
        self.files = {}
        
    def add_path_option(self, new_path: str):
        for key, value in self.path_options.items():
            if new_path == value:
                return f"The path is already in the Dictionary. Idx: '{key}'"
        
        new_index = str(len(self.path_options))
        self.path_options[new_index] = new_path
        self.files[new_index] = {}
        self.update_list_files(new_index)
        return prettyjson(self.path_options)

    def delete_path_option(self, index: str):
        if index not in self.path_options:
            return "Invalid index"

        del self.path_options[index]
        del self.files[index]

        # Shift path_options and files down from the deleted index
        index_int = int(index)
        for idx in range(index_int + 1, len(self.path_options) + 1):
            self.path_options[str(idx - 1)] = self.path_options.pop(str(idx))
            self.files[str(idx - 1)] = self.files.pop(str(idx))
        
        return prettyjson(self.path_options)
        
    def update_list_files(self, name_or_idx: str):
        if name_or_idx not in self.path_options:
            return "Invalid input"
        
        target_path = self.path_options[name_or_idx]
        file_dict = self.files[name_or_idx]
        
        if not file_dict:
            for root, dirs, files in os.walk(target_path):
                for file in files:
                    file_idx = str(len(file_dict))
                    file_dict[file_idx] = os.path.join(root, file)

        return prettyjson(file_dict)

    def delete_file(self, name_or_idx: str, file_idx: str):
        print(self.files.keys())
        if name_or_idx not in self.files:
            return "Invalid input"
        
        file_dict = self.files[name_or_idx]
        if file_idx in file_dict:
            os.remove(file_dict[file_idx])
            file_path = file_dict.pop(file_idx)
            return f"File: {file_path} has been removed."
        else:
            return "Invalid index"
    
    def search_file(self, name_or_idx: str, word: str):
        if name_or_idx not in self.files:
            return "Invalid input"
        
        file_dict = self.files[name_or_idx]
        matched_files = {file_idx: file_path for file_idx, file_path in file_dict.items() if word in file_path}
        
        return matched_files if matched_files else "No matching files found"

    def show_file_lists(self, name_or_idx: str):
        if name_or_idx not in self.files:
            return "Invalid input"
        
        return prettyjson(self.files[name_or_idx])

    def show_path_options(self, idx=None):
        if not idx:
            return prettyjson(self.path_options)
        else:
            return prettyjson(self.path_options.get(idx, {}))
    
    def move_file(self, name_or_idx: str, file_idx: str, dest_path: str):
        if name_or_idx not in self.files:
            return "Invalid path option index."

        if file_idx not in self.files[name_or_idx]:
            return "Invalid file index."

        src_file_path = self.files[name_or_idx][file_idx]
        file_name = os.path.basename(src_file_path)

        # Ensure the destination directory exists
        os.makedirs(dest_path, exist_ok=True)

        dest_file_path = os.path.join(dest_path, file_name)

        try:
            # Move the file using shutil.move which automatically handles file overwrite
            shutil.move(src_file_path, dest_file_path)
            # Update the internal record to reflect the new file location
            self.files[name_or_idx][file_idx] = dest_file_path
            return f"Moved file to {dest_file_path}"
        except Exception as e:
            return f"Error moving file: {str(e)}"

import socket

def get_ip_address():
	try:
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		s.connect(("8.8.8.8", 80))
		ip_address = s.getsockname()[0]
		s.close()
		return ip_address
	except Exception as e:
		print(f"Error retrieving IP address: {e}")
		return None

def discover_and_connect(svc_name, svc_type, max_attempts, ca_data=None):
    attempts = 0
    while attempts < max_attempts:
        print(f"({attempts+1}/{max_attempts}) ", end='')
        discovered_services = discover_service(svc_type)
        for name, address, port in discovered_services:
            dst_address = f"{address}:{port}"
            print(f"Discovered service\n{name} at {dst_address}")
            svc = setup_svc_connection(svc_name, dst_address, ca_data)

            if svc.test_conn():
                print(f"Successful connection established.")
                return True, dst_address
            else:
                print(f"Service found, but communication failed.")
        attempts += 1
    return False, None


def establish_svc_connection(src_address, svc_name: str, svc_type: str, max_attempts: int = 2, ca_data: bytes = None) -> Tuple[bool, str]:
    """
    Attempts to establish a service connection based on the service configuration.
    If the IP and port are set to dummy values, it tries to discover the service and establish a connection.
    If discovery fails or direct connection with predefined IP and port fails, it retries up to a maximum number of attempts.

    :param src_address: The source address to try for a direct connection. Uses a dummy address to initiate discovery.
    :param svc_name: The name of the service to connect to.
    :param svc_type: The type of the service used for discovery.
    :param max_attempts: The maximum number of discovery attempts if the direct connection fails or if in discovery mode.

    :return: A tuple (bool, str) indicating success status and the service address. Returns False and None on failure.
    
    How to use:
    src_ip = "192.168.1.1"
    success, address = establish_svc_connection(src_ip, "management", ""_mgmt._udp.local.", max_attempts=2)
    if not success:
        sys.exit()
    dst_ip = address
    """

    dummy_ip, dummy_port = "0.0.0.0", "0"
    dummy_address = f"{dummy_ip}:{dummy_port}"

    if src_address == dummy_address:
        success, address = discover_and_connect(svc_name, svc_type, max_attempts, ca_data)
        if success:
            return True, address
    else:
        print(f"Trying direct connection to {src_address}")
        svc = setup_svc_connection(svc_name, src_address, ca_data)
        if svc.test_conn():
            print("Successful connection established.")
            return True, src_address
        else:
            print("Direct connection failed.")
            success, address = discover_and_connect(svc_name, svc_type, max_attempts, ca_data)
            if success:
                return True, address

    print("Failed to establish connection after maximum attempts.")
    return False, None

def setup_svc_connection(svc_name, addr, ca_data=None):
    _addr = addr.split(':')
    _svc = conn_info(svc_name, ip=_addr[0], port=_addr[1], ca_data=ca_data)
    return _svc


def update_config_with_defaults(config, default):
    updated = False
    for key, value in default.items():
        if key not in config:
            config[key] = value
            updated = True
        elif isinstance(value, dict) and isinstance(config[key], dict):
            nested_updated = update_config_with_defaults(config[key], value)
            updated = updated or nested_updated
    return updated

def _save_config(file_path, config, add_timestamp=False):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    if add_timestamp:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        config = {"_comment": f"Configuration file created on {timestamp}", **config}
    with open(file_path, "w") as file:
        file.write(prettyjson(config))

def _load_config(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def eval_config(config_path, default_config_path, default_config, save_flag):
    file_created = False
    config_updated = False

    if os.path.exists(config_path):
        config = _load_config(config_path)
        config_updated = update_config_with_defaults(config, default_config)
        if save_flag and config_updated:
            _save_config(config_path, config)
            file_created = True
    else:
        print(f"{config_path} does not exist.")
        config = default_config
        if save_flag:
            _save_config(default_config_path, default_config, add_timestamp=True)
            file_created = True

    return config, file_created, config_updated


def eval_configs(configs, save_flag):
    file_created = False
    config_updated = False
    results = {}

    for key, config_info in configs.items():
        config_path = config_info["config_path"]
        default_config_path = config_info["default_config_path"]
        default_config = config_info["default_config"]

        config, created, updated = eval_config(config_path, default_config_path, default_config, save_flag)
        results[key] = config
        file_created = file_created or created
        config_updated = config_updated or updated

    if file_created:
        print("One or more configuration files were created.")
    if config_updated:
        print("One or more configurations were updated.")
    if save_flag and (file_created or config_updated):
        print("Shutting down.")
        sys.exit(0)

    return results

if __name__ == '__main__':
    f = FileManager()