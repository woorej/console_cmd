from console.template.title_template import default_title
from console.local.base_context import LocalContext
import os, sys, time
import os
from rev.prettyjson import prettyjson 
import threading
from console.utils import process_hints

class RootContext(LocalContext):
    lang_path = ['common', 'local', 'root']
    def __init__(self) -> None:
        super().__init__()

    def _update_lang(self):
        super()._update_lang()
        command_table = self.multi_lang.get_commands_table(RootContext.lang_path)
        self.commands_table.update(command_table)
                
    def _restart_svc(self):
        time.sleep(2)
        os.makedirs(os.path.dirname(self.instance.config_path), exist_ok=True)

        with open(self.instance.config_path, 'w') as f: # config_path라는 Attribute를 가지고 있어야 함 -> PID로 생성
            f.write(prettyjson(self.instance.config)) # config라는 Attribute를 가지고 있어야 함
            
        self.instance.log.debug(f"Saved configuration before restart: {self.instance.config_path}")

        script_path = os.path.abspath(sys.argv[0])
        args_list = [script_path, '-c' , self.instance.config_path]
        self.instance.log.debug(f"{self.instance.my_name} will be restart, => executable: {sys.executable} {args_list}")
        os.execl(sys.executable, sys.executable, *args_list)
    
    @default_title
    def restart(self, **kwargs):
        self._pre_restart()
        restart_thread = threading.Thread(target=self._restart_svc)
        restart_thread.start()
        return "svc will restart after 2 seconds."
    
    def read_property(self, *attr_names, **kwargs):
        current_obj = self.instance
        for attr_name in attr_names:
            try:
                current_obj = getattr(current_obj, attr_name)
            except AttributeError:
                return f"Attribute '{attr_name}' not found in object '{current_obj.__class__.__name__}'."
        
        return f"{current_obj}"
    
    def show_all_attribute(self, **kwargs):
        """
        Prints all attributes of the instance along with their values.
        """
        attributes = {}
        for attr in dir(self.instance):
            if not attr.startswith('_'):
                value = getattr(self.instance, attr)
                attributes[attr] = value
        return f"{prettyjson(attributes)}"
    
    def is_object_and_show_attributes(self, *attr_names, **kwargs):
        """
        Checks if the attribute with the given name is an object, and if so,
        returns all its attributes.
        """
        current_object = self.instance
        try:
            for attr_name in attr_names:
                current_object = getattr(current_object, attr_name)
            
            if hasattr(current_object, '__dict__'):
                return {attr: getattr(current_object, attr) for attr in dir(current_object) if not attr.startswith('_')}
            else:
                return f"The attribute '{attr_names[-1]}' is not an object or does not have '__dict__'."
        
        except AttributeError:
            return f"Attribute path {' -> '.join(attr_names)} not found in object '{self.instance.__class__.__name__}'."