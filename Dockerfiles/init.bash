#! /bin/bash

HOME_DIR="/home/palash"
STOCK_APP_DIR="/home/palash/stock-app"
# echo "Initializing stock-app dev container"

function setEnv() {
    cp $STOCK_APP_DIR/Dockerfiles/.bashrc $HOME_DIR
}

function setPythonPackages() {
    cd $STOCK_APP_DIR
    mkdir tmp && cd tmp \
    && wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz \
    && sudo tar -xzf ta-lib-0.4.0-src.tar.gz \
    && sudo rm ta-lib-0.4.0-src.tar.gz \
    && cd ta-lib/ \
    && sudo ./configure --prefix=/usr \
    && sudo make \
    && sudo make install \
    && cd $STOCK_APP_DIR \
    && sudo rm -rf tmp \

    pip install -r $STOCK_APP_DIR/requirements.txt
}

function makeDirs() {
    cd $STOCK_APP_DIR
    mkdir database && cd database
    mkdir fundamentals ohlc plot
    cd ohlc && mkdir day hour minute minute5 minute15 minute30 month week
}
"$@"
