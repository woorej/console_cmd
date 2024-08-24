from console.template.title_template import default_title
from console.local.base_context import LocalContext
from rev.prettyjson import prettyjson
from lib import *
import traceback
from console.utils import *
from console.utils import process_hints

class ConfigContext(LocalContext):  
    lang_path = ['common', 'local', 'config']
    def __init__(self):
        """
        Initialize the base config with a list of available methods excluding those starting with an underscore '_' in their function names
        """
        super().__init__()
    
    def _update_lang(self):
        super()._update_lang()
        command_table = self.multi_lang.get_commands_table(ConfigContext.lang_path)
        self.commands_table.update(command_table)
    
    def _validate_address(self, addr):
        try:
            ip, port = addr.split(':')
            return ip, port
        except :
            return None
        
    @default_title
    def get_config(self, **kwargs):
        return prettyjson(self.instance.config)
    
    def _set_flag(self, flag, key_path):
        config, final_key = self._navigate_config(key_path)
        if config is None:
            return final_key

        if final_key in config:
            if flag in ['1', '0'] and isinstance(config[final_key], bool):
                config[final_key] = True if flag == '1' else False
                return f"{key_path} is changed to {config[final_key]}"
            else:
                return "Please input 1 or 0 or ensure it is boolean type"
        else:
            return f"Configuration doesn't have a '{final_key}' in the specified path"

    def _set_path(self, value, key_path):
        config, final_key = self._navigate_config(key_path)
        if config is None:
            return final_key

        if final_key in config:
            old_value = config[final_key]
            
            if isinstance(old_value, int) and value.isdigit():
                config[final_key] = int(value)
                return f"{key_path.replace('.', '->')}:{old_value} is changed to {config[final_key]}"
            elif isinstance(old_value, str):    
                config[final_key] = value
                return f"{key_path.replace('.', '->')}:{old_value} is changed to {config[final_key]}"
            else:
                return "Can not set path, ensure both config and target type of value"
        else:
            return f"Configuration doesn't have a '{final_key}' in the specified path"
        
    def _set_list(self, values, key_path):
        config, final_key = self._navigate_config(key_path)
        
        if config is None:
            return final_key

        if final_key in config:
            if isinstance(config[final_key], list):
                new_values = [item.strip() for item in values.split(',')]
                if isinstance(new_values, list):
                    old_values = config[final_key]  
                    config[final_key] = new_values 
                    return f"{key_path.replace('.', '->')} changed from {old_values} to {config[final_key]}"
                else:
                    return "Provided values must be a list."
            else:
                return f"Target configuration '{final_key}' is not a list type."
        else:
            return f"Configuration doesn't have a '{final_key}' in the specified path."
        
    def _navigate_config(self, key_path):
        keys = key_path.split('.')
        config = self.instance.config
        
        for key in keys[:-1]:
            if key in config:
                config = config[key]
            else:
                return None, f"No such configuration path '{key_path.replace('.', '->')}'" 
            
        final_key = keys[-1]
        return config, final_key 
    
    @default_title
    @process_hints
    def set_management_address(self, addr, **kwargs):
        result = self._validate_address(addr)
        
        if not result:
            return "Input should be <ip>:<port>"
        
        res1 = self._set_path(result[0], key_path='services.management.ip')
        res2 = self._set_path(result[1], key_path='services.management.port')
        
        return res1+'\n'+res2
    
    @default_title
    @process_hints
    def set_msg_encryption(self, flag, **kwargs):
        return self._set_flag(flag, key_path='msg_encryption')
    
    @default_title
    @process_hints
    def set_serializer(self, path, **kwargs):
        return self._set_path(path, key_path='serializer')
    
    @default_title
    @process_hints
    def set_secure_comm(self, flag, **kwargs):
        return self._set_flag(flag, key_path='secure_comm') 
    
    @default_title
    @process_hints
    def set_ssl_key(self, path, **kwargs):
        return self._set_path(path, key_path='ssl_key')
    
    @default_title
    @process_hints
    def set_ssl_cert(self, path, **kwargs):
        return self._set_path(path, key_path='ssl_cert')

    @default_title
    @process_hints
    def set_zeroconfig(self, identifier, **kwargs):
       return self._set_path(identifier, key_path='zeroconf.svc_type')
        
