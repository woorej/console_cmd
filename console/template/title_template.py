from functools import wraps

HELP_LINE_LENGTH = 60

def title1(name: str):
    deco = "***"
    padding = (HELP_LINE_LENGTH - len(name) - (len(deco)*2)) // 2
    title_line = "-" * HELP_LINE_LENGTH
    title = f"{' '*padding}{deco} {name} {deco}"
    print(f"{title_line}\n{title}\n{title_line}")
            
def title2(name: str):
    deco = "✦✧✦"
    padding = (HELP_LINE_LENGTH - len(name) - (len(deco) * 2)) // 2
    title_line = "—" * HELP_LINE_LENGTH
    title = f"{' ' * padding}{deco} {name} {deco}"
    print(f"{title_line}\n{title}\n{title_line}")
    
def title3(name: str):
    deco = "❖❖❖"
    padding = (HELP_LINE_LENGTH - len(name) - (len(deco) * 2)) // 2
    title_line = "═" * HELP_LINE_LENGTH
    title = f"{' ' * padding}{deco} {name} {deco}"
    print(f"{title_line}\n{title}\n{title_line}")


def title4(name: str):
    deco = "●●●"
    padding = (HELP_LINE_LENGTH - len(name) - (len(deco) * 2)) // 2
    title_line = "—" * HELP_LINE_LENGTH
    title = f"{' ' * padding}{deco} {name} {deco}"
    print(f"{title_line}\n{title}\n{title_line}")

def title5(name: str):
    left_deco = ">>>"
    right_deco = "<<<"
    total_deco_length = len(left_deco) + len(right_deco)
    padding = (HELP_LINE_LENGTH - len(name) - total_deco_length) // 2
    title_line = "═" * HELP_LINE_LENGTH
    title = f"{' ' * padding}{left_deco} {name} {right_deco}"
    print(f"\n{title_line}\n{title}\n{title_line}")
    
def title6(name: str):
    upper_border = ">" * HELP_LINE_LENGTH
    lower_border = "<" * HELP_LINE_LENGTH
    padding = (HELP_LINE_LENGTH - len(name)) // 2
    title = f"{' ' * padding}{name}"
    print(f"{upper_border}\n{title}\n{lower_border}")

# Decorator Template, You can modify below func to change template
def default_title(method):
    """
    기능 실행
    """
    @wraps(method)
    def wrapper(*args, **kwargs):
        title5(method.__name__) 
        return method(*args, **kwargs)
    return wrapper