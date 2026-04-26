from datetime import datetime
import os
import tabulate
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


def format_table(data: list[dict], headers: list[str]) -> str:
    # 1. Prepare Table Data
    table_rows = []
    for item in data:
        row = []
        for key in headers:
            value = item.get(key.lower(), "")
            if key == 'datetime':
                time_obj = datetime.fromisoformat(value)
                time_str = time_obj.strftime("%Y-%m-%d %H:%M")
                value = time_str
            elif isinstance(value, (float, int)) and not isinstance(value, bool):
                value = f"{value:.2f}"
            row.append(value)
        table_rows.append(row)

    # 2. Generate ASCII Table
    # 'pretty' or 'grid' styles work best for Discord
    ascii_table = tabulate.tabulate(
        table_rows, headers=headers, tablefmt="pretty")

    # 3. Build Final Message
    message = (f"```prolog\n{ascii_table}\n```\n")

    return message
