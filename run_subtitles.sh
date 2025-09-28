#!/bin/bash
# Usage: ./run_subtitles.sh /path/to/videos
FOLDER="$1"
if [ -z "$FOLDER" ]; then
    echo "❌ Please provide folder path"
    exit 1
fi

python3 -m qbitsubtitles.download "$FOLDER" --debug
