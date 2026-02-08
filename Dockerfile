# using ubuntu LTS version
FROM python:3.12.3 as base

ARG USERNAME="palash"

# avoid stuck build due to user prompt
ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install --no-install-recommends -y \
    git \
    ssh \
    sudo \
    wget \
    curl \
    vim \
    net-tools \
    ca-certificates \
    openssl \
    libcurl4 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Create the user with a home directory
RUN useradd -m -s /bin/bash ${USERNAME} && \
    echo "${USERNAME} ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

WORKDIR /home/${USERNAME}/app
COPY .ssh /home/${USERNAME}/.ssh
COPY Dockerfile /home/${USERNAME}/app

# Change ownership of the entire home directory to the user
RUN chown -R ${USERNAME}:${USERNAME} /home/${USERNAME}

USER ${USERNAME}
# podman build -t db-server:latest .
# podman run -dit --name db-server --network=host db-server:latest