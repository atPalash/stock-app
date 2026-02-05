#! /bin/bash

function initContainer() {
    # Install influx db in Ubuntu and Debian
    # Add the InfluxData key to verify downloads and add the repository
    curl --silent --location -O https://repos.influxdata.com/influxdata-archive.key
    gpg --show-keys --with-fingerprint --with-colons ./influxdata-archive.key 2>&1 \
    | grep -q '^fpr:\+24C975CBA61A024EE1B631787C3D57159FC2F927:$' \
    && cat influxdata-archive.key \
    | gpg --dearmor \
    | sudo tee /etc/apt/keyrings/influxdata-archive.gpg > /dev/null \
    && echo 'deb [signed-by=/etc/apt/keyrings/influxdata-archive.gpg] https://repos.influxdata.com/debian stable main' \
    | sudo tee /etc/apt/sources.list.d/influxdata.list
    # Install influxdb
    sudo apt-get update && sudo apt-get install influxdb2
}

function initDeveloper() {
    # Add keys for github
    eval "$(ssh-agent -s)"
    ssh-add ~/.ssh/id_ed25519_asus
    source /usr/share/bash-completion/completions/git
    git config --global user.name "Palash Halder"
    git config --global user.email "mpalash.halder@gmail.com"
}

function runApp() {
    LOG_FILE="log.txt"
    PATTERN="maximum number of running instances reached (1)"
    ERROR_PATTERN="error"
    RESTART_COUNT=0

    kill_main_py() {
        pkill -f "./main.py"
    }

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
            kill_main_py
            sleep 2
            start_main_py
        fi
    done
}

function killApp() {
    pkill -f "./main.py"
}