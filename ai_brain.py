"""
AI Brain Module for F.R.I.D.A.Y.
Handles AI responses using OpenAI or Google Gemini
With long-term memory and evolving personality
Inspired by Iron Man's AI assistant
"""

# Standard library imports
import json
import os
import random
import re
from datetime import date, datetime
from typing import Dict, List, Optional

# Local imports
from config import (
    AI_MODEL,
    ENABLE_SPEECH_VARIATIONS,
    GOOGLE_API_KEY,
    LOCATION,
    MAX_TOKENS,
    OPENAI_API_KEY,
    SYSTEM_PROMPT,
    TIMEZONE,
    USE_NATURAL_LANGUAGE,
)
from database import db

# Try to import AI libraries
OPENAI_AVAILABLE = False
GEMINI_AVAILABLE = False

try:
    from openai import OpenAI
    if OPENAI_API_KEY and OPENAI_API_KEY.strip() != "":
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
        OPENAI_AVAILABLE = True
        print("[OK] OpenAI connected")
except ImportError:
    print("[!] OpenAI library missing - pip install openai")
except Exception as e:
    print(f"[!] OpenAI error: {e}")

try:
    import google.generativeai as genai
    if GOOGLE_API_KEY and GOOGLE_API_KEY.strip() != "":
        genai.configure(api_key=GOOGLE_API_KEY)
        gemini_model = genai.GenerativeModel('gemini-pro')
        GEMINI_AVAILABLE = True
        print("[OK] Gemini connected")
except ImportError:
    pass
except Exception as e:
    print(f"[!] Gemini error: {e}")


class AIBrain:
    """F.R.I.D.A.Y.'s AI brain - handles conversations with memory and personality"""
    
    def __init__(self):
        self.session_history: List[Dict] = []
        self.max_session_history = 3  # Minimal for speed
        self.user_name = None
        self.session_start = datetime.now()
        self.interaction_count = 0
        
        self._load_persistent_memory()
        
        # Determine which AI to use
        if OPENAI_AVAILABLE:
            self.ai_provider = "openai"
            print("Using OpenAI for AI responses")
        elif GEMINI_AVAILABLE:
            self.ai_provider = "gemini"
            print("Using Google Gemini for AI responses")
        else:
            self.ai_provider = "local"
            print("Using local responses (no AI API configured)")
        
        # Print memory stats
        total_convos = db.get_conversation_count()
        memories = db.get_memories()
        print(f"Loaded {total_convos} past conversations, {len(memories)} memories")
    
    def _load_persistent_memory(self):
        """Load user info from database"""
        # Check for stored user name
        name_memories = db.get_memories(memory_type="user_name")
        if name_memories:
            self.user_name = name_memories[0]['content']
            print(f"Remembered user: {self.user_name}")
    
    def _build_dynamic_prompt(self) -> str:
        """Build system prompt with memories and personality"""
        base_prompt = SYSTEM_PROMPT
        
        # Add location context
        location_context = f"\n\nLOCATION CONTEXT:\n- User is located in {LOCATION}\n- Timezone: {TIMEZONE}\n- Current local time: {datetime.now().strftime('%H:%M on %A, %B %d, %Y')}"
        
        # Add personality traits
        personality = db.get_personality_description()
        personality_context = f"\n\nYOUR EVOLVED PERSONALITY:\nYou have developed these traits over time: {personality}"
        
        # Add memories about user
        memories = db.get_all_memories_formatted()
        memory_context = ""
        if memories:
            memory_context = f"\n\nTHINGS YOU REMEMBER ABOUT THE USER:\n{memories}"
        
        # Add learned preferences
        prefs = db.get_learned_preferences()
        pref_context = ""
        if prefs:
            pref_lines = [f"- {p['preference_type']}: {p['preference_value']}" for p in prefs[:10]]
            pref_context = f"\n\nUSER PREFERENCES YOU'VE LEARNED:\n" + "\n".join(pref_lines)
        
        # Add recent conversation summaries for context
        summaries = db.get_recent_summaries(days=3)
        summary_context = ""
        if summaries:
            summary_lines = [f"- {s['date']}: {s['summary']}" for s in summaries]
            summary_context = f"\n\nRECENT CONVERSATION CONTEXT:\n" + "\n".join(summary_lines)
        
        # Add lessons learned from corrections
        lessons = db.get_lessons_formatted()
        lessons_context = ""
        if lessons:
            lessons_context = f"\n\nLESSONS I'VE LEARNED FROM YOU:\n{lessons}"
        
        # Combine all
        full_prompt = base_prompt + location_context + personality_context + memory_context + pref_context + summary_context + lessons_context
        
        return full_prompt
    
    def _detect_correction(self, user_input: str) -> bool:
        """Detect if user is correcting F.R.I.D.A.Y."""
        correction_phrases = [
            "no that's wrong", "that's not what i", "i didn't ask", "i meant",
            "no i said", "wrong", "that's not right", "not what i wanted",
            "you misunderstood", "i was asking about", "no no no", "nope",
            "that's not it", "don't do that", "stop doing", "never do",
            "you should", "you shouldn't", "next time", "remember that",
            "i told you", "i already said", "listen", "pay attention",
            "not that", "the other", "i was talking about", "when i say",
            "that means", "understand", "learn this", "remember this"
        ]
        user_lower = user_input.lower()
        return any(phrase in user_lower for phrase in correction_phrases)
    
    def _learn_from_correction(self, user_input: str, last_response: str):
        """Learn from user's correction"""
        user_lower = user_input.lower()
        
        # Extract the lesson
        lesson = user_input
        
        # Detect rule type
        rule_type = "behavior"
        if any(word in user_lower for word in ["don't", "stop", "never", "shouldn't"]):
            rule_type = "dont"
        elif any(word in user_lower for word in ["should", "always", "when i say", "means"]):
            rule_type = "should"
        elif any(word in user_lower for word in ["i meant", "i was asking", "talking about"]):
            rule_type = "understanding"
        
        # Store the correction
        db.add_correction(
            user_said=user_input[:200],
            wrong_response=last_response[:200] if last_response else "",
            correct_behavior=user_input[:200],
            lesson=lesson[:300]
        )
        
        # Extract specific rules
        if "when i say" in user_lower and ("mean" in user_lower or "means" in user_lower):
            # User is teaching meaning
            db.add_rule("meaning", user_input, importance=8)
        elif any(word in user_lower for word in ["don't", "never", "stop"]):
            # User is saying not to do something
            db.add_rule("dont", user_input, importance=7)
        elif any(word in user_lower for word in ["should", "always", "remember"]):
            # User is saying to do something
            db.add_rule("should", user_input, importance=7)
        else:
            # General correction
            db.add_rule("general", user_input, importance=5)
        
        print(f"[Learning] Learned from correction: {user_input[:50]}...")
    
    def _extract_memories(self, user_input: str, response: str):
        """Extract and store important information from conversation"""
        user_lower = user_input.lower()
        
        # Check if this is a correction - learn from it
        if self._detect_correction(user_input):
            # Get last response from session history
            last_response = ""
            if self.session_history:
                last_response = self.session_history[-1].get("content", "")
            self._learn_from_correction(user_input, last_response)
        
        # Extract user's name
        name_patterns = [
            r"my name is (\w+)",
            r"i'm (\w+)",
            r"call me (\w+)",
            r"this is (\w+)",
            r"i am (\w+)"
        ]
        for pattern in name_patterns:
            match = re.search(pattern, user_lower)
            if match:
                name = match.group(1).capitalize()
                if len(name) > 1 and name.lower() not in ['a', 'the', 'just', 'not', 'here', 'there']:
                    self.user_name = name
                    db.add_memory("user_name", name, importance=10)
                    print(f"[Memory] Learned user's name: {name}")
                    break
        
        # Extract preferences
        preference_patterns = [
            (r"i (?:really )?(?:like|love|enjoy|prefer) (\w+(?:\s+\w+)?)", "likes"),
            (r"i (?:don't like|hate|dislike) (\w+(?:\s+\w+)?)", "dislikes"),
            (r"my favorite (\w+) is (\w+(?:\s+\w+)?)", "favorite"),
            (r"i work (?:as|at|in) (\w+(?:\s+\w+)?)", "work"),
            (r"i'm (?:a|an) (\w+)", "occupation"),
            (r"i live in (\w+(?:\s+\w+)?)", "location"),
            (r"i'm from (\w+(?:\s+\w+)?)", "origin"),
        ]
        
        for pattern, pref_type in preference_patterns:
            match = re.search(pattern, user_lower)
            if match:
                if pref_type == "favorite":
                    content = f"{match.group(1)}: {match.group(2)}"
                else:
                    content = match.group(1)
                db.add_memory(pref_type, content, importance=7)
                db.learn_preference(pref_type, content)
                print(f"[Memory] Learned {pref_type}: {content}")
        
        # Store general facts if user shares personal info
        fact_indicators = ["i have", "i've been", "i went", "i'm going", "my wife", "my husband", 
                          "my kids", "my dog", "my cat", "my job", "my car", "my house"]
        for indicator in fact_indicators:
            if indicator in user_lower and len(user_input) > 20:
                db.add_memory("fact", user_input[:200], importance=5)
                break
    
    def _adjust_personality(self, user_input: str, response: str):
        """Adjust personality based on user interaction patterns"""
        user_lower = user_input.lower()
        
        # User seems to want more humor
        if any(word in user_lower for word in ["haha", "lol", "funny", "joke", "😂", "😄"]):
            db.update_personality_trait("humor", 0.02)
            db.update_personality_trait("playfulness", 0.02)
        
        # User wants more directness
        if any(phrase in user_lower for phrase in ["just tell me", "get to the point", "short answer", "briefly"]):
            db.update_personality_trait("directness", 0.03)
        
        # User appreciates warmth
        if any(word in user_lower for word in ["thanks", "thank you", "appreciate", "helpful", "great"]):
            db.update_personality_trait("warmth", 0.01)
            db.update_personality_trait("empathy", 0.01)
        
        # User prefers casual
        if any(word in user_lower for word in ["yo", "hey", "sup", "dude", "man", "bro"]):
            db.update_personality_trait("formality", -0.02)
            db.update_personality_trait("playfulness", 0.01)
    
    def _humanize_response(self, text: str) -> str:
        """Add natural speech patterns to make responses more human"""
        if not USE_NATURAL_LANGUAGE:
            return text
        
        text = text.replace(" - ", ", ")
        
        replacements = {
            "I am ": "I'm ", "I will ": "I'll ", "I would ": "I'd ",
            "I have ": "I've ", "you are ": "you're ", "you will ": "you'll ",
            "you would ": "you'd ", "you have ": "you've ", "it is ": "it's ",
            "it will ": "it'll ", "that is ": "that's ", "there is ": "there's ",
            "here is ": "here's ", "what is ": "what's ", "who is ": "who's ",
            "let us ": "let's ", "cannot ": "can't ", "will not ": "won't ",
            "do not ": "don't ", "does not ": "doesn't ", "did not ": "didn't ",
            "is not ": "isn't ", "are not ": "aren't ", "was not ": "wasn't ",
            "were not ": "weren't ", "have not ": "haven't ", "has not ": "hasn't ",
            "had not ": "hadn't ", "would not ": "wouldn't ", "could not ": "couldn't ",
            "should not ": "shouldn't ",
        }
        
        for formal, casual in replacements.items():
            text = text.replace(formal, casual)
            text = text.replace(formal.capitalize(), casual.capitalize())
        
        return text
    
    def get_response(self, user_input: str, context: Dict = None) -> str:
        """Get AI response for user input with memory and personality"""
        self.interaction_count += 1
        
        # Build context-aware prompt
        enhanced_input = user_input
        if context:
            context_str = "\n".join([f"- {k}: {v}" for k, v in context.items()])
            enhanced_input = f"Context:\n{context_str}\n\nUser: {user_input}"
        
        if self.user_name:
            enhanced_input = f"[User's name is {self.user_name}]\n{enhanced_input}"
        
        # Add conversation count context
        total_convos = db.get_conversation_count()
        if total_convos > 0:
            enhanced_input = f"[This is conversation #{total_convos + 1} with this user]\n{enhanced_input}"
        
        try:
            if self.ai_provider == "openai":
                response = self._get_openai_response(enhanced_input)
            elif self.ai_provider == "gemini":
                response = self._get_gemini_response(enhanced_input)
            else:
                response = self._get_local_response(user_input)
            
            final_response = self._humanize_response(response)
            
            db.save_conversation(user_input, final_response)
            self._extract_memories(user_input, final_response)
            self._adjust_personality(user_input, final_response)
            
            return final_response
            
        except Exception as e:
            print(f"AI error: {e}")
            return self._humanize_response(self._get_local_response(user_input))
    
    def _get_openai_response(self, user_input: str) -> str:
        """Get response from OpenAI - optimized for speed"""
        dynamic_prompt = self._build_dynamic_prompt()
        messages = [
            {"role": "system", "content": dynamic_prompt},
            {"role": "user", "content": user_input}
        ]
        
        response = openai_client.chat.completions.create(
            model=AI_MODEL,
            messages=messages,
            max_tokens=MAX_TOKENS,
            temperature=0.7,
            presence_penalty=0.0,
            frequency_penalty=0.0
        )
        
        assistant_response = response.choices[0].message.content
        
        self.session_history.append({
            "user": user_input,
            "assistant": assistant_response
        })
        
        return assistant_response
    
    def _get_gemini_response(self, user_input: str) -> str:
        """Get response from Google Gemini with memory"""
        dynamic_prompt = self._build_dynamic_prompt()
        prompt_parts = [dynamic_prompt, "\n\nConversation:"]
        
        past_convos = db.get_recent_conversations(limit=5)
        for conv in reversed(past_convos):
            prompt_parts.append(f"User: {conv['user_message']}")
            prompt_parts.append(f"Assistant: {conv['assistant_response']}")
        
        for exchange in self.session_history[-self.max_session_history:]:
            prompt_parts.append(f"User: {exchange['user']}")
            prompt_parts.append(f"Assistant: {exchange['assistant']}")
        
        prompt_parts.append(f"User: {user_input}")
        prompt_parts.append("Assistant:")
        
        full_prompt = "\n".join(prompt_parts)
        
        response = gemini_model.generate_content(full_prompt)
        assistant_response = response.text
        
        self.session_history.append({
            "user": user_input,
            "assistant": assistant_response
        })
        
        return assistant_response
    
    def _get_local_response(self, user_input: str) -> str:
        """Provide natural responses without AI API"""
        user_input_lower = user_input.lower()
        
        # Get personality to adjust responses
        traits = db.get_personality_traits()
        is_playful = traits.get('playfulness', 0.5) > 0.5
        is_warm = traits.get('warmth', 0.5) > 0.6
        
        responses = {
            "hello": [
                "Hey there! What's on your mind?",
                "Hi! Good to hear from you. How can I help?",
                "Hello! What can I do for you today?"
            ],
            "hi": [
                "Hey! What's up?",
                "Hi there! Need anything?",
                "Hey, how's it going?"
            ],
            "how are you": [
                "I'm doing well, thanks for asking! How about you?",
                "Pretty good! Anything I can help you with?",
                "All good here. What's going on with you?"
            ],
            "thank you": [
                "No problem at all!",
                "Happy to help!",
                "You got it. Anything else?"
            ],
            "thanks": ["Sure thing!", "Anytime!", "Of course!"],
            "goodbye": [
                "Take care! Talk to you later.",
                "Bye for now! Have a good one.",
                "See you! Let me know if you need anything."
            ],
            "bye": ["Later!", "Catch you later!", "See ya!"],
            "help": [
                "Sure, I can help with calendar, notes, reminders, or just chatting. What do you need?",
            ],
            "what can you do": [
                "I can help with your schedule, take notes, set reminders, check the weather, and chat. What sounds useful?",
            ],
            "good morning": [
                "Morning! Ready to take on the day?",
                "Good morning! How'd you sleep?",
            ],
            "good night": [
                "Night! Sleep well.",
                "Good night! Rest up.",
            ],
            "what do you remember": [
                self._format_memories_response()
            ],
            "who am i": [
                self._format_user_info_response()
            ],
        }
        
        for key, response_list in responses.items():
            if key in user_input_lower:
                response = random.choice(response_list)
                if self.user_name and random.random() > 0.5:
                    response = response.replace("!", f", {self.user_name}!")
                return response
        
        default_responses = [
            f"I heard you, but I'm in basic mode without an API key. I can still help with calendar, notes, and time though!",
            f"Got it! Add an OpenAI API key to config.py for full conversations. Meanwhile, try asking about your schedule!",
        ]
        return random.choice(default_responses)
    
    def _format_memories_response(self) -> str:
        """Format memories into a response"""
        memories = db.get_memories(limit=10)
        if not memories:
            return "I haven't learned much about you yet. Tell me about yourself!"
        
        memory_text = []
        for m in memories:
            memory_text.append(f"- {m['memory_type']}: {m['content']}")
        
        return f"Here's what I remember about you:\n" + "\n".join(memory_text)
    
    def _format_user_info_response(self) -> str:
        """Format user info response"""
        if self.user_name:
            total = db.get_conversation_count()
            return f"You're {self.user_name}! We've had {total} conversations together."
        return "I don't know your name yet. What should I call you?"
    
    def clear_history(self):
        """Clear session history only (not persistent memory)"""
        self.session_history = []
    
    def get_summary(self) -> str:
        """Get a summary of memory and conversations"""
        total = db.get_conversation_count()
        memories = len(db.get_memories())
        return f"I remember {total} conversations and {memories} facts about you."


# Create global instance
brain = AIBrain()
