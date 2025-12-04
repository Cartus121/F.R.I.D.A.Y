# 🤖 F.R.I.D.A.Y.
### Female Replacement Intelligent Digital Assistant Youth
*Your personal AI assistant inspired by Iron Man*

<p align="center">
  <img src="https://img.shields.io/badge/Version-stable--v1.2.0-purple?style=for-the-badge" alt="Version">
  <img src="https://img.shields.io/badge/AI-Multiple%20Providers-green?style=for-the-badge" alt="AI">
  <img src="https://img.shields.io/badge/Cost-FREE%20Options!-brightgreen?style=for-the-badge" alt="Cost">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge" alt="Python">
  <img src="https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-orange?style=for-the-badge" alt="Platform">
</p>

<p align="center">
  <b>🎤 Voice Controlled • 🧠 AI Powered • 💡 Smart Home • 🖥️ PC Control • 🆓 FREE!</b>
</p>

---

## 🤖 Choose Your AI Provider

F.R.I.D.A.Y. supports **3 AI providers** - pick what works best for you!

| Provider | Cost | Speed | Privacy | Setup |
|----------|------|-------|---------|-------|
| **🆓 Ollama (Recommended)** | FREE | Fast | 100% Private | Install app |
| **🆓 Gemini 1.5 Flash** | FREE | Fast | Cloud | API key |
| **💰 ChatGPT 4o-mini** | Paid | Fast | Cloud | API key |

### Option 1: Ollama (FREE & Offline) ⭐ Recommended
Works like ChatGPT but runs **locally on your PC** - no internet needed!

1. Download Ollama from [ollama.ai/download](https://ollama.ai/download)
2. Install and run it
3. Open terminal and run: `ollama pull llama3.2`
4. Start F.R.I.D.A.Y. - it will auto-detect Ollama!

**Benefits:** FREE forever, works offline, 100% private, no rate limits

### Option 2: Gemini (FREE Online)
Google's AI - powerful and completely FREE!

1. Go to [ai.google.dev](https://ai.google.dev/)
2. Click "Get API key"
3. Create key (starts with "AIza...")
4. Add in F.R.I.D.A.Y. Settings

**Benefits:** FREE, no software install, Google-quality AI

### Option 3: ChatGPT 4o-mini (Paid)
OpenAI's latest efficient model.

1. Go to [platform.openai.com](https://platform.openai.com/)
2. Create account & add payment
3. Generate API key (starts with "sk-...")
4. Add in F.R.I.D.A.Y. Settings

**Benefits:** OpenAI quality, very smart

---

## 🌟 What is F.R.I.D.A.Y.?

F.R.I.D.A.Y. is a sophisticated AI assistant that understands natural language, controls your PC, manages your smart home, and learns from your conversations. She speaks with an authentic Irish female voice (like Kerry Condon from Iron Man) and has a witty, professional personality.

**No keywords needed** - Just talk naturally. F.R.I.D.A.Y. uses AI to understand what you mean, not just what you say.

---

## ✨ Features

### 🧠 AI-Powered Understanding
- **Natural Language Processing** - No keywords, just talk naturally
- **Full Sentence Analysis** - AI understands context and intent
- **Mood Detection** - Adapts responses to how you're feeling
- **Deep Learning** - Learns your interests, communication style, and preferences
- **Long-term Memory** - Remembers your conversations and preferences

### 🎤 Voice & Speech
- **Irish Female Voice** - Authentic F.R.I.D.A.Y. voice (Kerry Condon style)
- **Text-to-Speech Sync** - Text appears in sync with speech
- **Multiple Wake Words** - "Friday", "Hey Friday", or custom
- **Conversation Mode** - Stays awake for follow-up questions
- **Multi-Language** - English and Russian support

### 🖥️ Full PC Control
| Feature | Examples |
|---------|----------|
| **🔊 Volume** | "Turn up the volume", "Set volume to 50%", "Mute" |
| **⏱️ Timer/Alarm** | "Set timer for 5 minutes", "Wake me up at 7am" |
| **💡 Brightness** | "Dim the screen", "Brightness to 80%" |
| **🎵 Media** | "Pause music", "Skip this song", "Play" |
| **📱 Apps** | "Open Chrome", "Launch VS Code", "Open Downloads" |
| **🔍 Search** | "Search for Python tutorials", "YouTube cat videos" |
| **🔒 System** | "Lock my PC", "Sleep", "System status" |
| **📸 Screenshot** | "Take a screenshot" |
| **📋 Clipboard** | "Copy this text", "What's in my clipboard?" |
| **🌐 WiFi/Bluetooth** | "Turn off WiFi", "Toggle Bluetooth" |

### 💡 Smart Home Control
F.R.I.D.A.Y. can control your smart lights and devices!

| Platform | Support |
|----------|---------|
| **Philips Hue** | ✅ Full support |
| **Home Assistant** | ✅ Universal (any device!) |
| **LIFX** | ✅ Cloud API |
| **Tuya / Smart Life** | ✅ Full support |
| **Fonri** | ✅ Full support (Tuya-based) |

**Examples:**
- "Turn on the lights"
- "Dim bedroom to 50%"
- "Make the lights red"
- "Turn off living room"

### 📊 Productivity
- **Calculator** - "What's 15% of 200?"
- **Unit Conversion** - "50 fahrenheit in celsius"
- **Weather** - "What's the weather?"
- **Time/Date** - "What time is it?"
- **Notes & Reminders** - "Remind me to call mom"
- **Knowledge Search** - "Who was Einstein?"

### 🎨 Beautiful UI
- **Modern Dark Theme** - Purple accent, smooth animations
- **Message Bubbles** - Chat-style interface
- **Status Panel** - Shows what F.R.I.D.A.Y. is doing
- **System Stats** - CPU and RAM usage
- **Auto-Updates** - Updates automatically when new version is available

---

## 🚀 Quick Start

### Windows (Recommended)
1. Download `FRIDAY.exe` from [**Releases**](../../releases/latest)
2. Run the executable
3. Enter your OpenAI API key when prompted
4. Say "Friday" to wake her up!

### Linux
```bash
# Clone repository
git clone https://github.com/Cartus121/F.R.I.D.A.Y.git
cd F.R.I.D.A.Y

# Install system dependencies
sudo apt install portaudio19-dev python3-pyaudio ffmpeg mpv -y

# Install Python dependencies
pip install -r requirements.txt

# Run
python main.py
```

### Build from Source
```bash
# Install PyInstaller
pip install pyinstaller

# Run build script
python build.py
# OR manually:
pyinstaller --name=FRIDAY --onefile --windowed --icon=icon.ico main.py
```

---

## 🎯 Example Commands

Just talk naturally! Here are some examples:

| You Say | F.R.I.D.A.Y. Does |
|---------|-------------------|
| "Hey Friday" | Wakes up and listens |
| "Crank up the volume" | Increases volume |
| "I need a timer for 10 minutes" | Sets a 10-minute timer |
| "Open YouTube and search for music" | Opens YouTube with search |
| "What's the weather like?" | Tells you current weather |
| "Lock my computer" | Locks your PC |
| "How are you doing?" | Has a conversation with you |
| "Turn off the bedroom lights" | Controls smart lights |
| "Thanks, that's all" | Goes back to sleep |

---

## 💡 Smart Home Setup

### For Fonri / Tuya / Smart Life Devices

1. **Install TinyTuya:**
   ```bash
   pip install tinytuya
   ```

2. **Get device credentials:**
   - Create account at [iot.tuya.com](https://iot.tuya.com)
   - Create a Cloud Project
   - Link your Fonri/Tuya app
   - Run: `python -m tinytuya wizard`

3. **Save to** `~/friday-assistant/smart_home.json`:
   ```json
   {
     "platform": "tuya",
     "devices": [
       {
         "name": "Living Room Light",
         "id": "your_device_id",
         "ip": "192.168.1.xxx",
         "key": "your_local_key",
         "version": 3.3
       }
     ]
   }
   ```

### For Philips Hue
```json
{
  "platform": "hue",
  "bridge_ip": "192.168.1.xxx",
  "username": "your_hue_username"
}
```

### For Home Assistant (Recommended - controls anything!)
```json
{
  "platform": "home_assistant",
  "host": "http://your-homeassistant:8123",
  "token": "your_long_lived_access_token"
}
```

---

## ⚙️ Configuration

Click ⚙️ in the app to configure:

| Setting | Description |
|---------|-------------|
| **OpenAI API Key** | Required for AI features |
| **Wake Word** | Custom activation phrase |
| **Voice** | Choose TTS voice |
| **Language** | English or Russian |
| **Weather Location** | Your city for weather |

---

## 📁 Project Structure

```
F.R.I.D.A.Y/
├── main.py           # Entry point with loading screen
├── gui.py            # Modern CustomTkinter interface
├── speech.py         # Voice recognition & TTS
├── commands.py       # AI-powered command processing
├── ai_brain.py       # AI responses, mood detection, learning
├── database.py       # SQLite data storage
├── config.py         # Configuration
├── settings.py       # User settings GUI
├── translations.py   # Multi-language support
├── updater.py        # Auto-update system
├── build.py          # Build script
└── requirements.txt  # Dependencies
```

---

## 🔧 Requirements

- **Python 3.10+**
- **OpenAI API Key** (get one at [platform.openai.com](https://platform.openai.com))
- **Microphone** (for voice commands)
- **Speakers** (for voice output)

### Optional
- **OpenWeather API Key** - For weather features
- **Smart Home devices** - For home automation

---

## 🐛 Troubleshooting

<details>
<summary><b>No voice output?</b></summary>

- Check your volume settings
- Make sure `mpv` or `ffplay` is installed (Linux)
- Try a different voice in settings
</details>

<details>
<summary><b>Microphone not working?</b></summary>

- Allow microphone permission
- Check audio device in system settings
- On Linux: `systemctl --user restart pipewire`
</details>

<details>
<summary><b>Update failed / _MEI error?</b></summary>

1. Close F.R.I.D.A.Y. completely
2. Go to `C:\Users\YourName\AppData\Local\Temp`
3. Delete `_MEI*` folders and `friday_update` folder
4. Re-download from Releases
</details>

<details>
<summary><b>Smart lights not working?</b></summary>

- Make sure device is on same WiFi network
- Check credentials in `smart_home.json`
- For Tuya devices, run `python -m tinytuya scan` to find devices
</details>

---

## 📜 Version History

| Version | Highlights |
|---------|------------|
| **alpha-v28** | Fixed Windows auto-update issues |
| **alpha-v27** | Fonri/Tuya smart light support |
| **alpha-v26** | Faster response, voice-text sync, stop button fix |
| **alpha-v25** | AI-powered intent analysis, mood detection, PC control |
| **alpha-v24** | Volume, timer, alarm, brightness controls |
| **alpha-v23** | New purple theme, better UI |

---

## 📜 License

MIT License - See [LICENSE](LICENSE)

---

## 🙏 Acknowledgments

- Inspired by Marvel's F.R.I.D.A.Y. from Iron Man
- Voice: Microsoft Edge TTS (Irish English - Emily)
- AI: OpenAI GPT-4o
- UI: CustomTkinter

---

<p align="center">
  <i>"I'll be here if you need me."</i> - F.R.I.D.A.Y.
</p>

<p align="center">
  Made with ❤️ by <a href="https://github.com/Cartus121">Cartus121</a>
</p>
