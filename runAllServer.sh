#!/bin/bash
rm -rf build/*
# cp -r ../stock-app/build . // Uncomment to copy from test executable folder

gnome-terminal -e "bash -c 'kill -9 $(lsof -i :8080 | awk 'NR==2 {print $2}'); 
cd $PWD/build/StockAppApi/processes/cpp/master;
./Master; 
exec bash'" &
sleep 2 &
gnome-terminal -e "bash -c 'kill -9 $(lsof -i :8081 | awk 'NR==2 {print $2}'); 
cd $PWD/build/StockAppApi/processes/cpp/discord;
./DiscordConnector; 
exec bash'" &
sleep 2 &
gnome-terminal -e "bash -c 'kill -9 $(lsof -i :8082 | awk 'NR==2 {print $2}'); 
cd $PWD/build/StockAppApi/processes/cpp/news;
./News; 
exec bash'"