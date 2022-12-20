#!/bin/bash

gnome-terminal -e "bash -c 'kill -9 $(lsof -i :8080 | awk 'NR==2 {print $2}'); 
cd $PWD/build/StockAppApi/processes/master;
./Master; 
exec bash'" &
sleep 2 &
gnome-terminal -e "bash -c 'kill -9 $(lsof -i :8081 | awk 'NR==2 {print $2}'); 
cd $PWD/build/StockAppApi/processes/discord;
./DiscordConnector; 
exec bash'" &
sleep 2 &
gnome-terminal -e "bash -c 'kill -9 $(lsof -i :8082 | awk 'NR==2 {print $2}'); 
cd $PWD/build/StockAppApi/processes/news;
./News; 
exec bash'"
