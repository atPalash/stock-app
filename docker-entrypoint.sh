#!/bin/bash
set -euo pipefail

# Create container-local venv if missing
if [ ! -d "$VENV_PATH" ]; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="${HOME}/.local/bin:${PATH}"
    uv venv "$VENV_PATH"
    uv pip install -r /home/palash/stock-app/requirements.txt 
    uv pip install -e /home/palash/stock-app
    echo "export PATH=\"$VENV_PATH/bin:\$PATH\"" >> /home/palash/.bashrc
    echo 'source /usr/share/bash-completion/completions/git' >> /home/palash/.bashrc
fi

export PATH="$VENV_PATH/bin:$PATH"
    
# Exec the CMD
exec "$@"
