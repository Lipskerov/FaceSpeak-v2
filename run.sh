#!/usr/bin/env bash
# Launch FaceSpeak V2 using miniforge3 Python
# Usage: ./run.sh

cd "$(dirname "$0")"
exec /Users/lipskerov/miniforge3/bin/python3 main.py "$@"
