import json

def read_json(filepath:str)->dict:
    try:
        with open(filepath) as fp:
            data = json.load(fp)
        return data
    except Exception as e:
        raise

def save_json(input: dict, filepath: str):
    try:
        with open(filepath, "w") as fp:
            json.dump(input, fp)
    except Exception as e:
        raise
