#!/bin/bash
clear
echo "======================================"
echo "  QBITSUBTITLES INSTALLER v1.0"
echo "======================================"
echo ""

read -p "Enter your OpenSubtitles API Key: " API_KEY
read -p "Enter default subtitle language (e.g., pl, en): " DEFAULT_LANG

mkdir -p /opt/subtitles
cat > /opt/subtitles/config.env <<EOL
API_KEY=$API_KEY
DEFAULT_LANG=$DEFAULT_LANG
EOL

echo ""
echo "Installing Python dependencies..."
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

echo ""
echo "Installation completed. Configuration saved in /opt/subtitles/config.env"
