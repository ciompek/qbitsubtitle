#!/bin/bash
clear
echo "======================================"
echo "       QBITSUBTITLES INSTALLER v1.0"
echo "======================================"
echo ""

# Ask user for config
read -p "Enter your OpenSubtitles API Key: " API_KEY
read -p "Enter default subtitle language (e.g., pl, en): " DEFAULT_LANG

# Create main folder
INSTALL_DIR="/opt/subtitles"
MODULE_DIR="$INSTALL_DIR/qbitsubtitles"
mkdir -p "$MODULE_DIR"

# Copy scripts and module files to /opt/subtitles
# Assumes you run install.sh from repo root
cp -r qbitsubtitles/* "$MODULE_DIR"
cp run_subtitles.sh "$INSTALL_DIR"
chmod +x "$INSTALL_DIR/run_subtitles.sh"

# Create config.env
cat > "$INSTALL_DIR/config.env" <<EOL
API_KEY=$API_KEY
DEFAULT_LANG=$DEFAULT_LANG
EOL

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

echo ""
echo "Installation completed!"
echo "Configuration saved in $INSTALL_DIR/config.env"
echo "Module files copied to $MODULE_DIR"
echo "Run subtitles script via: $INSTALL_DIR/run_subtitles.sh /path/to/videos"
