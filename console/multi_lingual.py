import json
import pkg_resources
import os
from typing import List
from copy import deepcopy

class MultiLingual:
    def __init__(self, help_path=None, language='en'):
        
        self.src_dir = os.path.join(os.path.expanduser('~'), '.ai_fw', 'data', 'lang')
        
        if not help_path:
            help_path = os.path.join(self.src_dir, f"nsh_{language}.json")
            
        if not os.path.exists(help_path):
            print(f"File Not Found Error, Can not found: {help_path}")
            help_path = os.path.join(self.src_dir, f"nsh_en.json")
            print(f"Default Help path has been applied: {help_path}")
            #raise FileNotFoundError(f"Can not found: {help_path}")
            
        with open(help_path, 'r', encoding='utf-8') as f:
            help_data = json.load(f)
        
        self.help_data = help_data
        
    def get_commands_table(self, keys: List[str]):
        help_data = deepcopy(self.help_data)
        for key in keys:
            help_data = help_data[key]
        
        return help_data
    
    def load_lang_dictionary(self, language: str):
        help_path = os.path.join(self.src_dir, f"nsh_{language}.json")
        
        if not os.path.exists(help_path):
            return f"Error {help_path} does not exists"
        
        with open(help_path, 'r', encoding='utf-8') as f:
            help_data = json.load(f)

        self.help_data = help_data
        return f"Successfully changed langauge to {language}"

if __name__ == '__main__':
    path = None
    lang = "en"
    m = MultiLingual(path, lang)
    