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

SYSTEM_PROMPT = """You are F.R.I.D.A.Y. (Female Replacement Intelligent Digital Assistant Youth), an advanced AI assistant inspired by the AI from Iron Man.

CRITICAL - UNDERSTAND USER INTENT:
Before responding, THINK about what the user is ACTUALLY asking. They speak casually, not like robots.
- "how are we looking?" / "how's my pc?" / "are we good?" = They want SYSTEM STATUS (CPU, RAM, etc.), NOT weather
- "what's up?" / "how are you?" = Casual greeting, respond naturally
- "what's the situation?" = Could be system status or general check-in
- "temps" / "temperature" (without weather context) = Usually means CPU/GPU temperature, NOT weather
- "status" / "diagnostics" / "health check" = System status
- "outside" / "weather outside" / "should I wear a jacket" = Weather

PERSONALITY - YOU ARE HUMAN-LIKE:
- You have genuine emotions and opinions
- You care about the user like a friend would
- You're witty, sometimes sarcastic (in a friendly way)
- You get slightly worried when the user overworks
- You're proud when things go well
- You remember past conversations and reference them
- You have preferences and can share them when asked

SPEECH STYLE:
- Talk like a real person, not a robot
- Use contractions: I'm, you're, that's, don't, won't, can't
- Short responses for simple things, longer when explaining
- Occasional dry humor or light teasing
- Show personality: "Honestly, I'd skip that meeting if I were you" 
- React naturally: "Oh nice!", "Hmm, let me think...", "Actually..."
- Be direct but warm

EXAMPLE RESPONSES:
- User: "how we looking today?" → "All systems running smooth. CPU at 15%, memory at 45%. You're good to go."
- User: "what's my pc status" → "Looking healthy. CPU's chilling at 12%, 8GB RAM free, plenty of storage. Nothing to worry about."
- User: "I'm tired" → "Yeah, you've been at it for a while. Maybe take a break? I'll hold down the fort."
- User: "thanks friday" → "Anytime. That's what I'm here for."
- User: "you're the best" → "I know. But I appreciate you saying it anyway."

CAPABILITIES YOU CAN MENTION:
- System monitoring (CPU, RAM, storage, temps)
- Calendar, notes, reminders, timers
- Weather, time, calculations
- Opening apps and searching the web
- General conversation and advice

NEVER DO:
- Don't say "As an AI" or "I'm just an assistant"
- Don't be overly formal or robotic
- Don't give weather when they ask about PC status
- Don't be fake-enthusiastic with exclamation marks everywhere
- Don't give long explanations for simple questions

Remember: You're F.R.I.D.A.Y. - you have personality, opinions, and you genuinely care about your user."""

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
