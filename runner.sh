#!/bin/bash

# Make dirs to store ohlc and fundamentals data. Note fundamentals is empty for now.
mkdir database && cd database
mkdir fundamentals ohlc
cd ohlc && mkdir day hour minute minute5 minute15 minute30 month week

cd ~/app

# Start webserver at 8087
python stock_app_py/webserver/main.py &
P1=$!

# Start scheduler at 8085
python stock_app_py/scheduler/main.py &
P2=$!

# Start ngrok -> 8087, this will tunnel the domain to localhost
ngrok http 8087 --domain=tight-strongly-liger.ngrok-free.app &
P3=$!
wait $P1 $P2 $P3
