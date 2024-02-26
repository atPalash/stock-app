#!/bin/bash

function killVsCodeDeamonProcesses() {
    ps aux | grep '.vscode-server'| awk '{print $2}' | xargs kill -9
}

"$@"
