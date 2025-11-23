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
}

function runApp() {
    LOG_FILE="log.txt"
    PATTERN="maximum number of running instances reached (1)"
    MAIN_CMD="./main.py >> log.txt 2>&1"
    RESTART_COUNT=0

    kill_main_py() {
        pkill -f "./main.py"
    }

    eval $MAIN_CMD &

    tail -Fn0 "$LOG_FILE" | \
    while read -r line; do
        if echo "$line" | grep -q "$PATTERN"; then
            # Get current hour in Asia/Kolkata timezone
            HOUR=$(TZ='Asia/Kolkata' date +%H)
            # if [ "$HOUR" -ge 9 ] && [ "$HOUR" -lt 16 ]; then
                RESTART_COUNT=$((RESTART_COUNT + 1))
                NOW=$(TZ='Asia/Kolkata' date '+%Y-%m-%d %H:%M:%S')
                echo "$RESTART_COUNT $NOW" >> "$LOG_FILE"
                kill_main_py
                sleep 2
                eval $MAIN_CMD &
            # fi
        fi
    done
}