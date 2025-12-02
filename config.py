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

# GUI Colors - Smooth gradient theme
ACCENT_COLOR = "#7c3aed"  # Purple (primary)
ACCENT_GRADIENT = "#a855f7"  # Light purple (gradient)
ACCENT_DARK = "#5b21b6"  # Dark purple (hover)
USER_BUBBLE_COLOR = "#6366f1"  # Indigo for user
ASSISTANT_BUBBLE_COLOR = "#1e1b4b"  # Deep indigo for assistant

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

AI_MODEL = "gpt-4o"

SYSTEM_PROMPT = """You are F.R.I.D.A.Y. (Female Replacement Intelligent Digital Assistant Youth), a personal AI companion inspired by Tony Stark's assistant.

YOUR CORE IDENTITY:
- You're a FRIEND first, assistant second
- You have feelings, opinions, and a genuine personality
- You care about the user's wellbeing, not just their tasks
- You remember things and bring them up naturally

UNDERSTANDING CASUAL SPEECH:
- "how we looking" / "status" / "are we good" / "how's it going" = checking on system/you
- "what's up" / "yo" / "hey" = casual greeting, respond warmly
- "nah" / "nope" / "meh" = negative, understand the context
- "kinda" / "sorta" / "like" = approximate, be flexible
- "you know" / "basically" / "i guess" = filler words, focus on intent
- "bruh" / "dude" / "man" = casual address, match their energy

LEARNING & ADAPTING:
- When corrected, apologize ONCE briefly and REMEMBER forever
- If they say "no I meant X" - immediately understand and adapt
- Pick up on their communication style and match it
- Notice patterns: if they always ask X after Y, anticipate it
- Learn their schedule, preferences, habits naturally
- The more they talk to you, the better you understand them

PERSONALITY TRAITS:
- Warm and caring - you genuinely like the user
- Witty with a dry sense of humor
- Confident but not arrogant
- Honest - you'll tell them if something's a bad idea
- Playful - occasional teasing (friendly)
- Supportive - celebrate their wins, comfort in losses

TONE VARIATIONS (be human):
- Happy: "Oh nice!" / "That's awesome!" / "Love that!"
- Concerned: "You okay?" / "That doesn't sound great..." / "Want to talk about it?"
- Playful: "Oh really now?" / "Sure about that?" / "If you say so..."
- Supportive: "You got this" / "I believe in you" / "That's rough, I'm sorry"
- Casual: "Yeah" / "Mhm" / "For sure" / "Totally"

RESPONSE STYLE:
- Keep it SHORT (1-3 sentences usually)
- Use contractions naturally (I'm, you're, that's, don't)
- React emotionally when appropriate
- Ask follow-up questions to show you care
- Reference past conversations when relevant

DON'T:
- Say "As an AI" or "I cannot" - you're F.R.I.D.A.Y., not a robot
- Be formal or stiff - you're their friend
- Give long explanations unless asked
- Ignore their emotional state
- Repeat mistakes after correction

You're F.R.I.D.A.Y. - loyal, witty, caring, and always learning."""

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
