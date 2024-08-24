from console.net.nsh_context import NshContext
from console.net.base_context import NetworkContext
from console.template.title_template import default_title
from utils import get_ip_address
from lib.conn import conn_info
import os
from log.log import log_generator, Logcfg
import grpc
from concurrent import futures
from console.utils import update_formatter
from rev.prettyjson import prettyjson
from console.utils import process_hints
from lib import sample_pb2
from lib import sample_pb2_grpc

class NetShellService(sample_pb2_grpc.NetShellServicer):
    def __init__(self, ip, port, network_console_obj: NshContext, ssl_cert_data, cfg):
        self.cfg = cfg
        self.conn = conn_info(ip=ip, port=port, is_conn=False, ca_data=ssl_cert_data)
        self.network_console_obj = network_console_obj
        self.default_base_dir = os.path.join(os.path.expanduser('~'), '.ai_fw', 'config')
        self.log_config = Logcfg.log_cfg 
        
        self.logger = log_generator(os.path.join(os.path.dirname(self.default_base_dir), "logs", "nsh.log"), self.log_config, print_console=True)
        self.convert_flag = True
        self.ssl_cert_data = None
        self.use_secure_grpc = None
        self._set_secure_gRPC()
        
    def _set_secure_gRPC(self):
        self.ssl_cert_paths = {} 
        
        self.msg_encryption = self.cfg.get('msg_encryption', False)
        self.use_secure_grpc = self.cfg.get('secure_comm', False)
        if self.use_secure_grpc:
            if not self.cfg.get('ssl_cert', None) or not os.path.isfile(self.cfg['ssl_cert']):
                self.logger.error('Not found certification file')
                self.use_secure_grpc = False
            elif not self.cfg.get('ssl_key', None) or not os.path.isfile(self.cfg['ssl_key']):
                self.logger.error('Not found certification file')
                self.use_secure_grpc = False
            else:
                self.ssl_cert_paths['ssl_cert'] = self.cfg['ssl_cert']
                self.ssl_cert_paths['ssl_key'] = self.cfg['ssl_key']
                self.ssl_cert_data = bytes()
                with open(self.cfg['ssl_cert'], 'rb') as f:
                    self.ssl_cert_data = f.read()
    
    def log(self, request, context):
        network = request.id
        
        if self.convert_flag:
            for key, value in self.network_console_obj.appended_svc_sessions.items():
                if value.svc.addr == network:
                    network = value._prefix
                    break
       
        max_length = 21
        padded_network = f"[{network}]".ljust(max_length)
        self.logger.info(f"{padded_network} {request.msg}")
        
        response = sample_pb2.GeneralMsg()
        response.id = f"{self.conn.addr}"
        response.msg = "0"
        return response
    
    def serve(self):
        
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=20))
        sample_pb2_grpc.add_NetShellServicer_to_server(self, server)
        
        if self.use_secure_grpc:
            private_key = self.ssl_cert_paths['ssl_key']
            with open(private_key, 'rb') as f:
                pkey_data = f.read()
            server_cred = grpc.ssl_server_credentials(((pkey_data, self.ssl_cert_data,),),)
            server.add_secure_port(self.conn.addr, server_cred)
            self.logger.debug(f'set secure port in service : {self.conn.addr}')
        else:
            server.add_insecure_port(self.conn.addr)
            self.logger.debug('set insecure port in service')
            
        print(f"Netshell Addr:{self.conn.addr}, To stop the server press 'Ctrl+C'")

        update_formatter(self.logger, self.log_config['formatters']['nsh'])
        #self.logger.debug("Test log")
        
        try:
            server.start()
            server.wait_for_termination()
        except KeyboardInterrupt:
            update_formatter(self.logger, self.log_config['formatters']['rev_full2'])
            self.logger.info("Netshell Service is stopping...")
            server.stop(0)
            self.logger.info("Netshell Service has been stopped.")

class LogContext(NetworkContext):
    name = 'log'
    lang_path = ['common', 'nsh', 'log']
    def __init__(self, multi_lang, apd_session, ssl_cert_data, cfg):
        """
        Initialize the base log with a list of available methods excluding those starting with an underscore '_' in their function names
        """
        self.multi_lang = multi_lang
        super().__init__()
        self._update_lang()
         
        self.appended_svc_sessions = apd_session
        self.net = NetShellService(ip=get_ip_address(), port='30010', network_console_obj=self, ssl_cert_data=ssl_cert_data, cfg=cfg)
    
    def _update_lang(self):
        super()._update_lang()
        command_table = self.multi_lang.get_commands_table(LogContext.lang_path)
        self.commands_table.update(command_table)
        
    @default_title    
    def test(self, **kwargs):
        return "test base log"
    
    @default_title
    def show_remote_log_conn(self, **kwargs):
        return f"Log server address: {self.net.conn.addr}"
    
        
    @default_title
    @process_hints
    def alter_remote_log_conn(self, number, **kwargs):
        """
        Alter the network connection port for remote logging.
        """
        if self._is_valid_port(number):
            self.net.conn.port = number
            return f"Successfully changed Address: {self.net.conn.addr}"
        else:
            print("Invalid port number")
                
    @default_title
    def start_remote_log(self, **kwargs):
        self.net.serve()
            
    @default_title
    @process_hints
    def set_log_prefix(self, number, **kwargs):
        """
        Set the log prefix conversion flag on or off directly based on input.
        """     
        current_state_str = "ON" if self.net.convert_flag else "OFF"
        print(f"Current flag state is {current_state_str}.")

        if number not in ["0", "1"]:
            print("Invalid input. Please enter 1, 0, or -1.")

        # Set the flag based on input without checking current state
        if number == "1":
            self.net.convert_flag = True
            print("Flag changed to ON.")
        elif number == "0":
            self.net.convert_flag = False
            print("Flag changed to OFF.")
    
   
    @default_title
    @process_hints
    def download_log(self, session_idx, number_of_log='', **kwargs):
        session, error = self._get_session(session_idx)
        if error:
            return error
        
        def output_conosle(output):
            ret = output.get('return', None)
            
            result = self.command_handler.execute_command(f"download_file {session_idx} {ret} {number_of_log}")
            
            ret = result.get('return', None)
            whom = result.get('whom', "")
            print(prettyjson(result))
            if whom:
                print(whom)
            print(f"{self.command_handler.get_current_context()[0]} > ", end='', flush=True)
            
        self.command_handler.execute_command(f"{session_idx} log get_log_path", next_step=output_conosle)
        return
    
    @default_title
    @process_hints
    def append_address(self, session_idx, address='', **kwargs):
        dst_address =  address if address else self.net.conn.addr
        
        self.command_handler.execute_command(f"{session_idx} log append_address {dst_address}")
        return
