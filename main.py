#!/usr/bin/env python3
"""
F.R.I.D.A.Y. - Female Replacement Intelligent Digital Assistant Youth
Main entry point with integrated loading screen
"""

import logging
import os
import sys
import threading
import time
import tkinter as tk
import math
from pathlib import Path
from queue import Queue

# Setup logging first
log_file = Path.home() / "friday-assistant" / "friday.log"
log_file.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class LoadingScreen:
    """Loading screen with smooth animations"""
    
    BG = "#0a0a0f"
    PRIMARY = "#00aaff"
    SECONDARY = "#0077bb"
    ACCENT = "#00ffff"
    TEXT = "#88ccff"
    DIM = "#334455"
    
    def __init__(self):
        self.root = None
        self.canvas = None
        self.active = True
        self.t0 = 0
        self.frame = 0
        self.status_text = "INITIALIZING..."
        self.progress = 0.0
        self.ready = False
        self.status_queue = Queue()
        self.fade_alpha = 0.0  # For smooth fade-in
        
    def create(self):
        """Create the loading window"""
        # Use CTk to avoid segfault when switching to ModernGUI later
        try:
            import customtkinter as ctk
            ctk.set_appearance_mode("dark")
            self.root = ctk.CTk()
            self.root.configure(corner_radius=20)  # Rounded corners
        except:
            self.root = tk.Tk()
        
        self.root.title("")
        self.root.overrideredirect(True)
        self.root.configure(bg=self.BG)
        
        w, h = 650, 420
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        self.root.attributes('-topmost', True)
        
        # Try to set rounded window on Windows
        try:
            import platform
            if platform.system() == 'Windows':
                import ctypes
                hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
                style = ctypes.windll.user32.GetWindowLongW(hwnd, -16)
                style = style & ~0x00C00000  # Remove WS_CAPTION
                ctypes.windll.user32.SetWindowLongW(hwnd, -16, style)
        except:
            pass
        
        self.canvas = tk.Canvas(self.root, width=w, height=h, bg=self.BG, highlightthickness=0)
        self.canvas.pack()
        
        # Start with transparent window for fade-in effect
        try:
            self.root.attributes('-alpha', 0.0)
        except:
            pass
        
        self.t0 = time.time()
        self._render()
        
    def set_status(self, text: str, progress: float = None):
        """Update status from any thread"""
        self.status_queue.put((text, progress))
        
    def set_ready(self):
        """Signal that loading is complete"""
        self.ready = True
        
    def close(self):
        """Close the loading screen"""
        self.active = False
        try:
            if self.root:
                self.root.quit()
        except:
            pass
    
    def _check_queue(self):
        """Check for status updates"""
        try:
            while not self.status_queue.empty():
                text, progress = self.status_queue.get_nowait()
                if text:
                    self.status_text = text
                if progress is not None:
                    self.progress = progress
        except:
            pass
    
    def _render(self):
        """Render frame with smooth animations"""
        if not self.active:
            return
            
        try:
            self._check_queue()
            
            elapsed = time.time() - self.t0
            
            # Smooth fade-in effect (0.5 seconds)
            if self.fade_alpha < 1.0:
                self.fade_alpha = min(1.0, elapsed / 0.5)
                try:
                    self.root.attributes('-alpha', self.fade_alpha)
                except:
                    pass
            
            # If ready, fade out then close
            if self.ready and elapsed > 2.0:
                self.close()
                return
            
            self.canvas.delete("all")
            
            w, h = 650, 420
            cx, cy = w // 2, h // 2 - 40
            
            # Smooth gradient background
            for i in range(0, h, 2):
                intensity = int(10 + 5 * math.sin(i * 0.05 + elapsed))
                color = f"#{intensity:02x}{intensity:02x}{intensity + 3:02x}"
                self.canvas.create_line(0, i, w, i, fill=color)
            
            # Draw arc reactor with glow
            self._draw_reactor(cx, cy, elapsed)
            
            # Title with fade-in
            title_y = cy + 95
            if elapsed > 0.3:
                title_alpha = min(1.0, (elapsed - 0.3) / 0.5)
                title_text = "F.R.I.D.A.Y."
                
                # Glow effect
                glow_color = f"#00{int(100 * title_alpha):02x}{int(150 * title_alpha):02x}"
                self.canvas.create_text(cx, title_y, text=title_text,
                    font=("Segoe UI", 38, "bold"), fill=glow_color)
                self.canvas.create_text(cx, title_y, text=title_text,
                    font=("Segoe UI", 38, "bold"), fill=self.PRIMARY)
            
            # Subtitle
            if elapsed > 0.6:
                sub_alpha = min(1.0, (elapsed - 0.6) / 0.5)
                sub_color = f"#{int(50 * sub_alpha):02x}{int(100 * sub_alpha):02x}{int(130 * sub_alpha):02x}"
                self.canvas.create_text(cx, title_y + 45, text="AI Voice Assistant",
                    font=("Segoe UI", 14), fill=sub_color)
            
            # Status panel
            self._draw_status(w, h)
            
            # Corner accents
            self._draw_frame(w, h)
            
            self.frame += 1
            self.root.after(16, self._render)  # ~60 FPS for smooth animation
            
        except tk.TclError:
            self.active = False
        except Exception as e:
            logger.error(f"Render error: {e}")
            self.close()
    
    def _draw_reactor(self, cx, cy, elapsed):
        """Draw arc reactor with smooth glow effect"""
        # Outer glow
        for i in range(3):
            r = 70 + i * 5
            alpha = 30 - i * 10
            self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r,
                outline=f"#00{alpha:02x}{alpha + 20:02x}", width=1)
        
        # Main rings with smooth rotation
        self.canvas.create_oval(cx - 60, cy - 60, cx + 60, cy + 60, outline=self.SECONDARY, width=2)
        self.canvas.create_oval(cx - 45, cy - 45, cx + 45, cy + 45, outline=self.PRIMARY, width=2)
        
        # Rotating segments - smooth
        angle_offset = elapsed * 45  # Slower rotation
        for i in range(8):
            angle = math.radians(angle_offset + i * 45)
            x1, y1 = cx + 48 * math.cos(angle), cy + 48 * math.sin(angle)
            x2, y2 = cx + 58 * math.cos(angle), cy + 58 * math.sin(angle)
            self.canvas.create_line(x1, y1, x2, y2, fill=self.PRIMARY, width=2)
        
        for i in range(6):
            angle = math.radians(-angle_offset * 0.7 + i * 60)
            x1, y1 = cx + 25 * math.cos(angle), cy + 25 * math.sin(angle)
            x2, y2 = cx + 35 * math.cos(angle), cy + 35 * math.sin(angle)
            self.canvas.create_line(x1, y1, x2, y2, fill=self.ACCENT, width=2)
        
        # Core with smooth pulse
        pulse = 0.85 + 0.15 * math.sin(elapsed * 3)  # Slower, subtler pulse
        for i in range(4):
            r = int(20 * pulse) - i * 3
            if r > 0:
                alpha = int((100 - i * 20) * pulse)
                self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r,
                    fill=f"#00{alpha:02x}{min(255, alpha + 50):02x}", outline="")
        
        self.canvas.create_oval(cx - 6, cy - 6, cx + 6, cy + 6, fill=self.ACCENT, outline="")
    
    def _draw_status(self, w, h):
        """Draw status panel with smooth styling"""
        panel_y = h - 85
        panel_w = 400
        px = (w - panel_w) // 2
        
        # Status text
        self.canvas.create_text(w // 2, panel_y, text=self.status_text,
            font=("Segoe UI", 11), fill=self.TEXT)
        
        # Progress bar background with rounded ends
        bar_y = panel_y + 25
        bar_h = 4
        self.canvas.create_rectangle(px, bar_y, px + panel_w, bar_y + bar_h, 
            fill=self.DIM, outline="")
        
        # Progress fill with glow
        fill_w = int(panel_w * self.progress)
        if fill_w > 0:
            # Glow
            self.canvas.create_rectangle(px, bar_y - 1, px + fill_w, bar_y + bar_h + 1,
                fill="#003355", outline="")
            # Main bar
            self.canvas.create_rectangle(px, bar_y, px + fill_w, bar_y + bar_h,
                fill=self.PRIMARY, outline="")
        
        # Percentage
        self.canvas.create_text(px + panel_w + 35, bar_y + 2, text=f"{int(self.progress * 100)}%",
            font=("Segoe UI", 10), fill=self.PRIMARY)
        
        # Bottom branding
        self.canvas.create_text(w // 2, h - 25, text="F.R.I.D.A.Y. • AI ASSISTANT",
            font=("Segoe UI", 9), fill=self.DIM)
    
    def _draw_frame(self, w, h):
        """Draw rounded corner accents"""
        import math
        radius = 20
        c = self.SECONDARY
        
        # Top-left rounded corner
        for i in range(90):
            angle = math.radians(180 + i)
            x = 20 + radius + int(radius * math.cos(angle))
            y = 20 + radius + int(radius * math.sin(angle))
            self.canvas.create_oval(x-1, y-1, x+1, y+1, fill=c, outline=c)
        
        # Top-right rounded corner
        for i in range(90):
            angle = math.radians(270 + i)
            x = w - 20 - radius + int(radius * math.cos(angle))
            y = 20 + radius + int(radius * math.sin(angle))
            self.canvas.create_oval(x-1, y-1, x+1, y+1, fill=c, outline=c)
        
        # Bottom-left rounded corner
        for i in range(90):
            angle = math.radians(90 + i)
            x = 20 + radius + int(radius * math.cos(angle))
            y = h - 20 - radius + int(radius * math.sin(angle))
            self.canvas.create_oval(x-1, y-1, x+1, y+1, fill=c, outline=c)
        
        # Bottom-right rounded corner
        for i in range(90):
            angle = math.radians(i)
            x = w - 20 - radius + int(radius * math.cos(angle))
            y = h - 20 - radius + int(radius * math.sin(angle))
            self.canvas.create_oval(x-1, y-1, x+1, y+1, fill=c, outline=c)
    
    def run(self):
        """Run the loading screen mainloop"""
        if self.root:
            self.root.mainloop()


# Global references
loading_screen = None
gui = None
recognizer = None
tts = None
is_listening = False


def initialize_app(loader: LoadingScreen):
    """Initialize all app components in background"""
    global gui, recognizer, tts, is_listening
    
    try:
        # Step 1: Load config
        loader.set_status("LOADING CONFIGURATION...", 0.1)
        time.sleep(0.3)
        
        from config import WAKE_WORD, OPENAI_API_KEY
        logger.info("Config loaded")
        
        # Step 2: Load settings and apply API key
        loader.set_status("LOADING USER SETTINGS...", 0.2)
        time.sleep(0.2)
        
        try:
            from settings import load_settings, apply_api_keys, get_ai_name
            settings = load_settings()
            
            # Apply API key from settings to environment
            if apply_api_keys():
                logger.info("API key loaded from settings")
            else:
                # Try from config as fallback
                if OPENAI_API_KEY and OPENAI_API_KEY.startswith("sk-"):
                    os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
                    logger.info("API key loaded from config")
            
            ai_name = get_ai_name()
            logger.info(f"AI Name: {ai_name}")
        except Exception as e:
            logger.error(f"Settings error: {e}")
        
        # Step 3: Initialize database
        loader.set_status("CONNECTING DATABASE...", 0.3)
        time.sleep(0.3)
        
        from database import db
        logger.info("Database connected")
        
        # Step 4: Load AI module
        loader.set_status("INITIALIZING AI CORE...", 0.45)
        time.sleep(0.3)
        
        from ai_brain import brain
        logger.info("AI brain loaded")
        
        # Step 5: Load commands
        loader.set_status("LOADING COMMAND PROTOCOLS...", 0.55)
        time.sleep(0.2)
        
        from commands import command_handler
        logger.info("Commands loaded")
        
        # Step 6: Skip speech init here - do it after GUI to avoid segfault
        loader.set_status("PREPARING VOICE INTERFACE...", 0.7)
        time.sleep(0.3)
        
        # Just import, don't init yet (PyAudio conflicts with CTK if inited first)
        logger.info("Speech module ready (will init after GUI)")
        
        # Step 7: Prepare GUI
        loader.set_status("PREPARING INTERFACE...", 0.85)
        time.sleep(0.2)
        
        from gui import ModernGUI
        logger.info("GUI module loaded")
        
        # Step 8: Final
        loader.set_status("SYSTEM READY", 1.0)
        time.sleep(0.5)
        
        # Signal ready
        loader.set_ready()
        logger.info("Initialization complete")
        
    except Exception as e:
        logger.error(f"Initialization error: {e}")
        loader.set_status(f"ERROR: {str(e)[:30]}", 0.0)
        time.sleep(2)
        loader.set_ready()


def setup_hotkey(callback):
    """Setup global hotkey - requires root on Linux"""
    try:
        from settings import load_settings
        settings = load_settings()
        if not settings.get("hotkey_enabled", True):
            return False
        
        from config import WAKE_HOTKEY
        import keyboard
        keyboard.add_hotkey(WAKE_HOTKEY, callback)
        logger.info(f"Hotkey registered: {WAKE_HOTKEY}")
        return True
    except ImportError:
        logger.warning("keyboard library not available")
        return False
    except Exception as e:
        # keyboard library often fails on Linux without root
        logger.warning(f"Hotkey setup failed (may need root): {e}")
        return False


def main():
    """Main entry point - direct to GUI"""
    global gui, recognizer, tts, is_listening
    
    # Get AI name for banner
    try:
        from settings import get_ai_name
        ai_name = get_ai_name()
    except:
        ai_name = "F.R.I.D.A.Y."
    
    print(f"""
    ╔═══════════════════════════════════════════════════════════════╗
    ║     {ai_name} - AI Assistant{' ' * (40 - len(ai_name))}║
    ║     Your Personal AI Voice Assistant                          ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)
    
    logger.info("Starting F.R.I.D.A.Y....")
    
    # Initialize components directly
    print("[*] Loading configuration...")
    try:
        from settings import load_settings, get_api_key, get_ai_name
        settings = load_settings()
        
        api_key = get_api_key("OPENAI_API_KEY")
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
    except Exception as e:
        logger.error(f"Settings error: {e}")
    
    print("[*] Connecting database...")
    from database import db
    
    print("[*] Loading AI...")
    from ai_brain import brain
    
    print("[*] Loading commands...")
    from commands import command_handler
    
    print("[*] Starting GUI...")
    logger.info("Starting main interface...")
    
    try:
        from config import WAKE_WORD
        from gui import ModernGUI
        
        def process_voice_command(command: str):
            """Process voice command"""
            global is_listening
            
            if command == "__WAKE__":
                gui.set_awake(True)
                gui.set_action("Listening...", "👂")
                response = "Yes? What do you need?"
                if tts:
                    tts.speak(response)
                gui.add_assistant_message(response)
                return
            
            gui.add_user_message(command)
            gui.set_status("Processing...")
            gui.set_action(f"Processing: {command[:30]}...", "⚡")
            
            response, should_continue = command_handler.process(command)
            gui.add_assistant_message(response)
            gui.set_status("Online")
            gui.set_action("Standing by...", "💤")
            
            if tts:
                tts.speak(response)
            
            if not should_continue:
                gui.set_awake(False)
                gui.set_action("Sleeping...", "😴")
                if recognizer:
                    recognizer.sleep()
        
        def process_text_command(command: str) -> str:
            """Process text command"""
            gui.set_action(f"Processing: {command[:30]}...", "⚡")
            response, _ = command_handler.process(command)
            gui.set_action("Standing by...", "💤")
            # Speak in background so text can display simultaneously
            if tts:
                threading.Thread(target=tts.speak, args=(response,), daemon=True).start()
            return response
        
        def toggle_microphone():
            """Toggle microphone"""
            global is_listening
            
            if recognizer:
                if is_listening:
                    recognizer.stop_listening()
                    is_listening = False
                    gui.set_listening(False)
                    gui.add_assistant_message("Voice input disabled.")
                else:
                    recognizer.start_listening(process_voice_command)
                    is_listening = True
                    gui.set_listening(True)
                    gui.add_assistant_message(f"Voice input active. Say '{WAKE_WORD}' when ready.")
            else:
                gui.add_assistant_message("Voice systems offline.")
        
        def wake_from_hotkey():
            """Wake via hotkey"""
            if recognizer:
                recognizer.wake_up()
            gui.set_awake(True)
            gui.add_assistant_message("Yes? What do you need?")
            if tts:
                threading.Thread(target=tts.speak, args=("Yes?",), daemon=True).start()
        
        # Create GUI FIRST (before speech to avoid PyAudio/CTK conflict)
        gui = ModernGUI(
            on_text_command=process_text_command,
            on_mic_toggle=toggle_microphone
        )
        
        command_handler.set_gui_callback(gui.add_assistant_message)
        
        # NOW initialize speech (after GUI is created)
        logger.info("Initializing speech systems...")
        from speech import init_speech
        recognizer, tts = init_speech()
        logger.info("Speech systems ready")
        
        # Start voice recognition
        def start_voice():
            global is_listening
            time.sleep(0.5)
            
            # Get AI name for messages
            try:
                from settings import get_ai_name, get_wake_word
                ai_name = get_ai_name()
                wake_word = get_wake_word()
            except Exception as e:
                logger.error(f"Error getting AI name: {e}")
                ai_name = "F.R.I.D.A.Y."
                wake_word = "friday"
            
            if recognizer:
                try:
                    recognizer.start_listening(process_voice_command)
                    is_listening = True
                    gui.set_listening(True)
                    gui.add_assistant_message(f"{ai_name} online. Say '{wake_word}' when you need me.")
                    if tts:
                        tts.speak(f"{ai_name} online and ready.")
                except Exception as e:
                    gui.add_assistant_message(f"Voice offline: {e}")
            else:
                gui.add_assistant_message(f"{ai_name} voice unavailable. Text input ready.")
        
        threading.Thread(target=start_voice, daemon=True).start()
        
        # Setup hotkey
        setup_hotkey(wake_from_hotkey)
        
        # Reminder checker
        def check_reminders():
            while True:
                try:
                    reminders = db.get_pending_reminders()
                    for reminder in reminders:
                        gui.add_assistant_message(f"⏰ Reminder: {reminder['message']}")
                        if tts:
                            tts.speak(f"Reminder: {reminder['message']}")
                        db.mark_reminder_complete(reminder['id'])
                except:
                    pass
                time.sleep(60)
        
        threading.Thread(target=check_reminders, daemon=True).start()
        
        # Run GUI
        print("[OK] F.R.I.D.A.Y. is online")
        gui.run()
        
    except Exception as e:
        logger.error(f"GUI error: {e}")
        print(f"[X] Error starting GUI: {e}")
        sys.exit(1)
    
    finally:
        # Stop all audio and cleanup
        if tts:
            tts.shutdown()
        if recognizer:
            recognizer.stop_listening()
        logger.info("F.R.I.D.A.Y. offline")


if __name__ == "__main__":
    main()
