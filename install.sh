#!/bin/bash
# Installer for qbitsubtitles v1.0
SUBTITLES_DIR="/opt/subtitles"
CONFIG_FILE="$SUBTITLES_DIR/config.env"

mkdir -p "$SUBTITLES_DIR"
clear
echo "=== qbitsubtitles v1.0 Installer ==="

# Python3 & pip
echo "🔹 Installing Python3 and pip..."
apt-get update && apt-get install -y python3 python3-pip

# Required packages
echo "🔹 Installing required Python packages..."
pip3 install --upgrade pip
pip3 install requests guessit

# Config
if [[ -f "$CONFIG_FILE" ]]; then
    echo "ℹ️ Config file exists: $CONFIG_FILE"
else
    echo "🔹 Creating config file..."
    touch "$CONFIG_FILE"
fi

# Prompt for API_KEY if not set
if ! grep -q "^API_KEY=" "$CONFIG_FILE"; then
    read -p "Enter your OpenSubtitles API Key: " api_key
    echo "API_KEY=$api_key" >> "$CONFIG_FILE"
else
    echo "ℹ️ API_KEY already set in config.env"
fi

# Prompt for DEFAULT_LANG if not set
if ! grep -q "^DEFAULT_LANG=" "$CONFIG_FILE"; then
    read -p "Enter default subtitle language (e.g. pl): " default_lang
    echo "DEFAULT_LANG=$default_lang" >> "$CONFIG_FILE"
else
    echo "ℹ️ DEFAULT_LANG already set in config.env"
fi

echo "✅ Installation complete! Run subtitles with:"
echo "   /opt/subtitles/run_subtitles.sh /path/to/videos"
