FROM ubuntu:24.04 AS base

ARG USERNAME=palash
ARG DEBIAN_FRONTEND=noninteractive

# 2. Packages
RUN apt update && apt install --no-install-recommends -y \
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
    iputils-ping \
    ninja-build \
    less \
    python3-pip \
    python3-venv \
    openssh-client \
    tmux \
    jq \
    && apt clean && rm -rf /var/lib/apt/lists/*

RUN apt update && apt upgrade --no-install-recommends -y \
    && apt clean && rm -rf /var/lib/apt/lists/*

RUN userdel -r ubuntu 2>/dev/null || true && \
    useradd -u 1000 -ms /bin/bash ${USERNAME} && \
    usermod -aG sudo ${USERNAME} && \
    echo "${USERNAME} ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/${USERNAME} && \
    chmod 0440 /etc/sudoers.d/${USERNAME}

# Set up known_hosts for GitHub to avoid authenticity prompts
RUN mkdir -p /home/${USERNAME}/.ssh \
    && ssh-keyscan -t rsa,ecdsa,ed25519 github.com >> /home/${USERNAME}/.ssh/known_hosts \
    && chown -R ${USERNAME}:${USERNAME} /home/${USERNAME}/.ssh

COPY docker-entrypoint.sh /tmp/docker-entrypoint.sh
RUN chmod 0755 /tmp/docker-entrypoint.sh

USER ${USERNAME}
# Create directory for SSH agent socket
RUN mkdir -p /home/${USERNAME}/.ssh-agent && chown ${USERNAME}:${USERNAME} /home/${USERNAME}/.ssh-agent

# Set default SSH_AUTH_SOCK path (can be overridden by docker-compose)
ENV SSH_AUTH_SOCK=/home/${USERNAME}/.ssh-agent/agent.sock

WORKDIR /home/${USERNAME}/stock-app

# Use entrypoint script from mounted volume
ENTRYPOINT ["/tmp/docker-entrypoint.sh"]

FROM base AS dev
CMD [ "bash" ]

FROM base AS rel
CMD [ "python3", "main.py" ]