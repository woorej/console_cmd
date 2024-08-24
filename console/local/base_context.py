from console.template.title_template import default_title
import os
from rev.prettyjson import prettyjson 
from log.log import *
from console.context import Context
import json
import traceback


class LocalContext(Context):
    lang_path = ['common', 'local', 'local']
    def __init__(self):
        """
        Initialize the base context with a list of available methods excluding those starting with an underscore '_' in their function names
        """
        super().__init__()
        self.default_path = os.path.join(os.path.expanduser('~'), '.ai_fw', 'contents')
        os.makedirs(self.default_path, exist_ok=True)
    
    def _update_lang(self):
        super()._update_lang()
        command_table = self.multi_lang.get_commands_table(LocalContext.lang_path)
        self.commands_table.update(command_table)
    
    def _validate_keys(self, data, required_keys):
        missing_keys = [key for key in required_keys if key not in data]
        if missing_keys:
            return False, f"Missing keys in data: {', '.join(missing_keys)}"
        return True, None
    
    def _load_data_and_validate(self, directory, required_keys):
        data, error = self._check_and_read(directory)
        if error:
            return None, error

        valid, error = self._validate_keys(data, required_keys)
        if not valid:
            return None, error

        return data, None
    
    def _check_and_read(self, path):
        if not os.path.isfile(path):
            return None, f"The file {path} does not exist."
        try:
            with open(path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                return data, None
        except json.JSONDecodeError:
            return None, f"The file {path} is not a valid JSON file"
        except Exception as e:
            err_traceback = traceback.format_exc()
            return None, f"An error occurred: {err_traceback}"
        
    def _check_and_save(self, data, file_name):
        if not data or len(data) == 0:
            return "Data Not Found"
        
        file_path = os.path.join(self.default_path, file_name)
        
        with open(file_path, 'w') as f:
            f.write(prettyjson(data))
            
        return f"Saved file: {file_path}"
    
    def _check_and_show(self, data):
        if not data or len(data) == 0:
            return "Data Not Found"

        return prettyjson(data)
    
    def _toggle_flag(self, flag_name: str, new_value: bool, flag_desc: str) -> str:
        """
        Toggle a boolean flag and return a message indicating the change.
        """
        current_flag_state = getattr(self.instance, flag_name)
        if current_flag_state == new_value:
            return f"{flag_desc} Flag is already {'On' if current_flag_state else 'Off'}."
        else:
            setattr(self.instance, flag_name, new_value)
            return f"{flag_desc} Flag is changed from {'On' if current_flag_state else 'Off'} to {'On' if new_value else 'Off'}."

    def _get_instance_attribute(self, attr_path: str):
        """Given an attribute path, return the value of the attribute from self.instance."""
        attrs = attr_path.split('.')
        attr_value = self.instance
        try:
            for attr in attrs:
                attr_value = getattr(attr_value, attr, None)
                if attr_value is None:
                    break
        except AttributeError:
            return None
        return attr_value
    
    def _set_svc_addr(self, instance, svc: str):
        user_input = input(f"enter the {svc} IP and port separated by a space: ")
        ip, port = user_input.split()
        
        if hasattr(instance, svc):
            svc_instance = getattr(instance, svc)
            tmp = svc_instance.addr
            svc_instance.set_address(ip, port)
            print(f"{svc} address changed from {tmp} to {svc_instance.addr}")
        else:
            print(f"{type(instance).__name__} has no attribute '{svc}'\ntry again.")


    def _common_edit(self, db_class, identifier, directory, required_keys, update_mapping):
        data, error = self._check_and_read(directory)
        
        if error:
            return error
        
        missing_keys = [key for key in required_keys if key not in data]
        
        if missing_keys:
            return f"Missing keys in data: {', '.join(missing_keys)}"
        
        db = db_class(self.instance.dbinfo)
        
        update_params = {update_mapping[key]: data[key] for key in required_keys if key in data}
        
        for key, param in update_mapping.items():
            if key not in required_keys and key in data:
                update_params[param] = data[key]
        
        message = db.update(identifier, **update_params)
        return message
    
    def _common_delete(self, db_class, identifier):
        db = db_class(self.instance.dbinfo)
        message = db.delete(identifier)
        return message
    
    def _common_add(self, db_class, file_path, required_keys, create_mapping):
        data, error = self._check_and_read(file_path)
        
        if error:
            return error
        
        missing_keys = [key for key in required_keys if key not in data]
        
        if missing_keys:
            return f"Missing keys in data: {', '.join(missing_keys)}"
        
        db = db_class(self.instance.dbinfo)
        
        create_params = {create_mapping[key]: data[key] for key in required_keys if key in data}

        for key, param in create_mapping.items():
            if key not in required_keys and key in data:
                create_params[param] = data[key]

        message = db.create(**create_params)
        return message