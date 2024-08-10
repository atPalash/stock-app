#!/bin/bash

function killVsCodeDeamonProcesses() {
    ps aux | grep '.vscode-server'| awk '{print $2}' | xargs kill -9
}

function initialiseEnv() {
    source /usr/share/bash-completion/completions/git
    eval `ssh-agent`
    ssh-add ~/.ssh/id_ed25519
}

function kill() {
    netstat -tulpn | grep ':8087' | awk '{print $7}' | sed 's/\/.*//' | xargs kill -9
    netstat -tulpn | grep ':8085' | awk '{print $7}' | sed 's/\/.*//' | xargs kill -9
}

"$@"
