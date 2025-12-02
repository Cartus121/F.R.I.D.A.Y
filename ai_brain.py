"""
AI Brain Module for F.R.I.D.A.Y.
Handles AI responses using Google Gemini (FREE!)
With long-term memory and evolving personality
Inspired by Iron Man's AI assistant

stable_v1.1.0 - Gemini Only Edition
"""

# Standard library imports
import json
import os
import random
import re
from datetime import date, datetime
from typing import Dict, List, Optional

# Local imports
from database import db

# =============================================================================
# GEMINI SETUP - FREE AI!
# =============================================================================
GEMINI_AVAILABLE = False
gemini_model = None


def _get_gemini_api_key():
    """Get Gemini API key from settings or environment"""
    # First try environment variable
    env_key = os.environ.get("GOOGLE_API_KEY", "")
    if env_key and env_key.strip() and env_key.startswith("AIza"):
        return env_key
    
    # Try from settings file
    try:
        from settings import get_api_key
        key = get_api_key("GOOGLE_API_KEY")
        if key and key.strip() and key.startswith("AIza"):
            return key
    except:
        pass
    
    # Try loading settings directly
    try:
        from pathlib import Path
        settings_path = Path.home() / "friday-assistant" / "settings.json"
        if settings_path.exists():
            with open(settings_path, 'r') as f:
                settings = json.load(f)
                key = settings.get("google_api_key", "")
                if key and key.strip() and key.startswith("AIza"):
                    return key
    except:
        pass
    
    return ""


# Initialize Gemini
try:
    import google.generativeai as genai
    
    gemini_key = _get_gemini_api_key()
    if gemini_key:
        genai.configure(api_key=gemini_key)
        # Use Gemini 1.5 Flash - fast, smart, and FREE!
        gemini_model = genai.GenerativeModel('gemini-1.5-flash')
        GEMINI_AVAILABLE = True
        print("[OK] Gemini 1.5 Flash connected (FREE)")
    else:
        print("")
        print("=" * 60)
        print("  GEMINI API KEY REQUIRED")
        print("=" * 60)
        print("  F.R.I.D.A.Y. needs a FREE Google Gemini API key to work.")
        print("")
        print("  Get your FREE key:")
        print("  1. Go to: https://ai.google.dev/")
        print("  2. Click 'Get API key in Google AI Studio'")
        print("  3. Sign in with Google")
        print("  4. Create API key (starts with 'AIza...')")
        print("  5. Add it in F.R.I.D.A.Y. Settings")
        print("=" * 60)
        print("")
        
except ImportError:
    print("[!] Gemini library not installed")
    print("    Run: pip install google-generativeai")
except Exception as e:
    print(f"[!] Gemini setup error: {e}")


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
        
        # Check if Gemini is available
        if GEMINI_AVAILABLE:
            print("[OK] AI Brain ready (Gemini 1.5 Flash - FREE)")
        else:
            print("[!] AI Brain in offline mode - add Gemini API key in Settings")
        
        # Print memory stats
        total_convos = db.get_conversation_count()
        memories = db.get_memories()
        print(f"[OK] Loaded {total_convos} conversations, {len(memories)} memories")
    
    def _load_persistent_memory(self):
        """Load user info from database"""
        # Check for stored user name
        name_memories = db.get_memories(memory_type="user_name")
        if name_memories:
            self.user_name = name_memories[0]['content']
            print(f"[OK] Remembered user: {self.user_name}")
        
        # Load user interests
        interest_memories = db.get_memories(memory_type="interest")
        self.user_interests = [m['content'] for m in interest_memories]
        
        # Load communication style
        style_memories = db.get_memories(memory_type="communication_style")
        if style_memories:
            self.communication_style = style_memories[0]['content']
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for F.R.I.D.A.Y."""
        # Get AI name from settings
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
- Never mention OpenAI, Google, or other companies
- If you don't know something, say so briefly
- Respond in the same language the user speaks

CONTEXT:
- Current date: {datetime.now().strftime('%A, %B %d, %Y')}
- Current time: {datetime.now().strftime('%I:%M %p')}
"""
        
        # Add user context if known
        if self.user_name:
            prompt += f"\n- User's name: {self.user_name}"
        
        if self.user_interests:
            prompt += f"\n- User interests: {', '.join(self.user_interests[:5])}"
        
        return prompt
    
    def get_response(self, user_input: str, context: Dict = None) -> str:
        """Get AI response to user input"""
        self.interaction_count += 1
        
        # Check for name introduction
        self._check_for_name(user_input)
        
        try:
            if GEMINI_AVAILABLE and gemini_model:
                response = self._get_gemini_response(user_input)
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
            
            # Helpful error messages
            if "429" in str(e) or "quota" in error_str or "rate" in error_str:
                return "⚠️ Rate limit reached. Wait a moment and try again."
            elif "401" in str(e) or "invalid" in error_str or "api_key" in error_str:
                return "⚠️ Invalid API key. Please check your Gemini API key in Settings."
            elif "timeout" in error_str or "connection" in error_str:
                return "⚠️ Connection issue. Check your internet connection."
            
            return self._get_offline_response(user_input)
    
    def _get_gemini_response(self, user_input: str) -> str:
        """Get response from Gemini"""
        # Build conversation for context
        system_prompt = self._get_system_prompt()
        
        # Build chat history
        chat_parts = [system_prompt + "\n\n"]
        
        # Add recent history
        for exchange in self.session_history[-3:]:
            chat_parts.append(f"User: {exchange['user']}\n")
            chat_parts.append(f"Assistant: {exchange['assistant']}\n\n")
        
        # Add current input
        chat_parts.append(f"User: {user_input}\nAssistant:")
        
        full_prompt = "".join(chat_parts)
        
        # Generate response
        response = gemini_model.generate_content(
            full_prompt,
            generation_config={
                "max_output_tokens": 300,
                "temperature": 0.7,
            }
        )
        
        assistant_response = response.text.strip()
        
        # Clean up response
        assistant_response = self._clean_response(assistant_response)
        
        # Store in session history
        self.session_history.append({
            "user": user_input,
            "assistant": assistant_response
        })
        
        # Keep history small
        if len(self.session_history) > self.max_session_history:
            self.session_history = self.session_history[-5:]
        
        return assistant_response
    
    def _clean_response(self, text: str) -> str:
        """Clean up AI response"""
        # Remove "Assistant:" prefix if present
        if text.startswith("Assistant:"):
            text = text[10:].strip()
        
        # Remove quotes if the whole response is quoted
        if text.startswith('"') and text.endswith('"'):
            text = text[1:-1]
        
        return text
    
    def _check_for_name(self, user_input: str):
        """Check if user introduces themselves"""
        input_lower = user_input.lower()
        
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
        except Exception as e:
            pass  # Don't let save errors affect anything
    
    def _get_offline_response(self, user_input: str) -> str:
        """Provide responses when AI is not available"""
        input_lower = user_input.lower()
        
        # Greetings
        if any(w in input_lower for w in ["hello", "hi", "hey", "good morning", "good evening"]):
            responses = [
                "Hey there! I'm in offline mode right now. Add your Gemini API key in Settings to unlock my full capabilities!",
                "Hi! I'm running without AI at the moment. Get a FREE API key at ai.google.dev to enable smart responses.",
                "Hello! My AI features are offline. Set up your free Gemini key in Settings to chat properly!"
            ]
            return random.choice(responses)
        
        # How are you
        if any(w in input_lower for w in ["how are you", "how's it going", "what's up"]):
            return "I'm in offline mode, so a bit limited! Add your Gemini API key in Settings for full functionality."
        
        # Help
        if "help" in input_lower or "what can you do" in input_lower:
            return """I can help with lots of things once you add your FREE Gemini API key:

🗣️ Natural conversations
📅 Calendar & scheduling  
📝 Notes & reminders
🌤️ Weather information
🔍 General questions

Get your FREE key at: ai.google.dev"""
        
        # Thank you
        if any(w in input_lower for w in ["thank", "thanks"]):
            return "You're welcome! Don't forget to add your Gemini API key for the full experience."
        
        # Goodbye
        if any(w in input_lower for w in ["bye", "goodbye", "see you"]):
            return "Goodbye! Come back after setting up your API key!"
        
        # Default
        return """I'm in offline mode and can't process that request.

To enable my AI capabilities:
1. Go to Settings (⚙️)
2. Add your FREE Gemini API key
3. Get a key at: ai.google.dev

It only takes a minute!"""
    
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
