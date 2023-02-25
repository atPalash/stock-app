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