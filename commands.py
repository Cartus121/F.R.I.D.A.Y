"""
Command Handler for F.R.I.D.A.Y.
FULLY AI-POWERED - No keyword detection
AI analyzes the full sentence to understand intent
"""

import threading
import time as time_module
from datetime import datetime, timedelta
from typing import Tuple, Dict, Any, Optional
import subprocess
import platform
import webbrowser
import json
import os
import re

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

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from config import LOCATION, TIMEZONE, DATE_FORMAT, TIME_FORMAT, WAKE_WORD, OPENAI_API_KEY
from database import db
from ai_brain import brain

# Get API keys from settings
try:
    from settings import get_api_key, play_alarm_sound, send_notification
except:
    play_alarm_sound = lambda: None
    send_notification = lambda t, m: None

# Active timers/alarms storage
active_timers: Dict[str, Dict[str, Any]] = {}

# Intent categories that F.R.I.D.A.Y. can handle
INTENT_CATEGORIES = """
AVAILABLE ACTIONS (return the exact action name):
- "open_app" - open any application (extract: app_name)
- "open_folder" - open a folder like Downloads, Documents (extract: folder_name)
- "open_website" - open a website or URL (extract: url or site_name)
- "search_web" - search Google/YouTube/web (extract: query, platform)
- "set_volume" - change system volume (extract: level as number 0-100, or "up"/"down"/"mute"/"unmute")
- "set_brightness" - change screen brightness (extract: level as number 0-100, or "up"/"down")
- "set_timer" - set a countdown timer (extract: duration_minutes or duration_seconds or duration_hours)
- "set_alarm" - set an alarm for specific time (extract: time in 24h format like "07:00" or "14:30")
- "cancel_timer" - cancel active timer
- "cancel_alarm" - cancel active alarm
- "media_control" - play/pause/skip media (extract: action as "play"/"pause"/"next"/"previous")
- "system_status" - get CPU, RAM, disk info
- "lock_pc" - lock the computer
- "sleep_pc" - put computer to sleep
- "restart_pc" - restart computer (needs confirmation)
- "shutdown_pc" - shutdown computer (needs confirmation)
- "take_screenshot" - capture screen
- "toggle_wifi" - turn WiFi on/off (extract: state as "on"/"off"/"toggle")
- "toggle_bluetooth" - turn Bluetooth on/off (extract: state as "on"/"off"/"toggle")
- "clipboard_copy" - copy text to clipboard (extract: text)
- "clipboard_read" - read clipboard contents
- "file_operation" - create/delete/move files (extract: operation, path, content if needed)
- "run_command" - run a terminal/cmd command (extract: command)
- "get_weather" - get weather info
- "get_time" - get current time
- "get_date" - get current date
- "knowledge_search" - look up factual information (extract: query)
- "smart_lights" - control smart lights/bulbs (extract: action as "on"/"off"/"toggle"/"dim"/"bright", device_name, brightness 0-100, color)
- "smart_home" - control other smart home devices (extract: device_type, device_name, action, value)
- "conversation" - just talking, no action needed

RESPOND WITH JSON ONLY:
{"intent": "action_name", "params": {"key": "value"}, "confidence": 0.0-1.0}

If it's just conversation or you're unsure, use:
{"intent": "conversation", "params": {}, "confidence": 1.0}
"""


class CommandHandler:
    """
    AI-Powered Command Handler
    Uses GPT to analyze sentences and determine intent
    NO keyword matching - full natural language understanding
    """
    
    def __init__(self):
        self.gui_callback = None
        self.system = platform.system()
        self.openai_client = None
        
        # Initialize OpenAI for intent detection
        self._init_openai()
    
    def _init_openai(self):
        """Initialize or reinitialize OpenAI client"""
        if self.openai_client:
            return  # Already initialized
        
        # Try getting API key - check env first, then settings
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            try:
                from settings import get_api_key
                api_key = get_api_key("OPENAI_API_KEY")
            except:
                pass
        
        if OPENAI_AVAILABLE and api_key:
            try:
                self.openai_client = OpenAI(api_key=api_key)
                print("[OK] AI Intent Analyzer ready")
            except Exception as e:
                print(f"[!] AI Intent Analyzer error: {e}")
    
    def set_gui_callback(self, callback):
        """Set callback for sending async messages to GUI"""
        self.gui_callback = callback
    
    def process(self, command: str) -> Tuple[str, bool]:
        """
        Process user input using AI to understand intent
        Returns: (response_text, should_continue_listening)
        """
        # Ensure OpenAI is initialized (in case key was added after startup)
        if not self.openai_client:
            self._init_openai()
        
        command = command.strip()
        
        if not command:
            return ("I didn't catch that.", True)
        
        # Wake word handling
        if command.lower() == "__wake__":
            return ("Yes? What do you need?", True)
        
        # Goodbye handling
        goodbye_phrases = ["goodbye", "go to sleep", "bye", "that's all", "goodnight", "night", "later"]
        if command.lower() in goodbye_phrases:
            return (f"Standing by. Say '{WAKE_WORD}' when you need me.", False)
        
        # Quick check for obvious actions (no AI needed)
        quick_action = self._quick_intent_check(command)
        if quick_action:
            return (quick_action, True)
        
        # For complex questions or conversation, use single optimized AI call
        response = self._get_smart_response(command)
        return (response, True)
    
    def _quick_intent_check(self, command: str) -> Optional[str]:
        """
        Quick pattern matching for obvious commands.
        No AI call needed for simple things.
        """
        cmd_lower = command.lower().strip()
        
        # Time/Date - instant response
        if any(x in cmd_lower for x in ["what time", "current time", "time is it"]):
            return f"It's {datetime.now().strftime('%I:%M %p')}."
        if any(x in cmd_lower for x in ["what date", "today's date", "what day"]):
            return f"Today is {datetime.now().strftime('%A, %B %d, %Y')}."
        
        # Volume - quick patterns
        if any(x in cmd_lower for x in ["volume up", "turn up", "louder", "crank up"]):
            return self._set_volume("up")
        if any(x in cmd_lower for x in ["volume down", "turn down", "quieter", "lower volume"]):
            return self._set_volume("down")
        if "mute" in cmd_lower:
            return self._set_volume("mute")
        
        # Media - quick patterns
        if any(x in cmd_lower for x in ["pause", "stop music", "stop playing"]):
            return self._media_control("pause")
        if cmd_lower in ["play", "resume", "continue"]:
            return self._media_control("play")
        if any(x in cmd_lower for x in ["next song", "skip", "next track"]):
            return self._media_control("next")
        
        # System - quick patterns  
        if any(x in cmd_lower for x in ["lock computer", "lock pc", "lock screen", "lock my"]):
            return self._lock_pc()
        if any(x in cmd_lower for x in ["system status", "how's my computer", "cpu usage"]):
            return self._get_system_status()
        if "screenshot" in cmd_lower:
            return self._take_screenshot()
        
        # None matched - need AI
        return None
    
    def _get_smart_response(self, command: str) -> str:
        """
        Single optimized AI call that handles both actions AND conversation.
        SPEED OPTIMIZED: Uses gpt-4o with minimal tokens for fastest response.
        """
        if not self.openai_client:
            # Fallback to brain if no OpenAI in commands
            return brain.get_response(command)
        
        try:
            # Compact prompt for speed
            system_prompt = f"""F.R.I.D.A.Y. AI assistant. Be witty, concise. Time: {datetime.now().strftime('%I:%M %p')}, OS: {self.system}

ACTION? Reply JSON: {{"action": "X", "params": {{}}}}
Actions: open_app, open_website, search_web, set_volume, set_brightness, set_timer, set_alarm, media_control, smart_lights

QUESTION? Reply naturally. Max 2-3 sentences."""

            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": command}
                ],
                max_tokens=200,  # Reduced for speed
                temperature=0.7
            )
            
            result = response.choices[0].message.content.strip()
            
            # Check if it's an action JSON
            if result.startswith("{") and "action" in result:
                try:
                    # Clean markdown if present
                    clean_result = result
                    if "```" in result:
                        clean_result = re.sub(r'```json?\s*', '', result)
                        clean_result = re.sub(r'\s*```', '', clean_result)
                    
                    action_data = json.loads(clean_result)
                    action = action_data.get("action", "")
                    params = action_data.get("params", {})
                    
                    # Execute action
                    action_response = self._execute_action_fast(action, params, command)
                    if action_response:
                        return action_response
                except json.JSONDecodeError:
                    pass  # Not valid JSON, treat as conversation
            
            # It's a conversation response
            return result
            
        except Exception as e:
            print(f"[SmartResponse] Error: {e}")
            # Fallback to brain
            return brain.get_response(command)
    
    def _execute_action_fast(self, action: str, params: Dict, original: str) -> Optional[str]:
        """Execute detected action quickly"""
        try:
            if action == "open_app":
                return self._open_app(params.get("app_name", "") or self._extract_app_name(original))
            elif action == "open_website":
                return self._open_website(params.get("url", "") or params.get("site", ""))
            elif action == "search_web":
                query = params.get("query", original)
                platform = params.get("platform", "google")
                return self._search_web(query, platform)
            elif action == "set_volume":
                return self._set_volume(params.get("level", "50"))
            elif action == "set_brightness":
                return self._set_brightness(params.get("level", "50"))
            elif action == "set_timer":
                return self._set_timer(
                    minutes=params.get("minutes") or params.get("duration_minutes"),
                    seconds=params.get("seconds"),
                    hours=params.get("hours")
                )
            elif action == "set_alarm":
                return self._set_alarm(params.get("time", ""))
            elif action == "media_control":
                return self._media_control(params.get("action", "pause"))
            elif action == "smart_lights":
                return self._control_smart_lights(params)
        except Exception as e:
            print(f"[ActionFast] Error: {e}")
        return None
    
    def _extract_app_name(self, text: str) -> str:
        """Extract app name from text"""
        text_lower = text.lower()
        apps = ["chrome", "firefox", "edge", "spotify", "discord", "steam", "vscode", "vs code",
                "notepad", "calculator", "terminal", "explorer", "files", "settings"]
        for app in apps:
            if app in text_lower:
                return app
        # Return last word as guess
        words = text.split()
        return words[-1] if words else ""
    
    def _analyze_intent(self, user_input: str) -> Optional[Dict]:
        """
        Use AI to analyze what the user wants
        Returns structured intent data
        """
        if not self.openai_client:
            return None
        
        try:
            # Build the analysis prompt
            analysis_prompt = f"""Analyze this user request and determine what action they want.
User said: "{user_input}"

Current context:
- Time: {datetime.now().strftime("%H:%M")}
- Date: {datetime.now().strftime("%A, %B %d, %Y")}
- OS: {self.system}

{INTENT_CATEGORIES}

IMPORTANT:
- Understand casual/slang speech (e.g., "crank up the volume" = set_volume up)
- Understand context (e.g., "make it louder" = set_volume up)
- Extract specific values when mentioned (e.g., "set volume to 50" = level: 50)
- For times, convert to 24h format (e.g., "5pm" = "17:00", "7 in the morning" = "07:00")
- For durations, extract the number and unit (e.g., "5 minutes" = duration_minutes: 5)
- If the user is just chatting or you're unsure, use "conversation"

Respond with ONLY valid JSON, no explanation."""

            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an intent classifier. Respond with JSON only."},
                    {"role": "user", "content": analysis_prompt}
                ],
                max_tokens=150,
                temperature=0.1  # Low temperature for consistent parsing
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Clean up the response (remove markdown if present)
            if result_text.startswith("```"):
                result_text = re.sub(r'^```json?\s*', '', result_text)
                result_text = re.sub(r'\s*```$', '', result_text)
            
            # Parse JSON
            intent_data = json.loads(result_text)
            
            # Validate confidence threshold
            if intent_data.get("confidence", 0) < 0.5:
                return {"intent": "conversation", "params": {}, "confidence": 1.0}
            
            print(f"[Intent] {intent_data.get('intent')} - {intent_data.get('params')} ({intent_data.get('confidence', 0):.0%})")
            return intent_data
            
        except json.JSONDecodeError as e:
            print(f"[Intent] JSON parse error: {e}")
            return None
        except Exception as e:
            print(f"[Intent] Analysis error: {e}")
            return None
    
    def _execute_intent(self, intent_data: Dict, original_input: str) -> Optional[str]:
        """Execute the detected intent"""
        intent = intent_data.get("intent", "")
        params = intent_data.get("params", {})
        
        try:
            # === APP/FOLDER/WEB ACTIONS ===
            if intent == "open_app":
                return self._open_app(params.get("app_name", ""))
            
            elif intent == "open_folder":
                return self._open_folder(params.get("folder_name", ""))
            
            elif intent == "open_website":
                url = params.get("url") or params.get("site_name", "")
                return self._open_website(url)
            
            elif intent == "search_web":
                query = params.get("query", original_input)
                platform = params.get("platform", "google").lower()
                return self._search_web(query, platform)
            
            # === VOLUME/BRIGHTNESS ===
            elif intent == "set_volume":
                level = params.get("level", "")
                return self._set_volume(level)
            
            elif intent == "set_brightness":
                level = params.get("level", "")
                return self._set_brightness(level)
            
            # === TIMER/ALARM ===
            elif intent == "set_timer":
                minutes = params.get("duration_minutes")
                seconds = params.get("duration_seconds")
                hours = params.get("duration_hours")
                return self._set_timer(minutes=minutes, seconds=seconds, hours=hours)
            
            elif intent == "set_alarm":
                time_str = params.get("time", "")
                return self._set_alarm(time_str)
            
            elif intent == "cancel_timer":
                return self._cancel_timer()
            
            elif intent == "cancel_alarm":
                return self._cancel_alarm()
            
            # === MEDIA CONTROL ===
            elif intent == "media_control":
                action = params.get("action", "pause")
                return self._media_control(action)
            
            # === SYSTEM ===
            elif intent == "system_status":
                return self._get_system_status()
            
            elif intent == "lock_pc":
                return self._lock_pc()
            
            elif intent == "sleep_pc":
                return self._sleep_pc()
            
            elif intent == "restart_pc":
                return "Are you sure you want to restart? Say 'yes, restart' to confirm."
            
            elif intent == "shutdown_pc":
                return "Are you sure you want to shut down? Say 'yes, shutdown' to confirm."
            
            # === SCREENSHOTS/CLIPBOARD ===
            elif intent == "take_screenshot":
                return self._take_screenshot()
            
            elif intent == "clipboard_copy":
                text = params.get("text", "")
                return self._clipboard_copy(text)
            
            elif intent == "clipboard_read":
                return self._clipboard_read()
            
            # === CONNECTIVITY ===
            elif intent == "toggle_wifi":
                state = params.get("state", "toggle")
                return self._toggle_wifi(state)
            
            elif intent == "toggle_bluetooth":
                state = params.get("state", "toggle")
                return self._toggle_bluetooth(state)
            
            # === FILE OPERATIONS ===
            elif intent == "file_operation":
                return self._file_operation(params)
            
            elif intent == "run_command":
                cmd = params.get("command", "")
                return self._run_command(cmd)
            
            # === INFO ===
            elif intent == "get_weather":
                return self._get_weather()
            
            elif intent == "get_time":
                return f"It's {datetime.now().strftime('%I:%M %p')}."
            
            elif intent == "get_date":
                return f"Today is {datetime.now().strftime('%A, %B %d, %Y')}."
            
            elif intent == "knowledge_search":
                query = params.get("query", original_input)
                return self._search_knowledge(query)
            
            # === SMART HOME ===
            elif intent == "smart_lights":
                return self._control_smart_lights(params)
            
            elif intent == "smart_home":
                return self._control_smart_home(params)
            
            return None
            
        except Exception as e:
            print(f"[Execute] Error: {e}")
            return None
    
    def _build_context(self) -> Dict:
        """Build context for AI conversations"""
        context = {
            "current_time": datetime.now().strftime(TIME_FORMAT),
            "current_date": datetime.now().strftime("%A, %B %d, %Y"),
            "location": LOCATION,
        }
        
        if PSUTIL_AVAILABLE:
            try:
                context["cpu_percent"] = f"{psutil.cpu_percent()}%"
                context["memory_percent"] = f"{psutil.virtual_memory().percent}%"
            except:
                pass
        
        return context
    
    # =========================================================================
    # ACTION IMPLEMENTATIONS
    # =========================================================================
    
    def _open_app(self, app_name: str) -> str:
        """Open an application by name"""
        if not app_name:
            return "What app would you like me to open?"
        
        app_name_lower = app_name.lower()
        
        # Common app mappings for Windows
        windows_apps = {
            "chrome": "chrome", "google chrome": "chrome",
            "firefox": "firefox", "mozilla": "firefox",
            "edge": "msedge", "microsoft edge": "msedge",
            "notepad": "notepad", "note pad": "notepad",
            "calculator": "calc", "calc": "calc",
            "paint": "mspaint",
            "word": "winword", "microsoft word": "winword",
            "excel": "excel", "microsoft excel": "excel",
            "powerpoint": "powerpnt", "ppt": "powerpnt",
            "outlook": "outlook",
            "vs code": "code", "vscode": "code", "visual studio code": "code",
            "terminal": "cmd", "command prompt": "cmd", "cmd": "cmd",
            "powershell": "powershell",
            "task manager": "taskmgr",
            "file explorer": "explorer", "explorer": "explorer", "files": "explorer",
            "settings": "ms-settings:",
            "control panel": "control",
            "spotify": "spotify:", "discord": "discord:", "steam": "steam:",
            "teams": "msteams:", "slack": "slack", "zoom": "zoom",
            "snipping tool": "snippingtool", "snip": "snippingtool",
            "store": "ms-windows-store:", "microsoft store": "ms-windows-store:",
        }
        
        # Linux app mappings
        linux_apps = {
            "chrome": "google-chrome", "google chrome": "google-chrome",
            "firefox": "firefox",
            "terminal": "gnome-terminal", "konsole": "konsole",
            "files": "nautilus", "file manager": "nautilus",
            "settings": "gnome-control-center",
            "calculator": "gnome-calculator",
            "vs code": "code", "vscode": "code",
            "spotify": "spotify", "discord": "discord",
        }
        
        try:
            if self.system == "Windows":
                app_cmd = windows_apps.get(app_name_lower, app_name)
                if app_cmd.endswith(":"):
                    subprocess.Popen(f"start {app_cmd}", shell=True,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:
                    subprocess.Popen(f"start \"\" {app_cmd}", shell=True,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                app_cmd = linux_apps.get(app_name_lower, app_name)
                subprocess.Popen([app_cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            return f"Opening {app_name}."
        except Exception as e:
            return f"Couldn't open {app_name}. It might not be installed."
    
    def _open_folder(self, folder_name: str) -> str:
        """Open a folder"""
        if not folder_name:
            return "What folder would you like me to open?"
        
        folder_lower = folder_name.lower()
        
        # Common folder mappings
        folders = {
            "downloads": "Downloads", "download": "Downloads",
            "documents": "Documents", "docs": "Documents",
            "pictures": "Pictures", "photos": "Pictures", "images": "Pictures",
            "music": "Music",
            "videos": "Videos",
            "desktop": "Desktop",
            "home": "",
        }
        
        folder = folders.get(folder_lower, folder_name)
        
        try:
            if self.system == "Windows":
                if folder:
                    subprocess.Popen(f"explorer shell:{folder}", shell=True,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:
                    subprocess.Popen("explorer", shell=True,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                home = os.path.expanduser("~")
                path = os.path.join(home, folder) if folder else home
                subprocess.Popen(["xdg-open", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            return f"Opening {folder_name or 'home folder'}."
        except Exception as e:
            return f"Couldn't open {folder_name}."
    
    def _open_website(self, url: str) -> str:
        """Open a website"""
        if not url:
            return "What website would you like me to open?"
        
        # Common site shortcuts
        sites = {
            "google": "https://www.google.com",
            "youtube": "https://www.youtube.com",
            "github": "https://github.com",
            "twitter": "https://twitter.com", "x": "https://twitter.com",
            "facebook": "https://www.facebook.com",
            "instagram": "https://www.instagram.com",
            "reddit": "https://www.reddit.com",
            "netflix": "https://www.netflix.com",
            "amazon": "https://www.amazon.com",
            "gmail": "https://mail.google.com",
            "linkedin": "https://www.linkedin.com",
        }
        
        url_lower = url.lower()
        final_url = sites.get(url_lower)
        
        if not final_url:
            # Add https if no protocol
            if not url.startswith(("http://", "https://")):
                if "." in url:
                    final_url = f"https://{url}"
                else:
                    final_url = f"https://www.{url}.com"
            else:
                final_url = url
        
        webbrowser.open(final_url)
        return f"Opening {url}."
    
    def _search_web(self, query: str, platform: str = "google") -> str:
        """Search the web"""
        if not query:
            return "What would you like me to search for?"
        
        if platform == "youtube":
            url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
            webbrowser.open(url)
            return f"Searching YouTube for {query}."
        else:
            url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            webbrowser.open(url)
            return f"Searching for {query}."
    
    def _set_volume(self, level) -> str:
        """Set system volume"""
        try:
            # Convert to appropriate type
            if isinstance(level, str):
                level_lower = level.lower()
                if level_lower in ["mute", "muted"]:
                    level = "mute"
                elif level_lower in ["unmute", "unmuted"]:
                    level = "unmute"
                elif level_lower in ["up", "higher", "louder", "increase"]:
                    level = "up"
                elif level_lower in ["down", "lower", "quieter", "decrease", "softer"]:
                    level = "down"
                elif level_lower in ["max", "maximum", "full", "100"]:
                    level = 100
                elif level_lower in ["min", "minimum", "silent", "0"]:
                    level = 0
                else:
                    try:
                        level = int(re.search(r'\d+', str(level)).group())
                    except:
                        pass
            
            if self.system == "Windows":
                if level == "mute":
                    subprocess.run('powershell -c "(New-Object -ComObject WScript.Shell).SendKeys([char]173)"',
                                 shell=True, capture_output=True)
                    return "Muted."
                elif level == "unmute":
                    subprocess.run('powershell -c "(New-Object -ComObject WScript.Shell).SendKeys([char]173)"',
                                 shell=True, capture_output=True)
                    return "Unmuted."
                elif level == "up":
                    for _ in range(5):  # Press volume up 5 times
                        subprocess.run('powershell -c "(New-Object -ComObject WScript.Shell).SendKeys([char]175)"',
                                     shell=True, capture_output=True)
                    return "Volume up."
                elif level == "down":
                    for _ in range(5):  # Press volume down 5 times
                        subprocess.run('powershell -c "(New-Object -ComObject WScript.Shell).SendKeys([char]174)"',
                                     shell=True, capture_output=True)
                    return "Volume down."
                elif isinstance(level, int):
                    # Set to specific level using nircmd or PowerShell
                    level = max(0, min(100, level))
                    # Use PowerShell to set exact volume
                    ps_script = f"""
                    Add-Type -TypeDefinition @'
                    using System.Runtime.InteropServices;
                    [Guid("5CDF2C82-841E-4546-9722-0CF74078229A"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
                    interface IAudioEndpointVolume {{
                        int f(); int g(); int h(); int i();
                        int SetMasterVolumeLevelScalar(float fLevel, System.Guid pguidEventContext);
                        int j();
                        int GetMasterVolumeLevelScalar(out float pfLevel);
                    }}
                    [Guid("D666063F-1587-4E43-81F1-B948E807363F"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
                    interface IMMDevice {{ int Activate(ref System.Guid id, int clsCtx, int activationParams, out IAudioEndpointVolume aev); }}
                    [Guid("A95664D2-9614-4F35-A746-DE8DB63617E6"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
                    interface IMMDeviceEnumerator {{ int f(); int GetDefaultAudioEndpoint(int dataFlow, int role, out IMMDevice endpoint); }}
                    [ComImport, Guid("BCDE0395-E52F-467C-8E3D-C4579291692E")] class MMDeviceEnumerator {{ }}
                    public class Audio {{
                        static IAudioEndpointVolume Vol() {{
                            var enumerator = new MMDeviceEnumerator() as IMMDeviceEnumerator;
                            IMMDevice dev = null;
                            enumerator.GetDefaultAudioEndpoint(0, 1, out dev);
                            IAudioEndpointVolume epv = null;
                            var epvid = typeof(IAudioEndpointVolume).GUID;
                            dev.Activate(ref epvid, 23, 0, out epv);
                            return epv;
                        }}
                        public static float GetVolume() {{ float v = -1; Vol().GetMasterVolumeLevelScalar(out v); return v*100; }}
                        public static void SetVolume(float v) {{ Vol().SetMasterVolumeLevelScalar(v/100, System.Guid.Empty); }}
                    }}
'@
                    [Audio]::SetVolume({level})
                    """
                    subprocess.run(['powershell', '-c', ps_script], capture_output=True)
                    return f"Volume set to {level}%."
            else:
                # Linux
                if level == "mute":
                    subprocess.run(['pactl', 'set-sink-mute', '@DEFAULT_SINK@', 'toggle'], capture_output=True)
                    return "Toggled mute."
                elif level == "unmute":
                    subprocess.run(['pactl', 'set-sink-mute', '@DEFAULT_SINK@', '0'], capture_output=True)
                    return "Unmuted."
                elif level == "up":
                    subprocess.run(['pactl', 'set-sink-volume', '@DEFAULT_SINK@', '+10%'], capture_output=True)
                    return "Volume up."
                elif level == "down":
                    subprocess.run(['pactl', 'set-sink-volume', '@DEFAULT_SINK@', '-10%'], capture_output=True)
                    return "Volume down."
                elif isinstance(level, int):
                    level = max(0, min(100, level))
                    subprocess.run(['pactl', 'set-sink-volume', '@DEFAULT_SINK@', f'{level}%'], capture_output=True)
                    return f"Volume set to {level}%."
            
            return "Volume adjusted."
        except Exception as e:
            print(f"[Volume] Error: {e}")
            return "Couldn't adjust volume."
    
    def _set_brightness(self, level) -> str:
        """Set screen brightness"""
        try:
            # Parse level
            if isinstance(level, str):
                level_lower = level.lower()
                if level_lower in ["up", "higher", "brighter", "increase"]:
                    level = "up"
                elif level_lower in ["down", "lower", "dimmer", "decrease", "dim"]:
                    level = "down"
                elif level_lower in ["max", "maximum", "full", "100"]:
                    level = 100
                elif level_lower in ["min", "minimum", "lowest"]:
                    level = 10
                else:
                    try:
                        level = int(re.search(r'\d+', str(level)).group())
                    except:
                        level = 50
            
            if self.system == "Windows":
                if level == "up":
                    subprocess.run(['powershell', '-c',
                        '(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1, [math]::Min(100, (Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightness).CurrentBrightness + 20))'],
                        capture_output=True)
                    return "Brightness increased."
                elif level == "down":
                    subprocess.run(['powershell', '-c',
                        '(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1, [math]::Max(0, (Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightness).CurrentBrightness - 20))'],
                        capture_output=True)
                    return "Brightness decreased."
                else:
                    level = max(0, min(100, int(level)))
                    subprocess.run(['powershell', '-c',
                        f'(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1, {level})'],
                        capture_output=True)
                    return f"Brightness set to {level}%."
            else:
                if level == "up":
                    subprocess.run(['brightnessctl', 'set', '+20%'], capture_output=True)
                    return "Brightness increased."
                elif level == "down":
                    subprocess.run(['brightnessctl', 'set', '20%-'], capture_output=True)
                    return "Brightness decreased."
                else:
                    level = max(0, min(100, int(level)))
                    subprocess.run(['brightnessctl', 'set', f'{level}%'], capture_output=True)
                    return f"Brightness set to {level}%."
            
        except Exception as e:
            print(f"[Brightness] Error: {e}")
            return "Couldn't adjust brightness. This might not be supported on your device."
    
    def _set_timer(self, minutes=None, seconds=None, hours=None) -> str:
        """Set a countdown timer"""
        total_seconds = 0
        duration_text = ""
        
        if hours:
            total_seconds += int(hours) * 3600
            duration_text = f"{hours} hour{'s' if int(hours) != 1 else ''}"
        if minutes:
            total_seconds += int(minutes) * 60
            if duration_text:
                duration_text += f" and {minutes} minute{'s' if int(minutes) != 1 else ''}"
            else:
                duration_text = f"{minutes} minute{'s' if int(minutes) != 1 else ''}"
        if seconds:
            total_seconds += int(seconds)
            if duration_text:
                duration_text += f" and {seconds} second{'s' if int(seconds) != 1 else ''}"
            else:
                duration_text = f"{seconds} second{'s' if int(seconds) != 1 else ''}"
        
        if total_seconds <= 0:
            return "How long should I set the timer for?"
        
        # Cancel existing timer
        if "main_timer" in active_timers:
            active_timers["main_timer"]["cancelled"] = True
        
        # Create new timer
        active_timers["main_timer"] = {"seconds": total_seconds, "cancelled": False}
        
        def timer_done():
            if "main_timer" in active_timers and not active_timers["main_timer"].get("cancelled"):
                play_alarm_sound()
                send_notification("Timer Done!", f"Your {duration_text} timer is complete!")
                if self.gui_callback:
                    self.gui_callback(f"⏰ Timer done! {duration_text} have passed.")
                try:
                    del active_timers["main_timer"]
                except:
                    pass
        
        timer = threading.Timer(total_seconds, timer_done)
        timer.daemon = True
        timer.start()
        active_timers["main_timer"]["thread"] = timer
        
        return f"Timer set for {duration_text}."
    
    def _set_alarm(self, time_str: str) -> str:
        """Set an alarm for a specific time"""
        if not time_str:
            return "What time should I set the alarm for?"
        
        try:
            # Parse the time string (expected format: "HH:MM" in 24h)
            # Handle various formats
            time_str = time_str.strip()
            
            # Try to parse
            hour, minute = 0, 0
            if ":" in time_str:
                parts = time_str.split(":")
                hour = int(parts[0])
                minute = int(parts[1].split()[0])  # Handle "07:00 AM" format
            else:
                hour = int(re.search(r'\d+', time_str).group())
            
            # Calculate time until alarm
            now = datetime.now()
            alarm_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            # If time already passed today, set for tomorrow
            if alarm_time <= now:
                alarm_time += timedelta(days=1)
            
            seconds_until = (alarm_time - now).total_seconds()
            display_time = alarm_time.strftime("%I:%M %p")
            
            # Cancel existing alarm
            if "main_alarm" in active_timers:
                active_timers["main_alarm"]["cancelled"] = True
            
            active_timers["main_alarm"] = {"time": alarm_time, "cancelled": False}
            
            def alarm_done():
                if "main_alarm" in active_timers and not active_timers["main_alarm"].get("cancelled"):
                    play_alarm_sound()
                    send_notification("Alarm!", f"It's {display_time}!")
                    if self.gui_callback:
                        self.gui_callback(f"⏰ Alarm! It's {display_time}!")
                    try:
                        del active_timers["main_alarm"]
                    except:
                        pass
            
            timer = threading.Timer(seconds_until, alarm_done)
            timer.daemon = True
            timer.start()
            active_timers["main_alarm"]["thread"] = timer
            
            return f"Alarm set for {display_time}."
            
        except Exception as e:
            print(f"[Alarm] Error: {e}")
            return "I couldn't understand that time. Try saying something like 'alarm for 7:30 AM'."
    
    def _cancel_timer(self) -> str:
        """Cancel active timer"""
        if "main_timer" in active_timers:
            active_timers["main_timer"]["cancelled"] = True
            if "thread" in active_timers["main_timer"]:
                active_timers["main_timer"]["thread"].cancel()
            del active_timers["main_timer"]
            return "Timer cancelled."
        return "No active timer to cancel."
    
    def _cancel_alarm(self) -> str:
        """Cancel active alarm"""
        if "main_alarm" in active_timers:
            active_timers["main_alarm"]["cancelled"] = True
            if "thread" in active_timers["main_alarm"]:
                active_timers["main_alarm"]["thread"].cancel()
            del active_timers["main_alarm"]
            return "Alarm cancelled."
        return "No active alarm to cancel."
    
    def _media_control(self, action: str) -> str:
        """Control media playback"""
        try:
            action = action.lower()
            
            if self.system == "Windows":
                if action in ["pause", "stop"]:
                    subprocess.run('powershell -c "(New-Object -ComObject WScript.Shell).SendKeys([char]179)"',
                                 shell=True, capture_output=True)
                    return "Paused."
                elif action in ["play", "resume"]:
                    subprocess.run('powershell -c "(New-Object -ComObject WScript.Shell).SendKeys([char]179)"',
                                 shell=True, capture_output=True)
                    return "Playing."
                elif action in ["next", "skip"]:
                    subprocess.run('powershell -c "(New-Object -ComObject WScript.Shell).SendKeys([char]176)"',
                                 shell=True, capture_output=True)
                    return "Next track."
                elif action in ["previous", "back", "prev"]:
                    subprocess.run('powershell -c "(New-Object -ComObject WScript.Shell).SendKeys([char]177)"',
                                 shell=True, capture_output=True)
                    return "Previous track."
            else:
                if action in ["pause", "stop"]:
                    subprocess.run(['playerctl', 'pause'], capture_output=True)
                    return "Paused."
                elif action in ["play", "resume"]:
                    subprocess.run(['playerctl', 'play'], capture_output=True)
                    return "Playing."
                elif action in ["next", "skip"]:
                    subprocess.run(['playerctl', 'next'], capture_output=True)
                    return "Next track."
                elif action in ["previous", "back", "prev"]:
                    subprocess.run(['playerctl', 'previous'], capture_output=True)
                    return "Previous track."
            
            return "Done."
        except Exception as e:
            return "Couldn't control media playback."
    
    def _get_system_status(self) -> str:
        """Get system status"""
        if not PSUTIL_AVAILABLE:
            return "System monitoring not available."
        
        try:
            cpu = psutil.cpu_percent(interval=0.5)
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Battery info if available
            battery_info = ""
            try:
                battery = psutil.sensors_battery()
                if battery:
                    battery_info = f" Battery at {battery.percent:.0f}%."
                    if battery.power_plugged:
                        battery_info += " Plugged in."
            except:
                pass
            
            if cpu > 80 or mem.percent > 85:
                return f"Running hot! CPU at {cpu:.0f}%, memory at {mem.percent:.0f}%.{battery_info} Consider closing some apps."
            elif cpu > 50:
                return f"Moderate load. CPU {cpu:.0f}%, memory {mem.percent:.0f}%, {disk.free / (1024**3):.0f}GB storage free.{battery_info}"
            else:
                return f"All systems nominal. CPU {cpu:.0f}%, memory {mem.percent:.0f}%.{battery_info}"
        except Exception as e:
            return "Couldn't get system status."
    
    def _lock_pc(self) -> str:
        """Lock the computer"""
        try:
            if self.system == "Windows":
                subprocess.run('rundll32.exe user32.dll,LockWorkStation', shell=True)
            else:
                subprocess.run(['loginctl', 'lock-session'], capture_output=True)
            return "Locking your PC."
        except:
            return "Couldn't lock the PC."
    
    def _sleep_pc(self) -> str:
        """Put computer to sleep"""
        try:
            if self.system == "Windows":
                subprocess.run('rundll32.exe powrprof.dll,SetSuspendState 0,1,0', shell=True)
            else:
                subprocess.run(['systemctl', 'suspend'], capture_output=True)
            return "Putting PC to sleep."
        except:
            return "Couldn't put PC to sleep."
    
    def _take_screenshot(self) -> str:
        """Take a screenshot"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if self.system == "Windows":
                # Use PowerShell to take screenshot
                pictures_folder = os.path.join(os.path.expanduser("~"), "Pictures")
                filepath = os.path.join(pictures_folder, f"screenshot_{timestamp}.png")
                
                ps_script = f'''
                Add-Type -AssemblyName System.Windows.Forms
                $screen = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
                $bitmap = New-Object System.Drawing.Bitmap($screen.Width, $screen.Height)
                $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
                $graphics.CopyFromScreen($screen.Location, [System.Drawing.Point]::Empty, $screen.Size)
                $bitmap.Save("{filepath}")
                '''
                subprocess.run(['powershell', '-c', ps_script], capture_output=True)
                return f"Screenshot saved to Pictures folder."
            else:
                home = os.path.expanduser("~")
                filepath = os.path.join(home, "Pictures", f"screenshot_{timestamp}.png")
                subprocess.run(['gnome-screenshot', '-f', filepath], capture_output=True)
                return f"Screenshot saved."
        except Exception as e:
            return "Couldn't take screenshot."
    
    def _clipboard_copy(self, text: str) -> str:
        """Copy text to clipboard"""
        if not text:
            return "What should I copy to the clipboard?"
        
        try:
            if self.system == "Windows":
                subprocess.run(['powershell', '-c', f'Set-Clipboard -Value "{text}"'], capture_output=True)
            else:
                process = subprocess.Popen(['xclip', '-selection', 'clipboard'], stdin=subprocess.PIPE)
                process.communicate(text.encode())
            return "Copied to clipboard."
        except:
            return "Couldn't copy to clipboard."
    
    def _clipboard_read(self) -> str:
        """Read clipboard contents"""
        try:
            if self.system == "Windows":
                result = subprocess.run(['powershell', '-c', 'Get-Clipboard'], capture_output=True, text=True)
                content = result.stdout.strip()
            else:
                result = subprocess.run(['xclip', '-selection', 'clipboard', '-o'], capture_output=True, text=True)
                content = result.stdout.strip()
            
            if content:
                # Truncate if too long
                if len(content) > 200:
                    content = content[:200] + "..."
                return f"Clipboard contains: {content}"
            return "Clipboard is empty."
        except:
            return "Couldn't read clipboard."
    
    def _toggle_wifi(self, state: str) -> str:
        """Toggle WiFi on/off"""
        try:
            if self.system == "Windows":
                if state == "off":
                    subprocess.run(['netsh', 'interface', 'set', 'interface', 'Wi-Fi', 'disable'], capture_output=True)
                    return "WiFi turned off."
                elif state == "on":
                    subprocess.run(['netsh', 'interface', 'set', 'interface', 'Wi-Fi', 'enable'], capture_output=True)
                    return "WiFi turned on."
                else:
                    # Toggle
                    result = subprocess.run(['netsh', 'interface', 'show', 'interface', 'Wi-Fi'], capture_output=True, text=True)
                    if "Disabled" in result.stdout:
                        subprocess.run(['netsh', 'interface', 'set', 'interface', 'Wi-Fi', 'enable'], capture_output=True)
                        return "WiFi turned on."
                    else:
                        subprocess.run(['netsh', 'interface', 'set', 'interface', 'Wi-Fi', 'disable'], capture_output=True)
                        return "WiFi turned off."
            else:
                if state == "off":
                    subprocess.run(['nmcli', 'radio', 'wifi', 'off'], capture_output=True)
                    return "WiFi turned off."
                elif state == "on":
                    subprocess.run(['nmcli', 'radio', 'wifi', 'on'], capture_output=True)
                    return "WiFi turned on."
                else:
                    result = subprocess.run(['nmcli', 'radio', 'wifi'], capture_output=True, text=True)
                    if "enabled" in result.stdout.lower():
                        subprocess.run(['nmcli', 'radio', 'wifi', 'off'], capture_output=True)
                        return "WiFi turned off."
                    else:
                        subprocess.run(['nmcli', 'radio', 'wifi', 'on'], capture_output=True)
                        return "WiFi turned on."
        except:
            return "Couldn't toggle WiFi."
    
    def _toggle_bluetooth(self, state: str) -> str:
        """Toggle Bluetooth on/off"""
        try:
            if self.system == "Windows":
                # Windows Bluetooth toggle via PowerShell
                if state == "off":
                    subprocess.run(['powershell', '-c', 
                        'Add-Type -AssemblyName System.Runtime.WindowsRuntime; ' +
                        '[Windows.Devices.Radios.Radio, Windows.System.Devices, ContentType=WindowsRuntime] | Out-Null; ' +
                        '$radios = [Windows.Devices.Radios.Radio]::GetRadiosAsync().GetResults(); ' +
                        '$bluetooth = $radios | Where-Object { $_.Kind -eq "Bluetooth" }; ' +
                        '$bluetooth.SetStateAsync("Off")'], capture_output=True)
                    return "Bluetooth turned off."
                elif state == "on":
                    subprocess.run(['powershell', '-c',
                        'Add-Type -AssemblyName System.Runtime.WindowsRuntime; ' +
                        '[Windows.Devices.Radios.Radio, Windows.System.Devices, ContentType=WindowsRuntime] | Out-Null; ' +
                        '$radios = [Windows.Devices.Radios.Radio]::GetRadiosAsync().GetResults(); ' +
                        '$bluetooth = $radios | Where-Object { $_.Kind -eq "Bluetooth" }; ' +
                        '$bluetooth.SetStateAsync("On")'], capture_output=True)
                    return "Bluetooth turned on."
            else:
                if state == "off":
                    subprocess.run(['bluetoothctl', 'power', 'off'], capture_output=True)
                    return "Bluetooth turned off."
                elif state == "on":
                    subprocess.run(['bluetoothctl', 'power', 'on'], capture_output=True)
                    return "Bluetooth turned on."
            
            return "Bluetooth toggled."
        except:
            return "Couldn't toggle Bluetooth."
    
    def _file_operation(self, params: Dict) -> str:
        """Perform file operations"""
        operation = params.get("operation", "").lower()
        path = params.get("path", "")
        content = params.get("content", "")
        
        try:
            if operation == "create":
                # Create a file
                if path:
                    # Expand path
                    if not os.path.isabs(path):
                        path = os.path.join(os.path.expanduser("~"), "Documents", path)
                    
                    os.makedirs(os.path.dirname(path), exist_ok=True)
                    with open(path, 'w') as f:
                        f.write(content or "")
                    return f"Created file: {os.path.basename(path)}"
            
            elif operation == "delete":
                if path and os.path.exists(path):
                    os.remove(path)
                    return f"Deleted: {os.path.basename(path)}"
            
            return "File operation completed."
        except Exception as e:
            return f"Couldn't complete file operation: {e}"
    
    def _run_command(self, cmd: str) -> str:
        """Run a terminal command"""
        if not cmd:
            return "What command should I run?"
        
        # Safety check - block dangerous commands
        dangerous = ["rm -rf", "format", "del /f", "rd /s", ":(){:|:&};:", "mkfs"]
        if any(d in cmd.lower() for d in dangerous):
            return "I can't run that command - it could be dangerous."
        
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            output = result.stdout or result.stderr
            
            if output:
                # Truncate long output
                if len(output) > 500:
                    output = output[:500] + "..."
                return f"Done. Output:\n{output}"
            return "Command executed."
        except subprocess.TimeoutExpired:
            return "Command timed out."
        except Exception as e:
            return f"Error running command: {e}"
    
    def _get_weather(self) -> str:
        """Get weather info"""
        if not REQUESTS_AVAILABLE:
            return "Weather service unavailable."
        
        try:
            # Try to get API key
            api_key = ""
            try:
                from settings import get_api_key
                api_key = get_api_key("OPENWEATHER_API_KEY")
            except:
                try:
                    from config import OPENWEATHER_API_KEY
                    api_key = OPENWEATHER_API_KEY
                except:
                    pass
            
            if not api_key:
                return "Weather API key not configured. Add it in settings."
            
            # Get weather
            url = f"http://api.openweathermap.org/data/2.5/weather?q={LOCATION}&appid={api_key}&units=metric"
            response = requests.get(url, timeout=5)
            data = response.json()
            
            if data.get("cod") == 200:
                temp = data["main"]["temp"]
                desc = data["weather"][0]["description"]
                humidity = data["main"]["humidity"]
                return f"In {LOCATION}: {temp:.0f}°C, {desc}. Humidity at {humidity}%."
            
            return f"Couldn't get weather for {LOCATION}."
        except:
            return "Weather service unavailable."
    
    def _search_knowledge(self, query: str) -> str:
        """Search Wikipedia/DuckDuckGo for information"""
        if not REQUESTS_AVAILABLE:
            return ""
        
        # Clean query
        clean_query = query
        for word in ["what is", "who is", "where is", "when was", "how does", "why is", "define", "meaning of", "the", "a", "an"]:
            clean_query = clean_query.replace(word, " ")
        clean_query = " ".join(clean_query.split()).strip()
        
        if not clean_query:
            return ""
        
        # Try Wikipedia
        try:
            url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + clean_query.replace(" ", "_")
            response = requests.get(url, timeout=5, headers={"User-Agent": "F.R.I.D.A.Y/1.0"})
            
            if response.status_code == 200:
                data = response.json()
                extract = data.get("extract", "")
                if extract and len(extract) > 50:
                    sentences = extract.split(". ")
                    return ". ".join(sentences[:2]) + "."
        except:
            pass
        
        # Try DuckDuckGo
        try:
            url = f"https://api.duckduckgo.com/?q={clean_query.replace(' ', '+')}&format=json&no_html=1"
            response = requests.get(url, timeout=5, headers={"User-Agent": "F.R.I.D.A.Y/1.0"})
            
            if response.status_code == 200:
                data = response.json()
                abstract = data.get("AbstractText", "")
                if abstract:
                    if len(abstract) > 300:
                        abstract = abstract[:300] + "..."
                    return abstract
        except:
            pass
        
        return ""
    
    def _control_smart_lights(self, params: Dict) -> str:
        """
        Control smart lights/bulbs
        Supports: Philips Hue, LIFX, Tuya, Home Assistant, etc.
        """
        action = params.get("action", "toggle").lower()
        device_name = params.get("device_name", "").lower()
        brightness = params.get("brightness")
        color = params.get("color", "").lower()
        
        # Try to get smart home config
        smart_config = self._get_smart_home_config()
        
        if not smart_config:
            return self._smart_home_setup_guide()
        
        # Determine which platform to use
        platform = smart_config.get("platform", "").lower()
        
        try:
            if platform == "hue":
                return self._control_hue_lights(smart_config, action, device_name, brightness, color)
            elif platform == "home_assistant":
                return self._control_home_assistant(smart_config, "light", action, device_name, brightness, color)
            elif platform == "tuya":
                return self._control_tuya_device(smart_config, "light", action, device_name, brightness)
            elif platform == "lifx":
                return self._control_lifx_lights(smart_config, action, device_name, brightness, color)
            else:
                # Try Home Assistant as default (most universal)
                return self._control_home_assistant(smart_config, "light", action, device_name, brightness, color)
        except Exception as e:
            print(f"[SmartHome] Error: {e}")
            return f"Couldn't control lights. Error: {str(e)[:50]}"
    
    def _control_smart_home(self, params: Dict) -> str:
        """Control generic smart home devices"""
        device_type = params.get("device_type", "").lower()
        device_name = params.get("device_name", "").lower()
        action = params.get("action", "toggle").lower()
        value = params.get("value")
        
        smart_config = self._get_smart_home_config()
        
        if not smart_config:
            return self._smart_home_setup_guide()
        
        try:
            platform = smart_config.get("platform", "home_assistant").lower()
            
            if platform == "home_assistant":
                return self._control_home_assistant(smart_config, device_type, action, device_name, value)
            else:
                return "This device type is only supported with Home Assistant."
        except Exception as e:
            return f"Couldn't control device. Error: {str(e)[:50]}"
    
    def _get_smart_home_config(self) -> Optional[Dict]:
        """Get smart home configuration from settings"""
        try:
            # Try to load from settings file
            settings_path = os.path.join(os.path.expanduser("~"), "friday-assistant", "smart_home.json")
            if os.path.exists(settings_path):
                with open(settings_path, 'r') as f:
                    return json.load(f)
        except:
            pass
        
        # Try environment variables
        if os.environ.get("HASS_TOKEN"):
            return {
                "platform": "home_assistant",
                "host": os.environ.get("HASS_HOST", "http://homeassistant.local:8123"),
                "token": os.environ.get("HASS_TOKEN")
            }
        
        if os.environ.get("HUE_BRIDGE_IP"):
            return {
                "platform": "hue",
                "bridge_ip": os.environ.get("HUE_BRIDGE_IP"),
                "username": os.environ.get("HUE_USERNAME", "")
            }
        
        return None
    
    def _smart_home_setup_guide(self) -> str:
        """Guide user on setting up smart home"""
        return ("To control smart lights, I need to be connected to your smart home system. "
                "Create a file at ~/friday-assistant/smart_home.json with your setup.\n\n"
                "I support: Philips Hue, Home Assistant, LIFX, Tuya/Smart Life, and Fonri!\n\n"
                "For Fonri lights (uses Tuya platform):\n"
                '{"platform": "tuya", "devices": [{"name": "Light", "id": "device_id", "ip": "192.168.1.x", "key": "local_key", "version": 3.3}]}\n\n'
                "To get device info: pip install tinytuya && python -m tinytuya wizard")
    
    def _control_hue_lights(self, config: Dict, action: str, device: str, brightness: int = None, color: str = None) -> str:
        """Control Philips Hue lights"""
        bridge_ip = config.get("bridge_ip", "")
        username = config.get("username", "")
        
        if not bridge_ip or not username:
            return "Hue bridge not configured. Need bridge IP and username."
        
        base_url = f"http://{bridge_ip}/api/{username}"
        
        try:
            # Get all lights
            response = requests.get(f"{base_url}/lights", timeout=5)
            lights = response.json()
            
            # Find matching light(s)
            target_ids = []
            for light_id, light_data in lights.items():
                light_name = light_data.get("name", "").lower()
                if not device or device in light_name or device == "all" or device == "lights":
                    target_ids.append(light_id)
            
            if not target_ids:
                return f"Couldn't find light named '{device}'."
            
            # Build state command
            state = {}
            if action in ["on", "turn on"]:
                state["on"] = True
            elif action in ["off", "turn off"]:
                state["on"] = False
            elif action == "toggle":
                # Get current state of first light and toggle
                first_light = lights.get(target_ids[0], {})
                current_on = first_light.get("state", {}).get("on", False)
                state["on"] = not current_on
            
            if brightness is not None:
                # Hue uses 0-254 for brightness
                state["bri"] = int(brightness * 254 / 100)
                state["on"] = True  # Turn on when setting brightness
            
            if color:
                # Convert color name to Hue values
                color_map = {
                    "red": {"hue": 0, "sat": 254},
                    "orange": {"hue": 6000, "sat": 254},
                    "yellow": {"hue": 12000, "sat": 254},
                    "green": {"hue": 25500, "sat": 254},
                    "blue": {"hue": 46920, "sat": 254},
                    "purple": {"hue": 50000, "sat": 254},
                    "pink": {"hue": 56100, "sat": 200},
                    "white": {"hue": 0, "sat": 0},
                    "warm": {"ct": 400},
                    "cool": {"ct": 200},
                }
                if color in color_map:
                    state.update(color_map[color])
                    state["on"] = True
            
            # Send command to all target lights
            for light_id in target_ids:
                requests.put(f"{base_url}/lights/{light_id}/state", json=state, timeout=5)
            
            # Build response
            action_text = "on" if state.get("on", True) else "off"
            if len(target_ids) == 1:
                light_name = lights[target_ids[0]].get("name", "Light")
                return f"{light_name} turned {action_text}."
            else:
                return f"{len(target_ids)} lights turned {action_text}."
                
        except Exception as e:
            print(f"[Hue] Error: {e}")
            return "Couldn't connect to Hue bridge."
    
    def _control_home_assistant(self, config: Dict, device_type: str, action: str, 
                                device: str = "", value: Any = None, color: str = None) -> str:
        """Control devices via Home Assistant"""
        host = config.get("host", "").rstrip("/")
        token = config.get("token", "")
        
        if not host or not token:
            return "Home Assistant not configured. Need host URL and token."
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        try:
            # Map device types to Home Assistant domains
            domain_map = {
                "light": "light",
                "lights": "light",
                "switch": "switch",
                "plug": "switch",
                "fan": "fan",
                "climate": "climate",
                "thermostat": "climate",
                "lock": "lock",
                "cover": "cover",
                "blinds": "cover",
                "curtains": "cover",
            }
            domain = domain_map.get(device_type, "light")
            
            # Map actions to Home Assistant services
            service_map = {
                "on": "turn_on",
                "turn on": "turn_on",
                "off": "turn_off",
                "turn off": "turn_off",
                "toggle": "toggle",
                "dim": "turn_on",
                "bright": "turn_on",
                "lock": "lock",
                "unlock": "unlock",
                "open": "open_cover",
                "close": "close_cover",
            }
            service = service_map.get(action, "toggle")
            
            # Find entity ID
            entity_id = None
            if device:
                # Try to find matching entity
                states_response = requests.get(f"{host}/api/states", headers=headers, timeout=10)
                states = states_response.json()
                
                for entity in states:
                    eid = entity.get("entity_id", "")
                    friendly_name = entity.get("attributes", {}).get("friendly_name", "").lower()
                    
                    if eid.startswith(f"{domain}.") and (device in friendly_name or device in eid):
                        entity_id = eid
                        break
            
            # Build service data
            data = {}
            if entity_id:
                data["entity_id"] = entity_id
            
            if domain == "light":
                if isinstance(value, int) or (isinstance(value, str) and value.isdigit()):
                    data["brightness_pct"] = int(value)
                elif action == "dim":
                    data["brightness_pct"] = 30
                elif action == "bright":
                    data["brightness_pct"] = 100
                
                if color:
                    color_map = {
                        "red": [255, 0, 0],
                        "green": [0, 255, 0],
                        "blue": [0, 0, 255],
                        "yellow": [255, 255, 0],
                        "purple": [128, 0, 128],
                        "orange": [255, 165, 0],
                        "pink": [255, 192, 203],
                        "white": [255, 255, 255],
                    }
                    if color in color_map:
                        data["rgb_color"] = color_map[color]
            
            # Call Home Assistant service
            url = f"{host}/api/services/{domain}/{service}"
            response = requests.post(url, headers=headers, json=data, timeout=10)
            
            if response.status_code == 200:
                device_display = device or domain
                action_display = "on" if "on" in service else "off" if "off" in service else action
                return f"{device_display.title()} turned {action_display}."
            else:
                return f"Home Assistant error: {response.status_code}"
                
        except requests.exceptions.ConnectionError:
            return "Couldn't connect to Home Assistant. Check if it's running."
        except Exception as e:
            print(f"[HomeAssistant] Error: {e}")
            return "Error controlling device via Home Assistant."
    
    def _control_lifx_lights(self, config: Dict, action: str, device: str, brightness: int = None, color: str = None) -> str:
        """Control LIFX lights"""
        token = config.get("token", "")
        
        if not token:
            return "LIFX token not configured."
        
        headers = {"Authorization": f"Bearer {token}"}
        
        try:
            # Selector for which lights to control
            selector = f"label:{device}" if device else "all"
            
            if action in ["on", "turn on"]:
                power = "on"
            elif action in ["off", "turn off"]:
                power = "off"
            else:
                power = None
            
            # Build state
            state = {}
            if power:
                state["power"] = power
            if brightness is not None:
                state["brightness"] = brightness / 100.0
            if color:
                state["color"] = color
            
            url = f"https://api.lifx.com/v1/lights/{selector}/state"
            response = requests.put(url, headers=headers, json=state, timeout=10)
            
            if response.status_code == 207:  # Multi-status (LIFX returns this)
                return f"Lights {'turned on' if power == 'on' else 'turned off' if power == 'off' else 'updated'}."
            else:
                return f"LIFX error: {response.status_code}"
                
        except Exception as e:
            return f"Error controlling LIFX: {str(e)[:50]}"
    
    def _control_tuya_device(self, config: Dict, device_type: str, action: str, device: str, value: Any = None) -> str:
        """
        Control Tuya/Smart Life/Fonri devices
        Fonri devices use Tuya platform
        """
        try:
            import tinytuya
            TINYTUYA_AVAILABLE = True
        except ImportError:
            TINYTUYA_AVAILABLE = False
        
        if not TINYTUYA_AVAILABLE:
            return ("To control Fonri/Tuya lights, I need the TinyTuya library. "
                   "Install it with: pip install tinytuya. "
                   "Then I'll need your device info from the Tuya IoT Platform.")
        
        # Get device config
        devices = config.get("devices", [])
        
        if not devices:
            return self._tuya_setup_guide()
        
        # Find matching device
        target_device = None
        for dev in devices:
            dev_name = dev.get("name", "").lower()
            if not device or device in dev_name or device == "all":
                target_device = dev
                break
        
        if not target_device:
            device_names = [d.get("name", "Unknown") for d in devices]
            return f"Couldn't find device '{device}'. Available: {', '.join(device_names)}"
        
        try:
            # Connect to device
            d = tinytuya.BulbDevice(
                dev_id=target_device.get("id"),
                address=target_device.get("ip"),
                local_key=target_device.get("key"),
                version=target_device.get("version", 3.3)
            )
            d.set_socketPersistent(False)
            
            # Execute action
            if action in ["on", "turn on"]:
                d.turn_on()
                return f"{target_device.get('name', 'Light')} turned on."
            elif action in ["off", "turn off"]:
                d.turn_off()
                return f"{target_device.get('name', 'Light')} turned off."
            elif action == "toggle":
                status = d.status()
                is_on = status.get("dps", {}).get("20", False) or status.get("dps", {}).get("1", False)
                if is_on:
                    d.turn_off()
                    return f"{target_device.get('name', 'Light')} turned off."
                else:
                    d.turn_on()
                    return f"{target_device.get('name', 'Light')} turned on."
            elif action in ["dim", "bright"] or value is not None:
                # Set brightness (Tuya uses 10-1000 scale typically)
                if action == "dim":
                    brightness = 100  # 10%
                elif action == "bright":
                    brightness = 1000  # 100%
                elif value is not None:
                    brightness = int(int(value) * 10)  # Convert 0-100 to 0-1000
                d.set_brightness(brightness)
                d.turn_on()
                return f"{target_device.get('name', 'Light')} brightness set."
            
            return "Done."
            
        except Exception as e:
            print(f"[Tuya] Error: {e}")
            return f"Couldn't control device. Make sure it's on the same network. Error: {str(e)[:40]}"
    
    def _tuya_setup_guide(self) -> str:
        """Guide for setting up Tuya/Fonri devices"""
        return ("To control your Fonri lights, I need device credentials. Here's how:\n\n"
                "1. Install TinyTuya: pip install tinytuya\n"
                "2. Create account at iot.tuya.com\n"
                "3. Create a Cloud Project and link your Fonri app\n"
                "4. Run: python -m tinytuya wizard\n"
                "5. Save the device info to ~/friday-assistant/smart_home.json like:\n"
                '{"platform": "tuya", "devices": [{"name": "Living Room", "id": "xxx", "ip": "192.168.1.x", "key": "xxx", "version": 3.3}]}')


# Global instance
command_handler = CommandHandler()
