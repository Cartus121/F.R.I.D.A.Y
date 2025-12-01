# 🤖 F.R.I.D.A.Y.
### Female Replacement Intelligent Digital Assistant Youth
*Inspired by Iron Man's AI assistant*

![F.R.I.D.A.Y.](https://img.shields.io/badge/AI-F.R.I.D.A.Y.-blue?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.10+-green?style=for-the-badge)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-orange?style=for-the-badge)

A sophisticated voice-controlled AI assistant with an Irish female voice (like Kerry Condon from Iron Man), natural language processing, and smart home automation capabilities.

---

## ✨ Features

### 🎤 Voice & Speech
- **Irish Female Voice** - Authentic F.R.I.D.A.Y. voice using neural TTS
- **Multiple Wake Words** - "Friday", "Hey Friday", or customizable
- **Conversation Mode** - Stay awake for follow-up questions
- **Multi-Language** - English and Russian support
- **Hotkey Activation** - `Ctrl+Shift+F` to wake instantly

### 🧠 Intelligence
- **OpenAI GPT-4o** - Powered by advanced AI
- **FRIDAY Personality** - Professional, witty, like Tony Stark's assistant
- **Long-term Memory** - Remembers your preferences
- **Context Awareness** - Understands conversation flow

### ⏱️ Productivity
- **Timer & Stopwatch** - "Set timer for 5 minutes"
- **Calculator** - "What's 15% of 200?"
- **Unit Conversions** - Temperature, distance, weight
- **Calendar Management** - Add and view events
- **Notes & Reminders** - With alarm sounds
- **Weather Updates** - Current conditions

### 🖥️ System
- **System Diagnostics** - CPU, memory, disk status
- **App Launcher** - "Open Chrome", "Open VS Code"
- **Web Search** - DuckDuckGo integration
- **System Tray** - Minimize to tray
- **Desktop Notifications** - For reminders

---

## 🚀 Quick Start

### Windows
1. Download `FRIDAY.exe` from [Releases](../../releases)
2. Run the executable
3. Enter your OpenAI API key when prompted
4. Say "Friday" or press `Ctrl+Shift+F`

### Linux
```bash
# Clone repository
git clone https://github.com/yourusername/FRIDAY.git
cd FRIDAY

# Install dependencies
sudo apt install portaudio19-dev python3-pyaudio ffmpeg -y
pip install -r requirements.txt

# Run
python main.py
```

---

## 🎯 Voice Commands

| Command | Response |
|---------|----------|
| **"Friday"** | "Yes? What do you need?" |
| **"What time is it?"** | "It's 2:30 PM." |
| **"Set timer for 10 minutes"** | "Timer set for 10 minutes." |
| **"What's 50 fahrenheit in celsius?"** | "50° is 10.0° Celsius." |
| **"Calculate 15% of 200"** | "That's 30." |
| **"Add event meeting tomorrow at 3pm"** | "Done. 'Meeting' added for..." |
| **"What's the weather?"** | "Currently 15°C in Istanbul..." |
| **"System status"** | "Systems nominal. CPU at 12%..." |
| **"Remind me to call mom in 2 hours"** | "I'll remind you..." |
| **"Search for Python tutorials"** | "Found: Python Tutorial..." |
| **"Thank you"** | "Of course. I'll be here." |

---

## ⚙️ Settings

Click the ⚙️ button in the app to configure:

- **API Keys** - OpenAI (optional), OpenWeather (optional)
- **Wake Word** - Custom activation phrase
- **Language** - English or Russian
- **Notifications** - Desktop alerts

---

## 🔧 Building from Source

### Windows Build
```bash
pip install pyinstaller
pyinstaller --name="FRIDAY" --onefile --windowed main.py
```

### Automated Builds
Push to `main` branch triggers GitHub Actions to build Windows executable.

---

## 📁 File Structure

```
FRIDAY/
├── main.py           # Entry point
├── gui.py            # User interface
├── speech.py         # Voice recognition & TTS
├── commands.py       # Command processing
├── ai_brain.py       # AI responses
├── database.py       # Data storage
├── config.py         # Configuration
├── settings.py       # User settings
├── translations.py   # Multi-language support
└── requirements.txt  # Dependencies
```

---

## 🎤 Voice

F.R.I.D.A.Y. uses the Irish female voice (Kerry Condon style) - the authentic voice from Iron Man.

---

## 🐛 Troubleshooting

**No voice output?**
- Check volume settings
- Try different voice in settings

**Microphone not working?**
- Allow microphone permission
- Check audio device settings

**API errors?**
- Verify API key in settings
- Check internet connection

**Hotkey not working?**
- Run as administrator (Windows)
- Check for conflicting shortcuts

---

## 📜 License

MIT License - See [LICENSE](LICENSE)

---

## 🙏 Credits

- Inspired by Marvel's F.R.I.D.A.Y. (Iron Man)
- Voice: Microsoft Edge TTS (Irish English)
- AI: OpenAI GPT-4o

---

*"I'll be here if you need me."* - F.R.I.D.A.Y.
