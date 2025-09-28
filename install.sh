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

# Create config.env interactively
CONFIG_FILE="/opt/subtitles/config.env"
echo "Creating configuration file at $CONFIG_FILE"

# Ask user for API key
read -p "Enter your OpenSubtitles API key: " USER_API_KEY
# Ask user for default subtitle language
read -p "Enter your default subtitle language (e.g., pl, en): " USER_LANG

cat > "$CONFIG_FILE" <<EOL
API_KEY=$USER_API_KEY
DEFAULT_LANG=$USER_LANG
EOL

echo "✅ Installation complete. Configuration saved to $CONFIG_FILE."
