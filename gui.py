"""
GUI Module for F.R.I.D.A.Y.
Beautiful graphical interface using CustomTkinter
Inspired by Iron Man's AI interface
"""

# Standard library imports
import os
import queue
import threading
import tkinter as tk
from datetime import datetime
from tkinter import scrolledtext
from typing import Callable, Optional

# Suppress pygame import message
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

# Third-party imports
try:
    import customtkinter as ctk
    from PIL import Image, ImageTk
    CTK_AVAILABLE = True
except ImportError:
    CTK_AVAILABLE = False
    print("customtkinter not available, falling back to basic tkinter")

# Local imports
from config import (
    ACCENT_COLOR,
    GUI_THEME,
    WAKE_WORD,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)

# Translation support
try:
    from translations import get_text, get_language
except ImportError:
    def get_text(key, lang="en", **kwargs):
        return key
    def get_language():
        return "en"


class ModernGUI:
    """Modern GUI for F.R.I.D.A.Y. using CustomTkinter"""
    
    def __init__(self, on_text_command: Callable[[str], None] = None,
                 on_mic_toggle: Callable[[], None] = None):
        
        self.on_text_command = on_text_command
        self.on_mic_toggle = on_mic_toggle
        self.message_queue = queue.Queue()
        self.is_listening = False
        self.is_awake = False
        self.lang = get_language()  # Get current language
        
        # Setup window
        if CTK_AVAILABLE:
            self._setup_modern_gui()
        else:
            self._setup_basic_gui()
    
    def _setup_modern_gui(self):
        """Setup modern GUI with smooth aesthetics"""
        ctk.set_appearance_mode("dark" if GUI_THEME == "dark" else "light")
        ctk.set_default_color_theme("blue")
        
        self.root = ctk.CTk()
        self.root.title(get_text("app_title", self.lang))
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.minsize(600, 450)
        
        # Smooth window appearance
        try:
            self.root.attributes('-alpha', 0.0)
            self.root.after(50, lambda: self._fade_in_window())
        except:
            pass
        
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(2, weight=1)  # Chat area expands
        
        self._create_header()
        self._create_status_panel()  # New status panel
        self._create_chat_area()
        self._create_input_area()
        self._create_status_bar()
        self._process_queue()
    
    def _fade_in_window(self, alpha=0.0):
        """Smooth fade-in effect for window"""
        if alpha < 1.0:
            alpha += 0.1
            try:
                self.root.attributes('-alpha', alpha)
                self.root.after(20, lambda: self._fade_in_window(alpha))
            except:
                pass
    
    def _create_header(self):
        """Create header section"""
        header_frame = ctk.CTkFrame(self.root, height=60, corner_radius=0)
        header_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        header_frame.grid_columnconfigure(1, weight=1)
        
        # App name - dynamic based on settings
        try:
            from settings import get_ai_name
            app_name = get_ai_name()
        except:
            app_name = "F.R.I.D.A.Y."
        
        title_label = ctk.CTkLabel(
            header_frame,
            text=app_name,
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.grid(row=0, column=0, padx=15, pady=10)
        
        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="Female Replacement Intelligent Digital Assistant Youth",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        subtitle_label.grid(row=0, column=1, padx=5, pady=10, sticky="w")
        
        # Settings button
        settings_btn = ctk.CTkButton(
            header_frame,
            text="⚙️",
            width=35,
            height=35,
            font=ctk.CTkFont(size=16),
            command=self._open_settings,
            fg_color="transparent",
            hover_color=("gray80", "gray30")
        )
        settings_btn.grid(row=0, column=2, padx=5, pady=10)
        
        self.status_indicator = ctk.CTkLabel(
            header_frame,
            text=get_text("sleeping", self.lang),
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.status_indicator.grid(row=0, column=3, padx=15, pady=10)
    
    def _create_status_panel(self):
        """Create small status panel showing what F.R.I.D.A.Y. is doing"""
        status_panel = ctk.CTkFrame(self.root, height=50, corner_radius=8, fg_color=("gray90", "gray17"))
        status_panel.grid(row=1, column=0, sticky="ew", padx=15, pady=(5, 5))
        status_panel.grid_columnconfigure(1, weight=1)
        
        # Status icon
        self.action_icon = ctk.CTkLabel(
            status_panel,
            text="💤",
            font=ctk.CTkFont(size=16)
        )
        self.action_icon.grid(row=0, column=0, padx=10, pady=8)
        
        # Action text
        self.action_label = ctk.CTkLabel(
            status_panel,
            text="Standing by...",
            font=ctk.CTkFont(size=12, family="Consolas"),
            text_color=("gray40", "gray60"),
            anchor="w"
        )
        self.action_label.grid(row=0, column=1, padx=5, pady=8, sticky="w")
        
        # System stats (small)
        self.stats_label = ctk.CTkLabel(
            status_panel,
            text="CPU: --% | RAM: --%",
            font=ctk.CTkFont(size=10),
            text_color=("gray50", "gray50")
        )
        self.stats_label.grid(row=0, column=2, padx=10, pady=8)
        
        # Start updating stats
        self._update_stats()
    
    def _update_stats(self):
        """Update system stats in status panel"""
        try:
            import psutil
            cpu = psutil.cpu_percent(interval=0)
            mem = psutil.virtual_memory().percent
            self.stats_label.configure(text=f"CPU: {cpu:.0f}% | RAM: {mem:.0f}%")
        except:
            pass
        # Update every 3 seconds
        self.root.after(3000, self._update_stats)
    
    def set_action(self, action: str, icon: str = "⚡"):
        """Set the current action in status panel"""
        try:
            self.action_icon.configure(text=icon)
            self.action_label.configure(text=action)
        except:
            pass
    
    def _create_chat_area(self):
        """Create scrollable chat area"""
        self.chat_frame = ctk.CTkScrollableFrame(
            self.root,
            corner_radius=10,
            fg_color=("gray95", "gray10")
        )
        self.chat_frame.grid(row=2, column=0, sticky="nsew", padx=15, pady=5)
        self.chat_frame.grid_columnconfigure(0, weight=1)
        
        self._add_message(get_text("welcome", self.lang), is_user=False)
        self._add_message(get_text("wake_hint", self.lang, wake_word=WAKE_WORD), is_user=False)
    
    def _create_input_area(self):
        """Create input area with text entry and buttons"""
        input_frame = ctk.CTkFrame(self.root, corner_radius=10)
        input_frame.grid(row=3, column=0, sticky="ew", padx=15, pady=10)
        input_frame.grid_columnconfigure(0, weight=1)
        
        self.text_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text=get_text("placeholder", self.lang),
            height=45,
            font=ctk.CTkFont(size=14)
        )
        self.text_entry.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        self.text_entry.bind("<Return>", self._on_text_submit)
        
        self.mic_button = ctk.CTkButton(
            input_frame,
            text=get_text("mic", self.lang),
            width=50,
            height=45,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._on_mic_click,
            fg_color=ACCENT_COLOR,
            hover_color="#7c3aed"
        )
        self.mic_button.grid(row=0, column=1, padx=5, pady=10)
        
        self.send_button = ctk.CTkButton(
            input_frame,
            text=get_text("send", self.lang),
            width=80,
            height=45,
            font=ctk.CTkFont(size=14),
            command=self._on_text_submit,
            fg_color=ACCENT_COLOR,
            hover_color="#7c3aed"
        )
        self.send_button.grid(row=0, column=2, padx=10, pady=10)
    
    def _create_status_bar(self):
        """Create status bar at bottom"""
        status_frame = ctk.CTkFrame(self.root, height=30, corner_radius=0)
        status_frame.grid(row=4, column=0, sticky="ew")
        
        self.status_label = ctk.CTkLabel(
            status_frame,
            text=get_text("ready", self.lang),
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.status_label.pack(side="left", padx=15, pady=5)
        
        self.time_label = ctk.CTkLabel(
            status_frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.time_label.pack(side="right", padx=15, pady=5)
        self._update_time()
    
    def _add_message(self, text: str, is_user: bool = False, typing_effect: bool = False):
        """Add a message bubble to the chat"""
        msg_frame = ctk.CTkFrame(
            self.chat_frame,
            corner_radius=15,
            fg_color=(ACCENT_COLOR if is_user else ("gray85", "gray20"))
        )
        
        if is_user:
            msg_frame.grid(sticky="e", padx=(100, 10), pady=5)
        else:
            msg_frame.grid(sticky="w", padx=(10, 100), pady=5)
        
        msg_label = ctk.CTkLabel(
            msg_frame,
            text="" if typing_effect and not is_user else text,
            font=ctk.CTkFont(size=14),
            text_color=("white" if is_user else ("black", "white")),
            wraplength=400,
            justify="left"
        )
        msg_label.pack(padx=15, pady=10)
        
        self.root.after(100, lambda: self.chat_frame._parent_canvas.yview_moveto(1.0))
        
        # Word-by-word typing effect for assistant messages
        if typing_effect and not is_user:
            self._type_words(msg_label, text)
        
        return msg_label
    
    def _type_words(self, label, text: str, words_per_minute: int = 750):
        """Display text word by word - fast typing effect"""
        words = text.split()
        current_text = ""
        
        # Fast display: 80ms per word (750 WPM)
        ms_per_word = 80
        
        def show_word(index):
            nonlocal current_text
            if index < len(words):
                current_text += (" " if current_text else "") + words[index]
                try:
                    label.configure(text=current_text)
                    self.chat_frame._parent_canvas.yview_moveto(1.0)
                except:
                    return
                self.root.after(ms_per_word, lambda: show_word(index + 1))
        
        show_word(0)
    
    def _on_text_submit(self, event=None):
        """Handle text submission"""
        text = self.text_entry.get().strip()
        if text:
            self._add_message(text, is_user=True)
            self.text_entry.delete(0, "end")
            
            if self.on_text_command:
                threading.Thread(
                    target=self._process_command,
                    args=(text,),
                    daemon=True
                ).start()
    
    def _on_mic_click(self):
        """Handle microphone button click"""
        if self.on_mic_toggle:
            self.on_mic_toggle()
    
    def _process_command(self, text: str):
        """Process command in background"""
        self.set_status("Processing...")
        response = self.on_text_command(text)
        if response:
            self.add_assistant_message(response)
        self.set_status("Ready")
    
    def _process_queue(self):
        """Process messages from queue"""
        try:
            while True:
                msg_type, data = self.message_queue.get_nowait()
                
                if msg_type == "user_message":
                    self._add_message(data, is_user=True)
                elif msg_type == "assistant_message":
                    self._add_message(data, is_user=False, typing_effect=True)
                elif msg_type == "status":
                    self.status_label.configure(text=data)
                elif msg_type == "listening_status":
                    self._update_listening_status(data)
        except queue.Empty:
            pass
        
        self.root.after(100, self._process_queue)
    
    def _update_listening_status(self, is_listening: bool):
        """Update the listening status indicator"""
        self.is_listening = is_listening
        
        if is_listening:
            if self.is_awake:
                self.status_indicator.configure(
                    text=get_text("listening", self.lang),
                    text_color="#22c55e"
                )
                self.mic_button.configure(fg_color="#22c55e")
            else:
                self.status_indicator.configure(
                    text=get_text("waiting_wake", self.lang),
                    text_color="#eab308"
                )
                self.mic_button.configure(fg_color="#eab308")
        else:
            self.status_indicator.configure(
                text=get_text("sleeping", self.lang),
                text_color="gray"
            )
            self.mic_button.configure(fg_color=ACCENT_COLOR)
    
    def _update_time(self):
        """Update time display"""
        now = datetime.now()
        self.time_label.configure(text=now.strftime("%I:%M %p"))
        self.root.after(1000, self._update_time)
    
    def _open_settings(self):
        """Open the settings dialog"""
        try:
            from settings import show_settings_dialog
            if show_settings_dialog(self.root):
                # Settings saved - update language if changed
                new_lang = get_language()
                if new_lang != self.lang:
                    self.lang = new_lang
                    self.add_assistant_message(
                        get_text("settings_saved", self.lang) + 
                        " " + ("Please restart for full effect." if self.lang == "en" 
                               else "Перезапустите для полного применения.")
                    )
                else:
                    self.add_assistant_message(get_text("settings_saved", self.lang))
        except Exception as e:
            self.add_assistant_message(f"Could not open settings: {e}")
    
    def _setup_basic_gui(self):
        """Fallback basic GUI using tkinter"""
        self.root = tk.Tk()
        self.root.title(get_text("app_title", self.lang))
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        
        bg_color = "#1a1a2e" if GUI_THEME == "dark" else "#ffffff"
        fg_color = "#ffffff" if GUI_THEME == "dark" else "#000000"
        
        self.root.configure(bg=bg_color)
        
        app_name = "ПЯТНИЦА" if self.lang == "ru" else "F.R.I.D.A.Y."
        header = tk.Label(
            self.root,
            text=f"{app_name} - {get_text('subtitle', self.lang)}",
            font=("Helvetica", 24, "bold"),
            bg=bg_color,
            fg=fg_color
        )
        header.pack(pady=20)
        
        self.chat_text = scrolledtext.ScrolledText(
            self.root,
            wrap=tk.WORD,
            font=("Helvetica", 12),
            bg="#2d2d44" if GUI_THEME == "dark" else "#f5f5f5",
            fg=fg_color,
            height=20
        )
        self.chat_text.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        self.chat_text.configure(state='disabled')
        
        input_frame = tk.Frame(self.root, bg=bg_color)
        input_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.text_entry = tk.Entry(
            input_frame,
            font=("Helvetica", 14),
            bg="#3d3d54" if GUI_THEME == "dark" else "#ffffff",
            fg=fg_color
        )
        self.text_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.text_entry.bind("<Return>", self._on_text_submit_basic)
        
        send_btn = tk.Button(
            input_frame,
            text=get_text("send", self.lang),
            command=self._on_text_submit_basic,
            bg=ACCENT_COLOR,
            fg="white",
            font=("Helvetica", 12)
        )
        send_btn.pack(side=tk.RIGHT)
        
        self.status_label = tk.Label(
            self.root,
            text=get_text("ready", self.lang),
            bg=bg_color,
            fg="gray"
        )
        self.status_label.pack(pady=5)
        
        self._process_queue_basic()
    
    def _on_text_submit_basic(self, event=None):
        """Handle text submission (basic GUI)"""
        text = self.text_entry.get().strip()
        if text:
            self._add_message_basic(f"You: {text}")
            self.text_entry.delete(0, "end")
            
            if self.on_text_command:
                threading.Thread(
                    target=self._process_command_basic,
                    args=(text,),
                    daemon=True
                ).start()
    
    def _add_message_basic(self, text: str):
        """Add message to basic GUI"""
        self.chat_text.configure(state='normal')
        self.chat_text.insert(tk.END, text + "\n")
        self.chat_text.configure(state='disabled')
        self.chat_text.see(tk.END)
    
    def _process_command_basic(self, text: str):
        """Process command (basic GUI)"""
        response = self.on_text_command(text)
        if response:
            self.message_queue.put(("assistant_message", f"F.R.I.D.A.Y.: {response}"))
    
    def _process_queue_basic(self):
        """Process queue for basic GUI"""
        try:
            while True:
                msg_type, data = self.message_queue.get_nowait()
                if msg_type in ["user_message", "assistant_message"]:
                    self._add_message_basic(data)
        except queue.Empty:
            pass
        self.root.after(100, self._process_queue_basic)
    
    # Public methods
    def add_user_message(self, text: str):
        """Add user message to chat (thread-safe)"""
        self.message_queue.put(("user_message", text))
    
    def add_assistant_message(self, text: str):
        """Add assistant message to chat (thread-safe)"""
        self.message_queue.put(("assistant_message", text))
    
    def set_status(self, status: str):
        """Set status bar text (thread-safe)"""
        self.message_queue.put(("status", status))
    
    def set_listening(self, is_listening: bool):
        """Set listening status (thread-safe)"""
        self.message_queue.put(("listening_status", is_listening))
    
    def set_awake(self, is_awake: bool):
        """Set awake status"""
        self.is_awake = is_awake
        self.set_listening(self.is_listening)
    
    def run(self):
        """Start the GUI main loop"""
        self.root.mainloop()
    
    def quit(self):
        """Close the GUI"""
        self.root.quit()
        self.root.destroy()
