#!/bin/bash
mkdir StockAppApi
cd StockAppApi
mkdir -p base/python
mkdir configuration

cd ..
cp -r ../../../base/python ./StockAppApi/base
cp -r ../../../configuration ./StockAppApi

docker build -t stock-app:master-v1 .
rm -rf StockAppApi

#to test from local
# docker run --rm -it --name scheduler --add-host=host.docker.internal:172.20.120.62 --network stock-app -p 8080:8080 stock-app:master-v1
docker run --rm -it --name master --network stock-app -p 8080:8080 stock-app:master-v1
