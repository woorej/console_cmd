from utils import print_console_message_for_thread, print_console_message

class Tokenizer:
    def __init__(self):
        pass

    def tokenize(self, script):
        tokens = []
        for line_number, line in enumerate(script.splitlines(), start=1):
            stripped_line = line.strip()
            if stripped_line and not stripped_line.startswith("#"):
                indent_level = len(line) - len(line.lstrip())
                tokens.append((indent_level, stripped_line, line_number))
        return tokens

class Parser:
    def __init__(self, context):
        self.command_handler = context
        self.name_space = context.variable_manager.name_space
        
        self.special_commands = {
            "if": self._parse_if_block,
            "for": self._parse_for,
        }

    def parse_and_execute(self, tokens):
        idx = 0
        while idx < len(tokens):
            indent_level, token, line_num = tokens[idx]
            command_key = token.split()[0]
            if command_key in self.special_commands:
                handler = self.special_commands[command_key]
                try:
                    result, idx = handler(tokens, idx)
                    self.execute_commands(result)
                except SyntaxError as e:
                    print(f"SyntaxError: {e}")
                    break
                except Exception as e:
                    print(f"Condition evaluation error: {e}")
                    break
            else:
                self.execute_command(token)
            idx += 1

    def _parse_indented_block(self, tokens, idx, base_indent):
        if idx < len(tokens) and tokens[idx][0] <= base_indent:
            raise SyntaxError(f"Indented block expected at token line[{tokens[idx][2]}]: '{tokens[idx][1]}'")
        
        block = []
        while idx < len(tokens):
            current_indent, line, _ = tokens[idx]
            if current_indent <= base_indent:
                break
            block.append(line)
            idx += 1
        return block, idx - 1  # Adjust index to the last processed line
    
    def _parse_if_block(self, tokens, idx):
        if not tokens[idx][1].endswith(":"):
            raise SyntaxError(f"':' expected but not found. line[{tokens[idx][2]}]: {tokens[idx][1]}")
        
        condition = tokens[idx][1][3:].strip().strip(':')
        true_block, idx = self._parse_indented_block(tokens, idx + 1, tokens[idx][0])
        false_block = []
        elif_blocks = []
        
        while idx + 1 < len(tokens) and tokens[idx + 1][1].startswith("elif"):
            idx += 1
            elif_condition = tokens[idx][1][5:].strip().strip(':')
            elif_block, idx = self._parse_indented_block(tokens, idx + 1, tokens[idx][0])
            elif_blocks.append((elif_condition, elif_block))
            
        if idx + 1 < len(tokens) and tokens[idx + 1][1].startswith("else"):
            idx += 1
            false_block, idx = self._parse_indented_block(tokens, idx + 1, tokens[idx][0])

        # Evaluate the condition and choose the appropriate block
        if self._evaluate_condition(condition):
            result_block = true_block
        else:
            for elif_condition, elif_block in elif_blocks:
                if self._evaluate_condition(elif_condition):
                    result_block = elif_block
                    break
            else:
                result_block = false_block

        # Return the result block and the updated index
        return result_block, idx

    def _evaluate_condition(self, condition):
        # Eval the condition within the context's scope
        return eval(condition, {"__builtins__": __builtins__}, self.name_space)

    def _parse_for(self, tokens, idx):
        if not tokens[idx][1].endswith(":"):
            raise SyntaxError(f"':' expected but not found. line[{tokens[idx][2]}]: '{tokens[idx][1]}'")
        
        # Extract the loop range
        loop_expression = tokens[idx][1][4:].strip().strip(':')
        var_names, iterable = loop_expression.split("in")
        var_names = [name.strip() for name in var_names.split(',')]
        
        iterable = iterable.strip()
        
        if iterable.startswith("enumerate(") and "_$" in iterable:
            # Handle enumerate(_$) case
            loop_iterable = enumerate(self.name_space["_$"])
        elif iterable == "_$":
            # Handle simple for-in loop with _$
            loop_iterable = self.name_space["_$"]
        else:
            # Handle other cases using eval
            loop_iterable = eval(iterable, {"__builtins__": __builtins__}, self.name_space)
            
        loop_block, idx = self._parse_indented_block(tokens, idx + 1, tokens[idx][0])
        
        result_block = []
        for item in loop_iterable:
            if not isinstance(item, tuple):
                item = (item,)
            
            for command in loop_block:
                formatted_command = command
                if "$" in command:
                    for i, var_name in enumerate(var_names):
                        if i < len(item):
                            formatted_command = formatted_command.replace(f"${var_name}", str(item[i]))
                result_block.append(formatted_command)

        return result_block, idx
        
    def execute_command(self, command):
        print(f"{self.command_handler.tap_completer.prompt}{command}")
        print()
        output = self.command_handler.execute_command(command)
        if output:
            print_console_message(output, self.command_handler)
    
    def execute_commands(self, commands):
        for command in commands:
            self.execute_command(command)
            
if __name__ == '__main__':
