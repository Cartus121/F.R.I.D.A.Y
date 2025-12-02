#!/usr/bin/env python3
"""
F.R.I.D.A.Y. Build Script
Female Replacement Intelligent Digital Assistant Youth
Creates a standalone executable using PyInstaller

Run: python3 build.py
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    print("═" * 60)
    print("  ███████╗██████╗ ██╗██████╗  █████╗ ██╗   ██╗")
    print("  ██╔════╝██╔══██╗██║██╔══██╗██╔══██╗╚██╗ ██╔╝")
    print("  █████╗  ██████╔╝██║██║  ██║███████║ ╚████╔╝ ")
    print("  ██╔══╝  ██╔══██╗██║██║  ██║██╔══██║  ╚██╔╝  ")
    print("  ██║     ██║  ██║██║██████╔╝██║  ██║   ██║   ")
    print("  ╚═╝     ╚═╝  ╚═╝╚═╝╚═════╝ ╚═╝  ╚═╝   ╚═╝   ")
    print("")
    print("  Build Script")
    print("═" * 60)
    
    # Check if PyInstaller is installed
    try:
        import PyInstaller
        print("[OK] PyInstaller found")
    except ImportError:
        print("[*] Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("[OK] PyInstaller installed")
    
    # Get the directory of this script
    script_dir = Path(__file__).parent.absolute()
    os.chdir(script_dir)
    
    print(f"[*] Building from: {script_dir}")
    
    # Determine platform
    is_windows = sys.platform == 'win32'
    exe_name = "FRIDAY.exe" if is_windows else "FRIDAY"
    
    # Icon file path
    icon_file = script_dir / "icon.ico"
    has_icon = icon_file.exists()
    
    # PyInstaller command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=FRIDAY",
        "--onefile",           # Single executable
        "--windowed",          # No console window (GUI app)
        "--noconfirm",         # Overwrite without asking
        "--clean",             # Clean cache before building
        
        # Add hidden imports for libraries that PyInstaller might miss
        "--hidden-import=customtkinter",
        "--hidden-import=PIL",
        "--hidden-import=PIL._tkinter_finder",
        "--hidden-import=speech_recognition",
        "--hidden-import=pyaudio",
        "--hidden-import=pyttsx3",
        "--hidden-import=edge_tts",
        "--hidden-import=openai",
        "--hidden-import=google.generativeai",
        "--hidden-import=requests",
        "--hidden-import=psutil",
        "--hidden-import=dateutil",
        "--hidden-import=duckduckgo_search",
        "--hidden-import=sqlalchemy",
        "--hidden-import=pygame",
        "--hidden-import=keyboard",
        "--hidden-import=pystray",
        
        # Collect all data for customtkinter (themes, etc.)
        "--collect-all=customtkinter",
    ]
    
    # Add icon if exists
    if has_icon:
        cmd.append(f"--icon={icon_file}")
        print(f"[OK] Using icon: {icon_file}")
    else:
        print("[!] No icon.ico found - using default icon")
    
    # Entry point
    cmd.append("main.py")
    
    print("[*] Running PyInstaller...")
    print(f"    Target: {exe_name}")
    
    try:
        subprocess.check_call(cmd)
        
        # Check if build succeeded
        exe_path = script_dir / "dist" / ("FRIDAY.exe" if is_windows else "FRIDAY")
        if exe_path.exists():
            print()
            print("═" * 60)
            print("[OK] BUILD SUCCESSFUL!")
            print("═" * 60)
            print(f"\nExecutable location:")
            print(f"  {exe_path}")
            if is_windows:
                print(f"\nTo run:")
                print(f"  dist\\FRIDAY.exe")
            else:
                print(f"\nTo run:")
                print(f"  ./dist/FRIDAY")
                print(f"\nTo install system-wide:")
                print(f"  sudo cp dist/FRIDAY /usr/local/bin/")
            print()
        else:
            print("[X] Build may have failed - executable not found")
            
    except subprocess.CalledProcessError as e:
        print(f"[X] Build failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
