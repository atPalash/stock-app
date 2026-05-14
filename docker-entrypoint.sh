#!/bin/bash
set -euo pipefail

curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="${HOME}/.local/bin:${PATH}"
uv venv "$VENV_PATH"
source "$VENV_PATH/bin/activate"

uv pip install -r /home/palash/stock-app/requirements.txt 
uv pip install -e /home/palash/stock-app

# Source git completion for this process
source /usr/share/bash-completion/completions/git
echo 'source /usr/share/bash-completion/completions/git' >> /home/palash/.bashrc

# Exec the CMD
exec "$@"
