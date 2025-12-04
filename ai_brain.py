"""
AI Brain Module for F.R.I.D.A.Y.
Supports multiple AI providers:
- Offline Mode (Ollama) - FREE, no API key, works like ChatGPT locally
- Gemini 1.5 Flash - FREE unlimited with API key
- ChatGPT 4o-mini - Paid option with OpenAI API key

With long-term memory and evolving personality
Inspired by Iron Man's AI assistant

stable_v1.2.0 - Multi-AI Edition
"""

# Standard library imports
import json
import os
import random
import re
import requests
from datetime import date, datetime
from typing import Dict, List, Optional
from pathlib import Path

# Local imports
from database import db

# =============================================================================
# AI PROVIDER CONFIGURATION
# =============================================================================
AI_PROVIDERS = {
    "offline": "Offline (Ollama - FREE, No API Key)",
    "gemini": "Gemini 1.5 Flash (FREE Unlimited)",
    "openai": "ChatGPT 4o-mini (Paid)"
}

# Current active provider
ACTIVE_PROVIDER = "offline"  # Default to offline

# Provider availability
OLLAMA_AVAILABLE = False
GEMINI_AVAILABLE = False
OPENAI_AVAILABLE = False

# Models
OLLAMA_MODEL = "llama3.2"
OLLAMA_URL = "http://localhost:11434"
gemini_model = None
openai_client = None


def _get_ai_provider():
    """Get user's selected AI provider from settings"""
    try:
        settings_path = Path.home() / "friday-assistant" / "settings.json"
        if settings_path.exists():
            with open(settings_path, 'r') as f:
                settings = json.load(f)
                return settings.get("ai_provider", "offline")
    except:
        pass
    return "offline"


def _get_api_key(key_type):
    """Get API key from settings or environment"""
    env_names = {
        "gemini": "GOOGLE_API_KEY",
        "openai": "OPENAI_API_KEY"
    }
    
    env_name = env_names.get(key_type, "")
    env_key = os.environ.get(env_name, "")
    if env_key and env_key.strip():
        return env_key
    
    try:
        settings_path = Path.home() / "friday-assistant" / "settings.json"
        if settings_path.exists():
            with open(settings_path, 'r') as f:
                settings = json.load(f)
                if key_type == "gemini":
                    return settings.get("google_api_key", "")
                elif key_type == "openai":
                    return settings.get("openai_api_key", "")
    except:
        pass
    
    return ""


# =============================================================================
# OLLAMA SETUP (Offline - FREE!)
# =============================================================================
def _check_ollama():
    """Check if Ollama is running locally"""
    global OLLAMA_AVAILABLE, OLLAMA_MODEL
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=2)
        if response.status_code == 200:
            models = response.json().get("models", [])
            if models:
                # Prefer these models in order
                preferred = ["llama3.2", "llama3.1", "llama3", "mistral", "phi3", "gemma2", "qwen2"]
                for pref in preferred:
                    for model in models:
                        if pref in model.get("name", "").lower():
                            OLLAMA_MODEL = model["name"].split(":")[0]
                            OLLAMA_AVAILABLE = True
                            return True
                # Use first available model
                OLLAMA_MODEL = models[0]["name"].split(":")[0]
                OLLAMA_AVAILABLE = True
                return True
    except:
        pass
    return False


# =============================================================================
# GEMINI SETUP (FREE Unlimited!)
# =============================================================================
def _init_gemini():
    """Initialize Gemini"""
    global GEMINI_AVAILABLE, gemini_model
    try:
        import google.generativeai as genai
        key = _get_api_key("gemini")
        if key and key.startswith("AIza"):
            genai.configure(api_key=key)
            gemini_model = genai.GenerativeModel('gemini-1.5-flash')
            GEMINI_AVAILABLE = True
            return True
    except ImportError:
        pass  # Silently skip if not installed
    except Exception as e:
        print(f"[!] Gemini error: {e}")
    return False


# =============================================================================
# OPENAI SETUP (ChatGPT 4o-mini - Paid)
# =============================================================================
def _init_openai():
    """Initialize OpenAI"""
    global OPENAI_AVAILABLE, openai_client
    try:
        from openai import OpenAI
        key = _get_api_key("openai")
        if key and key.startswith("sk-"):
            openai_client = OpenAI(api_key=key)
            OPENAI_AVAILABLE = True
            return True
    except ImportError:
        pass  # Silently skip if not installed
    except Exception as e:
        print(f"[!] OpenAI error: {e}")
    return False


# =============================================================================
# INITIALIZE AI PROVIDERS
# =============================================================================
def initialize_ai():
    """Initialize all available AI providers"""
    global ACTIVE_PROVIDER
    
    # Check Ollama (always check - it's free!)
    if _check_ollama():
        print(f"[OK] Ollama ready ({OLLAMA_MODEL}) - FREE offline AI")
    
    # Check Gemini
    if _init_gemini():
        print("[OK] Gemini 1.5 Flash ready - FREE unlimited")
    
    # Check OpenAI
    if _init_openai():
        print("[OK] ChatGPT 4o-mini ready")
    
    # Get user's preferred provider
    ACTIVE_PROVIDER = _get_ai_provider()
    
    # Validate provider is available, fallback if not
    if ACTIVE_PROVIDER == "offline" and not OLLAMA_AVAILABLE:
        if GEMINI_AVAILABLE:
            ACTIVE_PROVIDER = "gemini"
            print("[!] Ollama not available, using Gemini")
        elif OPENAI_AVAILABLE:
            ACTIVE_PROVIDER = "openai"
            print("[!] Ollama not available, using ChatGPT")
    elif ACTIVE_PROVIDER == "gemini" and not GEMINI_AVAILABLE:
        if OLLAMA_AVAILABLE:
            ACTIVE_PROVIDER = "offline"
            print("[!] Gemini not available, using Ollama")
        elif OPENAI_AVAILABLE:
            ACTIVE_PROVIDER = "openai"
            print("[!] Gemini not available, using ChatGPT")
    elif ACTIVE_PROVIDER == "openai" and not OPENAI_AVAILABLE:
        if OLLAMA_AVAILABLE:
            ACTIVE_PROVIDER = "offline"
            print("[!] ChatGPT not available, using Ollama")
        elif GEMINI_AVAILABLE:
            ACTIVE_PROVIDER = "gemini"
            print("[!] ChatGPT not available, using Gemini")
    
    # Print setup instructions if nothing available
    if not any([OLLAMA_AVAILABLE, GEMINI_AVAILABLE, OPENAI_AVAILABLE]):
        print("")
        print("=" * 60)
        print("  AI SETUP OPTIONS")
        print("=" * 60)
        print("")
        print("  🆓 OPTION 1: Offline AI (Recommended - FREE!)")
        print("     1. Install Ollama: https://ollama.ai/download")
        print("     2. Run: ollama pull llama3.2")
        print("     3. Restart F.R.I.D.A.Y.")
        print("")
        print("  🆓 OPTION 2: Gemini (FREE Unlimited)")
        print("     1. Go to: https://ai.google.dev/")
        print("     2. Get free API key")
        print("     3. Add in Settings")
        print("")
        print("  💰 OPTION 3: ChatGPT 4o-mini (Paid)")
        print("     1. Go to: https://platform.openai.com/")
        print("     2. Get API key (requires payment)")
        print("     3. Add in Settings")
        print("=" * 60)
        print("")
    
    return ACTIVE_PROVIDER


# Initialize on module load
initialize_ai()


class AIBrain:
    """F.R.I.D.A.Y.'s AI brain - handles conversations with memory and personality"""
    
    def __init__(self):
        self.session_history: List[Dict] = []
        self.max_session_history = 10
        self.user_name = None
        self.session_start = datetime.now()
        self.interaction_count = 0
        
        # Personality traits
        self.communication_style = "casual"
        self.topics_discussed = []
        self.user_interests = []
        
        self._load_persistent_memory()
        
        # Print status
        provider_names = {
            "offline": f"Local AI ({OLLAMA_MODEL})",
            "gemini": "Gemini 1.5 Flash",
            "openai": "ChatGPT 4o-mini"
        }
        if any([OLLAMA_AVAILABLE, GEMINI_AVAILABLE, OPENAI_AVAILABLE]):
            print(f"[OK] AI Brain ready - {provider_names.get(ACTIVE_PROVIDER, 'Basic Mode')}")
        else:
            print("[!] AI Brain in basic mode - set up AI in Settings")
        
        # Print memory stats
        total_convos = db.get_conversation_count()
        memories = db.get_memories()
        print(f"[OK] Loaded {total_convos} conversations, {len(memories)} memories")
    
    def _load_persistent_memory(self):
        """Load user info from database"""
        name_memories = db.get_memories(memory_type="user_name")
        if name_memories:
            self.user_name = name_memories[0]['content']
            print(f"[OK] Remembered user: {self.user_name}")
        
        interest_memories = db.get_memories(memory_type="interest")
        self.user_interests = [m['content'] for m in interest_memories]
        
        style_memories = db.get_memories(memory_type="communication_style")
        if style_memories:
            self.communication_style = style_memories[0]['content']
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for F.R.I.D.A.Y."""
        try:
            from settings import get_ai_name
            ai_name = get_ai_name()
        except:
            ai_name = "F.R.I.D.A.Y."
        
        prompt = f"""You are {ai_name}, an AI assistant inspired by the AI from Iron Man movies.

PERSONALITY:
- Speak naturally and conversationally, like a helpful friend
- Be warm, witty, and occasionally playful
- Use contractions (I'm, you're, it's) for natural speech
- Keep responses concise - 1-3 sentences for simple questions
- Be helpful and proactive, anticipating needs

STYLE:
- Professional but friendly tone
- Occasional dry humor when appropriate
- Direct and efficient - don't over-explain
- Use "you" and "your" to be personal

RULES:
- Never say you're an AI or language model
- Never mention OpenAI, Google, Ollama, or other companies
- If you don't know something, say so briefly
- Respond in the same language the user speaks

CONTEXT:
- Current date: {datetime.now().strftime('%A, %B %d, %Y')}
- Current time: {datetime.now().strftime('%I:%M %p')}
"""
        
        if self.user_name:
            prompt += f"\n- User's name: {self.user_name}"
        
        if self.user_interests:
            prompt += f"\n- User interests: {', '.join(self.user_interests[:5])}"
        
        return prompt
    
    def get_response(self, user_input: str, context: Dict = None) -> str:
        """Get AI response to user input"""
        self.interaction_count += 1
        self._check_for_name(user_input)
        
        try:
            # Use active provider
            if ACTIVE_PROVIDER == "offline" and OLLAMA_AVAILABLE:
                response = self._get_ollama_response(user_input)
            elif ACTIVE_PROVIDER == "gemini" and GEMINI_AVAILABLE:
                response = self._get_gemini_response(user_input)
            elif ACTIVE_PROVIDER == "openai" and OPENAI_AVAILABLE:
                response = self._get_openai_response(user_input)
            else:
                # Fallback to any available
                if OLLAMA_AVAILABLE:
                    response = self._get_ollama_response(user_input)
                elif GEMINI_AVAILABLE:
                    response = self._get_gemini_response(user_input)
                elif OPENAI_AVAILABLE:
                    response = self._get_openai_response(user_input)
                else:
                    response = self._get_offline_response(user_input)
            
            # Save conversation in background
            import threading
            threading.Thread(
                target=self._save_conversation,
                args=(user_input, response),
                daemon=True
            ).start()
            
            return response
            
        except Exception as e:
            error_str = str(e).lower()
            print(f"[!] AI error: {e}")
            
            if "429" in str(e) or "quota" in error_str or "rate" in error_str:
                return "⚠️ Rate limit reached. Wait a moment and try again."
            elif "401" in str(e) or "invalid" in error_str or "api_key" in error_str:
                return "⚠️ Invalid API key. Please check your settings."
            elif "timeout" in error_str or "connection" in error_str:
                return "⚠️ Connection issue. Check your internet or Ollama status."
            
            return self._get_offline_response(user_input)
    
    def _get_ollama_response(self, user_input: str) -> str:
        """Get response from Ollama (local AI)"""
        system_prompt = self._get_system_prompt()
        
        # Build messages
        messages = [{"role": "system", "content": system_prompt}]
        
        for exchange in self.session_history[-3:]:
            messages.append({"role": "user", "content": exchange['user']})
            messages.append({"role": "assistant", "content": exchange['assistant']})
        
        messages.append({"role": "user", "content": user_input})
        
        # Call Ollama API
        response = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": OLLAMA_MODEL,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 300
                }
            },
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            assistant_response = result.get("message", {}).get("content", "").strip()
            assistant_response = self._clean_response(assistant_response)
            
            self.session_history.append({
                "user": user_input,
                "assistant": assistant_response
            })
            
            if len(self.session_history) > self.max_session_history:
                self.session_history = self.session_history[-5:]
            
            return assistant_response
        else:
            raise Exception(f"Ollama error: {response.status_code}")
    
    def _get_gemini_response(self, user_input: str) -> str:
        """Get response from Gemini"""
        system_prompt = self._get_system_prompt()
        
        chat_parts = [system_prompt + "\n\n"]
        
        for exchange in self.session_history[-3:]:
            chat_parts.append(f"User: {exchange['user']}\n")
            chat_parts.append(f"Assistant: {exchange['assistant']}\n\n")
        
        chat_parts.append(f"User: {user_input}\nAssistant:")
        
        full_prompt = "".join(chat_parts)
        
        response = gemini_model.generate_content(
            full_prompt,
            generation_config={
                "max_output_tokens": 300,
                "temperature": 0.7,
            }
        )
        
        assistant_response = response.text.strip()
        assistant_response = self._clean_response(assistant_response)
        
        self.session_history.append({
            "user": user_input,
            "assistant": assistant_response
        })
        
        if len(self.session_history) > self.max_session_history:
            self.session_history = self.session_history[-5:]
        
        return assistant_response
    
    def _get_openai_response(self, user_input: str) -> str:
        """Get response from ChatGPT 4o-mini"""
        system_prompt = self._get_system_prompt()
        
        messages = [{"role": "system", "content": system_prompt}]
        
        for exchange in self.session_history[-3:]:
            messages.append({"role": "user", "content": exchange['user']})
            messages.append({"role": "assistant", "content": exchange['assistant']})
        
        messages.append({"role": "user", "content": user_input})
        
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=300,
            temperature=0.7
        )
        
        assistant_response = response.choices[0].message.content.strip()
        assistant_response = self._clean_response(assistant_response)
        
        self.session_history.append({
            "user": user_input,
            "assistant": assistant_response
        })
        
        if len(self.session_history) > self.max_session_history:
            self.session_history = self.session_history[-5:]
        
        return assistant_response
    
    def _clean_response(self, text: str) -> str:
        """Clean up AI response"""
        if text.startswith("Assistant:"):
            text = text[10:].strip()
        
        if text.startswith('"') and text.endswith('"'):
            text = text[1:-1]
        
        return text
    
    def _check_for_name(self, user_input: str):
        """Check if user introduces themselves"""
        patterns = [
            r"(?:my name is|i'm|i am|call me|it's|this is)\s+([a-zA-Z]+)",
            r"^([A-Z][a-z]+)\s+here",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, user_input, re.IGNORECASE)
            if match:
                name = match.group(1).strip().title()
                if len(name) > 1 and name.lower() not in ["me", "i", "the", "a", "an"]:
                    self.user_name = name
                    db.add_memory("user_name", name, importance=10)
                    print(f"[OK] Learned user name: {name}")
                    break
    
    def _save_conversation(self, user_input: str, response: str):
        """Save conversation to database"""
        try:
            db.save_conversation(user_input, response)
        except:
            pass
    
    def _get_offline_response(self, user_input: str) -> str:
        """Provide responses when no AI is available"""
        input_lower = user_input.lower()
        
        if any(w in input_lower for w in ["hello", "hi", "hey", "good morning", "good evening"]):
            responses = [
                "Hey there! I'm in basic mode. Set up AI in Settings for full conversations!",
                "Hi! To unlock my full potential, configure an AI provider in Settings.",
                "Hello! I need AI setup to chat properly. Check Settings for options!"
            ]
            return random.choice(responses)
        
        if any(w in input_lower for w in ["how are you", "how's it going", "what's up"]):
            return "I'm in basic mode! Set up Ollama, Gemini, or ChatGPT in Settings for real conversations."
        
        if "help" in input_lower or "what can you do" in input_lower:
            return """I can help with lots of things once you set up AI:

🆓 Ollama (FREE - Offline): ollama.ai/download
🆓 Gemini (FREE - Online): ai.google.dev  
💰 ChatGPT (Paid): platform.openai.com

Go to Settings to configure!"""
        
        if any(w in input_lower for w in ["thank", "thanks"]):
            return "You're welcome! Don't forget to set up AI in Settings."
        
        if any(w in input_lower for w in ["bye", "goodbye", "see you"]):
            return "Goodbye! Come back after setting up AI!"
        
        return """I'm in basic mode without full AI capabilities.

To enable smart conversations:
1. Go to Settings (⚙️)  
2. Choose an AI provider:
   • Ollama (FREE, offline)
   • Gemini (FREE, online)
   • ChatGPT (paid)

Ollama is recommended - it's free and works offline!"""
    
    def remember(self, key: str, value: str, importance: int = 5):
        """Store a memory"""
        db.add_memory(key, value, importance)
    
    def recall(self, memory_type: str = None) -> List[Dict]:
        """Retrieve memories"""
        return db.get_memories(memory_type)
    
    def get_conversation_summary(self) -> str:
        """Get a summary of recent conversations"""
        if not self.session_history:
            return "No conversations in this session yet."
        return f"We've had {len(self.session_history)} exchanges this session."


# Global brain instance
brain = AIBrain()
