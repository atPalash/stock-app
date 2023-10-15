# from pyparsing import *
# alphanum = Word(alphanums + '<' + '>' + '<=' + '>=' + ',' + '_' + '-')

# key_operator= Literal('--')
# # key_operator = oneOf(key_symbol, caseless=True)

# # Define a forward declarations
# key_value = Forward()
# key_value <<= ZeroOrMore(key_operator + ZeroOrMore(alphanum))

# # Complete command query string
# cmd_with_query = Forward()
# cmd_with_query <<= Group(alphanum + key_value)
# from pyparsing import *
# word = Word(alphas + '<' + '>' + '<=' + '>=' + ',' + '_' + '-')
# dashed = Literal("--")
# key_value = Forward()
# key_value <<= ZeroOrMore(dashed + ZeroOrMore(word))
# cmd_with_query = Forward()
# cmd_with_query <<= Group(word + key_value)

# @DeprecationWarning
def parse_message(message:str, parser_symbol='--') -> dict:
    try:
        messageToParse = message
        messageToParse.strip()
        messageArr = messageToParse.split(parser_symbol)
        result = {}

        # first element is always command
        result["command"] = messageArr[0].strip()
        
        for i in range(1, len(messageArr)):
            if messageArr[i] != "":
                argVal = messageArr[i].split(" ", 1)
                argument = argVal[0].strip()
                value = argVal[1].strip()
                result[argument] = value
                
        return result
    except Exception as e:
        raise

'''
def parse_message(message:str)->dict:
    """
    Parse the message string into key, value pairs. The string with the ``parser_symbol``
    is taken as the key and the value is represented by the string after it. The
    first string is the command.

    e.g. select --stock all --interval day | where --indicator ema --interval 20,100 --condition value<=1000 & 
    where --indicator macd --interval 20,100 --condition slope>0
    
    Args:
        message (str): The query string message to be parsed
        parser_symbol (str): String used to indicate key.

    Returns:
        dict: Of key value pairs
    """
    try:
        # parse the string to a list of commands with query
        cmd_query = cmd_with_query.parseString(message)
        pipe_found = False # signifies there are sub-commands
        condition_found = False # used to push the last sub-command to ret
        ret = [] # place holder for parsed result
        
        for i in range(len(cmd_query)):
            # find the main command
            if cmd_query[i] == "|":
                pipe_found = True
                ret.append(make_map(cmd_query[i-1]))
                ret.append(make_map(cmd_query[i]))    
            
            # find the sub-command
            if cmd_query[i] == "&&" or cmd_query[i] == "||" or cmd_query[i] == "!!":
                condition_found = True
                ret.append(make_map(cmd_query[i-1]))
                ret.append(make_map(cmd_query[i]))    
        
        # only main command
        if not pipe_found:
            ret.append(make_map(cmd_query[0]))
        else:
            # with sub-command
            if condition_found:
                ret.append(make_map(cmd_query[len(cmd_query) - 1]))
            else:
                ret.append(make_map(cmd_query[2]))

        return ret
    except Exception as e:
        print(e.args)

'''

# 
# def make_map(input: list)->dict:
#     """convert the list of commands to key-value pairs

#     Args:
#         input (list): of parsed string

#     Returns:
#         dict: of key-value key are the identifiers of action
#     """
#     ret = {}
#     for i in range(len(input)):
#         if i == 0:            
#             if(isinstance(input, str)):
#                 ret['command'] = input
#             else:
#                 ret['command'] = input[i]
#         else:
#             if(input[i] == "--"):
#                 ret[input[i+1]] = input[i+2]
#                 i+=2
#     return ret
        
if __name__ == "__main__":
    # test = f'select --stock all --interval day | where --indicator ema --interval 20,100 \
    #     --condition value<=1000 && where --indicator macd --interval 20,100 --condition slope>0 \
    #     || where --indicator rsi --condition value>70'
    # test2 = f'select --stock all --interval day,week --condition helo>100'
    test3 = "elder --ema_window 13 --ema_n 100 --macd_fast_period 13 --macd_slow_period 26 --macd_signal_period 9 --macdhist_n 20"
    # test4 ="sendMessage --channel general --message |    | stock      |   ema_day_slope |   ema_week_slope |   macd_hist_day_slope |   macd_hist_week_slope |   ema_action |   machdhist_action | trend   |\n|---:|:-----------|----------------:|-----------------:|----------------------:|-----------------------:|-------------:|-------------------:|:--------|\n|  1 | ASIANPAINT |        -3.59613 |         -7.20985 |              -1.56491 |                 -0.948 |           -2 |                 -2 | bearish |"
    test4 =f"talibquery --ticker BAJAJ-AUTO --interval day --do get --indicator  \
        macdhist --fastperiod 13 --slowperiod 26 --signalperiod 9 --n 2"
    # print(parse_message(test))
    # print(parse_message(test2))
    print(parse_message(test3))
    print(parse_message(test4))
    