from console.template.title_template import default_title
from console.local.base_context import LocalContext
import os
from log.log import grpcHandler
from console.utils import *
import logging
from console.utils import process_hints

class LogContext(LocalContext):
    lang_path = ['common', 'local', 'log']
    def __init__(self) -> None:
        super().__init__()
    
    def _update_lang(self):
        super()._update_lang()
        command_table = self.multi_lang.get_commands_table(LogContext.lang_path)
        self.commands_table.update(command_table)
    
    def _get_grpc_log_handler(self):
        for handler in self.instance.log.handlers:
            if isinstance(handler, grpcHandler):
                return handler
        return None
        
    @check_attribute("log", logging.Logger)
    @default_title
    @process_hints
    def append_address(self, server_addr, **kwargs):
        grpc_handler = self._get_grpc_log_handler()
            
        if not grpc_handler:
            return "Can not find gRPC Handler"
            
        return grpc_handler.append_address(server_addr)
   
    @check_attribute("log", logging.Logger)
    @default_title
    def log_status(self, **kwargs):
        result = []
        for handler in self.instance.log.handlers:
            if isinstance(handler, grpcHandler):
                for address in handler.db.keys():
                    result.append(address)
            else:
                result.append(handler.__class__.__name__)
                
        return result if result else "log doesn't have any handler"
    
    @check_attribute("log", logging.Logger)
    @default_title
    @process_hints
    def delete_address(self, server_addr, **kwargs):
        grpc_handler = self._get_grpc_log_handler()
            
        if not grpc_handler:
            return "Can not find gRPC Handler"
            
        return grpc_handler.remove_address(server_addr)
    
    @default_title
    @process_hints
    def test_log_n(self, n, **kwargs):
        n = int(n)
        i = 0
        while n > i:
            self.instance.log.debug(f"Test log {i+1}")
            i+=1
        return f"Finished Test log for {n} times"  
    
    @default_title
    def get_log_path(self, **kwargs):
        file_path = os.path.join(os.path.expanduser('~'), '.ai_fw', 'logs', f"{self.instance.my_name}.log")
        if os.path.exists(file_path):
            return file_path
        else :
            return f"File Does Not Exists: {file_path}"