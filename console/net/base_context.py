import random
import json
from lib.conn import conn_info
import os
from lib import sample_pb2
from lib import sample_pb2_grpc
from console.context import Context
from console.template.title_template import default_title
import traceback
import zipfile
from io import BytesIO
from console.utils import process_hints

class NetworkContext(Context):    
    lang_path = ['common', 'nsh', 'network']
    def __init__(self):
        """
        Initialize the base context with a list of available methods excluding those starting with an underscore '_' in their function names
        """
        super().__init__()
    
    def _update_lang(self):
        super()._update_lang()
        command_table = self.multi_lang.get_commands_table(NetworkContext.lang_path)
        self.commands_table.update(command_table)
        
    @default_title
    @process_hints
    def upload_file(self, session_idx, file_path, **kwargs):
        session, error = self._get_session(session_idx)
        if error:
            return error

        return_msg = self._send_file_message(session, file_path)
        return return_msg
    
    @default_title
    @process_hints
    def download_file(self, session_idx, file_path, number_of_files='', **kwargs):
        
        session, error = self._get_session(session_idx)
        if error:
            return error

        id, file_info = self._get_file_message(session, file_path, number_of_files)
        return file_info
    
    def _set_svc(self, svc_name, ip, port, ssl_cert_data: bytes=None):

        conn = conn_info(name=svc_name, ip=ip, port=port, ca_data=ssl_cert_data)
        
        if conn.test_conn():
            print(f"Successfully established connection.")
            print(f"Address has been set: '{conn.addr}'")
            return conn
        else:
            print(f"Connection to '{conn.addr}' failed.")
            return None
                
    # def _handle_failure(self, callback, message):
    #     if callback:
    #         callback(message, self.command_handler)
    #     else:
    #         print(message)
            
    def _handle_general_message(self, svc: conn_info, message):
        try:
            general_message = sample_pb2.GeneralMsg()
            general_message.id = "network_console"
            general_message.msg = json.dumps(message)
            
            response = svc.stub.Command(general_message)
            for resp in response:
                if resp is None:
                    return "Communication Failed."
                else:
                    response_dictionary = json.loads(resp.msg)
                    if 'message' in response_dictionary and response_dictionary['message'] == 'Fail':
                        return "Command failed"
                    else:
                        return response_dictionary['message']
                    
        except Exception as e:
            additonal_expt = traceback.format_exc()
            print(additonal_expt)    

    def _try_connect_to_service(self, svc_name, addr, ssl_cert_data=None):
        ip, port = addr.split(':')
        svc_session = conn_info(name=svc_name, ip=ip, port=port, ca_data=ssl_cert_data)
        if svc_session.test_conn():
            print("Successfully Connected")
            return svc_session
        else:
            return None
    
    def _run_command(self, idx, args, print_ouput, next_step=None):
        dash_index = args.find('-')

        if dash_index != -1:
            options = args[dash_index:]
            args = args[:dash_index].strip()
        
            verbose_flag = '-v' in options
        else:
            verbose_flag = False
            
        payload = self._make_payload(args)
        
        session = self.appended_svc_sessions[idx]
        result_msg = self._handle_general_message(session.svc, message=payload)
        whom = f"{session.name}_{session.idx}"
    
        return_value = {"return": result_msg, "whom": ""} 
        
        if verbose_flag == True: 
            return_value['whom'] = whom
            
        if next_step: # message
            next_step(return_value)
        else:
            print_ouput(return_value, self.command_handler)

    def _get_session(self, session_idx):
        if session_idx.isdigit() and session_idx in self.appended_svc_sessions:
            return self.appended_svc_sessions[session_idx], None
        else:
            return None, "Invalid session idx"
        
    def _make_payload(self, args, etc=""):
        payload = {
            "cmd": args,
            "message": {"count": etc}
        }
        return payload
    
    def _send_file_message(self, session, file_path):
        there_is_a_file =  os.path.exists(file_path)
        if not there_is_a_file:
            return f"File Doesn't Exists: {file_path}"
        
        payload = self._make_payload(file_path)
        file_message = sample_pb2.CFileMsg()
        file_message.id = "network_console"
        file_message.file_info = json.dumps(payload)
        
        def file_request_generator():
            with open(file_path, 'rb') as file:
                file_data = file.read()
            chunk_size = 1024 * 1024
            
            for i in range(0, len(file_data), chunk_size):
                file_message.data = file_data[i:i+chunk_size]
                yield file_message
        try:
            response = session.svc.stub.UploadFileCommand(file_request_generator())
            return response.msg
        except Exception as e:
            error_msg = f"Failed to send file {file_path}: {str(e)}"
            return error_msg
        
    def _get_file_message(self, session, file_path, number_of_files=''):
        payload = self._make_payload(file_path, number_of_files) # {"cmd": "/home/log.log", "message": ""}
        
        general_message = sample_pb2.GeneralMsg()
        general_message.id = "network_console"
        general_message.msg = json.dumps(payload)
        
        bytes_arr = bytearray(b'')
        response_stream = session.svc.stub.DownloadFileCommand(general_message)
        
        file_path = None
        for response in response_stream:
            if not file_path:
                id = response.id
                file_info = json.loads(response.file_info)
                file_path = file_info['file_path']

            bytes_arr.extend(response.data)
        
        if len(bytes_arr) == 0:
            return None, "Download Failed"
        
        local_path = os.path.join(os.path.expanduser('~'), '.ai_fw', 'contents')
        os.makedirs(local_path, exist_ok=True)
        
        compressed_file = BytesIO(bytes_arr)
        with zipfile.ZipFile(compressed_file, 'r') as zip_ref:
            zip_ref.extractall(local_path)
        
        extracted_files = zip_ref.namelist()
        file_info['file_paths'] = [os.path.join(local_path, name) for name in extracted_files]
                
        return id, file_info

    def _is_valid_port(self, port):
        try:
            port = int(port)
            return 0 < port < 65536
        except ValueError:
            return False

