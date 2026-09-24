#!/bin/zsh
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
rtk proxy python3 "${0:A:h}/scripts/start.py"
