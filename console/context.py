from typing import List, Dict
from rev.prettyjson import prettyjson 

class Context():
    lang_path = ['common', 'context']
    def __init__(self):
        """
        Initialize the base context with a list of available methods excluding those starting with an underscore '_' in their function names
        """
        self._initialize_methods()
    
    def _update_lang(self):
        self.commands_table = {}
        command_table = self.multi_lang.get_commands_table(Context.lang_path)
        self.commands_table.update(command_table)
        
    def _initialize_methods(self):
        self.methods = [method for method in dir(self)
                        if callable(getattr(self, method)) and not method.startswith('_')]

    def _execute_command(self, command: str, command_handler):
        if command in self.methods:
            return getattr(self, command)()
        elif not command_handler.change_mode(command):
            print(f"'{command}' command is not available in {command_handler.get_current_context()[0]} context")
    
    def _allocate_command_handler(self, command_handler_obj):
        self.command_handler = command_handler_obj
    
    def __getattr__(self, attr): # if  name attribute doesn't exists
        if attr == 'name':
            return self.__class__.__name__.lower().replace('context', '')
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{attr}'")

    # def _process_input(self, parameters=[], hints=[]):
    #     basket = []
        
    #     for i in range(len(hints)):
    #         prompt = hints[i]
    #         current_value = parameters[i] if i < len(parameters) else None

    #         if not current_value:
    #             current_value = self._auto_input(prompt)
                
    #         basket.append(current_value)
            
    #     # hints는 1개인데 hints에 관한 파라미터를 우선 순서로 담고 이후 1개이상의 변수를 담은경우
    #     for param in parameters[len(hints):]:
    #         basket.append(param)
            
    #     return basket
    
    # def _auto_input(self, prompt):
    #     return input(f"{prompt} ")
    
    def helps(self, **kwrags) -> Dict[str, str]:
        """
        Returns a dictionary with command names as keys and their descriptions as values,
        dynamically reflecting the commands_table of the current instance.
        """
        if hasattr(self, 'commands_table'):
            return prettyjson(self.commands_table)
        else:
            return {"error": "No commands_table found"}
        