#!/bin/bash
set -euo pipefail

# Create container-local venv if missing
if [ ! -d "$VENV_PATH" ]; then
  python3 -m venv "$VENV_PATH"
  "$VENV_PATH/bin/pip" install -r /home/palash/stock-app/requirements.txt 
  "$VENV_PATH/bin/pip" install -e /home/palash/stock-app/app/pytick
fi

# Activate the venv for this process
source "$VENV_PATH/bin/activate"
# Source git completion for this process
source /usr/share/bash-completion/completions/git

# Activate the venv in all interactive shells
echo 'source "$VENV_PATH/bin/activate"' >> /home/palash/.bashrc
echo 'source /usr/share/bash-completion/completions/git' >> /home/palash/.bashrc

# Exec the CMD
exec "$@"
