#!/bin/bash

# Make dirs to store ohlc and fundamentals data. Note fundamentals is empty for now.
# mkdir database && cd database
# mkdir fundamentals ohlc
# cd ohlc && mkdir day hour minute minute5 minute15 minute30 month week
CONTAINER_NAME="stock-server"
REMOTE_USER="palash"
REMOTE_HOST="palashserver"

# Open three separate terminals and execute the Python file
gnome-terminal -- bash -c "ssh ${REMOTE_USER}@${REMOTE_HOST} 'podman exec -it ${CONTAINER_NAME} ngrok http --domain=tight-strongly-liger.ngrok-free.app 8087; echo \"ngrok started\"; exec bash'"
gnome-terminal -- bash -c "ssh ${REMOTE_USER}@${REMOTE_HOST} 'podman exec -it ${CONTAINER_NAME} python ~/app/stock_app_py/scheduler/main.py; exec bash'"
gnome-terminal -- bash -c "ssh ${REMOTE_USER}@${REMOTE_HOST} 'podman exec -it ${CONTAINER_NAME} python ~/app/stock_app_py/webserver/main.py; exec bash'"
