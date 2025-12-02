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
        
        # === PC CONTROL: VOLUME ===
        volume_words = ["volume", "sound", "audio"]
        if any(word in user_input for word in volume_words):
            return self._handle_volume(user_input)
        
        # === PC CONTROL: TIMER ===
        if "timer" in user_input or "countdown" in user_input:
            return self._handle_timer(user_input)
        
        # === PC CONTROL: ALARM ===
        if "alarm" in user_input or "wake me" in user_input or "remind me at" in user_input:
            return self._handle_alarm(user_input)
        
        # === PC CONTROL: BRIGHTNESS ===
        if "brightness" in user_input or "screen bright" in user_input:
            return self._handle_brightness(user_input)
        
        # === PC CONTROL: MEDIA ===
        media_words = ["pause", "play", "skip", "next track", "previous track", "stop music", "resume"]
        if any(word in user_input for word in media_words):
            return self._handle_media(user_input)
        
        # === PC CONTROL: SHUTDOWN/RESTART/SLEEP ===
        power_words = ["shutdown", "shut down", "restart", "reboot", "sleep", "hibernate", "lock"]
        if any(word in user_input for word in power_words):
            return self._handle_power(user_input)
        
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
    
    # === PC CONTROL FUNCTIONS ===
    
    def _handle_volume(self, user_input: str) -> str:
        """Handle volume control commands"""
        import re
        
        # Check for mute/unmute
        if "mute" in user_input:
            return self._set_volume("mute")
        if "unmute" in user_input:
            return self._set_volume("unmute")
        if "max" in user_input or "full" in user_input or "100" in user_input:
            return self._set_volume(100)
        
        # Extract number from input
        numbers = re.findall(r'\d+', user_input)
        if numbers:
            level = int(numbers[0])
            if 0 <= level <= 100:
                return self._set_volume(level)
        
        # Volume up/down
        if any(word in user_input for word in ["up", "higher", "increase", "louder"]):
            return self._set_volume("up")
        if any(word in user_input for word in ["down", "lower", "decrease", "quieter", "softer"]):
            return self._set_volume("down")
        
        return "What volume level? Say a number from 0 to 100, or up/down/mute."
    
    def _set_volume(self, level) -> str:
        """Set system volume"""
        try:
            if self.system == "Windows":
                # Use nircmd for Windows volume control (or PowerShell)
                if level == "mute":
                    subprocess.run('powershell -c "(New-Object -ComObject WScript.Shell).SendKeys([char]173)"', 
                                 shell=True, capture_output=True)
                    return "Muted."
                elif level == "unmute":
                    subprocess.run('powershell -c "(New-Object -ComObject WScript.Shell).SendKeys([char]173)"',
                                 shell=True, capture_output=True)
                    return "Unmuted."
                elif level == "up":
                    subprocess.run('powershell -c "(New-Object -ComObject WScript.Shell).SendKeys([char]175)"',
                                 shell=True, capture_output=True)
                    return "Volume up."
                elif level == "down":
                    subprocess.run('powershell -c "(New-Object -ComObject WScript.Shell).SendKeys([char]174)"',
                                 shell=True, capture_output=True)
                    return "Volume down."
                else:
                    # Set exact volume using PowerShell
                    ps_cmd = f'''
                    $wshell = New-Object -ComObject WScript.Shell
                    # Mute then set volume
                    1..50 | ForEach-Object {{ $wshell.SendKeys([char]174) }}
                    1..{level // 2} | ForEach-Object {{ $wshell.SendKeys([char]175) }}
                    '''
                    subprocess.run(['powershell', '-c', ps_cmd], capture_output=True)
                    return f"Volume set to {level}%."
            else:
                # Linux with pactl
                if level == "mute":
                    subprocess.run(['pactl', 'set-sink-mute', '@DEFAULT_SINK@', 'toggle'], capture_output=True)
                    return "Muted."
                elif level == "unmute":
                    subprocess.run(['pactl', 'set-sink-mute', '@DEFAULT_SINK@', '0'], capture_output=True)
                    return "Unmuted."
                elif level == "up":
                    subprocess.run(['pactl', 'set-sink-volume', '@DEFAULT_SINK@', '+10%'], capture_output=True)
                    return "Volume up."
                elif level == "down":
                    subprocess.run(['pactl', 'set-sink-volume', '@DEFAULT_SINK@', '-10%'], capture_output=True)
                    return "Volume down."
                else:
                    subprocess.run(['pactl', 'set-sink-volume', '@DEFAULT_SINK@', f'{level}%'], capture_output=True)
                    return f"Volume set to {level}%."
        except Exception as e:
            print(f"[Volume] Error: {e}")
            return "Couldn't change volume."
    
    def _handle_timer(self, user_input: str) -> str:
        """Handle timer commands - set timer for X minutes/hours"""
        import re
        
        # Cancel timer
        if "cancel" in user_input or "stop" in user_input:
            timer_id = "main_timer"
            if timer_id in active_timers:
                active_timers[timer_id]["cancelled"] = True
                del active_timers[timer_id]
                return "Timer cancelled."
            return "No active timer to cancel."
        
        # Extract time
        numbers = re.findall(r'\d+', user_input)
        if not numbers:
            return "How long should I set the timer for? Say something like 'timer for 5 minutes'."
        
        duration = int(numbers[0])
        
        # Determine unit
        if "hour" in user_input:
            seconds = duration * 3600
            unit = "hour" if duration == 1 else "hours"
        elif "second" in user_input:
            seconds = duration
            unit = "second" if duration == 1 else "seconds"
        else:  # Default to minutes
            seconds = duration * 60
            unit = "minute" if duration == 1 else "minutes"
        
        # Start timer thread
        timer_id = "main_timer"
        active_timers[timer_id] = {"duration": seconds, "cancelled": False}
        
        def timer_callback():
            if timer_id in active_timers and not active_timers[timer_id].get("cancelled"):
                play_alarm_sound()
                send_notification("Timer Done!", f"Your {duration} {unit} timer is complete!")
                if self.gui_callback:
                    self.gui_callback(f"Timer done! {duration} {unit} have passed.")
                del active_timers[timer_id]
        
        timer = threading.Timer(seconds, timer_callback)
        timer.daemon = True
        timer.start()
        
        return f"Timer set for {duration} {unit}."
    
    def _handle_alarm(self, user_input: str) -> str:
        """Handle alarm commands - set alarm for specific time"""
        import re
        
        # Cancel alarm
        if "cancel" in user_input or "stop" in user_input:
            if "main_alarm" in active_timers:
                active_timers["main_alarm"]["cancelled"] = True
                del active_timers["main_alarm"]
                return "Alarm cancelled."
            return "No active alarm to cancel."
        
        # Parse time from input (e.g., "5am", "5:30pm", "17:00")
        time_match = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)?', user_input, re.IGNORECASE)
        
        if not time_match:
            return "What time should I set the alarm? Say something like 'alarm for 7am' or 'alarm for 5:30 pm'."
        
        hour = int(time_match.group(1))
        minute = int(time_match.group(2)) if time_match.group(2) else 0
        ampm = time_match.group(3).lower() if time_match.group(3) else None
        
        # Convert to 24-hour
        if ampm == "pm" and hour < 12:
            hour += 12
        elif ampm == "am" and hour == 12:
            hour = 0
        
        # Calculate seconds until alarm
        now = datetime.now()
        alarm_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        # If time already passed today, set for tomorrow
        if alarm_time <= now:
            alarm_time += timedelta(days=1)
        
        seconds_until = (alarm_time - now).total_seconds()
        
        # Format display time
        display_time = alarm_time.strftime("%I:%M %p")
        
        # Start alarm thread
        active_timers["main_alarm"] = {"time": alarm_time, "cancelled": False}
        
        def alarm_callback():
            if "main_alarm" in active_timers and not active_timers["main_alarm"].get("cancelled"):
                play_alarm_sound()
                send_notification("Alarm!", f"It's {display_time}!")
                if self.gui_callback:
                    self.gui_callback(f"Alarm! It's {display_time}!")
                del active_timers["main_alarm"]
        
        timer = threading.Timer(seconds_until, alarm_callback)
        timer.daemon = True
        timer.start()
        
        return f"Alarm set for {display_time}."
    
    def _handle_brightness(self, user_input: str) -> str:
        """Handle screen brightness control"""
        import re
        
        numbers = re.findall(r'\d+', user_input)
        
        if any(word in user_input for word in ["max", "full", "highest"]):
            level = 100
        elif any(word in user_input for word in ["min", "lowest", "dim"]):
            level = 10
        elif any(word in user_input for word in ["up", "higher", "increase", "brighter"]):
            level = "up"
        elif any(word in user_input for word in ["down", "lower", "decrease", "dimmer"]):
            level = "down"
        elif numbers:
            level = int(numbers[0])
            if level > 100:
                level = 100
        else:
            return "What brightness level? Say a number from 0 to 100, or up/down."
        
        return self._set_brightness(level)
    
    def _set_brightness(self, level) -> str:
        """Set screen brightness"""
        try:
            if self.system == "Windows":
                if level == "up":
                    subprocess.run(['powershell', '-c', 
                        '(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1, [math]::Min(100, (Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightness).CurrentBrightness + 10))'],
                        capture_output=True)
                    return "Brightness increased."
                elif level == "down":
                    subprocess.run(['powershell', '-c',
                        '(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1, [math]::Max(0, (Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightness).CurrentBrightness - 10))'],
                        capture_output=True)
                    return "Brightness decreased."
                else:
                    subprocess.run(['powershell', '-c',
                        f'(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1, {level})'],
                        capture_output=True)
                    return f"Brightness set to {level}%."
            else:
                # Linux with brightnessctl
                if level == "up":
                    subprocess.run(['brightnessctl', 'set', '+10%'], capture_output=True)
                    return "Brightness increased."
                elif level == "down":
                    subprocess.run(['brightnessctl', 'set', '10%-'], capture_output=True)
                    return "Brightness decreased."
                else:
                    subprocess.run(['brightnessctl', 'set', f'{level}%'], capture_output=True)
                    return f"Brightness set to {level}%."
        except Exception as e:
            print(f"[Brightness] Error: {e}")
            return "Couldn't change brightness. This might not be supported on your device."
    
    def _handle_media(self, user_input: str) -> str:
        """Handle media playback control (play/pause/skip)"""
        try:
            if self.system == "Windows":
                if "pause" in user_input or "stop" in user_input:
                    subprocess.run('powershell -c "(New-Object -ComObject WScript.Shell).SendKeys([char]179)"',
                                 shell=True, capture_output=True)
                    return "Paused."
                elif "play" in user_input or "resume" in user_input:
                    subprocess.run('powershell -c "(New-Object -ComObject WScript.Shell).SendKeys([char]179)"',
                                 shell=True, capture_output=True)
                    return "Playing."
                elif "next" in user_input or "skip" in user_input:
                    subprocess.run('powershell -c "(New-Object -ComObject WScript.Shell).SendKeys([char]176)"',
                                 shell=True, capture_output=True)
                    return "Skipping to next track."
                elif "previous" in user_input or "back" in user_input:
                    subprocess.run('powershell -c "(New-Object -ComObject WScript.Shell).SendKeys([char]177)"',
                                 shell=True, capture_output=True)
                    return "Going back to previous track."
            else:
                # Linux with playerctl
                if "pause" in user_input or "stop" in user_input:
                    subprocess.run(['playerctl', 'pause'], capture_output=True)
                    return "Paused."
                elif "play" in user_input or "resume" in user_input:
                    subprocess.run(['playerctl', 'play'], capture_output=True)
                    return "Playing."
                elif "next" in user_input or "skip" in user_input:
                    subprocess.run(['playerctl', 'next'], capture_output=True)
                    return "Skipping to next track."
                elif "previous" in user_input or "back" in user_input:
                    subprocess.run(['playerctl', 'previous'], capture_output=True)
                    return "Going back to previous track."
            
            return "Media control done."
        except Exception as e:
            print(f"[Media] Error: {e}")
            return "Couldn't control media playback."
    
    def _handle_power(self, user_input: str) -> str:
        """Handle power commands (shutdown, restart, sleep, lock)"""
        try:
            if self.system == "Windows":
                if "lock" in user_input:
                    subprocess.run('rundll32.exe user32.dll,LockWorkStation', shell=True, capture_output=True)
                    return "Locking your PC."
                elif "sleep" in user_input:
                    subprocess.run('rundll32.exe powrprof.dll,SetSuspendState 0,1,0', shell=True, capture_output=True)
                    return "Putting PC to sleep."
                elif "hibernate" in user_input:
                    subprocess.run('shutdown /h', shell=True, capture_output=True)
                    return "Hibernating."
                elif "restart" in user_input or "reboot" in user_input:
                    return "Are you sure? Say 'yes restart' to confirm restarting your PC."
                elif "yes restart" in user_input:
                    subprocess.run('shutdown /r /t 5', shell=True, capture_output=True)
                    return "Restarting in 5 seconds."
                elif "shutdown" in user_input or "shut down" in user_input:
                    return "Are you sure? Say 'yes shutdown' to confirm shutting down your PC."
                elif "yes shutdown" in user_input:
                    subprocess.run('shutdown /s /t 5', shell=True, capture_output=True)
                    return "Shutting down in 5 seconds."
            else:
                if "lock" in user_input:
                    subprocess.run(['loginctl', 'lock-session'], capture_output=True)
                    return "Locking your PC."
                elif "sleep" in user_input:
                    subprocess.run(['systemctl', 'suspend'], capture_output=True)
                    return "Putting PC to sleep."
                elif "restart" in user_input or "reboot" in user_input:
                    return "Are you sure? Say 'yes restart' to confirm."
                elif "yes restart" in user_input:
                    subprocess.run(['systemctl', 'reboot'], capture_output=True)
                    return "Restarting."
                elif "shutdown" in user_input or "shut down" in user_input:
                    return "Are you sure? Say 'yes shutdown' to confirm."
                elif "yes shutdown" in user_input:
                    subprocess.run(['systemctl', 'poweroff'], capture_output=True)
                    return "Shutting down."
            
            return "What power action? Lock, sleep, restart, or shutdown?"
        except Exception as e:
            print(f"[Power] Error: {e}")
            return "Couldn't perform power action."


# Global instance
command_handler = CommandHandler()
