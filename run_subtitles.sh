#!/bin/bash
# run_subtitles.sh
# Called by qBittorrent after a torrent finishes downloading

FOLDER="$1"

if [ -z "$FOLDER" ]; then
    echo "❌ No folder specified"
    exit 1
fi

# Run Python script
python3 /opt/subtitles/download_subtitles.py "$FOLDER" --debug
