#!/bin/bash

# F.R.I.D.A.Y. Installation Script for Pop!_OS (PipeWire-based system)
# Female Replacement Intelligent Digital Assistant Youth
# Run with: bash scripts/install.sh

echo "════════════════════════════════════════════════════════════════"
echo "  ███████╗██████╗ ██╗██████╗  █████╗ ██╗   ██╗"
echo "  ██╔════╝██╔══██╗██║██╔══██╗██╔══██╗╚██╗ ██╔╝"
echo "  █████╗  ██████╔╝██║██║  ██║███████║ ╚████╔╝ "
echo "  ██╔══╝  ██╔══██╗██║██║  ██║██╔══██║  ╚██╔╝  "
echo "  ██║     ██║  ██║██║██████╔╝██║  ██║   ██║   "
echo "  ╚═╝     ╚═╝  ╚═╝╚═╝╚═════╝ ╚═╝  ╚═╝   ╚═╝   "
echo ""
echo "  Female Replacement Intelligent Digital Assistant Youth"
echo "════════════════════════════════════════════════════════════════"
echo ""

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check if running on Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo -e "${RED}This script is designed for Linux (Pop!_OS/Ubuntu)${NC}"
    exit 1
fi

echo -e "${BLUE}Step 1: Installing system dependencies for PipeWire...${NC}"
sudo apt update
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    python3-tk \
    python3-pil \
    python3-pil.imagetk \
    portaudio19-dev \
    libportaudio2 \
    espeak-ng \
    libespeak-ng-dev \
    ffmpeg \
    mpv \
    libsndfile1 \
    libasound2-dev \
    pipewire \
    pipewire-audio-client-libraries \
    wireplumber

echo ""
echo -e "${BLUE}Step 2: Ensuring PipeWire is running...${NC}"
systemctl --user restart pipewire pipewire-pulse wireplumber 2>/dev/null || true

echo ""
echo -e "${BLUE}Step 3: Adding user to audio group...${NC}"
sudo usermod -aG audio $USER

echo ""
echo -e "${BLUE}Step 4: Creating virtual environment...${NC}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

python3 -m venv venv
source venv/bin/activate

echo ""
echo -e "${BLUE}Step 5: Installing Python packages...${NC}"
pip install --upgrade pip wheel setuptools

# Install PyAudio with proper flags for PipeWire
pip install pyaudio

# Install all packages
pip install openai
pip install google-generativeai
pip install SpeechRecognition
pip install pyttsx3
pip install edge-tts
pip install customtkinter
pip install Pillow
pip install sqlalchemy
pip install psycopg2-binary
pip install pymysql
pip install icalendar
pip install python-dateutil
pip install pytz
pip install requests
pip install python-dotenv
pip install schedule
pip install psutil
pip install geocoder
pip install duckduckgo-search
pip install pygame
pip install keyboard
pip install pystray

echo ""
echo -e "${GREEN}Installation complete!${NC}"
echo ""

echo -e "${YELLOW}Testing audio system...${NC}"
python3 -c "
import pyaudio
p = pyaudio.PyAudio()
count = 0
print('  Available microphones:')
for i in range(p.get_device_count()):
    dev = p.get_device_info_by_index(i)
    if dev['maxInputChannels'] > 0:
        count += 1
        print(f'    [{i}] {dev[\"name\"]}')
p.terminate()
if count == 0:
    print('  WARNING: No microphone found!')
else:
    print(f'  OK: {count} microphone(s) detected')
"

echo ""
echo "════════════════════════════════════════════════════════════════"
echo -e "${GREEN}F.R.I.D.A.Y. Setup Complete!${NC}"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo -e "To run F.R.I.D.A.Y.:"
echo -e "  ${YELLOW}cd $PROJECT_DIR${NC}"
echo -e "  ${YELLOW}source venv/bin/activate${NC}"
echo -e "  ${YELLOW}python main.py${NC}"
echo ""
echo -e "Or simply run: ${YELLOW}bash scripts/run.sh${NC}"
echo ""
