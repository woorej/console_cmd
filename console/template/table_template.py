def table1(command_list):
    header = f"{'Key':<30} {'Value':<35}"

    print(header)
    print("-" * (30 + 1 + 35))

    for key, value in command_list:
        print(f"{key:<30} {value:<35}")


def table2(command_list):
    border = "+" + "—"*20 + "+" + "—"*60 + "+"
    header = f"|{'Command':<20}|{'Description':<60}|"

    print(border)
    print(header)
    print(border)

    for command, description in command_list:
        print(f"|{command:<20}|{description:<60}|")
        print(border)

def table3(command_list):
    border_top = "┌" + "─"*20 + "┬" + "─"*60 + "┐"
    border_middle = "├" + "─"*20 + "┼" + "─"*60 + "┤"
    border_bottom = "└" + "─"*20 + "┴" + "─"*60 + "┘"

    header = f"│{'Command':<20}│{'Description':<60}│"

    print(border_top)
    print(header)
    print(border_middle)

    for command, description in command_list:
        print(f"│{command:<20}│{description:<60}│")

    print(border_bottom)


def table4(command_list):
    border_top = "┌" + "─"*20 + "┬" + "─"*60 + "┐"
    border_middle = "├" + "─"*20 + "┼" + "─"*60 + "┤"
    border_bottom = "└" + "─"*20 + "┴" + "─"*60 + "┘"

    header = f"│{'Command':<20}│{'Description':<60}│"

    print(border_top)
    print(header)

    for command, description in command_list:
        print(border_middle)
        print(f"│{command:<20}│{description:<60}│")
    
    print(border_bottom)
    
def table5(command_list):
    border_top = "╔" + "═"*20 + "╦" + "═"*60 + "╗"
    border_divider = "╠" + "═"*20 + "╬" + "═"*60 + "╣"
    border_row = "║" + "─"*20 + "╫" + "─"*60 + "║"
    border_bottom = "╚" + "═"*20 + "╩" + "═"*60 + "╝"

    header = f"║{'Command':<20}║{'Description':<60}║"

    print(border_top)
    print(header)
    print(border_divider)

    for i, (command, description) in enumerate(command_list):
        if i > 0:
            print(border_row)
        print(f"║{command:<20}║{description:<60}║")
    
    print(border_bottom)

def table5(command_list):
    max_command_length = max(len(command) for command, _ in command_list)
    max_description_length = max(len(description) for _, description in command_list)

    min_command_width = 20
    min_description_width = 40

    command_width = max(max_command_length + 2, min_command_width)  
    description_width = max(max_description_length + 2, min_description_width) 

    border_top = "╔" + "═"*command_width + "╦" + "═"*description_width + "╗"
    border_divider = "╠" + "═"*command_width + "╬" + "═"*description_width + "╣"
    border_row = "║" + "─"*command_width + "╫" + "─"*description_width + "║"
    border_bottom = "╚" + "═"*command_width + "╩" + "═"*description_width + "╝"

    header_format = f"║{{:<{command_width}}}║{{:<{description_width}}}║"
    header = header_format.format('Command', 'Description')

    print(border_top)
    print(header)
    print(border_divider)

    row_format = f"║{{:<{command_width}}}║{{:<{description_width}}}║"

    for i, (command, description) in enumerate(command_list):
        if i > 0:
            print(border_row)
        print(row_format.format(command, description))
    
    print(border_bottom)


def table6(command_list):
    max_length = 0

    for command, description in command_list:
        max_length = max(max_length, len(command))
        if isinstance(description, dict):
            for key, value in description.items():
                max_length = max(max_length, len(f"{key}: {value}")+5)
        else:
            max_length = max(max_length, len(description))
    
    width = max_length + 4

    def print_line(content, prefix="", suffix=""):
        print(f"║ {prefix}{content:<{width-4-len(prefix)-len(suffix)}}{suffix} ║")

    def print_divider():
        print(f"╟{'─' * (width-2)}╢")

    print(f"╔{'═' * (width-2)}╗")

    for i, (command, description) in enumerate(command_list):
        if i > 0:  
            print_divider()
        print_line(command) 

        if isinstance(description, dict):
            for key, value in description.items():
                print_line(f"{key}: {value}", prefix="  ")
        else:
            print_line(description) 

    print(f"╚{'═' * (width-2)}╝")


def dict_status_table(func):
    def wrapper(*args, **kwargs):
        command_list = func(*args, **kwargs)
        table6(command_list)

    return wrapper


# Decorator Template, You can modify below funcs to change template
def status_table(func):
    """
    Fro Mode settings
    """
    def wrapper(*args, **kwargs):
        command_list = func(*args, **kwargs)
        if command_list is None:
            print("Nothing to show settings")
            return
        table5(command_list)

    return wrapper

def custom_help_table(func):
    """
    For help
    """
    def wrapper(*args, **kwargs):
        command_list = func(*args, **kwargs)
        table4(command_list)
    return wrapper

def default_help_table(func):
    """
    For Commmon help
    """
    def wrapper(*args, **kwargs):
        command_list = func(*args, **kwargs)
        table3(command_list)

    return wrapper

def pretty_print_message(message):
    border_length = len(message) + 5
    border = '═' * border_length
    print(border)
    print(" ", message)
    print(border)