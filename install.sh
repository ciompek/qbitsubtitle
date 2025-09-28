#!/bin/bash
set -e

APP_NAME="qbitsubtitles"
VERSION="1.0"
INSTALL_DIR="/opt/subtitles"
CONFIG_FILE="$INSTALL_DIR/config.env"

# Clear the console
clear

# Colors
GREEN="\033[0;32m"
CYAN="\033[0;36m"
YELLOW="\033[1;33m"
RESET="\033[0m"

echo -e "${CYAN}=============================================${RESET}"
echo -e "${CYAN}        $APP_NAME Installer v$VERSION        ${RESET}"
echo -e "${CYAN}=============================================${RESET}\n"

echo -e "${YELLOW}📦 Installing Python 3 and pip...${RESET}"
sudo apt update
sudo apt install -y python3 python3-pip

echo -e "${YELLOW}📦 Installing required Python packages (requests, guessit)...${RESET}"
pip3 install requests guessit

# Create installation directory
echo -e "${YELLOW}🗂 Creating installation folder at $INSTALL_DIR...${RESET}"
sudo mkdir -p "$INSTALL_DIR"
sudo chown $USER:$USER "$INSTALL_DIR"

# Copy scripts
echo -e "${YELLOW}📄 Copying scripts to $INSTALL_DIR...${RESET}"
cp download_subtitles.py run_subtitles.sh "$INSTALL_DIR/"
chmod +x "$INSTALL_DIR/download_subtitles.py"
chmod +x "$INSTALL_DIR/run_subtitles.sh"

# Interactive configuration
echo -e "\n${CYAN}================ Configuration ================${RESET}"
read -p "🔑 Enter your OpenSubtitles API key: " USER_API_KEY
read -p "🌐 Enter your default subtitle language (e.g., pl, en): " USER_LANG

cat > "$CONFIG_FILE" <<EOL
API_KEY=$USER_API_KEY
DEFAULT_LANG=$USER_LANG
EOL

echo -e "\n${GREEN}✅ Installation complete!${RESET}"
echo -e "${GREEN}Configuration saved to $CONFIG_FILE${RESET}"
echo -e "${GREEN}You can now configure qBittorrent to run /opt/subtitles/run_subtitles.sh after torrent completion.${RESET}"
echo -e "${CYAN}=============================================${RESET}\n"
