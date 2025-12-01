#!/usr/bin/env python3
"""
F.R.I.D.A.Y. Microphone Diagnostic Tool
Female Replacement Intelligent Digital Assistant Youth
Run this to diagnose microphone issues on Pop!_OS
"""

import sys

def test_pyaudio():
    """Test PyAudio installation and list devices"""
    print("\n=== PyAudio Test ===")
    try:
        import pyaudio
        print("PyAudio imported successfully")
        
        p = pyaudio.PyAudio()
        print(f"PyAudio version: {pyaudio.get_portaudio_version_text()}")
        
        print("\nAudio Devices:")
        input_devices = []
        output_devices = []
        
        for i in range(p.get_device_count()):
            dev = p.get_device_info_by_index(i)
            if dev['maxInputChannels'] > 0:
                input_devices.append((i, dev['name']))
                print(f"  [INPUT  {i}] {dev['name']}")
            if dev['maxOutputChannels'] > 0:
                output_devices.append((i, dev['name']))
                print(f"  [OUTPUT {i}] {dev['name']}")
        
        p.terminate()
        
        print(f"\nSummary: {len(input_devices)} input(s), {len(output_devices)} output(s)")
        
        if not input_devices:
            print("\nWARNING: No input devices (microphones) found!")
            print("Possible fixes:")
            print("  1. Check if microphone is plugged in")
            print("  2. Run: pavucontrol (and check Input Devices tab)")
            print("  3. Run: pactl list sources")
            print("  4. Log out and log back in (for permission changes)")
            return False
        
        return True
        
    except ImportError as e:
        print(f"ERROR: PyAudio not installed: {e}")
        print("Fix: pip install pyaudio")
        print("If that fails: sudo apt install python3-pyaudio portaudio19-dev")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False


def test_speech_recognition():
    """Test speech recognition"""
    print("\n=== Speech Recognition Test ===")
    try:
        import speech_recognition as sr
        print("SpeechRecognition imported successfully")
        
        r = sr.Recognizer()
        
        try:
            mic = sr.Microphone()
            print("Microphone object created successfully")
            
            print("\nTesting microphone capture (speak for 3 seconds)...")
            with mic as source:
                r.adjust_for_ambient_noise(source, duration=1)
                print(f"Energy threshold: {r.energy_threshold:.0f}")
                print("Listening...")
                try:
                    audio = r.listen(source, timeout=5, phrase_time_limit=3)
                    print("Audio captured successfully!")
                    
                    # Try to recognize
                    try:
                        text = r.recognize_google(audio)
                        print(f"Recognized: '{text}'")
                        return True
                    except sr.UnknownValueError:
                        print("Audio captured but couldn't understand speech")
                        print("(This is OK - microphone is working!)")
                        return True
                    except sr.RequestError as e:
                        print(f"Google API error: {e}")
                        print("(Microphone works, but need internet for recognition)")
                        return True
                        
                except sr.WaitTimeoutError:
                    print("No audio detected within timeout")
                    print("Make sure you're speaking into the microphone")
                    return False
                    
        except OSError as e:
            print(f"ERROR creating microphone: {e}")
            print("The microphone device couldn't be opened")
            return False
            
    except ImportError as e:
        print(f"ERROR: SpeechRecognition not installed: {e}")
        print("Fix: pip install SpeechRecognition")
        return False


def test_audio_playback():
    """Test audio output"""
    print("\n=== Audio Playback Test ===")
    import subprocess
    import shutil
    
    players = ["mpv", "ffplay", "paplay", "aplay"]
    found = None
    
    for player in players:
        if shutil.which(player):
            found = player
            print(f"Found audio player: {player}")
            break
    
    if not found:
        print("WARNING: No audio player found!")
        print("Fix: sudo apt install mpv")
        return False
    
    # Also check pygame
    try:
        import pygame
        pygame.mixer.init()
        pygame.mixer.quit()
        print("pygame audio available")
    except:
        print("pygame audio not available (optional)")
    
    return True


def main():
    print("═" * 60)
    print("  ███████╗██████╗ ██╗██████╗  █████╗ ██╗   ██╗")
    print("  ██╔════╝██╔══██╗██║██╔══██╗██╔══██╗╚██╗ ██╔╝")
    print("  █████╗  ██████╔╝██║██║  ██║███████║ ╚████╔╝ ")
    print("  ██╔══╝  ██╔══██╗██║██║  ██║██╔══██║  ╚██╔╝  ")
    print("  ██║     ██║  ██║██║██████╔╝██║  ██║   ██║   ")
    print("  ╚═╝     ╚═╝  ╚═╝╚═╝╚═════╝ ╚═╝  ╚═╝   ╚═╝   ")
    print("")
    print("  Microphone Diagnostic Tool")
    print("═" * 60)
    
    results = []
    
    results.append(("PyAudio", test_pyaudio()))
    results.append(("Audio Playback", test_audio_playback()))
    results.append(("Speech Recognition", test_speech_recognition()))
    
    print("\n" + "═" * 60)
    print("  Results")
    print("═" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        symbol = "✓" if passed else "✗"
        print(f"  {symbol} {name}: {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n✓ All tests passed! F.R.I.D.A.Y. should work with voice input.")
    else:
        print("\n✗ Some tests failed. See details above for fixes.")
        print("\nQuick fixes to try:")
        print("  1. sudo apt install python3-pyaudio portaudio19-dev pulseaudio pavucontrol mpv")
        print("  2. pulseaudio --start")
        print("  3. Log out and log back in")
        print("  4. Run: pavucontrol (check Input Devices tab)")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
