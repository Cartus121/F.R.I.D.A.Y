"""
Command Handler for F.R.I.D.A.Y.
Processes voice commands and executes actions
Features: Timer, Calculator, Unit Conversions, Calendar, Notes, Weather, System
"""

import re
import threading
import time as time_module
from datetime import datetime, timedelta
from typing import Tuple, Optional, Dict, Any
import webbrowser
import subprocess
import psutil

try:
    from dateutil import parser as date_parser
    from dateutil.relativedelta import relativedelta
    DATEUTIL_AVAILABLE = True
except ImportError:
    DATEUTIL_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    from duckduckgo_search import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    DDGS_AVAILABLE = False

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
    """Handles and routes voice commands - F.R.I.D.A.Y. style"""
    
    def __init__(self):
        self.last_command_time = None
        self.gui_callback = None  # For sending messages to GUI
        
    def set_gui_callback(self, callback):
        """Set callback for sending async messages to GUI"""
        self.gui_callback = callback
        
    def process(self, command: str) -> Tuple[str, bool]:
        """
        Process a voice command and return response
        Returns: (response_text, should_continue_listening)
        """
        command = command.lower().strip()
        
        if not command:
            return ("I didn't catch that.", True)
        
        # Wake word response - F.R.I.D.A.Y. style
        if command == "__wake__":
            return ("Yes? What do you need?", True)
        
        # === Time & Date ===
        if any(phrase in command for phrase in ["what time", "current time", "tell me the time"]):
            return self._get_time(), True
        
        if any(phrase in command for phrase in ["what date", "what's the date", "today's date", "what day"]):
            return self._get_date(), True
        
        # === Timer Commands ===
        if any(phrase in command for phrase in ["set timer", "set a timer", "timer for", "start timer"]):
            return self._set_timer(command), True
        
        if any(phrase in command for phrase in ["cancel timer", "stop timer", "clear timer"]):
            return self._cancel_timer(command), True
        
        if any(phrase in command for phrase in ["how much time", "timer status", "time left"]):
            return self._get_timer_status(), True
        
        # === Calculator ===
        if any(phrase in command for phrase in ["calculate", "what is", "what's", "how much is"]):
            calc_result = self._calculate(command)
            if calc_result:
                return calc_result, True
        
        # === Unit Conversions ===
        if any(phrase in command for phrase in ["convert", "how many", "how much"]):
            conv_result = self._convert_units(command)
            if conv_result:
                return conv_result, True
        
        # === Calendar ===
        if any(phrase in command for phrase in ["add event", "schedule", "create event", "add to calendar"]):
            return self._add_calendar_event(command), True
        
        if any(phrase in command for phrase in ["my calendar", "my events", "what's on", "upcoming events", "today's events"]):
            return self._get_calendar_events(command), True
        
        # === Notes ===
        if any(phrase in command for phrase in ["take a note", "write down", "remember this", "note that"]):
            return self._add_note(command), True
        
        if any(phrase in command for phrase in ["read my notes", "my notes", "show notes", "list notes"]):
            return self._get_notes(), True
        
        # === Weather ===
        if any(phrase in command for phrase in ["weather", "temperature", "forecast"]):
            return self._get_weather(), True
        
        # === System ===
        if any(phrase in command for phrase in ["system status", "system info", "how's my computer", "pc status", "diagnostics"]):
            return self._get_system_status(), True
        
        # === Web Search ===
        if any(phrase in command for phrase in ["search for", "look up", "google", "find information", "search google", "search firefox", "search in"]):
            return self._web_search(command), True
        
        # === Open URL / Website ===
        if any(phrase in command for phrase in ["go to website", "open website", "visit"]):
            return self._open_website(command), True
        
        # === Open Application ===
        if command.startswith("open "):
            return self._open_application(command), True
        
        # === Reminders ===
        if any(phrase in command for phrase in ["remind me", "set reminder", "set a reminder"]):
            return self._set_reminder(command), True
        
        # === Sleep Commands - F.R.I.D.A.Y. style ===
        if any(phrase in command for phrase in ["goodbye", "go to sleep", "that's all", "stop listening", 
                                                  "пока", "до свидания"]):
            return (f"Standing by. Say '{WAKE_WORD}' when you need me.", False)
        
        if any(phrase in command for phrase in ["thank you", "thanks", "спасибо"]):
            return ("Of course. I'll be here.", False)
        
        # === Default: AI Response ===
        response = brain.get_response(command, context={
            "current_time": datetime.now().strftime(TIME_FORMAT),
            "current_date": datetime.now().strftime(DATE_FORMAT),
            "location": LOCATION
        })
        
        return response, True
    
    # ==================== TIME & DATE ====================
    
    def _get_time(self) -> str:
        now = datetime.now()
        return f"It's {now.strftime(TIME_FORMAT)}."
    
    def _get_date(self) -> str:
        now = datetime.now()
        day_name = now.strftime("%A")
        date_str = now.strftime(DATE_FORMAT)
        return f"Today is {day_name}, {date_str}."
    
    # ==================== TIMER ====================
    
    def _set_timer(self, command: str) -> str:
        """Set a countdown timer"""
        # Parse duration from command
        duration_seconds = 0
        
        # Match patterns like "5 minutes", "1 hour 30 minutes", "90 seconds"
        hour_match = re.search(r'(\d+)\s*hours?', command)
        min_match = re.search(r'(\d+)\s*minutes?', command)
        sec_match = re.search(r'(\d+)\s*seconds?', command)
        
        if hour_match:
            duration_seconds += int(hour_match.group(1)) * 3600
        if min_match:
            duration_seconds += int(min_match.group(1)) * 60
        if sec_match:
            duration_seconds += int(sec_match.group(1))
        
        if duration_seconds == 0:
            return "How long should I set the timer for?"
        
        # Create timer
        timer_id = f"timer_{int(time_module.time())}"
        end_time = datetime.now() + timedelta(seconds=duration_seconds)
        
        def timer_callback():
            if timer_id in active_timers:
                del active_timers[timer_id]
                # Play alarm and notify
                play_alarm_sound()
                send_notification("F.R.I.D.A.Y.", "Timer complete!")
                if self.gui_callback:
                    self.gui_callback("⏰ Time's up.")
        
        timer_thread = threading.Timer(duration_seconds, timer_callback)
        timer_thread.daemon = True
        timer_thread.start()
        
        active_timers[timer_id] = {
            "end_time": end_time,
            "duration": duration_seconds,
            "thread": timer_thread
        }
        
        # Format duration for response
        if duration_seconds >= 3600:
            hours = duration_seconds // 3600
            mins = (duration_seconds % 3600) // 60
            duration_str = f"{hours} hour{'s' if hours > 1 else ''}"
            if mins > 0:
                duration_str += f" {mins} minute{'s' if mins > 1 else ''}"
        elif duration_seconds >= 60:
            mins = duration_seconds // 60
            secs = duration_seconds % 60
            duration_str = f"{mins} minute{'s' if mins > 1 else ''}"
            if secs > 0:
                duration_str += f" {secs} second{'s' if secs > 1 else ''}"
        else:
            duration_str = f"{duration_seconds} second{'s' if duration_seconds > 1 else ''}"
        
        return f"Timer set for {duration_str}."
    
    def _cancel_timer(self, command: str) -> str:
        """Cancel active timer(s)"""
        if not active_timers:
            return "No active timers."
        
        for timer_id, timer_data in list(active_timers.items()):
            timer_data["thread"].cancel()
            del active_timers[timer_id]
        
        return "Timer cancelled."
    
    def _get_timer_status(self) -> str:
        """Get status of active timers"""
        if not active_timers:
            return "No active timers."
        
        statuses = []
        for timer_id, timer_data in active_timers.items():
            remaining = (timer_data["end_time"] - datetime.now()).total_seconds()
            if remaining > 0:
                mins, secs = divmod(int(remaining), 60)
                hours, mins = divmod(mins, 60)
                if hours > 0:
                    statuses.append(f"{hours}h {mins}m remaining")
                elif mins > 0:
                    statuses.append(f"{mins}m {secs}s remaining")
                else:
                    statuses.append(f"{secs}s remaining")
        
        return f"Timer: {', '.join(statuses)}" if statuses else "No active timers."
    
    # ==================== CALCULATOR ====================
    
    def _calculate(self, command: str) -> Optional[str]:
        """Evaluate mathematical expressions"""
        # Clean up command
        for phrase in ["calculate", "what is", "what's", "how much is", "compute"]:
            command = command.replace(phrase, "")
        
        expr = command.strip()
        
        # Handle word-based operations
        expr = expr.replace("plus", "+").replace("minus", "-")
        expr = expr.replace("times", "*").replace("multiplied by", "*")
        expr = expr.replace("divided by", "/").replace("over", "/")
        expr = expr.replace("to the power of", "**").replace("squared", "**2").replace("cubed", "**3")
        expr = expr.replace("percent of", "* 0.01 *").replace("%", "* 0.01")
        expr = expr.replace("x", "*")
        
        # Clean expression
        expr = re.sub(r'[^0-9+\-*/().^ ]', '', expr)
        expr = expr.replace("^", "**")
        
        if not expr or not re.search(r'\d', expr):
            return None
        
        try:
            # Safe evaluation
            allowed_chars = set('0123456789+-*/.() ')
            if not all(c in allowed_chars or c == '*' for c in expr):
                return None
            
            result = eval(expr)
            
            # Format result
            if isinstance(result, float):
                if result == int(result):
                    result = int(result)
                else:
                    result = round(result, 4)
            
            return f"That's {result}."
        except:
            return None
    
    # ==================== UNIT CONVERSIONS ====================
    
    def _convert_units(self, command: str) -> Optional[str]:
        """Convert between units"""
        
        # Temperature conversions
        temp_match = re.search(r'(\d+(?:\.\d+)?)\s*(celsius|c|fahrenheit|f|kelvin|k)\s*(?:to|in)\s*(celsius|c|fahrenheit|f|kelvin|k)', command)
        if temp_match:
            value = float(temp_match.group(1))
            from_unit = temp_match.group(2).lower()[0]
            to_unit = temp_match.group(3).lower()[0]
            
            # Convert to Celsius first
            if from_unit == 'f':
                celsius = (value - 32) * 5/9
            elif from_unit == 'k':
                celsius = value - 273.15
            else:
                celsius = value
            
            # Convert from Celsius
            if to_unit == 'f':
                result = celsius * 9/5 + 32
                to_name = "Fahrenheit"
            elif to_unit == 'k':
                result = celsius + 273.15
                to_name = "Kelvin"
            else:
                result = celsius
                to_name = "Celsius"
            
            return f"{value}° is {round(result, 1)}° {to_name}."
        
        # Distance conversions
        dist_patterns = [
            (r'(\d+(?:\.\d+)?)\s*(miles?|mi)\s*(?:to|in)\s*(kilometers?|km)', lambda v: v * 1.60934, "kilometers"),
            (r'(\d+(?:\.\d+)?)\s*(kilometers?|km)\s*(?:to|in)\s*(miles?|mi)', lambda v: v / 1.60934, "miles"),
            (r'(\d+(?:\.\d+)?)\s*(feet|ft)\s*(?:to|in)\s*(meters?|m)', lambda v: v * 0.3048, "meters"),
            (r'(\d+(?:\.\d+)?)\s*(meters?|m)\s*(?:to|in)\s*(feet|ft)', lambda v: v / 0.3048, "feet"),
            (r'(\d+(?:\.\d+)?)\s*(inches?|in)\s*(?:to|in)\s*(centimeters?|cm)', lambda v: v * 2.54, "centimeters"),
            (r'(\d+(?:\.\d+)?)\s*(centimeters?|cm)\s*(?:to|in)\s*(inches?|in)', lambda v: v / 2.54, "inches"),
        ]
        
        for pattern, converter, to_name in dist_patterns:
            match = re.search(pattern, command)
            if match:
                value = float(match.group(1))
                result = converter(value)
                return f"{value} is {round(result, 2)} {to_name}."
        
        # Weight conversions
        weight_patterns = [
            (r'(\d+(?:\.\d+)?)\s*(pounds?|lbs?)\s*(?:to|in)\s*(kilograms?|kg)', lambda v: v * 0.453592, "kilograms"),
            (r'(\d+(?:\.\d+)?)\s*(kilograms?|kg)\s*(?:to|in)\s*(pounds?|lbs?)', lambda v: v / 0.453592, "pounds"),
            (r'(\d+(?:\.\d+)?)\s*(ounces?|oz)\s*(?:to|in)\s*(grams?|g)', lambda v: v * 28.3495, "grams"),
            (r'(\d+(?:\.\d+)?)\s*(grams?|g)\s*(?:to|in)\s*(ounces?|oz)', lambda v: v / 28.3495, "ounces"),
        ]
        
        for pattern, converter, to_name in weight_patterns:
            match = re.search(pattern, command)
            if match:
                value = float(match.group(1))
                result = converter(value)
                return f"{value} is {round(result, 2)} {to_name}."
        
        # Currency (basic - would need API for real rates)
        currency_match = re.search(r'(\d+(?:\.\d+)?)\s*(usd|dollars?|eur|euros?|gbp|pounds?)\s*(?:to|in)\s*(usd|dollars?|eur|euros?|gbp|pounds?)', command)
        if currency_match:
            return "Currency conversion requires live exchange rates. I'd recommend checking xe.com for current rates."
        
        return None
    
    # ==================== CALENDAR ====================
    
    def _add_calendar_event(self, command: str) -> str:
        for phrase in ["add event", "schedule", "create event", "add to calendar"]:
            command = command.replace(phrase, "")
        
        command = command.strip()
        event_title = command
        event_time = datetime.now() + timedelta(hours=1)
        
        if DATEUTIL_AVAILABLE:
            time_patterns = [
                r"(tomorrow|today|monday|tuesday|wednesday|thursday|friday|saturday|sunday)",
                r"at (\d{1,2}(?::\d{2})?\s*(?:am|pm)?)",
                r"on (\d{1,2}/\d{1,2}(?:/\d{2,4})?)",
            ]
            
            for pattern in time_patterns:
                match = re.search(pattern, command, re.IGNORECASE)
                if match:
                    try:
                        parsed = date_parser.parse(match.group(), fuzzy=True)
                        event_time = parsed
                        event_title = re.sub(pattern, "", event_title, flags=re.IGNORECASE).strip()
                    except:
                        pass
        
        event_title = re.sub(r'\s+', ' ', event_title).strip()
        if not event_title:
            event_title = "Untitled Event"
        
        db.add_event(title=event_title, start_time=event_time)
        time_str = event_time.strftime(f"{DATE_FORMAT} at {TIME_FORMAT}")
        return f"Done. '{event_title}' added for {time_str}."
    
    def _get_calendar_events(self, command: str) -> str:
        if "today" in command:
            events = db.get_todays_events()
            time_frame = "today"
        else:
            events = db.get_upcoming_events(days=7)
            time_frame = "the next 7 days"
        
        if not events:
            return f"Your calendar is clear for {time_frame}."
        
        event_list = []
        for event in events[:5]:
            title = event['title']
            start = datetime.fromisoformat(event['start_time'])
            time_str = start.strftime(f"%A at {TIME_FORMAT}")
            event_list.append(f"{title} on {time_str}")
        
        return f"You have {len(events)} event{'s' if len(events) > 1 else ''}: {', '.join(event_list)}."
    
    # ==================== NOTES ====================
    
    def _add_note(self, command: str) -> str:
        for phrase in ["take a note", "write down", "remember this", "note that"]:
            command = command.replace(phrase, "")
        
        note_content = command.strip()
        if not note_content:
            return "What should I note down?"
        
        db.add_note(content=note_content)
        return f"Noted: {note_content[:50]}{'...' if len(note_content) > 50 else ''}"
    
    def _get_notes(self) -> str:
        notes = db.get_notes(limit=5)
        if not notes:
            return "No notes on file."
        
        notes_text = []
        for i, note in enumerate(notes, 1):
            content = note['content'][:50] + ("..." if len(note['content']) > 50 else "")
            notes_text.append(f"{i}. {content}")
        
        return f"Your recent notes: {'. '.join(notes_text)}"
    
    # ==================== WEATHER ====================
    
    def _get_weather(self) -> str:
        if not REQUESTS_AVAILABLE:
            return "Weather module offline."
        
        if not OPENWEATHER_API_KEY:
            return f"Weather requires an API key. Add it in settings. Current location: {LOCATION}."
        
        try:
            url = f"http://api.openweathermap.org/data/2.5/weather?q={LOCATION}&appid={OPENWEATHER_API_KEY}&units=metric"
            response = requests.get(url, timeout=5)
            data = response.json()
            
            if response.status_code == 200:
                temp = round(data['main']['temp'])
                feels_like = round(data['main']['feels_like'])
                description = data['weather'][0]['description']
                humidity = data['main']['humidity']
                
                return f"Currently {temp}°C in {LOCATION}, {description}. Feels like {feels_like}°C, {humidity}% humidity."
            else:
                return f"Weather data unavailable for {LOCATION}."
        except Exception as e:
            return f"Weather systems offline: {str(e)[:30]}"
    
    # ==================== SYSTEM ====================
    
    def _get_system_status(self) -> str:
        try:
            cpu = psutil.cpu_percent(interval=1)
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Add assessment
            status = "nominal"
            if cpu > 80 or mem.percent > 85:
                status = "elevated"
            if cpu > 95 or mem.percent > 95:
                status = "critical"
            
            return (
                f"Systems {status}. CPU at {cpu}%, "
                f"memory at {mem.percent}%, "
                f"storage at {disk.percent}%."
            )
        except Exception as e:
            return f"Diagnostics unavailable: {str(e)[:30]}"
    
    # ==================== WEB SEARCH ====================
    
    def _web_search(self, command: str) -> str:
        """Search the web - opens in browser"""
        import platform
        system = platform.system()
        
        # Clean up the query
        original_command = command.lower()
        for phrase in ["search for", "look up", "google", "find information about", "find information on", 
                       "search google for", "search firefox for", "search in firefox", "search in chrome",
                       "search in google", "search in browser"]:
            command = command.lower().replace(phrase, "")
        
        query = command.strip()
        if not query:
            return "What should I search for?"
        
        # Determine which browser/search engine to use
        use_google = "google" in original_command
        use_firefox = "firefox" in original_command
        
        # Build search URL
        if use_google:
            search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        else:
            search_url = f"https://duckduckgo.com/?q={query.replace(' ', '+')}"
        
        # Open in specific browser if requested
        try:
            if use_firefox:
                if system == "Windows":
                    subprocess.Popen(["start", "firefox", search_url], shell=True)
                else:
                    subprocess.Popen(["firefox", search_url])
            else:
                webbrowser.open(search_url)
        except:
            webbrowser.open(search_url)
        
        return f"Searching for '{query}'."
    
    def _open_website(self, command: str) -> str:
        """Open a specific website"""
        for phrase in ["go to website", "open website", "visit", "go to"]:
            command = command.replace(phrase, "")
        
        url = command.strip()
        if not url:
            return "Which website should I open?"
        
        # Add https if not present
        if not url.startswith("http"):
            url = "https://" + url
        
        webbrowser.open(url)
        return f"Opening {url}."
    
    # ==================== APPLICATIONS ====================
    
    def _open_application(self, command: str) -> str:
        app_name = command.replace("open", "").strip()
        
        import platform
        system = platform.system()
        
        if system == "Windows":
            app_commands = {
                # Browsers
                "browser": "start chrome",
                "chrome": "start chrome",
                "firefox": "start firefox",
                "edge": "start msedge",
                "brave": "start brave",
                # File locations
                "files": "explorer",
                "file manager": "explorer",
                "downloads": "explorer shell:Downloads",
                "download folder": "explorer shell:Downloads",
                "download files": "explorer shell:Downloads",
                "documents": "explorer shell:Personal",
                "my documents": "explorer shell:Personal",
                "pictures": "explorer shell:My Pictures",
                "my pictures": "explorer shell:My Pictures",
                "music": "explorer shell:My Music",
                "my music": "explorer shell:My Music",
                "videos": "explorer shell:My Video",
                "my videos": "explorer shell:My Video",
                "desktop": "explorer shell:Desktop",
                # System
                "terminal": "start cmd",
                "command prompt": "start cmd",
                "powershell": "start powershell",
                "calculator": "calc",
                "notepad": "notepad",
                "settings": "start ms-settings:",
                "control panel": "control",
                "task manager": "taskmgr",
                # Dev tools
                "code": "code",
                "vs code": "code",
                "visual studio code": "code",
                # Apps
                "spotify": "start spotify:",
                "discord": "start discord:",
                "steam": "start steam:",
                "teams": "start msteams:",
                "outlook": "start outlook",
                "word": "start winword",
                "excel": "start excel",
                "powerpoint": "start powerpnt",
            }
        else:
            app_commands = {
                "browser": "firefox",
                "firefox": "firefox",
                "chrome": "google-chrome",
                "files": "nautilus",
                "file manager": "nautilus",
                "terminal": "gnome-terminal",
                "calculator": "gnome-calculator",
                "settings": "gnome-control-center",
                "text editor": "gedit",
                "code": "code",
                "vs code": "code",
                "spotify": "spotify",
                "discord": "discord",
            }
        
        app_cmd = app_commands.get(app_name.lower(), app_name)
        
        try:
            if system == "Windows" and app_cmd.startswith("start"):
                subprocess.Popen(app_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                subprocess.Popen([app_cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return f"Opening {app_name}."
        except Exception:
            return f"Couldn't open {app_name}. Verify it's installed."
    
    # ==================== REMINDERS ====================
    
    def _set_reminder(self, command: str) -> str:
        for phrase in ["remind me to", "remind me", "set reminder", "set a reminder"]:
            command = command.replace(phrase, "")
        
        command = command.strip()
        reminder_time = datetime.now() + timedelta(hours=1)
        reminder_text = command
        
        time_patterns = {
            r"in (\d+) minutes?": lambda m: timedelta(minutes=int(m.group(1))),
            r"in (\d+) hours?": lambda m: timedelta(hours=int(m.group(1))),
            r"in (\d+) days?": lambda m: timedelta(days=int(m.group(1))),
            r"tomorrow": lambda m: timedelta(days=1),
        }
        
        for pattern, delta_func in time_patterns.items():
            match = re.search(pattern, command, re.IGNORECASE)
            if match:
                reminder_time = datetime.now() + delta_func(match)
                reminder_text = re.sub(pattern, "", reminder_text, flags=re.IGNORECASE).strip()
                break
        
        if not reminder_text:
            reminder_text = "Reminder"
        
        db.add_reminder(message=reminder_text, remind_at=reminder_time)
        time_str = reminder_time.strftime(f"{DATE_FORMAT} at {TIME_FORMAT}")
        return f"I'll remind you: '{reminder_text}' on {time_str}."


# Global instance
command_handler = CommandHandler()
