#! /bin/bash

# Cap native BLAS/OpenMP thread pools to avoid oversubscription
export OPENBLAS_NUM_THREADS=${OPENBLAS_NUM_THREADS:-1}
export OMP_NUM_THREADS=${OMP_NUM_THREADS:-1}
export NUMEXPR_NUM_THREADS=${NUMEXPR_NUM_THREADS:-1}
export MKL_NUM_THREADS=${MKL_NUM_THREADS:-1}
export APP_DIR=~/app
# Add export PYTHONPATH=/home/palash/dev/stock-app:$PYTHONPATH
# cd pytick && pip install -e . 

function initWorkspace() {
    git config --global user.name "Palash Halder"
    git config --global user.email "mpalash.halder@gmail.com"
}

function runApp() {
    LOG_FILE="log.txt"
    PATTERN="maximum number of running instances reached (1)"
    ERROR_PATTERN="error"
    RESTART_COUNT=0
    killApp

    find_free_port() {
        # Find a free port in range 1024-65535
        for port in $(seq 5000 65535); do
            if ! lsof -i:$port >/dev/null; then
                echo $port
                return
            fi
        done
    }

    start_main_py() {
        PORT=$(find_free_port)
        echo "Starting main.py on port $PORT" >> "$LOG_FILE"
        nohup ./main.py --port $PORT >> "$LOG_FILE" 2>&1 &
    }

    start_main_py

    tail -Fn0 "$LOG_FILE" | \
    while read -r line; do
        if echo "$line" | grep -qi "$ERROR_PATTERN" || echo "$line" | grep -q "$PATTERN"; then
            RESTART_COUNT=$((RESTART_COUNT + 1))
            NOW=$(TZ='Asia/Kolkata' date '+%Y-%m-%d %H:%M:%S')
            echo "$RESTART_COUNT $NOW - Restarting main.py due to failure" >> "$LOG_FILE"
            killApp
            sleep 2
            start_main_py
        fi
    done
}

function killApp() {
    pkill -9 -f "main.py" || true
    pkill -9 -f "python.*main.py" || true
    # openclaw gateway stop
    # pkill -f openclaw-ga
}

# Run as a new tmux session: tmux new -s redis
function runRedis() {
    tmux kill-session -t redis || true
    tmux new-session -d -s redis redis-server --port 6379
    OLLAMA_KEEP_ALIVE=-1 ollama serve
}

function backupRedis() {
    cd $APP_DIR
    redis-cli --rdb dump.rdb
    rdb -c json dump.rdb > dump.json
}

: <<'EOF'
Step-by-Step Discord Bot Setup Guide
Step 1: Create a Discord Application on Discord Developer Portal
Go to Discord Developer Portal
Click "New Application" button
Enter a name for your bot (e.g., "Stock-Query-Bot")
Accept the terms and click "Create"
Go to the "Bot" tab on the left sidebar
Click "Add Bot"
Under the TOKEN section, click "Copy" to copy your bot token
Save this token securely - you'll need it in a .env file
Step 2: Configure Bot Permissions
In Developer Portal, go to "OAuth2" → "URL Generator"
Under "SCOPES", select:
bot
applications.commands
Under "PERMISSIONS", select:
Send Messages
Read Messages/View Channels
Embed Links
Read Message History
Use Slash Commands
Copy the generated URL and paste it in your browser to invite the bot to your server
Step 3: Set Up Your Environment (.env file)
Create a .env file in your project root:
EOF
