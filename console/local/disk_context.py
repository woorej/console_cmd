from console.local.base_context import LocalContext
from console.utils import FileManager
from console.template.title_template import default_title
from console.utils import process_hints
import collections

class DiskContext(LocalContext):
    lang_path = ['common', 'local', 'disk']
    def __init__(self):
        super().__init__()
        self.file_manager = FileManager()
        self.local_path_option = None
        
    def _update_lang(self):
        super()._update_lang()
        command_table = self.multi_lang.get_commands_table(DiskContext.lang_path)
        self.commands_table.update(command_table)
        
    def _initialize_file_path(self):
        self.local_path_option = True
        print("Please set _initialize_file_path on your context")
        
    @default_title
    @process_hints
    def add_path_option(self, path, **kwargs):
        return self.file_manager.add_path_option(path)
    
    @default_title
    def show_path_options(self, **kwargs):
        if not self.local_path_option:
            self._initialize_file_path()
            
        return self.file_manager.show_path_options()
    
    @default_title
    @process_hints
    def delete_path_option(self, path_idx, **kwargs):
        if not self.local_path_option:
            self._initialize_file_path()
            
        return self.file_manager.delete_path_option(path_idx)
    
    @default_title
    @process_hints
    def show_file_lists(self, name_or_idx, **kwargs):
        if not self.local_path_option:
            self._initialize_file_path()
            
        return self.file_manager.show_file_lists(name_or_idx)
            
    @default_title
    @process_hints
    def delete_file(self, name_or_idx, file_idx, **kwargs):
        if not self.local_path_option:
            self._initialize_file_path()
            
        return self.file_manager.delete_file(name_or_idx, file_idx)    

    @default_title
    @process_hints
    def search_file(self, keyword, **kwargs):
        if not self.local_path_option:
            self._initialize_file_path()
        
        result = collections.defaultdict(list)
        for idx in self.file_manager.files.keys():
            search_results = self.file_manager.search_file(idx, keyword)
            for key, value in search_results.items():
                result[key].append(value)
            
        return result

    @default_title
    @process_hints
    def update_list_files(self, idx, **kwargs):
        if not self.local_path_option:
            self._initialize_file_path()

        return self.file_manager.update_list_files(idx) 
    
    @default_title
    @process_hints
    def move_file(self, name_or_idx, file_idx, dest_path, **kwargs):
        if not self.local_path_option:
            self._initialize_file_path()
            
        return self.file_manager.move_file(name_or_idx, file_idx, dest_path)
    

