import yaml

def read_config(path):
    with open(path, 'r') as stream:
        try:
            parsed_yaml = yaml.safe_load(stream)
            return parsed_yaml
        except Exception as exc:
            print(exc)
            return None

def save_config(data:dict, path:str):   
    # Save the dictionary to a YAML file
    with open(path, "w") as file:
        yaml.dump(data, file)
    