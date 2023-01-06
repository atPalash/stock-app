from pyparsing import Word, alphanums, Group, Forward, ZeroOrMore, oneOf, Keyword, Suppress, OneOrMore

# Define the grammar for the command
command = Word(alphanums)

# Define the grammar for the argument
argument = Word(alphanums)

operator = oneOf("+ -- * / < > <=")

# Define the grammar for the pipe operator
pipe_operator = Keyword("&&", caseless=True)

# Define a forward declaration for the command with pipes
cmd = Forward()
arg_cmd = Forward()
pipe_command = Forward()
cmd_with_pipes = Forward()
# Define the grammar for the command with pipes
cmd <<= command
arg_cmd <<= ZeroOrMore(operator + ZeroOrMore(argument))
pipe_command <<=ZeroOrMore(pipe_operator)

cmd_with_pipes <<= ZeroOrMore(Group(command + arg_cmd + pipe_command))

# Parse an input string
# input_str = "select --stock all && where --indicator ema20 --condition <=1000"
input_str = "select --stock all && where --indicator ema --intervals 20,100 --condition <=1000"
parsed_expr = cmd_with_pipes.parseString(input_str)

# Access the parsed elements
commands = []
current_cmd = []

for element in parsed_expr:
    if element == "|":
        commands.append(current_cmd)
        current_cmd = []
    else:
        current_cmd.append(element)

commands.append(current_cmd)

print(f"Commands: {commands}")
