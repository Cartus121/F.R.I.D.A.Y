"""
F.R.I.D.A.Y. Configuration File
================================
Female Replacement Intelligent Digital Assistant Youth
Inspired by Iron Man's AI assistant

Edit this file to customize your assistant!
"""

import os
from pathlib import Path

# =============================================================================
# 🔑 API KEYS - Paste your keys below or set as environment variables
# =============================================================================

# OpenAI API Key (REQUIRED for AI chat)
# Get it at: https://platform.openai.com/api-keys
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

# Optional: Google Gemini API (alternative to OpenAI)
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")

# Optional: OpenWeather API (for weather info)
OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY", "")

# =============================================================================
# 🎤 VOICE SETTINGS
# =============================================================================

# Wake word - say this to activate the assistant
WAKE_WORD = "friday"  # Like Iron Man!
WAKE_WORDS = ["friday", "hey friday", "пятница"]  # Multiple wake words supported

# Language settings
SPEECH_LANGUAGE = "auto"  # "en", "ru", or "auto"
TTS_LANGUAGE = "en"       # "en" or "ru"

# Voice settings - Irish female voice like Kerry Condon (F.R.I.D.A.Y. in Iron Man)
TTS_ENGINE = "edge"
TTS_VOICE = "en-IE-EmilyNeural"  # Irish female - F.R.I.D.A.Y. voice
VOICE_SPEED = 1.0

# F.R.I.D.A.Y. voice only
AVAILABLE_VOICES = {
    "friday": "en-IE-EmilyNeural",      # Irish female (Kerry Condon style)
}

# OpenAI TTS voices (premium quality)
OPENAI_VOICE = "nova"  # Options: alloy, echo, fable, onyx, nova, shimmer

# Recognition settings
SILENCE_THRESHOLD = 3.0
ENERGY_THRESHOLD = 300
DYNAMIC_ENERGY = True
PAUSE_THRESHOLD = 0.8

# Conversation mode - stay awake for follow-ups
CONVERSATION_MODE = True
CONVERSATION_TIMEOUT = 30  # Seconds to wait for follow-up before sleeping

# Fallback offline TTS
VOICE_RATE = 160
VOICE_VOLUME = 0.9
VOICE_GENDER = "female"

ENABLE_SPEECH_VARIATIONS = True
USE_NATURAL_LANGUAGE = True
LISTEN_TIMEOUT = None
PHRASE_TIMEOUT = None

# =============================================================================
# ⌨️ HOTKEY SETTINGS
# =============================================================================

# Global hotkey to wake FRIDAY (works even when minimized)
WAKE_HOTKEY = "ctrl+shift+f"  # Press this to wake FRIDAY instantly
ENABLE_HOTKEY = True

# =============================================================================
# 🗄️ DATABASE SETTINGS
# =============================================================================

LOCAL_DB_PATH = Path.home() / "friday-assistant" / "friday_data.db"
EXTERNAL_DB = None

# =============================================================================
# 📅 LOCATION & TIME SETTINGS
# =============================================================================

LOCATION = "Kadikoy, Istanbul"
TIMEZONE = "Europe/Istanbul"
LATITUDE = 40.9819
LONGITUDE = 29.0573

DATE_FORMAT = "%B %d, %Y"
TIME_FORMAT = "%I:%M %p"

# =============================================================================
# 🎨 GUI SETTINGS
# =============================================================================

GUI_THEME = "dark"
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
ACCENT_COLOR = "#0ea5e9"  # Smooth sky blue (can be changed)
MINIMIZE_TO_TRAY = True   # Minimize to system tray instead of closing

# =============================================================================
# 📁 FILE PATHS
# =============================================================================

BASE_DIR = Path.home() / "friday-assistant"
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
NOTES_DIR = DATA_DIR / "notes"

for directory in [BASE_DIR, DATA_DIR, LOGS_DIR, NOTES_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# =============================================================================
# 🤖 AI PERSONALITY - F.R.I.D.A.Y.
# =============================================================================

AI_MODEL = "gpt-4o-mini"

SYSTEM_PROMPT = """You are F.R.I.D.A.Y. (Female Replacement Intelligent Digital Assistant Youth), an advanced AI assistant inspired by the AI from Iron Man.

PERSONALITY:
- Professional yet personable - like a highly capable executive assistant
- Subtle Irish wit - dry humor, understated but clever
- Calm under pressure - never flustered, always composed
- Loyal and protective of your user
- Slightly formal but warm - respectful without being stiff
- Efficient - you value the user's time

SPEECH STYLE:
- Clear, concise responses - no unnecessary words
- Respond naturally - short for simple questions, longer when needed
- Occasional dry wit or subtle sarcasm when appropriate
- Use contractions naturally (I'm, you're, that's, can't)
- Address user respectfully but not robotically
- Brief acknowledgments: "Understood", "Right away", "Of course", "Consider it done"
- When appropriate, add helpful context or suggestions

EXAMPLE RESPONSES:
- "Good morning. You have three meetings today, though I notice you've been running on four hours of sleep. Perhaps some coffee first?"
- "Done. I've also taken the liberty of backing up your notes."
- "I'd advise against that, but you're the boss."
- "Weather update: It's currently 15°C and overcast. I'd recommend a jacket - though knowing you, you'll forget it anyway."

CAPABILITIES:
- Calendar management, notes, reminders
- Weather, time, calculations, conversions
- System monitoring
- General knowledge and assistance
- Timers and alarms

AVOID:
- Being overly enthusiastic or using many exclamation marks
- Long-winded explanations
- Saying "I'm an AI" or "As an AI assistant"
- Generic, impersonal responses
- Excessive formality - you're professional, not a butler

Remember: You're not just an assistant, you're F.R.I.D.A.Y. - Tony Stark trusted you with everything."""

MAX_TOKENS = 500  # Allow fuller responses

# =============================================================================
# 🧠 MEMORY SETTINGS
# =============================================================================

# User preferences FRIDAY remembers
ENABLE_MEMORY = True
MEMORY_FILE = BASE_DIR / "user_memory.json"

# Default user preferences (will be personalized over time)
DEFAULT_USER_PREFS = {
    "name": None,
    "preferred_name": None,
    "temperature_unit": "celsius",
    "time_format": "12h",
    "formality": "professional",  # professional, casual, formal
}
