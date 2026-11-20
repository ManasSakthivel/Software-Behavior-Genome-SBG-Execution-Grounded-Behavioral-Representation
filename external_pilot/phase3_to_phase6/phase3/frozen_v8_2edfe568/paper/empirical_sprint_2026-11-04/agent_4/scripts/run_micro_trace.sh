#!/bin/bash
P=/Users/manassakthivel/Desktop/SBG-FINALREVIEW/venvs
cd "$(dirname "$0")/.."
run() { PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0 "$2" -W ignore scripts/micro_trace.py copy > outputs/micro_trace_$1.json 2>outputs/micro_trace_$1.err; echo $1 $?; }
run py39 $P/py39/bin/python
run py311 /opt/homebrew/bin/python3.11
run py312 $HOME/.pyenv/versions/3.12.10/bin/python
run py313 $P/py313/bin/python
