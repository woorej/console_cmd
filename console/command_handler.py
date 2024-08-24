import readline
import inspect
import threading
import json
import traceback
import os
import sys
from inspect import Parameter
# from distutils.util import strtobool
from console.utils import process_input
import zipfile
from io import BytesIO
from console.console_ast import Node, MultiTree
from console.utils import clean_input
from typing import List
import readline
import shutil
from console.utils import print_console_message_for_thread

from lib import sample_pb2
from lib import sample_pb2_grpc

from log.log import *

def _download_file_command(request, id, log):
    file_message = sample_pb2.CFileMsg()
    
    file_message.id = id
    request_file_info = json.loads(request.msg)
    file_path = request_file_info['cmd']
    
    number_of_files = request_file_info['message']['count']
    directory = os.path.dirname(file_path)
    base_name = os.path.basename(file_path)
    
    file_list = []
    
    if os.path.exists(file_path):
        file_list.append(file_path)
    
    if number_of_files and number_of_files.isdigit():
        number_of_files = int(number_of_files)
        
        all_files = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.startswith(base_name) and os.path.join(root, file) != file_path:
                    full_path = os.path.join(root, file)
                    all_files.append(full_path)
        
        all_files.sort()
        
        additional_files = all_files[:number_of_files - 1]
        file_list.extend(additional_files)
    
    try:
        if not file_list:
            file_message.file_info = json.dumps({
                'file_path': file_path,
                'message': 'No files found.'
            })
            file_message.data = b''
            yield file_message
            return
        
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for file in file_list:
                zip_file.write(file, os.path.basename(file))
        
        zip_buffer.seek(0)
        compressed_file = zip_buffer.read()
        
        file_message.file_info = json.dumps({
            'file_path': file_path,
            'message': f'Compressed {len(file_list)} files.'
        })
        
        chunk_size = 1024 * 1024
        for i in range(0, len(compressed_file), chunk_size):
            file_message.data = compressed_file[i:i+chunk_size]
            yield file_message

    except Exception as e:
        log.error(f"Cannot Send File {traceback.format_exc()}")
            

def _upload_file_command(request_iterator, id, log):
    bytes_arr = bytearray(b'')
    file_path = None
    
    try:
        for request in request_iterator:
            if not file_path:
                file_info = json.loads(request.file_info)
                file_path = file_info['cmd']
                file_name = os.path.basename(file_path)
                dst_path = os.path.join(os.path.expanduser('~'), '.ai_fw', 'contents')
                os.makedirs(dst_path, exist_ok=True)
                dst_file_path = os.path.join(dst_path, file_name)
            
            bytes_arr.extend(request.data)    
                
        with open(dst_file_path, 'wb') as f:
            f.write(bytes_arr)
            
        return sample_pb2.GeneralMsg(id=id, msg=f"File uploaded '{dst_file_path}' successfully in the {id}.")
    
    except Exception as e:
        log.error(f"Error while uploading file: {traceback.format_exc()}")
        return sample_pb2.GeneralMsg(id=id, msg=str(e))


def _command(request, command_handler, id, log):
    general_message = sample_pb2.GeneralMsg()
    general_message.id = id
    request_dc = json.loads(request.msg)
    response_dictionary = {}
    
    try:
        if request.id == "network_console":
            response_dictionary['cmd'] = request_dc['cmd']
            response_dictionary['message'] = command_handler.execute_command(response_dictionary['cmd'])
            
        else:
            response_dictionary['cmd'] = request_dc['cmd']
            response_dictionary['message'] = "Fail"
        
        general_message.msg = json.dumps(response_dictionary)
        
        yield general_message
    
    except Exception as e:
        log.error(f"Can not execute command {traceback.format_exc()}")
        response_dictionary['message'] = str(traceback.format_exc())
    
    general_message.msg = json.dumps(response_dictionary)
    yield general_message

class VariableManager:
    def __init__(self, name_space):
        self.variables = {}
        self.name_space = {"context": name_space.context, **self.variables}
    
    def set_variable(self, var_name, var_value):
        try:
            self.variables[var_name] = eval(var_value, {"__builtins__": __builtins__}, self.name_space)
            self.name_space.update(self.variables)
            return f"Variable '{var_name}' set to '{self.variables[var_name]}'"
        except Exception as e:
            return f"Error setting variable '{var_name}': {e}"
    
    def get_variable(self, var_name):
        if var_name in self.variables:
            return f"{self.variables[var_name]}"
        else:
            return f"Variable '{var_name}' not found"
        
    def replace_variables(self, parts):
        for i, part in enumerate(parts):
            if part.startswith('$'):
                var_name = part[1:]  # Remove the $ prefix
                if var_name in self.variables:
                    parts[i] = self.variables[var_name]
                else:
                    return f"Variable '{var_name}' not found"
                
            # elif part == '_$':
            #     var_name = part
            #     if var_name in self.variables:
            #         parts[i] = self.variables[var_name]
            #     else:
            #         return f"Variable '{var_name}' not found"
        return parts
    
class TapCompleter:
    def __init__(self, helper, command_handler):
        self.command_handler = command_handler
        self.helper = helper
        self.key_bind()
    
    @property
    def prompt(self):
        return f"{self.command_handler.get_current_context()[0]} > "

    def completer(self, text, state):
        line = readline.get_line_buffer()
        split_lines = line.split()
        options = []
        
        if split_lines and split_lines[0] == 'help': # help로 시작하는 경우 제거
            split_lines.pop(0)  # Remove 'help' to handle the rest of the command
            
        if not split_lines: # 아무것도 입력하지 않은 경우
            commands = self.helper.get_context_commands(self.helper.current_node)
            options = sorted(commands.keys())
        else: # 어떤 입력이 있었던 경우
            temp_node, command_to_execute, context_changed, _, _ = self.command_handler.parse_regular_command(self.helper.current_node, split_lines)
            
            if command_to_execute: # 마지막 입력이 명령어라면
                help_table = self.helper.get_context_commands(temp_node)
                help_info = help_table.get(command_to_execute, {})
                usage = help_info.get('usage', [])
                options = []
                if usage:
                    options = [f"{usage}", ""]
            else: # 컨텍스트 또는 입력중인 명령어라면
                # 명령어와 컨텍스트 이름이 동일한 경우에 대해서
                # if temp_node and temp_node.context.name == text: # 컨텍스트와 명령어가 겹치는 부분이 있다면? ex) log 컨텍스트안에 log_status란 명령어가 있는데 log(탭) 을 한 경우 이는 로그 컨텍스의 명령어를 보여줘야 하는데 log로 시작하는 명령어가 있어서 자동완성이 되어버림. 명령어 리스트만을 보여줘야함
                #     options = sorted(self.helper.search_node(split_lines)[0])
                # #     if len(split_lines) > 1 and temp_node.context.name == split_lines[-2]: # 근데 log log(탭) 을 한 경우 이때 첫번째 log는 컨텍스트 두번째 log는 명령어이기 때문에 startwith(text)가 되야한다.
                # #         options = [cmd for cmd in options if cmd.startswith(text)]
                # else: # 명령어와 컨텍스트 이름이 다른 경우   
                #     options = sorted(self.helper.search_node(split_lines)[0])
                #     options = [cmd for cmd in options if cmd.startswith(text)]
                
                options = sorted(self.helper.search_node(split_lines)[0])
                
                if not (temp_node and temp_node.context.name == text):
                    options = [cmd for cmd in options if cmd.startswith(text)]
                
        return options[state] if state < len(options) else None
    
    def display_matches_hook(self, substitution, matches, longest_match_length):
        print()
        help_parameter = False
        
        terminal_width = shutil.get_terminal_size((80, 20)).columns

        column_width = longest_match_length + 2

        num_columns = max(1, terminal_width // column_width)

        for i, match in enumerate(matches):
            if '' == match or readline.get_line_buffer() == match.split(' ')[0]:
                print(match, end='')
                help_parameter = True
            else:
                print(match.ljust(column_width), end='' if (i + 1) % num_columns else '\n')
        
        if len(matches) % num_columns: # # 명령어가 한 줄에 다 채워지지 않았다면 한칸 띄움
            print()  

        if help_parameter:
            print()
            
        print(self.prompt, readline.get_line_buffer(), sep='', end='')
        sys.stdout.flush()
        
    def key_bind(self):
        readline.set_history_length(20)
        readline.set_completer(self.completer)
        readline.set_completion_display_matches_hook(self.display_matches_hook)
        readline.parse_and_bind('tab: complete')
        
class Helper:
    def __init__(self, tree):
        self.tree = tree
        self.current_node = tree.root
        #self.context_structure = self.build_structure()
        self.context_structure = self.build_structure(self.tree.root)

    def build_structure(self, node: Node=None):
        # if not node:
        #     self.context_structure = {}
        #     node = self.tree.root
                    
        context_name = self.tree._get_context_name(node.context).lower()
        
        structure = {
            "commands": self.extract_commands(node),
            "subcontexts": self.extract_subcontexts(node)
        }
        
        return {context_name: structure}
    
    def extract_commands(self, node):
        commands = {}
        if hasattr(node.context, 'commands_table'):
            commands_table = node.context.commands_table
            common_prompt = commands_table.get('_command', {}).get('common_prompt', '')
            
            for cmd_name, details in node.context.commands_table.items():
                if cmd_name == '_command':
                    continue
                
                src_hint = details.get('hints', [])
                if common_prompt and src_hint:
                    dst_hints = [f"{common_prompt} {h}" for h in src_hint if common_prompt not in h]
                else:
                    dst_hints = src_hint
                
                commands[cmd_name] = {
                    "description": details['description'],
                    "usage": details['usage'],
                    "data_type": details['data_type'],
                    "hints": dst_hints
                }
        return commands
    
    def extract_subcontexts(self, node):
        sub_contexts = {}
        for child in node.children:
            child_name = self.tree._get_context_name(child.context).lower()
            sub_contexts[child_name] = self.build_structure(child)[child_name]
            
        return sub_contexts
    
    def get_context_commands(self, node=None):
        if not node:
            node = self.current_node
            
        commands = self.extract_commands(node)
        return commands
    
    def update_node(self, node):
        self.current_node = node
            
    def search_node(self, tokens: List[str], node=None):
        if not node:
            node = self.current_node

        result = []
        last_node = None
        last_command = None

        def dfs(current_node, index):
            nonlocal last_node, last_command
            if index == len(tokens):
                commands = self.get_context_commands(current_node)
                result.extend(commands.keys())
                last_node = current_node
                return

            next_token = tokens[index]
            next_node = self._find_child_by_name(current_node, next_token)

            if next_node is None:
                commands = self.get_context_commands(current_node)
                last_node = current_node
                last_command = next_token
                result.extend(commands.keys())
                return

            last_command = next_token
            dfs(next_node, index + 1)

        dfs(node, 0)
        return result, last_node, last_command
        
    def _find_child_by_name(self, node, name):
        for child in node.children:
            if self.tree._get_context_name(child.context).lower() == name:
                return child
        return None
        
    def create_tree_from_structure(self, structure, current_node, name_of_root):
        
        def dfs(parent_node, sub_structure):
            for context_name, contents in sub_structure.items():
                sub_node = Node(type(context_name, (object,), {'name': context_name, 'commands_table': contents['commands'], 'methods': list(contents['commands'])}))
                parent_node.add_child(sub_node)
                dfs(sub_node, contents['subcontexts'])
            
            
        root_node = Node(type(name_of_root, (object,), {'name': name_of_root, 'commands_table': structure['main']['commands'], 'methods': list(structure['main']['commands'])}))
        dfs(root_node, structure['main']['subcontexts'])
        

        processed_help_table = self.build_structure(root_node)
        
        self.context_structure['main']['commands'].update(
            { 
                name_of_root:{
                    "description": f"change context to {name_of_root} context",
                    "usage": name_of_root,
                    "data_type": "none",
                    "hints": []
                }
            }
        )
        
        current_node.context.commands_table[name_of_root] = {
            "description": f"change context to {name_of_root} context",
            "usage": name_of_root,
            "data_type": "none",
            "hints": []
        }
        
        current_node.add_child(root_node)
        self.context_structure['main']['subcontexts'].update(processed_help_table)
        return
    
    def get_contexts_path(self):    
        result = []
        node = self.current_node
        
        def dfs(current_node):
        
            if current_node.context.name == 'main':
                return
            
            result.append(current_node.context.name)
            
            if current_node.parent:
                dfs(current_node.parent)
            
        dfs(node)
        return list(reversed(result))
        
    
    def find_session_index_path(self, session_index, node, path):
        """
        현재 노드에서 세션 인덱스를 찾고 경로를 반환
        """
        context_name = self.tree._get_context_name(node.context)
        if context_name == session_index:
            path.append(context_name)
            return True

        for child in node.children:
            if self.find_session_index_path(session_index, child, path):
                path.append(context_name)
                return True
        
        return False
    
    def _change_language(self):
        def dfs(node):
            if not node:
                return
            
            for child in node.children:
                dfs(child)
            
            #if hasattr(node.context, '_update_lang'):
            node.context._update_lang()
        
        dfs(self.tree.root)

class AbsCommands:
    def __init__(self, handler):
        self.handler = handler
        self.helper = handler.helper
        self.tree = handler.tree
        self.commands = {
            'exit': self.exit,
            'terminate': self.terminate,
            'where': self.where_am_i,
            'help': self.handle_help,
            'init': self.initialize_context,
            'show_all_contexts_and_commands': self.show_all_contexts_and_commands
        }

    def exit(self, parts=None):
        if self.helper.current_node.parent:
            parent_context_name = self.tree._get_context_name(self.helper.current_node.parent.context)
            self.helper.update_node(self.helper.current_node.parent)
            return f"Returned to {parent_context_name} context"
        else:
            return "Already at the root context. Cannot exit further. If you would like to stop ccmd, input terminate"
    
    def terminate(self, parts=None):
        sys.exit()

    def where_am_i(self, parts=None):
        return f"You are in {self.tree._get_context_name(self.helper.current_node.context)} context."
    
    def handle_help(self, parts=None):
        if len(parts) == 2:
            commands = self.helper.get_context_commands(self.helper.current_node)
            usage = commands.get(parts[1], {}).get('usage', '')
            return usage if usage else f"No help available for '{parts[1]}'"
                            
        return "Help command requires more arguments."

    def initialize_context(self, parts=None):
        self.helper.update_node(self.tree.root)
        current_context_name = self.tree._get_context_name(self.helper.current_node.context)
        return f"Initialized to the root context: {current_context_name}"
    
    def show_all_contexts_and_commands(self, parts=None):
        return self.helper.context_structure

    def get_command(self, command_name):
        return self.commands.get(command_name, None)



class CommandHandler:
    """
    A class to handle commands and manage modes in a command-driven application.
    """
    
    def __init__(self, tree: MultiTree, variable_manager: VariableManager):
        self.tree = tree
        self.helper = Helper(self.tree)
        self.tap_completer = TapCompleter(self.helper, self)
        self.special_commands = AbsCommands(self)
        self.has_session_db = hasattr(self.tree.root.context, 'current_svc_session_db')
        self.variable_manager = variable_manager
        #self.variable_manager = VariableManager(self.helper)
    
    def get_current_context(self):
        """
        use at command_handler loop
        """
        current_context_name = self.tree._get_context_name(self.helper.current_node.context)
        return current_context_name, self.helper.current_node.context
        
    def change_mode(self, mode_name):
        children_contexts = self.tree.get_children_contexts(self.helper.current_node)
        
        if mode_name in children_contexts:
            new_node = children_contexts[mode_name]
            self.helper.update_node(new_node)
            return True
        else:
            return False
        
    def _get_session_index_and_args(self, parts):
        session_index = ''
        args = []
        session_db = self.tree.root.context.current_svc_session_db
        
        # 현재 로그 컨텍스트에 있는데, 명령어가 이렇게 온다면 example [0, 'log', 'get_log_path]
        context_paths = self.helper.get_contexts_path()  # 현재 위치에서 모든 부모 노드의 경로를 가져온다. (비어있다면 main 경로에 있다)
        
        if context_paths and context_paths[0] in session_db.keys(): # 세션 인덱스 안에 있는 경우
            session_index = context_paths[0]
            args.extend(context_paths + parts)
        #elif not context_paths and parts[0] in session_db.keys():  # 세션 인덱스 밖에 있는 경우는 어차피 전체경로를 날려야한다. main 컨텍스트에 있고 입력한 값이 세션 인덱스 디비안에 있으면 ['system' 'get_disk_info'] -> ['0' 'system' 'get_disk_info']
        elif parts[0] in session_db.keys():  # 세션 인덱스 밖에 있는 경우는 어차피 전체경로를 날려야한다. main 컨텍스트에 있고 입력한 값이 세션 인덱스 디비안에 있으면 ['system' 'get_disk_info'] -> ['0' 'system' 'get_disk_info']
            session_index = parts[0]
            args.extend(parts)
        # 로그 컨텍스트에 있는데 0 log get_log_path를 한 경우
        return session_index, args
    

    def _session_execute_command(self, session_index, args, next_step):
        _, last_node, last_command = self.helper.search_node(args, self.tree.root)
        help_table = self.helper.get_context_commands(last_node)

        if last_command in help_table or self.special_commands.get_command(last_command):
            #command_info = help_table[last_command]
            command_info = help_table.get(last_command, {})
            hints = command_info.get('hints', [])
            dst_parameters = ' '.join(args[1:])
            if hints:
                src_parameters = process_input(hints=hints, parameters=args[args.index(last_command) + 1:])
                dst_parameters = ' '.join(args[1:args.index(last_command) + 1] + src_parameters)

            func = getattr(self.tree.root.context, '_run_command')
            thread = threading.Thread(target=func, args=(session_index, dst_parameters, print_console_message_for_thread, next_step))
            thread.start()
            return f"Successfully sent to {session_index}: {dst_parameters}"
        else:
            return f"Invalid Commands for session `{session_index}`, Commands: {args}"
    
    def parse_regular_command(self, node, parts):
        temp_node = node
        command_to_execute = False
        context_changed = False

        for part in parts:
            if part in self.tree.get_children_contexts(temp_node):
                temp_node = self.tree.get_children_contexts(temp_node)[part]
                context_changed = True
            elif part in temp_node.context.methods:
                command_to_execute = part
                break
            else:
                return None, None, None, None, f"Error: '{part}' is not a valid context or command. {self.special_commands.where_am_i()}"

        args = []
        if command_to_execute:
            args.extend(parts[parts.index(command_to_execute):])

        return temp_node, command_to_execute, context_changed, args, None

    def get_parameter_count(self, func):
        sig = inspect.signature(func)
        parameters = sig.parameters.values()
        total_param = sum(1 for p in parameters if p.kind not in (Parameter.VAR_POSITIONAL, Parameter.VAR_KEYWORD))
        return total_param

    def execute_command(self, command, next_step=None):
        if not command.strip():
            return "No command entered"
        
        parts = [clean_input(arg) for arg in command.split()]
        args = []
        

        # 특수 명령어의 입력인 경우 >>>>>
        abs_command_func = self.special_commands.get_command(parts[0])
        if abs_command_func:
            return abs_command_func(parts)
        # <<<<<
    
        # Check if the command is a variable name
        if len(parts) == 1 and parts[0].startswith('$'):
            var_name = parts[0][1:]  # Remove the $ prefix
            return self.variable_manager.get_variable(var_name)
        
        # Replace variables in the command with their values
        parts = self.variable_manager.replace_variables(parts)
        if isinstance(parts, str):  # Error message returned from replace_variables
            return parts
    
        # dynamic vairables
        # if '=' in command:
        #     var_name, var_value = map(str.strip, command.split('='))
        #     return self.variable_manager.set_variable(var_name, var_value)
        
        if '=' in parts:
            equals_index = parts.index('=')
            var_name = parts[equals_index - 1].strip()
            var_value = parts[equals_index + 1].strip()
            return self.variable_manager.set_variable(var_name, var_value)
        # <<<<<
        
        
        # session index의 명령인 경우 >>>>>
        if self.has_session_db:
            session_index, args = self._get_session_index_and_args(parts)
            
            if session_index:
                if len(parts) == 1 and parts[0] in self.tree.get_children_contexts(self.helper.current_node):  # 세션 인덱스만 입력한 경우, 컨텍스트 변경으로 처리
                    if not self.change_mode(parts[0]):
                        return f"Failed to change mode to {parts[0]}"
                    current_context_name = self.tree._get_context_name(self.helper.current_node.context)
                    return f"Changed to {current_context_name} mode"
                
                return self._session_execute_command(session_index, args, next_step)
        # <<<<<<

        
        # Regular command parsing >>>>
        temp_node, command_to_execute, context_changed, args, error_message = self.parse_regular_command(self.helper.current_node, parts)
        
        if error_message:
            return error_message
        
        # Change context only if there is no commands to execute
        if context_changed and not command_to_execute: 
            for part in parts:
                if not self.change_mode(part):
                    return f"Failed to change mode to {parts}"
                current_context_name = self.tree._get_context_name(self.helper.current_node.context)
            return f"Changed to {current_context_name} mode"
        
        
        # Regular command execution
        elif command_to_execute:
            func = getattr(temp_node.context, command_to_execute)
            
            help_table = self.helper.get_context_commands(temp_node)
            help_command = help_table.get(args.pop(0), {})
            hints = []
            
            if not help_command:
                return f"help doesn't have '{command_to_execute}' command"
            else:
                hints = help_command.get('hints', [])
            
            kwargs = {}
            kwargs['hints'] = hints
            kwargs['total_param'] = self.get_parameter_count(func)
            
            output = func(*args, **kwargs)
            
            if next_step:
                return next_step(output)
            
            return output
            
        
        


    