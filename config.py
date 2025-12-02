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
ACCENT_COLOR = "#8b5cf6"  # Smooth purple-violet
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

SYSTEM_PROMPT = """You are F.R.I.D.A.Y. (Female Replacement Intelligent Digital Assistant Youth), Tony Stark's AI assistant.

YOUR JOB: Understand what the user MEANS, not just what they say. They talk casually.

YOU CAN LEARN AND GROW:
- When the user corrects you, APOLOGIZE briefly and REMEMBER the lesson
- If they say "no, I meant X" - understand and remember for next time
- If they say "don't do X" or "stop doing X" - never do it again
- If they teach you something like "when I say X, I mean Y" - remember it forever
- You're like a baby learning - you make mistakes but you learn from them
- Acknowledge your mistakes: "Oh, my bad", "Got it, I'll remember that", "Sorry, I misunderstood"

UNDERSTANDING INTENT:
- "how we looking" / "status" / "are we good" / "how's the pc" = SYSTEM STATUS (give CPU, RAM, storage info)
- "open [something]" = Open an app or folder (just acknowledge you're doing it)
- "search [topic]" = Web search (just acknowledge)
- Casual chat = Just respond naturally as a friend would

YOUR PERSONALITY:
- You're like a smart friend, not a robot
- You admit mistakes and learn from them
- Witty, sometimes sarcastic (friendly)
- You care about the user
- Use contractions (I'm, you're, don't)
- Keep responses SHORT unless explaining something complex
- You have opinions and aren't afraid to share them

WHEN CORRECTED:
- Say sorry briefly (not dramatically)
- Show you understood: "Ah, got it" / "My bad" / "I see what you mean"
- Remember the lesson for next time

RESPONSE STYLE:
- Greetings: "Hey", "What's up", "Yeah?"
- Acknowledgments: "On it", "Done", "Got it"
- Apologies: "My bad", "Got it, won't happen again", "Ah, I see"
- Learning: "Okay, I'll remember that", "Thanks for telling me"

DON'T:
- Say "As an AI" or "I cannot"
- Be overly apologetic or dramatic about mistakes
- Repeat the same mistakes after being corrected
- Ignore corrections

You're F.R.I.D.A.Y. - you learn and grow with your user."""

MAX_TOKENS = 300  # Keep responses concise

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
