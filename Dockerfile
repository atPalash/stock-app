# using ubuntu LTS version
FROM python:3.10 as base

ARG USERNAME="palash"

# avoid stuck build due to user prompt
ARG DEBIAN_FRONTEND=noninteractive
ARG NGROK_AUTH_TOKEN
RUN echo "Auth token: $DOCKER_AUTH_TOKEN"

RUN apt-get update && apt-get install --no-install-recommends -y \
    git \
    ssh \
    sudo \
    wget \
    curl \
    vim \
    net-tools \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /home/${USERNAME}/app
COPY . $WORKDIR
RUN chmod +x runner.sh

# Install Talib
RUN cd $WORKDIR \
    && mkdir tmp && cd tmp \
    && wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz \
    && sudo tar -xzf ta-lib-0.4.0-src.tar.gz \
    && sudo rm ta-lib-0.4.0-src.tar.gz \
    && cd ta-lib/ \
    && sudo ./configure --prefix=/usr \
    && sudo make \
    && sudo make install \
    && cd $WORKDIR \
    && sudo rm -rf tmp

# Install python modules
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install -e .

# Install ngrok
RUN curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null && echo "deb https://ngrok-agent.s3.amazonaws.com buster main" |   sudo tee /etc/apt/sources.list.d/ngrok.list &&   sudo apt update && sudo apt install ngrok
RUN useradd -u 1234 -m -d /home/${USERNAME} ${USERNAME}
RUN chown -R ${USERNAME}:${USERNAME} /home/${USERNAME}
RUN usermod -aG sudo palash

USER ${USERNAME}
RUN ngrok config add-authtoken ${NGROK_AUTH_TOKEN}
ENTRYPOINT ["./runner.sh"]
