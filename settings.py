"""
Settings Manager for F.R.I.D.A.Y.
Handles user settings, API keys, voice selection, and preferences
"""

import json
import os
import math
import wave
import struct
from pathlib import Path
from typing import Optional

# Settings file location
SETTINGS_DIR = Path.home() / "friday-assistant"
SETTINGS_FILE = SETTINGS_DIR / "settings.json"
ALARM_SOUND_FILE = SETTINGS_DIR / "alarm.wav"
MEMORY_FILE = SETTINGS_DIR / "user_memory.json"

# Voice option - F.R.I.D.A.Y. only
VOICE_OPTIONS = {
    "F.R.I.D.A.Y. (Irish Female)": "en-IE-EmilyNeural",
}

# AI Name
AI_NAMES = {
    "F.R.I.D.A.Y. (Irish Female)": "F.R.I.D.A.Y.",
}

# Default settings
DEFAULT_SETTINGS = {
    "openai_api_key": "",
    "google_api_key": "",
    "openweather_api_key": "",
    "ai_provider": "auto",  # "auto", "gemini", or "openai"
    "language": "en",
    "voice": "F.R.I.D.A.Y. (Irish Female)",
    "ai_name": "F.R.I.D.A.Y.",
    "wake_word": "friday",
    "theme": "dark",
    "conversation_timeout": 30,
    "hotkey_enabled": False,
    "minimize_to_tray": True,
    "notifications_enabled": True,
}


def load_settings() -> dict:
    """Load settings from file"""
    SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
    
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, 'r') as f:
                settings = json.load(f)
                for key, value in DEFAULT_SETTINGS.items():
                    if key not in settings:
                        settings[key] = value
                return settings
        except Exception as e:
            print(f"[!] Error loading settings: {e}")
    
    return DEFAULT_SETTINGS.copy()


def save_settings(settings: dict):
    """Save settings to file"""
    SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=2)
        print("[OK] Configuration saved")
    except Exception as e:
        print(f"[!] Error saving settings: {e}")


def get_api_key(key_name: str) -> str:
    """Get API key from settings or environment"""
    env_key = os.environ.get(key_name.upper(), "")
    if env_key and not env_key.startswith("YOUR_"):
        return env_key
    
    settings = load_settings()
    key_map = {
        "OPENAI_API_KEY": "openai_api_key",
        "GOOGLE_API_KEY": "google_api_key", 
        "OPENWEATHER_API_KEY": "openweather_api_key",
    }
    
    settings_key = key_map.get(key_name.upper(), key_name.lower())
    return settings.get(settings_key, "")


def get_voice_id() -> str:
    """Get the Edge TTS voice ID from settings"""
    settings = load_settings()
    voice_name = settings.get("voice", "F.R.I.D.A.Y. (Irish Female)")
    return VOICE_OPTIONS.get(voice_name, "en-IE-EmilyNeural")


def get_ai_name() -> str:
    """Get the AI name based on voice selection"""
    settings = load_settings()
    voice_name = settings.get("voice", "F.R.I.D.A.Y. (Irish Female)")
    return AI_NAMES.get(voice_name, settings.get("ai_name", "F.R.I.D.A.Y."))


def get_wake_word() -> str:
    """Get the wake word from settings"""
    settings = load_settings()
    return settings.get("wake_word", "friday")


def apply_api_keys():
    """Apply API keys from settings to environment"""
    settings = load_settings()
    
    api_key = settings.get("openai_api_key", "")
    if api_key and api_key.startswith("sk-"):
        os.environ["OPENAI_API_KEY"] = api_key
        return True
    return False


def load_user_memory() -> dict:
    """Load user memory/preferences"""
    if MEMORY_FILE.exists():
        try:
            with open(MEMORY_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {
        "user_name": None,
        "preferences": {},
        "facts": [],
    }


def save_user_memory(memory: dict):
    """Save user memory"""
    SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(MEMORY_FILE, 'w') as f:
            json.dump(memory, f, indent=2)
    except Exception as e:
        print(f"[!] Error saving memory: {e}")


def show_settings_dialog(parent=None) -> bool:
    """Show comprehensive settings dialog"""
    try:
        from translations import get_text
    except:
        def get_text(k, l="en", **kw):
            return k
    
    try:
        import customtkinter as ctk
    except ImportError:
        import tkinter as tk
        from tkinter import simpledialog, messagebox
        
        root = tk.Tk() if parent is None else parent
        if parent is None:
            root.withdraw()
        
        api_key = simpledialog.askstring(
            "F.R.I.D.A.Y. Setup",
            "Enter your OpenAI API Key:",
            parent=root
        )
        
        if api_key and api_key.startswith("sk-"):
            settings = load_settings()
            settings["openai_api_key"] = api_key
            save_settings(settings)
            messagebox.showinfo("Success", "Configuration saved!")
            return True
        return False
    
    settings = load_settings()
    current_lang = settings.get("language", "en")
    result = {"saved": False}
    
    # Get current AI name
    ai_name = AI_NAMES.get(settings.get("voice", "F.R.I.D.A.Y. (Irish Female)"), "F.R.I.D.A.Y.")
    
    dialog = ctk.CTkToplevel(parent) if parent else ctk.CTk()
    dialog.title(f"{ai_name} Settings")
    dialog.geometry("520x700")
    dialog.resizable(False, False)
    
    dialog.update_idletasks()
    x = (dialog.winfo_screenwidth() - 520) // 2
    y = (dialog.winfo_screenheight() - 700) // 2
    dialog.geometry(f"520x700+{x}+{y}")
    
    # Title
    title = ctk.CTkLabel(
        dialog,
        text=f"⚙️ {ai_name} Settings",
        font=ctk.CTkFont(size=24, weight="bold")
    )
    title.pack(pady=(15, 0))
    
    # Subtitle - Full name
    subtitle = ctk.CTkLabel(
        dialog,
        text="Female Replacement Intelligent Digital Assistant Youth",
        font=ctk.CTkFont(size=11),
        text_color="gray"
    )
    subtitle.pack(pady=(0, 15))
    
    # Scrollable frame
    scroll_frame = ctk.CTkScrollableFrame(dialog, height=480)
    scroll_frame.pack(fill="both", expand=True, padx=20, pady=5)
    
    # === API Keys Section ===
    api_section = ctk.CTkLabel(scroll_frame, text="🔑 API Keys & AI Provider", font=ctk.CTkFont(size=16, weight="bold"))
    api_section.pack(anchor="w", pady=(10, 5))
    
    # OpenAI API Key
    api_frame = ctk.CTkFrame(scroll_frame)
    api_frame.pack(fill="x", pady=5)
    
    # AI Provider Selection
    ctk.CTkLabel(api_frame, text="AI Provider:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=10, pady=(8, 0))
    ctk.CTkLabel(api_frame, text="Select which AI to use (changing requires restart)", font=ctk.CTkFont(size=10), text_color="gray").pack(anchor="w", padx=10, pady=(0, 3))
    
    provider_map = {"auto": "Auto (Gemini → OpenAI)", "gemini": "Google Gemini (FREE)", "openai": "OpenAI GPT-4o (Paid)"}
    current_provider = settings.get("ai_provider", "auto")
    provider_var = ctk.StringVar(value=provider_map.get(current_provider, "Auto (Gemini → OpenAI)"))
    provider_menu = ctk.CTkOptionMenu(
        api_frame,
        values=["Auto (Gemini → OpenAI)", "Google Gemini (FREE)", "OpenAI GPT-4o (Paid)"],
        variable=provider_var,
        width=250
    )
    provider_menu.pack(anchor="w", padx=10, pady=(0, 10))
    
    ctk.CTkLabel(api_frame, text="OpenAI API Key:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=10, pady=(8, 0))
    ctk.CTkLabel(api_frame, text="Get key at platform.openai.com (paid)", font=ctk.CTkFont(size=10), text_color="gray").pack(anchor="w", padx=10, pady=(0, 3))
    api_entry = ctk.CTkEntry(api_frame, width=440, placeholder_text="sk-proj-...", show="*")
    api_entry.pack(padx=10, pady=(0, 8))
    if settings.get("openai_api_key"):
        api_entry.insert(0, settings["openai_api_key"])
    
    # Google Gemini API Key (FREE!)
    ctk.CTkLabel(api_frame, text="Google Gemini API Key:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=10, pady=(8, 0))
    ctk.CTkLabel(api_frame, text="Get FREE key at ai.google.dev", font=ctk.CTkFont(size=10), text_color="#22c55e").pack(anchor="w", padx=10, pady=(0, 3))
    gemini_entry = ctk.CTkEntry(api_frame, width=440, placeholder_text="AIza...", show="*")
    gemini_entry.pack(padx=10, pady=(0, 8))
    if settings.get("google_api_key"):
        gemini_entry.insert(0, settings["google_api_key"])
    
    # OpenWeather API Key
    ctk.CTkLabel(api_frame, text="OpenWeather API Key (optional):", font=ctk.CTkFont(size=12)).pack(anchor="w", padx=10, pady=(8, 3))
    weather_entry = ctk.CTkEntry(api_frame, width=440, placeholder_text="For weather information...")
    weather_entry.pack(padx=10, pady=(0, 8))
    if settings.get("openweather_api_key"):
        weather_entry.insert(0, settings["openweather_api_key"])
    
    # === Voice Section ===
    voice_section = ctk.CTkLabel(scroll_frame, text="🎤 Voice & Language", font=ctk.CTkFont(size=16, weight="bold"))
    voice_section.pack(anchor="w", pady=(15, 5))
    
    voice_frame = ctk.CTkFrame(scroll_frame)
    voice_frame.pack(fill="x", pady=5)
    
    # Wake word
    ctk.CTkLabel(voice_frame, text="Wake Word:", font=ctk.CTkFont(size=12)).pack(anchor="w", padx=10, pady=(8, 3))
    wake_entry = ctk.CTkEntry(voice_frame, width=200, placeholder_text="friday")
    wake_entry.pack(anchor="w", padx=10, pady=(0, 8))
    wake_entry.insert(0, settings.get("wake_word", "friday"))
    
    # Language
    ctk.CTkLabel(voice_frame, text="Language:", font=ctk.CTkFont(size=12)).pack(anchor="w", padx=10, pady=(8, 3))
    lang_map = {"en": "English", "ru": "Русский", "auto": "Auto-detect"}
    lang_var = ctk.StringVar(value=lang_map.get(settings.get("language", "en"), "English"))
    lang_menu = ctk.CTkOptionMenu(
        voice_frame,
        values=["English", "Русский", "Auto-detect"],
        variable=lang_var,
        width=200
    )
    lang_menu.pack(anchor="w", padx=10, pady=(0, 8))
    
    # === Behavior Section ===
    behavior_section = ctk.CTkLabel(scroll_frame, text="⚡ Behavior", font=ctk.CTkFont(size=16, weight="bold"))
    behavior_section.pack(anchor="w", pady=(15, 5))
    
    behavior_frame = ctk.CTkFrame(scroll_frame)
    behavior_frame.pack(fill="x", pady=5)
    
    # Conversation timeout
    ctk.CTkLabel(behavior_frame, text="Conversation timeout (seconds):", font=ctk.CTkFont(size=12)).pack(anchor="w", padx=10, pady=(8, 3))
    timeout_var = ctk.StringVar(value=str(settings.get("conversation_timeout", 30)))
    timeout_entry = ctk.CTkEntry(behavior_frame, width=100, textvariable=timeout_var)
    timeout_entry.pack(anchor="w", padx=10, pady=(0, 8))
    
    # Toggles
    tray_var = ctk.BooleanVar(value=settings.get("minimize_to_tray", True))
    tray_cb = ctk.CTkCheckBox(behavior_frame, text="Minimize to system tray", variable=tray_var)
    tray_cb.pack(anchor="w", padx=10, pady=5)
    
    notif_var = ctk.BooleanVar(value=settings.get("notifications_enabled", True))
    notif_cb = ctk.CTkCheckBox(behavior_frame, text="Enable desktop notifications", variable=notif_var)
    notif_cb.pack(anchor="w", padx=10, pady=(5, 10))
    
    # === Data Section ===
    data_section = ctk.CTkLabel(scroll_frame, text="🗑️ Data Management", font=ctk.CTkFont(size=16, weight="bold"))
    data_section.pack(anchor="w", pady=(15, 5))
    
    data_frame = ctk.CTkFrame(scroll_frame)
    data_frame.pack(fill="x", pady=5)
    
    ctk.CTkLabel(data_frame, text="Clear all saved data and start fresh:", font=ctk.CTkFont(size=12)).pack(anchor="w", padx=10, pady=(8, 5))
    
    def reset_all_data():
        """Delete all user data for clean start"""
        import shutil
        import gc
        import sqlite3
        from tkinter import messagebox
        
        confirm = messagebox.askyesno(
            "Reset All Data",
            "This will delete:\n\n• All conversations\n• All settings\n• All cached data\n\nThe app will close. Are you sure?",
            icon='warning'
        )
        
        if confirm:
            try:
                # Force garbage collection to release any open connections
                gc.collect()
                
                # Close any SQLite connections
                try:
                    sqlite3.connect(':memory:').execute('PRAGMA optimize').close()
                except:
                    pass
                
                # Delete individual files first (more reliable than rmtree on Windows)
                db_path = SETTINGS_DIR / "friday_data.db"
                if db_path.exists():
                    try:
                        db_path.unlink()
                    except PermissionError:
                        # If still locked, mark for deletion on restart
                        pass
                
                # Delete settings file
                if SETTINGS_FILE.exists():
                    SETTINGS_FILE.unlink()
                
                # Delete memory file
                if MEMORY_FILE.exists():
                    MEMORY_FILE.unlink()
                
                # Delete alarm file
                if ALARM_SOUND_FILE.exists():
                    ALARM_SOUND_FILE.unlink()
                
                # Delete temp audio files
                import tempfile
                temp_friday = Path(tempfile.gettempdir()) / "friday_audio"
                if temp_friday.exists():
                    try:
                        shutil.rmtree(temp_friday)
                    except:
                        pass
                
                messagebox.showinfo("Reset Complete", "Data cleared! App will now close.\nRestart F.R.I.D.A.Y. for a fresh start.")
                dialog.destroy()
                
                # Force exit
                import os
                os._exit(0)
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to reset: {e}\n\nTry closing the app and manually deleting:\n{SETTINGS_DIR}")
    
    reset_btn = ctk.CTkButton(
        data_frame, 
        text="🔄 Reset All Data", 
        command=reset_all_data,
        width=200, 
        height=35,
        fg_color="#dc2626",
        hover_color="#b91c1c"
    )
    reset_btn.pack(anchor="w", padx=10, pady=(5, 10))
    
    # Error label
    error_label = ctk.CTkLabel(dialog, text="", text_color="red")
    error_label.pack()
    
    # Track if provider changed (needs restart)
    original_provider = settings.get("ai_provider", "auto")
    
    def save_and_close():
        api_key = api_entry.get().strip()
        gemini_key = gemini_entry.get().strip()
        
        # API key validation - both are optional now
        if api_key and not api_key.startswith("sk-"):
            error_label.configure(text="⚠️ Invalid OpenAI key format (should start with 'sk-')")
            return
        
        if gemini_key and not gemini_key.startswith("AIza"):
            error_label.configure(text="⚠️ Invalid Gemini key format (should start with 'AIza')")
            return
        
        # Get selected provider
        provider_reverse = {
            "Auto (Gemini → OpenAI)": "auto",
            "Google Gemini (FREE)": "gemini", 
            "OpenAI GPT-4o (Paid)": "openai"
        }
        new_provider = provider_reverse.get(provider_var.get(), "auto")
        
        # Check if selected provider has valid key
        if new_provider == "gemini" and not gemini_key:
            error_label.configure(text="⚠️ Gemini selected but no Gemini API key provided")
            return
        if new_provider == "openai" and not api_key:
            error_label.configure(text="⚠️ OpenAI selected but no OpenAI API key provided")
            return
        if new_provider == "auto" and not api_key and not gemini_key:
            error_label.configure(text="⚠️ Please add at least one API key")
            return
        
        try:
            timeout = int(timeout_var.get())
        except:
            timeout = 30
        
        lang_reverse = {"English": "en", "Русский": "ru", "Auto-detect": "auto"}
        
        settings["openai_api_key"] = api_key
        settings["google_api_key"] = gemini_key
        settings["openweather_api_key"] = weather_entry.get().strip()
        settings["ai_provider"] = new_provider
        settings["voice"] = "F.R.I.D.A.Y. (Irish Female)"
        settings["ai_name"] = "F.R.I.D.A.Y."
        settings["wake_word"] = wake_entry.get().strip().lower() or "friday"
        settings["language"] = lang_reverse.get(lang_var.get(), "en")
        
        # Apply API keys to environment
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
        if gemini_key:
            os.environ["GOOGLE_API_KEY"] = gemini_key
        settings["conversation_timeout"] = timeout
        settings["minimize_to_tray"] = tray_var.get()
        settings["notifications_enabled"] = notif_var.get()
        
        save_settings(settings)
        result["saved"] = True
        
        # Check if provider changed - needs restart
        if new_provider != original_provider:
            from tkinter import messagebox
            restart = messagebox.askyesno(
                "Restart Required",
                f"AI provider changed to {provider_var.get()}.\n\nRestart F.R.I.D.A.Y. now to apply changes?",
                icon='question'
            )
            if restart:
                dialog.destroy()
                restart_app()
                return
        
        dialog.destroy()
    
    def cancel():
        dialog.destroy()
    
    # Buttons
    btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
    btn_frame.pack(pady=15)
    
    save_btn = ctk.CTkButton(btn_frame, text="💾 Save", command=save_and_close, width=140, height=40)
    save_btn.pack(side="left", padx=20)
    
    cancel_btn = ctk.CTkButton(btn_frame, text="Cancel", command=cancel, width=140, height=40, fg_color="gray")
    cancel_btn.pack(side="left", padx=20)
    
    if parent:
        dialog.transient(parent)
        dialog.grab_set()
        parent.wait_window(dialog)
    else:
        dialog.mainloop()
    
    return result["saved"]


def restart_app():
    """Restart F.R.I.D.A.Y. application"""
    import sys
    import subprocess
    
    try:
        if getattr(sys, 'frozen', False):
            # Running as compiled exe (PyInstaller)
            exe_path = sys.executable
            if sys.platform == 'win32':
                # Windows: use start command to launch new instance
                subprocess.Popen(['cmd', '/c', 'start', '', exe_path], 
                               creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                # Linux/Mac
                subprocess.Popen([exe_path], start_new_session=True)
        else:
            # Running as script
            python = sys.executable
            script = sys.argv[0]
            if sys.platform == 'win32':
                subprocess.Popen([python, script], 
                               creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                subprocess.Popen([python, script], start_new_session=True)
        
        # Exit current instance
        os._exit(0)
    except Exception as e:
        print(f"Restart failed: {e}")


def needs_setup() -> bool:
    """Check if first-time setup is needed"""
    api_key = get_api_key("OPENAI_API_KEY")
    return not api_key or api_key.startswith("YOUR_") or len(api_key) < 20


def generate_alarm_sound():
    """Generate a pleasant alarm sound WAV file"""
    SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
    
    if ALARM_SOUND_FILE.exists():
        return str(ALARM_SOUND_FILE)
    
    try:
        sample_rate = 44100
        duration = 1.5
        frequencies = [523.25, 659.25, 783.99]
        
        samples = []
        num_samples = int(sample_rate * duration)
        
        for i in range(num_samples):
            t = i / sample_rate
            envelope = math.exp(-t * 2)
            
            sample = 0
            for freq in frequencies:
                sample += math.sin(2 * math.pi * freq * t) * envelope
            
            if t > 0.5:
                t2 = t - 0.5
                envelope2 = math.exp(-t2 * 2)
                for freq in [587.33, 739.99, 880.00]:
                    sample += math.sin(2 * math.pi * freq * t2) * envelope2
            
            sample = sample / 6
            sample = max(-1, min(1, sample))
            samples.append(int(sample * 32767))
        
        with wave.open(str(ALARM_SOUND_FILE), 'w') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            
            for sample in samples:
                wav_file.writeframes(struct.pack('<h', sample))
        
        return str(ALARM_SOUND_FILE)
        
    except Exception as e:
        print(f"[!] Could not generate alarm sound: {e}")
        return None


def play_alarm_sound():
    """Play the alarm sound"""
    sound_file = generate_alarm_sound()
    if not sound_file:
        return
    
    import platform
    system = platform.system()
    
    try:
        if system == "Windows":
            try:
                import pygame
                pygame.mixer.init()
                pygame.mixer.music.load(sound_file)
                pygame.mixer.music.play()
                import time
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
            except:
                import winsound
                winsound.PlaySound(sound_file, winsound.SND_FILENAME)
        else:
            import subprocess
            for player in ["mpv", "ffplay", "paplay", "aplay"]:
                try:
                    if player == "mpv":
                        subprocess.run([player, "--no-video", "--really-quiet", sound_file], 
                                      capture_output=True, timeout=5)
                    elif player == "ffplay":
                        subprocess.run([player, "-nodisp", "-autoexit", sound_file],
                                      capture_output=True, timeout=5)
                    else:
                        subprocess.run([player, sound_file], capture_output=True, timeout=5)
                    break
                except:
                    continue
    except Exception as e:
        print(f"[!] Could not play alarm: {e}")


def send_notification(title: str, message: str):
    """Send a desktop notification"""
    import platform
    system = platform.system()
    
    try:
        if system == "Windows":
            try:
                from win10toast import ToastNotifier
                toaster = ToastNotifier()
                toaster.show_toast(title, message, duration=5, threaded=True)
            except:
                pass
        elif system == "Darwin":
            import subprocess
            subprocess.run([
                "osascript", "-e",
                f'display notification "{message}" with title "{title}"'
            ])
        else:
            import subprocess
            subprocess.run(["notify-send", title, message], capture_output=True)
    except Exception as e:
        print(f"[!] Notification error: {e}")
