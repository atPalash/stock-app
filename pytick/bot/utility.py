import os
import yaml

def get_user_ids(users_dir):
    user_ids = []
    for fname in os.listdir(users_dir):
        if fname.endswith('.yaml'):
            with open(os.path.join(users_dir, fname), 'r') as f:
                data = yaml.safe_load(f) or {}
                uid = data.get('user_id')
                if uid:
                    user_ids.append(uid)
    return user_ids