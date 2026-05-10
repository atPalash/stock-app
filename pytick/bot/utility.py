import argparse
from datetime import datetime
import io
import os
import discord
import pandas
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

class ArgumentParserError(Exception): pass
class ThrowingArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise ArgumentParserError(message)
    

async def send_csv(interaction: discord.Interaction, df: pandas.DataFrame, title: str):
    with io.BytesIO() as binary_stream:
        df = df.round(2)
        df.to_csv(binary_stream, index=False,
            encoding='utf-8', float_format='%.2f')
        binary_stream.seek(0)
        discord_file = discord.File(binary_stream, filename=f"{title}.csv")
        await interaction.followup.send(f"**{title}**", file=discord_file)

async def send_image(interaction: discord.Interaction, image: io.BytesIO, title: str):
    image.seek(0)
    discord_file = discord.File(image, filename=f"{title}.png")
    await interaction.followup.send(f"**{title}**", file=discord_file)
    image.close()
