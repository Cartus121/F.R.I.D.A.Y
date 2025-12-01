@echo off
REM F.R.I.D.A.Y. Windows Build Script
REM Female Replacement Intelligent Digital Assistant Youth
REM Run this on a Windows machine with Python installed

echo ================================================================
echo   ███████╗██████╗ ██╗██████╗  █████╗ ██╗   ██╗
echo   ██╔════╝██╔══██╗██║██╔══██╗██╔══██╗╚██╗ ██╔╝
echo   █████╗  ██████╔╝██║██║  ██║███████║ ╚████╔╝
echo   ██╔══╝  ██╔══██╗██║██║  ██║██╔══██║  ╚██╔╝
echo   ██║     ██║  ██║██║██████╔╝██║  ██║   ██║
echo   ╚═╝     ╚═╝  ╚═╝╚═╝╚═════╝ ╚═╝  ╚═╝   ╚═╝
echo.
echo   Windows Build Script
echo ================================================================

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [X] Python not found! Please install Python 3.10+ from python.org
    pause
    exit /b 1
)

echo [OK] Python found

REM Install dependencies
echo [*] Installing dependencies...
pip install pyinstaller
pip install customtkinter pillow
pip install SpeechRecognition pyaudio pyttsx3 edge-tts
pip install openai google-generativeai
pip install requests psutil python-dateutil
pip install duckduckgo-search sqlalchemy
pip install pygame keyboard pystray

echo [*] Building FRIDAY.exe...
pyinstaller --name="FRIDAY" --onefile --windowed --noconfirm --clean ^
    --hidden-import=customtkinter ^
    --hidden-import=PIL ^
    --hidden-import=PIL._tkinter_finder ^
    --hidden-import=speech_recognition ^
    --hidden-import=pyttsx3 ^
    --hidden-import=edge_tts ^
    --hidden-import=openai ^
    --hidden-import=requests ^
    --hidden-import=psutil ^
    --hidden-import=dateutil ^
    --hidden-import=pygame ^
    --hidden-import=keyboard ^
    --hidden-import=pystray ^
    --collect-all=customtkinter ^
    main.py

if exist "dist\FRIDAY.exe" (
    echo.
    echo ================================================================
    echo [OK] F.R.I.D.A.Y. BUILD SUCCESSFUL!
    echo ================================================================
    echo.
    echo Executable: dist\FRIDAY.exe
    echo.
    echo You can now copy FRIDAY.exe to any Windows PC!
) else (
    echo [X] Build failed!
)

pause
