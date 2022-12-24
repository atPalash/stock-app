def parse_message(message:str, parser_symbol:str) -> dict:
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
