"""
Speech Module for F.R.I.D.A.Y.
Handles speech recognition and text-to-speech with human-like voice
Features Irish female voice (like Kerry Condon from Iron Man)
Optimized for Pop!_OS with PipeWire
"""

# Standard library imports
import os
import queue
import re
import subprocess
import sys
import tempfile
import threading
import time
import warnings
from contextlib import contextmanager
from pathlib import Path
from typing import Callable, Optional

@contextmanager
def suppress_alsa_errors():
    """Suppress ALSA error messages that appear on PipeWire systems"""
    try:
        from ctypes import CFUNCTYPE, c_char_p, c_int, cdll
        
        ERROR_HANDLER_FUNC = CFUNCTYPE(None, c_char_p, c_int, c_char_p, c_int, c_char_p)
        
        def py_error_handler(filename, line, function, err, fmt):
            pass
        
        c_error_handler = ERROR_HANDLER_FUNC(py_error_handler)
        
        try:
            asound = cdll.LoadLibrary('libasound.so.2')
            asound.snd_lib_error_set_handler(c_error_handler)
        except OSError:
            pass
        
        yield
    except Exception:
        yield


with suppress_alsa_errors():
    pass


try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    SR_AVAILABLE = False
    print("Warning: speech_recognition not available")

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import edge_tts
    import asyncio
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False

from config import (
    WAKE_WORD, WAKE_WORDS, OPENAI_API_KEY, TTS_ENGINE, OPENAI_VOICE, VOICE_SPEED,
    SILENCE_THRESHOLD, ENERGY_THRESHOLD, DYNAMIC_ENERGY, PAUSE_THRESHOLD,
    VOICE_RATE, VOICE_VOLUME, VOICE_GENDER, ENABLE_SPEECH_VARIATIONS,
    AVAILABLE_VOICES, CONVERSATION_MODE, CONVERSATION_TIMEOUT
)

# Try to import language settings
try:
    from config import SPEECH_LANGUAGE, TTS_LANGUAGE, TTS_VOICE
except ImportError:
    SPEECH_LANGUAGE = "auto"
    TTS_LANGUAGE = "en"
    TTS_VOICE = "en-IE-EmilyNeural"  # Irish female - F.R.I.D.A.Y. voice

# Language codes for speech recognition
LANGUAGE_CODES = {
    "en": "en-US",
    "ru": "ru-RU",
    "auto": None,  # Will try multiple languages
}

# Edge TTS voices - Irish female is default (like Kerry Condon as F.R.I.D.A.Y.)
EDGE_TTS_VOICES = {
    "en": "en-IE-EmilyNeural",      # Irish female - F.R.I.D.A.Y. voice!
    "ru": "ru-RU-SvetlanaNeural",   # Russian female
}


def check_pipewire_status():
    """Check if PipeWire is running"""
    try:
        result = subprocess.run(
            ["systemctl", "--user", "is-active", "pipewire"],
            capture_output=True, text=True
        )
        if result.stdout.strip() == "active":
            print("[OK] PipeWire is running")
            return True
        else:
            print("[!] PipeWire not active, trying to start...")
            subprocess.run(
                ["systemctl", "--user", "start", "pipewire", "pipewire-pulse"],
                capture_output=True
            )
            return True
    except Exception as e:
        print(f"[!] Could not check PipeWire: {e}")
        return False


def find_audio_player():
    """Find available audio player on the system"""
    import platform
    system = platform.system()
    
    if system == "Windows":
        # On Windows, we'll use pygame or the built-in winsound
        try:
            import pygame
            pygame.mixer.init()
            print("[OK] Audio player: pygame")
            return "pygame"
        except:
            pass
        
        # Fallback to Windows Media Player via subprocess
        print("[OK] Audio player: Windows default")
        return "windows"
    
    # Linux/Mac players
    players = [
        ("mpv", ["mpv", "--no-video", "--really-quiet"]),
        ("ffplay", ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet"]),
        ("pw-play", ["pw-play"]),
        ("paplay", ["paplay"]),
        ("aplay", ["aplay", "-q"]),
    ]
    
    for name, cmd in players:
        try:
            result = subprocess.run(["which", name], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"[OK] Audio player: {name}")
                return cmd
        except:
            continue
    
    print("[!] No audio player found - install mpv: sudo apt install mpv")
    return None


class SmartSpeechRecognizer:
    """
    Smart speech recognition with automatic silence detection.
    Keeps listening while you talk, stops when you pause for 3 seconds.
    """
    
    def __init__(self):
        if not SR_AVAILABLE:
            raise ImportError("speech_recognition library not installed")
        
        self.recognizer = sr.Recognizer()
        self.device_index = None
        self.is_listening = False
        self.is_awake = False
        self.callback = None
        self.listen_thread = None
        
        # Get wake word from settings
        try:
            from settings import get_wake_word
            self.wake_word = get_wake_word().lower()
        except:
            self.wake_word = WAKE_WORD.lower()
        
        self.wake_words = [self.wake_word] + [w.lower() for w in WAKE_WORDS if w.lower() != self.wake_word]
        self.last_interaction = 0  # For conversation mode
        
        self.recognizer.pause_threshold = PAUSE_THRESHOLD
        self.recognizer.non_speaking_duration = 0.5
        self.recognizer.dynamic_energy_threshold = False  # We'll set it manually
        self.recognizer.energy_threshold = 150  # Lower = more sensitive
        self.recognizer.phrase_threshold = 0.1
        
        check_pipewire_status()
        self._init_microphone()
    
    def _init_microphone(self):
        """Initialize microphone with PipeWire compatibility"""
        with suppress_alsa_errors():
            try:
                import pyaudio
                p = pyaudio.PyAudio()
                
                print("\n--- Audio Devices ---")
                input_devices = []
                pipewire_devices = []  # Prefer PipeWire/Pulse devices
                default_input = None
                
                try:
                    default_info = p.get_default_input_device_info()
                    default_input = default_info.get('index')
                    print(f"  System default: [{default_input}] {default_info.get('name', 'Unknown')}")
                except Exception:
                    print("  No system default input device")
                
                for i in range(p.get_device_count()):
                    try:
                        dev = p.get_device_info_by_index(i)
                        max_input = dev.get('maxInputChannels', 0)
                        if max_input > 0:
                            name = dev['name']
                            input_devices.append((i, name, max_input))
                            
                            # Skip direct hardware devices - they conflict with PipeWire
                            is_hw = 'hw:' in name
                            is_arctis = 'arctis' in name.lower()
                            is_pipewire = 'pipewire' in name.lower() or 'pulse' in name.lower()
                            is_default = 'default' in name.lower()
                            
                            marker = ""
                            if is_hw:
                                marker = " (hardware - skipping)"
                            elif is_pipewire or is_default:
                                pipewire_devices.append((i, name))
                                marker = " <-- RECOMMENDED"
                            elif is_arctis:
                                pipewire_devices.append((i, name))
                                marker = " <-- HEADSET"
                            
                            print(f"  [{i}] {name} (ch:{max_input}){marker}")
                    except Exception:
                        continue
                
                p.terminate()
                
                if not input_devices:
                    print("\n[ERROR] No microphones found!")
                    self.device_index = None
                    return
                
                print(f"\nFound {len(input_devices)} input device(s)")
                
                # Prefer PipeWire/Pulse devices, then default, then first available
                if pipewire_devices:
                    self.device_index = pipewire_devices[0][0]
                    device_name = pipewire_devices[0][1]
                    print(f"[OK] Using device [{self.device_index}]: {device_name}")
                elif default_input is not None:
                    self.device_index = default_input
                    device_name = next((name for idx, name, _ in input_devices if idx == self.device_index), "Unknown")
                    print(f"[OK] Using default device [{self.device_index}]: {device_name}")
                else:
                    # Find first non-hardware device
                    for idx, name, _ in input_devices:
                        if 'hw:' not in name:
                            self.device_index = idx
                            device_name = name
                            print(f"[OK] Using device [{self.device_index}]: {device_name}")
                            break
                    else:
                        print("[!] Only hardware devices available - this may cause issues")
                        self.device_index = input_devices[0][0]
                        device_name = input_devices[0][1]
                
                # Test microphone
                print("Testing microphone...")
                try:
                    with sr.Microphone(device_index=self.device_index) as source:
                        # Quick calibration
                        self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                        threshold = self.recognizer.energy_threshold
                        self.recognizer.energy_threshold = max(100, threshold * 0.5)
                    print(f"[OK] Microphone ready (sensitivity: {self.recognizer.energy_threshold:.0f})")
                except Exception as e:
                    print(f"[!] Calibration issue: {e}")
                    self.recognizer.energy_threshold = 150
                    print(f"[OK] Using high sensitivity: 150")
                
            except ImportError:
                print("[ERROR] PyAudio not installed! Run: pip install pyaudio")
                self.device_index = None
            except OSError as e:
                print(f"[ERROR] Audio system error: {e}")
                print("Try: systemctl --user restart pipewire pipewire-pulse")
                self.device_index = None
            except Exception as e:
                print(f"[ERROR] Microphone init failed: {type(e).__name__}: {e}")
                self.device_index = None
    
    def start_listening(self, callback: Callable[[str], None]):
        """Start continuous background listening"""
        if self.device_index is None:
            print("[!] Microphone not available - voice input disabled")
            print("    You can still type commands in the text box")
            return
            
        self.is_listening = True
        self.callback = callback
        self.listen_thread = threading.Thread(target=self._smart_listen_loop, daemon=True)
        self.listen_thread.start()
        print(f"\n[OK] Listening for wake word: '{self.wake_word}'")
        print("    Say '{0}' followed by your command, or just '{0}' to wake me up\n".format(self.wake_word))
    
    def stop_listening(self):
        """Stop background listening"""
        self.is_listening = False
        if self.listen_thread:
            self.listen_thread.join(timeout=2)
    
    def _smart_listen_loop(self):
        """Smart listening loop with automatic silence detection"""
        consecutive_errors = 0
        max_consecutive_errors = 5
        microphone = None
        
        while self.is_listening:
            with suppress_alsa_errors():
                try:
                    # Create microphone instance fresh each time to avoid stale handles
                    microphone = sr.Microphone(device_index=self.device_index)
                    with microphone as source:
                        # Very quick ambient check
                        self.recognizer.adjust_for_ambient_noise(source, duration=0.2)
                        
                        try:
                            audio = self.recognizer.listen(
                                source,
                                timeout=10,
                                phrase_time_limit=20
                            )
                        except sr.WaitTimeoutError:
                            # Normal - no speech detected, continue listening
                            consecutive_errors = 0
                            continue
                    
                    # Got audio, process it
                    consecutive_errors = 0
                    self._process_audio(audio)
                    
                except sr.WaitTimeoutError:
                    consecutive_errors = 0
                    continue
                except (OSError, IOError) as e:
                    consecutive_errors += 1
                    err_msg = str(e)[:60]
                    if consecutive_errors <= 2:
                        print(f"[!] Audio error ({consecutive_errors}): {err_msg}")
                    
                    if consecutive_errors >= max_consecutive_errors:
                        print("[!] Too many audio errors, restarting audio system...")
                        try:
                            subprocess.run(
                                ["systemctl", "--user", "restart", "pipewire", "pipewire-pulse", "wireplumber"],
                                capture_output=True,
                                timeout=10
                            )
                        except Exception:
                            pass
                        time.sleep(3)
                        consecutive_errors = 0
                    else:
                        time.sleep(1)
                except AttributeError as e:
                    # Handle NoneType errors from closed streams
                    consecutive_errors += 1
                    if consecutive_errors <= 2:
                        print(f"[!] Stream error ({consecutive_errors}): {str(e)[:40]}")
                    time.sleep(1)
                except Exception as e:
                    consecutive_errors += 1
                    err_str = str(e)
                    if consecutive_errors <= 2 and err_str and "aborted" not in err_str.lower():
                        print(f"[!] Listen error ({consecutive_errors}): {type(e).__name__}")
                    time.sleep(0.5)
                finally:
                    # Clean up microphone reference
                    microphone = None
    
    def _process_audio(self, audio):
        """Process captured audio and handle commands"""
        try:
            print("[...] Processing speech...")
            
            # Try recognition with configured language or auto-detect
            text = None
            if SPEECH_LANGUAGE == "auto":
                # Try English first, then Russian
                for lang in ["en-US", "ru-RU"]:
                    try:
                        text = self.recognizer.recognize_google(audio, language=lang).lower().strip()
                        if text:
                            break
                    except:
                        continue
            else:
                lang_code = LANGUAGE_CODES.get(SPEECH_LANGUAGE, "en-US")
                text = self.recognizer.recognize_google(audio, language=lang_code).lower().strip()
            
            if not text:
                return
            
            print(f"[HEARD] \"{text}\"")
            
            # Check conversation mode - stay awake if recent interaction
            if CONVERSATION_MODE and self.last_interaction > 0:
                if time.time() - self.last_interaction < CONVERSATION_TIMEOUT:
                    self.is_awake = True
            
            if not self.is_awake:
                # Check for any configured wake word
                is_wake = any(ww in text for ww in self.wake_words)
                
                if is_wake:
                    self.is_awake = True
                    self.last_interaction = time.time()
                    print("[AWAKE] Wake word detected! Listening for commands...")
                    
                    # Extract command after wake word
                    command = text
                    for ww in self.wake_words:
                        if ww in text:
                            idx = text.find(ww)
                            command = text[idx + len(ww):].strip()
                            break
                    
                    if command:
                        self.callback(command)
                    else:
                        self.callback("__WAKE__")
            else:
                self.last_interaction = time.time()
                self.callback(text)
                
                # Only sleep on explicit farewell phrases (at start of sentence or standalone)
                # Don't sleep on "thank you" in the middle of a longer sentence
                sleep_phrases_strict = ["goodbye", "go to sleep", "that's all", 
                                       "bye bye", "see you", "goodnight", "stop listening", 
                                       "nevermind", "never mind", "пока", "до свидания"]
                
                # These only trigger sleep if they're the whole message or at the start
                sleep_phrases_start = ["thanks", "thank you", "bye", "спасибо"]
                
                text_clean = text.strip().lower()
                
                # Check strict phrases anywhere
                should_sleep = any(phrase in text_clean for phrase in sleep_phrases_strict)
                
                # Check start phrases only if at beginning or standalone
                if not should_sleep:
                    for phrase in sleep_phrases_start:
                        if text_clean == phrase or text_clean.startswith(phrase + " ") or text_clean.startswith(phrase + ","):
                            # Only sleep if it's short (likely a farewell, not mid-conversation)
                            if len(text_clean) < 30:
                                should_sleep = True
                                break
                
                if should_sleep:
                    self.is_awake = False
                    self.last_interaction = 0
                    print(f"[SLEEP] Going to sleep... say '{self.wake_word}' to wake me up")
        
        except sr.UnknownValueError:
            print("[...] Heard audio but couldn't understand")
        except sr.RequestError as e:
            print(f"[!] Google Speech API error: {e}")
    
    def listen_once(self) -> Optional[str]:
        """Listen for a single command with smart silence detection"""
        if self.device_index is None:
            return None
        
        with suppress_alsa_errors():
            try:
                with sr.Microphone(device_index=self.device_index) as source:
                    print("Listening... (speak naturally)")
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.3)
                    
                    audio = self.recognizer.listen(
                        source,
                        timeout=15,
                        phrase_time_limit=30
                    )
                
                text = self.recognizer.recognize_google(audio)
                print(f"Got: \"{text}\"")
                return text.lower()
                
            except sr.WaitTimeoutError:
                print("No speech detected")
                return None
            except sr.UnknownValueError:
                print("Couldn't understand that")
                return None
            except sr.RequestError as e:
                print(f"Recognition error: {e}")
                return None
            except Exception as e:
                print(f"[!] Listen error: {type(e).__name__}: {e}")
                return None
    
    def wake_up(self):
        """Manually wake up the assistant"""
        self.is_awake = True
        print("[AWAKE] Assistant is now listening for commands")
    
    def sleep(self):
        """Put the assistant to sleep"""
        self.is_awake = False
        print(f"[SLEEP] Assistant is sleeping. Say '{self.wake_word}' to wake up")


class HumanVoiceTTS:
    """
    Text-to-speech with human-like neural voices.
    """
    
    def __init__(self):
        self.engine_type = TTS_ENGINE
        self.is_speaking = False
        self.speak_lock = threading.Lock()  # Prevent voice overlap
        self.temp_dir = Path(tempfile.gettempdir()) / "friday_audio"
        self.temp_dir.mkdir(exist_ok=True)
        
        self.audio_player = find_audio_player()
        
        if OPENAI_AVAILABLE and OPENAI_API_KEY and len(OPENAI_API_KEY) > 20:
            try:
                self.openai_client = OpenAI(api_key=OPENAI_API_KEY)
            except Exception as e:
                print(f"[!] OpenAI client error: {e}")
                self.openai_client = None
        else:
            self.openai_client = None
        
        self.pyttsx3_engine = None
        if PYTTSX3_AVAILABLE:
            try:
                self.pyttsx3_engine = pyttsx3.init()
                self.pyttsx3_engine.setProperty('rate', VOICE_RATE)
                self.pyttsx3_engine.setProperty('volume', VOICE_VOLUME)
            except Exception as e:
                print(f"[!] pyttsx3 init error: {e}")
        
        self._select_best_engine()
        print(f"[OK] Voice engine: {self.engine_type}")
    
    def _select_best_engine(self):
        """Select the best available TTS engine"""
        if self.engine_type == "openai" and self.openai_client and self.audio_player:
            return
        elif self.engine_type == "edge" and EDGE_TTS_AVAILABLE and self.audio_player:
            return
        elif self.openai_client and self.audio_player:
            self.engine_type = "openai"
        elif EDGE_TTS_AVAILABLE and self.audio_player:
            self.engine_type = "edge"
        elif self.pyttsx3_engine:
            self.engine_type = "pyttsx3"
        else:
            print("[!] No TTS engine available!")
            self.engine_type = None
    
    def _is_russian(self, text: str) -> bool:
        """Check if text contains Russian characters"""
        russian_chars = set('абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ')
        return any(char in russian_chars for char in text)
    
    def _clean_text_for_speech(self, text: str) -> str:
        """Clean text for natural speech - remove symbols that shouldn't be spoken"""
        import re
        # Remove asterisks, underscores (markdown)
        text = re.sub(r'[\*_~`]', '', text)
        # Remove multiple periods (ellipsis spoken weird)
        text = re.sub(r'\.{2,}', '.', text)
        # Remove bullet points
        text = re.sub(r'^[\-•▪►]\s*', '', text, flags=re.MULTILINE)
        # Remove URLs
        text = re.sub(r'https?://\S+', '', text)
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def speak(self, text: str, block: bool = True):
        """Speak text with human-like voice"""
        if not text or not self.engine_type:
            return
        
        # Clean text for natural speech
        text = self._clean_text_for_speech(text)
        if not text:
            return
        
        # Prevent voice overlap - wait for previous speech to finish
        with self.speak_lock:
            self.is_speaking = True
            
            try:
                if self.engine_type == "openai":
                    self._speak_openai(text, block)
                elif self.engine_type == "edge":
                    self._speak_edge(text, block)
                else:
                    self._speak_pyttsx3(text, block)
            except Exception as e:
                print(f"[!] TTS error with {self.engine_type}: {e}")
                if self.pyttsx3_engine and self.engine_type != "pyttsx3":
                    self._speak_pyttsx3(text, block)
            finally:
                self.is_speaking = False
    
    def _speak_openai(self, text: str, block: bool):
        """Use OpenAI's neural TTS"""
        if not self.openai_client:
            raise Exception("OpenAI client not available")
        
        response = self.openai_client.audio.speech.create(
            model="tts-1-hd",
            voice=OPENAI_VOICE,
            input=text,
            speed=VOICE_SPEED
        )
        
        audio_path = self.temp_dir / f"speech_{int(time.time())}.mp3"
        response.stream_to_file(str(audio_path))
        
        self._play_audio(audio_path, block)
        
        try:
            audio_path.unlink()
        except:
            pass
    
    def _speak_edge(self, text: str, block: bool):
        """Use Microsoft Edge TTS - free neural voices"""
        async def _generate():
            # Get voice from settings (F.R.I.D.A.Y. only)
            try:
                from settings import get_voice_id
                voice = get_voice_id()
            except:
                voice = TTS_VOICE
            
            # Auto-detect Russian text and switch voice
            if self._is_russian(text):
                voice = EDGE_TTS_VOICES.get("ru", "ru-RU-SvetlanaNeural")
            
            communicate = edge_tts.Communicate(text, voice)
            audio_path = self.temp_dir / f"speech_{int(time.time())}.mp3"
            await communicate.save(str(audio_path))
            return audio_path
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        audio_path = loop.run_until_complete(_generate())
        
        self._play_audio(audio_path, block)
        
        try:
            audio_path.unlink()
        except:
            pass
    
    def _speak_pyttsx3(self, text: str, block: bool):
        """Fallback to pyttsx3"""
        if not self.pyttsx3_engine:
            print("[!] No offline TTS available")
            return
        
        self.pyttsx3_engine.say(text)
        if block:
            self.pyttsx3_engine.runAndWait()
    
    def _play_audio(self, audio_path: Path, block: bool):
        """Play audio file using system audio player"""
        if not self.audio_player:
            print("[!] No audio player available")
            return
        
        try:
            import platform
            
            if self.audio_player == "pygame":
                # Use pygame for Windows
                import pygame
                pygame.mixer.init()
                pygame.mixer.music.load(str(audio_path))
                pygame.mixer.music.play()
                if block:
                    while pygame.mixer.music.get_busy():
                        time.sleep(0.1)
            elif self.audio_player == "windows":
                # Use Windows default player
                import os
                if block:
                    os.system(f'start /wait "" "{audio_path}"')
                else:
                    os.system(f'start "" "{audio_path}"')
            else:
                # Linux players (list format)
                cmd = self.audio_player + [str(audio_path)]
                if block:
                    subprocess.run(cmd, capture_output=True)
                else:
                    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            print(f"[!] Audio playback error: {e}")
    
    def stop(self):
        """Stop current speech immediately"""
        self.is_speaking = False
        # Kill any running audio processes
        try:
            import subprocess
            subprocess.run(['pkill', '-f', 'mpv'], capture_output=True, timeout=1)
            subprocess.run(['pkill', '-f', 'ffplay'], capture_output=True, timeout=1)
        except:
            pass
        if self.pyttsx3_engine:
            try:
                self.pyttsx3_engine.stop()
            except:
                pass
    
    def shutdown(self):
        """Complete shutdown of TTS system"""
        self.stop()
        self.engine_type = None


# Global instances
recognizer = None
tts = None

def init_speech():
    """Initialize speech modules after GUI is ready"""
    global recognizer, tts
    
    print("\n=== Initializing Speech System ===")
    
    with suppress_alsa_errors():
        try:
            recognizer = SmartSpeechRecognizer()
        except Exception as e:
            print(f"[!] Speech recognizer failed: {e}")
            recognizer = None
        
        try:
            tts = HumanVoiceTTS()
            print("[OK] Text-to-speech ready")
        except Exception as e:
            print(f"[!] Text-to-speech failed: {e}")
            tts = None
    
    print("=== Speech System Ready ===\n")
    
    return recognizer, tts
