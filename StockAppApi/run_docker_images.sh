#!/bin/bash

docker network create stock-app
docker run -d --name master --network stock-app -p 8080:8080 stock-app:master-v1
docker run -d --name discord --network stock-app -p 8081:8081 stock-app:discord-v1
docker run -d --name news --network stock-app -p 8082:8082 stock-app:news-v1