#!/bin/bash
set -e

# Install Python 3 and pip
sudo apt update
sudo apt install -y python3 python3-pip

# Install required Python packages
pip3 install requests guessit

# Create scripts folder
sudo mkdir -p /opt/subtitles
sudo chown $USER:$USER /opt/subtitles

# Copy scripts
cp download_subtitles.py run_subtitles.sh /opt/subtitles/
chmod +x /opt/subtitles/download_subtitles.py
chmod +x /opt/subtitles/run_subtitles.sh

# Create config.env if it doesn't exist
CONFIG_FILE="/opt/subtitles/config.env"
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Creating config.env..."
    cp config.env.example $CONFIG_FILE
    echo "Edit $CONFIG_FILE and set your API key and default language."
fi

echo "✅ Installation complete. Configure your API key in /opt/subtitles/config.env."
