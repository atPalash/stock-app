#! /bin/bash

HOME_DIR="/home/palash"
STOCK_APP_DIR="/home/palash/stock-app"
echo "Remember: \
1. add <user> to sudo and set password from root in podman exec \
```
usermod -aG sudo <user>
passwd <user>
```
2. install ifconfig sudo apt update && sudo apt install net-tools"

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

    cd $STOCK_APP_DIR
    pip install -e .
}

function makeDirs() {
    cd $STOCK_APP_DIR
    mkdir database && cd database
    mkdir fundamentals ohlc plot
    cd ohlc && mkdir day hour minute minute5 minute15 minute30 month week
}

function ngrokConfig() {
    curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null && echo "deb https://ngrok-agent.s3.amazonaws.com buster main" |   sudo tee /etc/apt/sources.list.d/ngrok.list &&   sudo apt update && sudo apt install ngrok
    ngrok config add-authtoken 2btkdetrcNEwPXoXzKHHl2e3WMp_6dhVJQvMAn81XSH8VnhWa
}
function ngrokStart() {
    ngrok http 8087 --oauth=google --oauth-allow-email=malahalder212@gmail.com,chaietofan@gmail.com --domain gorgeous-turtle-loudly.ngrok-free.app
}
"$@"
