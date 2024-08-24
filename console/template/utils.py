from functools import wraps
from console.utils import print_console_message_for_thread, print_console_message
from rev.prettyjson import prettyjson 

def check_management(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if getattr(self, "management") is None:
            print("Please set address before")
            #self.set_management()
            print_console_message(self.command_handler.execute_command("set_management"))
            if getattr(self, "management") is not None:
                print("successfully Address set. Continuing...")
                return func(self, *args, **kwargs)
            else:
                print("Address setting was not successful.")
                return
        else:
            _svc = getattr(self, "management")
            print(f"Address: {getattr(_svc, 'addr')}")
            return func(self, *args, **kwargs)
    return wrapper


def check_svc_lists_from_mgmt(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not getattr(self, "svc_list_from_mgmt"):
            print("Please request lists before")
            print_console_message(self.command_handler.execute_command("get_svc_lists_from_mgmt"))
            if getattr(self, "svc_list_from_mgmt"):
                print("Successfully got Request svc lists. Continuing...")
                print(f"Current remote session DB is '{self.appended_svc_sessions}'")
                print(prettyjson(self.svc_list_from_mgmt))
                return func(self, *args, **kwargs)
            else:
                print("Failed to get request lists.")
                return
        else:
            return func(self, *args, **kwargs)
    return wrapper


def check_make_connection(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not getattr(self, "appended_svc_sessions"):
            print("Please append svc session before")
            print_console_message(self.command_handler.execute_command("make_connection"))
            if getattr(self, "appended_svc_sessions"):
                print("Successfully Remote svc appended. Continuing...")
                return func(self, *args, **kwargs)
            else:
                print("Failed to append remote svc.")
                return
        else:
            return func(self, *args, **kwargs)
    return wrapper

def check_elect_current_svc_session(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not getattr(self, "current_svc_session"): # current_svc_session 변수가 None이면
            print("please set current_svc_session before")
            print_console_message(self.command_handler.execute_command("elect_current_svc_session"))
            if getattr(self, "current_svc_session"):
                print("Successfully set current svc.")
                return func(self, *args, **kwargs)
            else:
                print("Failed to set current svc.")
                return
        else:
            return func(self, *args, **kwargs)
    return wrapper


def check_remote_commands(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not getattr(self, "current_svc_session_db"):
            print("Please get remote commands lists before")
            print_console_message(self.command_handler.execute_command("get_remote_commands"))
            if getattr(self, "current_svc_session_db"):
                print("Successfully get remote command lists. Continuing...")
                return func(self, *args, **kwargs)
            else:
                print("Failed to append remote svc.")
                return
        else:
            return func(self, *args, **kwargs)
    return wrapper


def check_set_remote_log(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not getattr(self, "net"):
            print("Please get remote log before")
            print_console_message(self.command_handler.execute_command("set_remote_log"))
            if getattr(self, "net"):
                print("Successfully set remote log object. Continuing...")
                return func(self, *args, **kwargs)
            else:
                print("Failed to append remote svc.")
                return
        else:
            return func(self, *args, **kwargs)
    return wrapper




