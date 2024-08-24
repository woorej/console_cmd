from __future__ import annotations
from console.net.base_context import NetworkContext
from console.console_ast import Node, MultiTree
from console.template.title_template import default_title
from console.command_handler import CommandHandler, VariableManager
from console.template.utils import *
from console.template.table_template import *
from rev.prettyjson import prettyjson
import traceback
import os
import argparse
from console.utils import SessionTable, ShareData, print_console_message
from console.script_parser import Parser
from console.script_parser import Tokenizer
from console.utils import process_hints
from utils import establish_svc_connection
from console.multi_lingual import MultiLingual
from console.utils import eval_configs

class NshContext(NetworkContext):
    """
    step 1. set_management O
    step 2. get_svc_lists_from_mgmt O
    step 3. make_connection
    step 4. elect_current_svc_session
    step 5. get_remote_commands

    """
    name = 'main'
    lang_path = ['common', 'nsh', 'nsh']
    def __init__(self, multi_lang, apd_session, ssl_cert_data: bytes=None):
        self.multi_lang = multi_lang
        super().__init__()
        self._update_lang()
                
        self.management = None
        self.svc_list_from_mgmt = {} # ip lists of services
        self.current_svc_session = None # current session
        self.current_svc_session_db = {}
        self.zero_config_id = None
        
        self.added_services = set()
        self.service_index_mapping = {}
        
        self.ssl_cert_data = ssl_cert_data
        self.appended_svc_sessions = apd_session
        self.result_save_path = os.path.join(os.path.expanduser("~"), '.ai_fw', 'contents')
        os.makedirs(self.result_save_path, exist_ok=True)
    
    def _update_lang(self):
        super()._update_lang()
        command_table = self.multi_lang.get_commands_table(NshContext.lang_path)
        self.commands_table.update(command_table)
    
    @process_hints
    def change_language(self, lang, **kwargs):
        msg = self.multi_lang.load_lang_dictionary(lang)
        if 'Error' in msg:
            return msg
        
        self.command_handler.helper._change_language()
        return msg
    
    @process_hints
    def run_shell_script(self, session_idx, file_path, **kwargs):
        session, error = self._get_session(session_idx)
        if error:
            return error
        
        def _run_shell_script(output):
            dst_output = output.get('return', "")
            whom = output.get('whom', "")
        
            paths = dst_output.split("'")
            path = paths[1].strip() if len(paths) > 1 else ""
                
            if not path:
                msg = f"Invalid output value: {dst_output}"
                if whom:
                    msg = f"{whom}: {msg}"
                
                return msg
            
            self.command_handler.execute_command(f"0 system run_shell_script {path}") # 세션이 있는 경우에는 자동으로 출력 함수를 콜백으로 넣어준다.
        
        self.command_handler.execute_command(f"upload_file {session_idx} {file_path}", next_step=_run_shell_script)
            
    
    @process_hints
    def run_my_script(self, script_path, **kwargs):
        """
        Run comands from a script file line by line.
        """
        try:
            with open(script_path, 'r') as script_file:
                script = script_file.read()
            
            tokenizer = Tokenizer()
            tokens = tokenizer.tokenize(script)
            parser = Parser(self.command_handler)        
            parser.parse_and_execute(tokens)

        except FileNotFoundError:
            return f"Script file '{script_path}' not found."
        except Exception as e:
            return f"An error occurred while running the script: {traceback.format_exc()}"
    
    @process_hints
    def ping(self, session_idx, **kwargs):         
        if session_idx in self.appended_svc_sessions:
            session = self.appended_svc_sessions[session_idx]
            return "Ping was successful" if session.svc.test_conn() else "ping was not successful"
        else:
            return f"{session_idx} not in your session. please construct session first"
    
    
    @process_hints
    def set_adv_management(self, zero_id, **kwargs):
        """
        set zero config id and search mgmt
        """
        self.zero_config_id = f"_{zero_id}._udp.local."
        success, address = establish_svc_connection("0.0.0.0:0", "management", self.zero_config_id, max_attempts=2, ca_data=self.ssl_cert_data)
        if success:
            ip , port = address.split(':')
            new_conn = self._set_svc("management", ip, port, self.ssl_cert_data)
            self.management = new_conn
        else:
            print(f"Can not find SVC from {zero_id}")
    
    @process_hints
    def set_management(self, address, **kwargs): # mgmt 설정
        """
        set mgmt address
        """  
        try:
            ip, port = address.split(':')
        except Exception as e:
            print("Invalid input, format should be IP:PORT.")
            return None
        
        new_conn = self._set_svc("management", ip, port, self.ssl_cert_data)
        
        if new_conn:
            self.management = new_conn
            #self.svc_list_from_mgmt = self._assign_idx((["management", "192.168.1.7:40001"]))
        else:
            return "Management address setting was cancelled"
    
    @process_hints
    def test_two_params(self, param1, param2, **kwargs):
        return f"First Input: {param1}, Second Input: {param2}"
    
    @check_management # mgmt 확인
    def get_svc_lists_from_mgmt(self, **kwargs): # mgmt 에게 서비스 목록 요청
        """
        Garner svc addresses from management
        """
        try:
            request_dictionary = dict(
                cmd = "get_remote_lists" #"get_svc_lists_from_mgmt"
            )        
            res_msg = super()._handle_general_message(self.management, request_dictionary)
            management_entry = [self.management.name, self.management.addr]
            
            if 'Error' in res_msg:
                self.svc_list_from_mgmt = self._assign_idx(management_entry)
                return res_msg
            
            svc_lists = [management_entry] + res_msg
            self.svc_list_from_mgmt = self._assign_idx(svc_lists)
        except Exception as e:
            self.svc_list_from_mgmt = self._assign_idx(management_entry)
            return self.svc_list_from_mgmt
            
        return self.svc_list_from_mgmt
    
    def _assign_idx(self, svc_lists):
        sorted_items = sorted(svc_lists, key=lambda x: (x[0], x[1].split(":")[-1]))
        indexed_dict = {str(index): {item[0]: item[1]} for index, item in enumerate(sorted_items)}
        return indexed_dict
    
    @check_management
    def show_get_svc_lists_from_mgmt(self):
        return self.svc_list_from_mgmt
    
    def _fast_request_remote_command(self, service_name, service_address, index):
        svc_session = super()._try_connect_to_service(service_name, service_address, self.ssl_cert_data)
        if svc_session:
            self.appended_svc_sessions[index] = SessionTable(index, svc_session, service_name)
            self.current_svc_session, temp = self.appended_svc_sessions[index], self.current_svc_session  # elect_current_svc_session
            try:
                self.get_remote_commands()
            except Exception as e:
                self.current_svc_session = temp
                del self.appended_svc_sessions[index]
                print(e)
                return False
            
            self.service_index_mapping[service_address] = index
            return True
        return False
    
    def _add_service_by_name(self, svc_list_from_mgmt, appended_svc_sessions, service_index_mapping, name):
        for index, service in svc_list_from_mgmt.items():
            service_name, service_address = next(iter(service.items()))
            if service_name == name:
                index = service_index_mapping.get(service_address, str(len(appended_svc_sessions)))
                if self._fast_request_remote_command(service_name, service_address, index):
                    return True
        return False

    def _add_service_by_index(self, svc_list_from_mgmt, appended_svc_sessions, service_index_mapping, index):
        item = svc_list_from_mgmt.get(index)
        if item:
            service_name, service_address = next(iter(item.items()))
            index = service_index_mapping.get(service_address, str(len(appended_svc_sessions)))
            if self._fast_request_remote_command(service_name, service_address, index):
                return True
        return False
    
    @check_svc_lists_from_mgmt
    @process_hints
    def make_connection(self, identifier, **kwargs):
        """
        Append a service session by selecting a service from a list.
        """
        #print(f"Current remote session DB is '{self.appended_svc_sessions}'")
        #print(prettyjson(self.svc_list_from_mgmt))
        
        if identifier == "-1":
            return "Entered -1"

        if identifier.isdigit():
            added = self._add_service_by_index(self.svc_list_from_mgmt, self.appended_svc_sessions, self.service_index_mapping, identifier)
        else:
            added = self._add_service_by_name(self.svc_list_from_mgmt, self.appended_svc_sessions, self.service_index_mapping, identifier)
        
        if not added:
            print("Already added or not found")
        else:
            print(f"Service added or updated\n{self.show_appended_svc_sessions()}")
        
    def _show_appended_svc_sessions(self):
        formatted_sessions = {}
        for session_id, info in self.appended_svc_sessions.items():
            formatted_sessions[session_id] = {info.svc.name :  info.svc.addr}
        
        return formatted_sessions
    
    @check_make_connection
    def show_appended_svc_sessions(self, **kwargs): 
        return self._show_appended_svc_sessions()
    
    @check_make_connection
    @process_hints
    def elect_current_svc_session(self, session_idx, **kwargs):        
        print(prettyjson(self._show_appended_svc_sessions()))
                
        if session_idx in self.appended_svc_sessions: # {"0": {"client": "192.168.1.7:30000"}}
            self.current_svc_session = self.appended_svc_sessions[session_idx]
            return f"'{session_idx}' - {self.current_svc_session.svc.name} Remote is set"
        else:
            return "Invalid Input"
    
    @check_elect_current_svc_session
    def show_current_session(self, **kwargs):
        return { self.current_svc_session.idx :{self.current_svc_session.svc.name: self.current_svc_session.svc.addr}}


    @check_make_connection
    def get_remote_commands(self, **kwargs):
        payload = {
            "cmd": "show_all_contexts_and_commands", # 모든 명령어를 가져오도록 함
            "message": ""
        }
        res_msg = super()._handle_general_message(self.current_svc_session.svc, payload)
        
        if res_msg is not None:
            self.current_svc_session_db[self.current_svc_session.idx] = res_msg
            self.command_handler.helper.create_tree_from_structure(res_msg, self.command_handler.helper.current_node, self.current_svc_session.idx)
            #self.command_handler.helper.context_structure = self.command_handler.helper.build_structure()
            return res_msg
        else:
            return "Failed to get remote cmd lists"
    
def main():
    global command_handler
    
    fw_root = os.path.join(os.path.expanduser('~'), '.ai_fw')
    default_config_path = os.path.join(fw_root, "config", "nsh_config.json")
    
    parser = argparse.ArgumentParser(description='nsh configuration')
    parser.add_argument('-c', '--config', default=default_config_path, type=str, help='config json file path')
    parser.add_argument('-s', '--script', type=str, help='my script file path to run')
    parser.add_argument('-l', '--lang', type=str, help='language setting')
    parser.add_argument('-p', '--lang_path', type=str, help='language file path')
    parser.add_argument('-g', '--generator', action='store_true', help="config save")


    args = parser.parse_args()
    
    cfg = dict(
        secure=dict(
            msg_encryption = False,
            serializer = f"{fw_root}/lib/libAINcrypto.so",
            secure_comm = False,
            ssl_key =    f"{fw_root}/etc/server.key",
            ssl_cert =   f"{fw_root}/etc/server.crt"),
        config=dict(
            language = "en"
        )

    )
    
    if args.lang:
        cfg['config']['language'] = args.lang
        
    configs = {
        "cfg": {
            "config_path": args.config,
            "default_config_path": default_config_path,
			"default_config": cfg
		},
    }
    
    from pprint import pprint
        
    result = eval_configs(configs, args.generator)
    cfg = result['cfg']
    
    pprint(cfg)
    
    ssl_cert_data = None
    if 'secure_comm' in cfg and cfg['secure_comm']:
        cert_path = cfg.get('ssl_cert', None)
        if cert_path and os.path.isfile(cert_path):
            with open(cert_path, 'rb') as f:
                ssl_cert_data = f.read()
        else:
            print("Failed to start NSH with seacure communication: Not found certification file")
            print("Start NSH with insecure communication when Run Command or get logs from other svcs")
    
    share_data = ShareData()
    
    if ssl_cert_data:
        print("Run based on Secure Mode")

    from console.net.log_context import LogContext
    
    
    multi_lang = MultiLingual(args.lang_path, cfg['config']['language'])
    nsh = NshContext(multi_lang, share_data.appended_svc_sessions, ssl_cert_data)
    nsh_node = Node(nsh)
    
    log = LogContext(multi_lang, share_data.appended_svc_sessions, ssl_cert_data, cfg)
    log_node = Node(log)
    tree = MultiTree(nsh_node)
    nsh_node.add_child(log_node)
    
    variable_manager = VariableManager(nsh_node)
    command_handler = CommandHandler(tree, variable_manager)
    
    nsh._allocate_command_handler(command_handler)
    log._allocate_command_handler(command_handler)
    
    if args.script:
        nsh.run_my_script(args.script)
        return
    
    
    while True:
        try:
            command = input(command_handler.tap_completer.prompt)
            output = command_handler.execute_command(command)
            print_console_message(output, command_handler)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Unexpected Problem Occured - {traceback.format_exc()}")
            continue


if __name__=='__main__':
    main()