#!/bin/bash
set -e

APP_NAME="qbitsubtitles"
INSTALL_DIR="/opt/subtitles"
CONFIG_FILE="$INSTALL_DIR/config.env"

# Install Python 3 and pip
sudo apt update
sudo apt install -y python3 python3-pip

# Install required Python packages
pip3 install requests guessit

# Create scripts folder
sudo mkdir -p "$INSTALL_DIR"
sudo chown $USER:$USER "$INSTALL_DIR"

# Copy scripts
cp download_subtitles.py run_subtitles.sh "$INSTALL_DIR/"
chmod +x "$INSTALL_DIR/download_subtitles.py"
chmod +x "$INSTALL_DIR/run_subtitles.sh"

# Interactive configuration
echo "Creating configuration file at $CONFIG_FILE"

read -p "Enter your OpenSubtitles API key: " USER_API_KEY
read -p "Enter your default subtitle language (e.g., pl, en): " USER_LANG

cat > "$CONFIG_FILE" <<EOL
API_KEY=$USER_API_KEY
DEFAULT_LANG=$USER_LANG
EOL

echo "✅ Installation complete. Configuration saved to $CONFIG_FILE"
echo "You can now configure qBittorrent to run /opt/subtitles/run_subtitles.sh after torrent completion."
