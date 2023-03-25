#!/bin/bash

CALLER_DIR=$PWD

# Go the root folder and copy all required files to a temporary mirror 
cd /home/palash/dev/stock-app
STOCK_APP_API_DIR="/home/palash/dev/stock-app/StockAppApi" 
STOCK_APP_API_MIRROR_DIR="/home/palash/dev/stock-app/mirror" 

mkdir $STOCK_APP_API_MIRROR_DIR
# First go to mirror and create the required dirs
cd $STOCK_APP_API_MIRROR_DIR
mkdir StockAppApi
cd StockAppApi

mkdir -p base/python
mkdir configuration
mkdir database
mkdir -p processes/python
cd ..

cp -r $STOCK_APP_API_DIR/base/python $STOCK_APP_API_MIRROR_DIR/StockAppApi/base
cp -r $STOCK_APP_API_DIR/configuration $STOCK_APP_API_MIRROR_DIR/StockAppApi
cp -r $STOCK_APP_API_DIR/database $STOCK_APP_API_MIRROR_DIR/StockAppApi
cp -r $STOCK_APP_API_DIR/processes/python/scheduler $STOCK_APP_API_MIRROR_DIR/StockAppApi/processes/python 
cp -r $STOCK_APP_API_DIR/processes/python/system $STOCK_APP_API_MIRROR_DIR/StockAppApi/processes/python
cp -r $STOCK_APP_API_DIR/processes/python/talib $STOCK_APP_API_MIRROR_DIR/StockAppApi/processes/python
cp -r $STOCK_APP_API_DIR/processes/python/yahoofinance $STOCK_APP_API_MIRROR_DIR/StockAppApi/processes/python

cp $STOCK_APP_API_DIR/requirements.txt $STOCK_APP_API_MIRROR_DIR/StockAppApi

# Copy the complete mirror folder to the caller
cp -r $STOCK_APP_API_MIRROR_DIR $CALLER_DIR

# Remove the mirror now
rm -rf $STOCK_APP_API_MIRROR_DIR

# return to the caller
cd $CALLER_DIR

docker build -t stock-app:scheduler-v1 .

rm -rf mirror

# #to test from local
# # docker run --rm -it --name scheduler --add-host=host.docker.internal:172.20.120.62 --network stock-app -p 8080:8080 stock-app:master-v1
docker run --rm -it --name scheduler --network stock-app -p 8085:8085 stock-app:scheduler-v1