#!/bin/bash

BUILD_DIR="/home/palash/dev/stock-app/build"

# Set the path to the executable, update this executable
EXEC_DIR=$BUILD_DIR/StockAppApi/processes/cpp/discord
EXECUTABLE_PATH=$EXEC_DIR/DiscordConnector

# Set the destination directory in the Docker container
DESTINATION_DIR="dockerfiles"
rm -rf $DESTINATION_DIR
mkdir -p $DESTINATION_DIR/libs
# Get the list of required libraries from ldd
LIBRARIES=$(ldd $EXECUTABLE_PATH | awk '{print $3}')

# Copy each library to the Docker container
for LIBRARY in $LIBRARIES; do
  cp $LIBRARY $DESTINATION_DIR/libs
done

mkdir $DESTINATION_DIR/exec
cp $EXECUTABLE_PATH $DESTINATION_DIR/exec
cp -r $EXEC_DIR/configuration $DESTINATION_DIR/exec
