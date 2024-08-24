from console.local.base_context import LocalContext
from console.template.title_template import default_title
from rev.prettyjson import prettyjson
from lib import *


class InpContext(LocalContext):
    lang_path = ['common', 'local', 'inp']
    def __init__(self):
        super().__init__()
    
    def _update_lang(self):
        super()._update_lang()
        command_table = self.multi_lang.get_commands_table(InpContext.lang_path)
        self.commands_table.update(command_table)
    