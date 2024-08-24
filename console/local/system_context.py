
from console.template.title_template import default_title
from console.local.base_context import LocalContext
from rev.prettyjson import prettyjson
from console.local.help import HelpSystemContext
from utility.lib import *
import traceback
from console.utils import *
import psutil
from typing import Dict, List
import subprocess
import time
from console.utils import display_gpu_info
from datetime import datetime, timedelta
from console.utils import process_hints

class SystemContext(LocalContext):
    lang_path = ['common', 'local', 'system']
    
    def __init__(self):
        super().__init__()
        self.file_path = os.path.join(os.path.expanduser('~'), '.ai_fw', "contents")
    
    def _update_lang(self):
        super()._update_lang()
        command_table = self.multi_lang.get_commands_table(SystemContext.lang_path)
        self.commands_table.update(command_table)
    
    @default_title
    @process_hints
    def run_shell_script(self, file_path, **kwargs):
        try:
            # Using subprocess to execute the shell script
            result = subprocess.run(['bash', file_path], check=True, text=True, capture_output=True)
            
            message = f"Successfully excuted: {file_path} "
            if result.stdout:
                message+= f"Script output: {result.stdout}"
            
            return message
            
        except subprocess.CalledProcessError as e:
            # Handling errors if the script execution fails
            return f"Error occurred while running script: {e.stderr}"
        
    def _format_size(self, size_in_bytes): # bytes 
        KB = 1024
        MB = KB * 1024
        GB = MB * 1024
        TB = GB * 1024
        
        if size_in_bytes >= TB:
            return f"{size_in_bytes / TB:.2f} TB"
        elif size_in_bytes >= GB:
            return f"{size_in_bytes / GB:.2f} GB"
        elif size_in_bytes >= MB:
            return f"{size_in_bytes / MB:.2f} MB"
        elif size_in_bytes >= KB:
            return f"{size_in_bytes / KB:.2f} KB"
        else:
            return f"{size_in_bytes:.2f} Bytes"
    
    @default_title
    @process_hints
    def get_network_info(self, interval=5, callback=None, command_handler=None, **kwargs):  # 기본 (5초)
        initial_stats = psutil.net_io_counters(pernic=True)
        time.sleep(int(interval))
        final_stats = psutil.net_io_counters(pernic=True)
        delta_stats = {}
        
        for interface in final_stats:
            if interface in initial_stats:
                initial = initial_stats[interface]
                final = final_stats[interface]
                delta_stats[interface] = {
                    "bytes_sent": self._format_size(final.bytes_sent - initial.bytes_sent),
                    "bytes_recv": self._format_size(final.bytes_recv - initial.bytes_recv),
                    "packets_sent": final.packets_sent - initial.packets_sent,
                    "packets_recv": final.packets_recv - initial.packets_recv,
                    "errors_in": final.errin - initial.errin,
                    "errors_out": final.errout - initial.errout,
                    "drop_in": final.dropin - initial.dropin,
                    "drop_out": final.dropout - initial.dropout
                }
        if callback:
            callback(delta_stats, command_handler)
        else:
            return delta_stats
    
    @default_title
    @process_hints
    def get_cpu_info(self, **kwargs):
        cpu_info = {
        'Physical cores': psutil.cpu_count(logical=False),
        'Logical cores': psutil.cpu_count(logical=True),
        'Total CPU Usage': f"{psutil.cpu_percent(interval=1)}%"
        }

        core_usages = psutil.cpu_percent(interval=1, percpu=True)
        cpu_info['Core Usages'] = {f"Core {i}": f"{usage}%" for i, usage in enumerate(core_usages)}

        return cpu_info
    
    @default_title
    @process_hints
    def get_gpu_info(self, **kwargs):
        return display_gpu_info()
    
    @default_title
    @process_hints
    def get_memory_info(self, **kwargs):        
        timestamp = datetime.now().strftime("%Y-%m-%d-%H:%M-%a")
        result = subprocess.run(['free', '-h'], stdout=subprocess.PIPE)
        output = result.stdout.decode('utf-8')
        lines = output.split('\n')
        mem_info = lines[1].split()
        
        mem_info = {
            timestamp: {
                'total': mem_info[1],
                'used' : mem_info[2],
                'free' : mem_info[3],
                'shared': mem_info[4],
                'buff/cache': mem_info[5], 
                'available': mem_info[6]
            }
        }
        return mem_info

    @default_title
    def get_all_status(self, **kwargs):
        result = {'network': '', 'cpu': '', 'gpu': '', 'mem': '', 'disk': ''}
        result['network'] = self.get_network_info()
        result['cpu'] = self.get_cpu_info()
        result['gpu'] = self.get_gpu_info()
        result['mem'] = self.get_memory_info()
        result['disk']= self.get_disk_info()
        
        self._check_and_save(result, 'all_status_info.json')
     
    @default_title
    def get_disk_info(self, **kwargs) -> List[Dict[str, str]]:
        disk_info_list = []
        
        partitions = psutil.disk_partitions()
        for partition in partitions:
            partition_info = {
                "device": partition.device,
                "mountpoint": partition.mountpoint,
                "fstype": partition.fstype
            }
            
            try:
                partition_usage = psutil.disk_usage(partition.mountpoint)
                partition_info.update({
                    "total": self._format_size(partition_usage.total),
                    "used": self._format_size(partition_usage.used),
                    "free": self._format_size(partition_usage.free),
                    "percent": f"{partition_usage.percent:.2f}%"
                })
            except PermissionError:
                partition_info.update({
                    "total": "you do not have permission to access.",
                    "used": "you do not have permission to access.",
                    "free": "you do not have permission to access.",
                    "percent": "you do not have permission to access."
                })

            disk_info_list.append(partition_info)
        
        result = {}
        for i, disk_info in enumerate(disk_info_list):
            result[i] = disk_info
        
        return result
            
            
        