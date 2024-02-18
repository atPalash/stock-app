#!/bin/bash
python app.py &
P1=$!
python app2.py &
P2=$!
ngrok http 9000 --domain gorgeous-turtle-loudly.ngrok-free.app &
P3=$!
wait $P1 $P2 $P3
