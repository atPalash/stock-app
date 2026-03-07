# 1. Build image
#    podman build -t cuda-pytick:latest -f Dockerfile .
# 2. Run container
#    podman run -dit --device nvidia.com/gpu=all --name cuda-pytick --network=host --restart=unless-stopped cuda-pytick:latest bash

FROM nvidia/cuda:13.1.1-cudnn-runtime-ubuntu24.04 AS base

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
    cmake \
    g++ \
    gdb \
    libxkbcommon-x11-0 \
    libwayland-cursor0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-shm0 \
    libxcb-util1 \
    libxcb-keysyms1 \
    libxcb-render-util0 \
    libxcb-render0 \
    libxcb-xinerama0 \
    mesa-common-dev \
    libglu1-mesa-dev \
    libxcb-xfixes0 \
    x11-utils \
    libegl1 \
    libxcb-cursor0 \
    python3-pip \
    python3-venv \
    openssh-client \
    redis-server \
    lsof \
    zstd \
    pciutils \
    lshw \
    tmux \
 && apt clean && rm -rf /var/lib/apt/lists/*

RUN apt update && apt upgrade --no-install-recommends -y \
 && apt clean && rm -rf /var/lib/apt/lists/*

# 3. Create user
RUN useradd -m -s /bin/bash "${USERNAME}" \
 && echo "${USERNAME} ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# 4. Copy SSH + build files (from build context)
WORKDIR /home/${USERNAME}/app

# .ssh in your build context must contain: id_ed25519 and optional known_hosts
COPY .ssh /home/${USERNAME}/.ssh

# fix ownership
RUN chown -R ${USERNAME}:${USERNAME} /home/${USERNAME}
# As root: setup perms + known_hosts
RUN chmod 700 /home/${USERNAME}/.ssh \
 && chmod 600 /home/${USERNAME}/.ssh/*

RUN ssh-keyscan -t rsa,ecdsa,ed25519 github.com >> /home/${USERNAME}/.ssh/known_hosts

USER ${USERNAME}

RUN GIT_SSH_COMMAND='ssh -i /home/${USERNAME}/.ssh/id_ed25519 -o StrictHostKeyChecking=yes' \
    ssh -T git@github.com || true

RUN GIT_SSH_COMMAND='ssh -i /home/${USERNAME}/.ssh/id_ed25519 -o StrictHostKeyChecking=yes' \
    git clone git@github.com:atPalash/stock-app.git && mv stock-app/* . && rm -rf stock-app
RUN git init \
 && git remote add origin git@github.com:atPalash/stock-app.git \
 && git fetch origin \
 && git checkout -f dev \
 && git branch -M dev
RUN python3 -m venv venv && . venv/bin/activate && pip install -r requirements.txt
RUN echo 'eval "$(ssh-agent -s)"' >> /home/${USERNAME}/.bashrc && \
    echo 'ssh-add ~/.ssh/id_ed25519' >> /home/${USERNAME}/.bashrc && \
    echo 'source /usr/share/bash-completion/completions/git' >> /home/${USERNAME}/.bashrc && \
    echo 'source ~/app/venv/bin/activate' >> /home/${USERNAME}/.bashrc

COPY Dockerfile /home/${USERNAME}/app
COPY runner.sh /home/${USERNAME}/app
