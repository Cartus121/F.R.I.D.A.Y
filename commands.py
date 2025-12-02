"""
Command Handler for F.R.I.D.A.Y.
AI-powered intent understanding - NO keyword detection
Let the AI understand what user wants naturally
"""

import threading
import time as time_module
from datetime import datetime, timedelta
from typing import Tuple, Dict, Any
import subprocess
import platform
import webbrowser
import json

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from config import LOCATION, TIMEZONE, DATE_FORMAT, TIME_FORMAT, WAKE_WORD
from database import db
from ai_brain import brain

# Get API keys from settings
try:
    from settings import get_api_key, play_alarm_sound, send_notification
    OPENWEATHER_API_KEY = get_api_key("OPENWEATHER_API_KEY")
except:
    try:
        from config import OPENWEATHER_API_KEY
    except:
        OPENWEATHER_API_KEY = ""
    play_alarm_sound = lambda: None
    send_notification = lambda t, m: None


# Active timers storage
active_timers: Dict[str, Dict[str, Any]] = {}


class CommandHandler:
    """Handles commands using AI for natural understanding"""
    
    def __init__(self):
        self.gui_callback = None
        self.system = platform.system()
        
    def set_gui_callback(self, callback):
        """Set callback for sending async messages to GUI"""
        self.gui_callback = callback
    
    def process(self, command: str) -> Tuple[str, bool]:
        """
        Process user input - let AI understand intent naturally
        Returns: (response_text, should_continue_listening)
        """
        command = command.strip()
        
        if not command:
            return ("I didn't catch that.", True)
        
        # Wake word only
        if command.lower() == "__wake__":
            return ("Yes? What do you need?", True)
        
        # Simple goodbye detection (exact match only)
        if command.lower() in ["goodbye", "go to sleep", "bye", "that's all"]:
            return (f"Standing by. Say '{WAKE_WORD}' when you need me.", False)
        
        # Build context for AI
        context = self._build_context()
        
        # First check if this is an action request
        action_response = self._try_execute_action(command.lower())
        if action_response:
            return (action_response, True)
        
        # Otherwise ask AI to understand and respond
        response = brain.get_response(command, context=context)
        
        return (response, True)
    
    def _build_context(self) -> Dict:
        """Build context for AI"""
        context = {
            "current_time": datetime.now().strftime(TIME_FORMAT),
            "current_date": datetime.now().strftime("%A, %B %d, %Y"),
            "location": LOCATION,
        }
        
        # Add system stats if available
        if PSUTIL_AVAILABLE:
            try:
                context["cpu_percent"] = f"{psutil.cpu_percent()}%"
                context["memory_percent"] = f"{psutil.virtual_memory().percent}%"
            except:
                pass
        
        return context
    
    def _try_execute_action(self, user_input: str) -> str:
        """
        Try to detect and execute an action from user input
        Returns response if action was taken, None otherwise
        """
        
        # === OPEN ACTIONS ===
        # Only trigger if user actually wants to open something
        wants_to_open = any(word in user_input for word in ["open", "launch", "start", "run"])
        
        if wants_to_open:
            # Apps and folders to open
            open_targets = {
                # Windows Store and Settings
                "microsoft store": ("app", "ms-windows-store:"),
                "store": ("app", "ms-windows-store:"),
                "settings": ("app", "ms-settings:"),
                "control panel": ("app", "control"),
                
                # Folders
                "downloads": ("folder", "Downloads"),
                "download": ("folder", "Downloads"),
                "documents": ("folder", "Documents"),
                "pictures": ("folder", "Pictures"),
                "photos": ("folder", "Pictures"),
                "music": ("folder", "My Music"),
                "videos": ("folder", "My Video"),
                "desktop": ("folder", "Desktop"),
                
                # System Apps
                "file explorer": ("app", "explorer"),
                "explorer": ("app", "explorer"),
                "files": ("app", "explorer"),
                "calculator": ("app", "calc"),
                "notepad": ("app", "notepad"),
                "paint": ("app", "mspaint"),
                "task manager": ("app", "taskmgr"),
                "terminal": ("app", "cmd"),
                "command prompt": ("app", "cmd"),
                "powershell": ("app", "powershell"),
                
                # Browsers
                "chrome": ("browser", "chrome"),
                "google chrome": ("browser", "chrome"),
                "firefox": ("browser", "firefox"),
                "edge": ("browser", "msedge"),
                "microsoft edge": ("browser", "msedge"),
                "browser": ("browser", "chrome"),
                
                # Dev Tools
                "vs code": ("app", "code"),
                "vscode": ("app", "code"),
                "visual studio code": ("app", "code"),
                "code": ("app", "code"),
                
                # Communication
                "spotify": ("app", "spotify:"),
                "discord": ("app", "discord:"),
                "steam": ("app", "steam:"),
                "teams": ("app", "msteams:"),
                "slack": ("app", "slack"),
                "zoom": ("app", "zoom"),
                
                # Office
                "word": ("app", "winword"),
                "excel": ("app", "excel"),
                "powerpoint": ("app", "powerpnt"),
                "outlook": ("app", "outlook"),
            }
            
            for target, (action_type, param) in open_targets.items():
                if target in user_input:
                    if action_type == "app":
                        self._open_app(param)
                    elif action_type == "folder":
                        self._open_folder(param)
                    elif action_type == "browser":
                        self._open_browser(param)
                    return f"Opening {target}."
        
        # === SEARCH ACTIONS ===
        wants_to_search = any(word in user_input for word in ["search", "google", "look up", "youtube"])
        
        if wants_to_search:
            # Extract search query
            query = user_input
            for word in ["search", "search for", "google", "look up", "find", "youtube", "on", "for", "about"]:
                query = query.replace(word, " ")
            query = " ".join(query.split()).strip()
            
            if query and len(query) > 2:
                if "youtube" in user_input:
                    self._search_youtube(query)
                    return f"Searching YouTube for {query}."
                else:
                    self._search_google(query)
                    return f"Searching for {query}."
        
        # === SYSTEM STATUS ===
        wants_status = any(word in user_input for word in ["status", "diagnostics", "how we doing", "how are we", "system"])
        if wants_status and PSUTIL_AVAILABLE:
            return self._get_system_status()
        
        # === KNOWLEDGE QUESTIONS ===
        # If it seems like a factual question, try to look it up
        question_words = ["what is", "who is", "where is", "when was", "how does", "why is", "define", "meaning of"]
        is_question = any(q in user_input for q in question_words)
        
        if is_question:
            knowledge = self._search_knowledge(user_input)
            if knowledge:
                return knowledge
        
        # No action detected
        return None
    
    # === ACTION FUNCTIONS ===
    
    def _open_app(self, app: str):
        """Open an application"""
        try:
            if self.system == "Windows":
                if app.endswith(":"):
                    subprocess.Popen(f"start {app}", shell=True, 
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:
                    subprocess.Popen(f"start \"\" {app}", shell=True,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                subprocess.Popen([app], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"[Action] Opened {app}")
        except Exception as e:
            print(f"[Action] Failed to open {app}: {e}")
    
    def _open_folder(self, folder: str):
        """Open a folder"""
        try:
            if self.system == "Windows":
                subprocess.Popen(f"explorer shell:{folder}", shell=True,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                subprocess.Popen(["xdg-open", f"~/{folder}"],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"[Action] Opened folder {folder}")
        except Exception as e:
            print(f"[Action] Failed to open folder {folder}: {e}")
    
    def _open_browser(self, browser: str):
        """Open a web browser"""
        try:
            if self.system == "Windows":
                subprocess.Popen(f"start \"\" {browser}", shell=True,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                subprocess.Popen([browser], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"[Action] Opened browser {browser}")
        except:
            webbrowser.open("https://www.google.com")
    
    def _search_google(self, query: str):
        """Search Google"""
        url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        webbrowser.open(url)
        print(f"[Action] Searching Google: {query}")
    
    def _search_youtube(self, query: str):
        """Search YouTube"""
        url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
        webbrowser.open(url)
        print(f"[Action] Searching YouTube: {query}")
    
    def _get_system_status(self) -> str:
        """Get system status"""
        try:
            cpu = psutil.cpu_percent(interval=0.5)
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            mem_free_gb = mem.available / (1024**3)
            disk_free_gb = disk.free / (1024**3)
            
            if cpu > 80 or mem.percent > 85:
                return f"Running hot. CPU at {cpu}%, memory at {mem.percent}%. You might want to close some applications."
            elif cpu > 50 or mem.percent > 70:
                return f"Moderate load. CPU {cpu}%, memory {mem.percent}%, {mem_free_gb:.1f}GB RAM free."
            else:
                return f"All systems nominal. CPU {cpu}%, memory {mem.percent}%, {disk_free_gb:.0f}GB storage available."
        except:
            return "Couldn't get system diagnostics."
    
    def _search_knowledge(self, query: str) -> str:
        """Search Wikipedia and DuckDuckGo for knowledge"""
        if not REQUESTS_AVAILABLE:
            return ""
        
        # Clean query for search
        clean_query = query
        for word in ["what is", "who is", "where is", "when was", "how does", "why is", "define", "meaning of", "the", "a", "an"]:
            clean_query = clean_query.replace(word, " ")
        clean_query = " ".join(clean_query.split()).strip()
        
        if not clean_query:
            return ""
        
        # Try Wikipedia first
        wiki_result = self._search_wikipedia(clean_query)
        if wiki_result:
            return wiki_result
        
        # Try DuckDuckGo instant answers
        ddg_result = self._search_duckduckgo(clean_query)
        if ddg_result:
            return ddg_result
        
        return ""
    
    def _search_wikipedia(self, query: str) -> str:
        """Search Wikipedia for information"""
        try:
            # Use Wikipedia API
            url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + query.replace(" ", "_")
            response = requests.get(url, timeout=5, headers={"User-Agent": "F.R.I.D.A.Y/1.0"})
            
            if response.status_code == 200:
                data = response.json()
                extract = data.get("extract", "")
                if extract and len(extract) > 50:
                    # Limit to 2-3 sentences for voice
                    sentences = extract.split(". ")
                    short_answer = ". ".join(sentences[:2]) + "."
                    return short_answer
        except Exception as e:
            print(f"[Knowledge] Wikipedia error: {e}")
        
        return ""
    
    def _search_duckduckgo(self, query: str) -> str:
        """Search DuckDuckGo instant answers"""
        try:
            url = f"https://api.duckduckgo.com/?q={query.replace(' ', '+')}&format=json&no_html=1"
            response = requests.get(url, timeout=5, headers={"User-Agent": "F.R.I.D.A.Y/1.0"})
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for instant answer
                abstract = data.get("AbstractText", "")
                if abstract and len(abstract) > 30:
                    # Limit length
                    if len(abstract) > 300:
                        abstract = abstract[:300] + "..."
                    return abstract
                
                # Check for answer
                answer = data.get("Answer", "")
                if answer:
                    return answer
        except Exception as e:
            print(f"[Knowledge] DuckDuckGo error: {e}")
        
        return ""


# Global instance
command_handler = CommandHandler()
