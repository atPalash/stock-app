import yaml

def read_config(path):
    with open(path, 'r') as stream:
        try:
            parsed_yaml = yaml.safe_load(stream)
            return parsed_yaml
        except Exception as exc:
            print(exc)
            return None