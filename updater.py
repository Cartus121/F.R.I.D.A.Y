"""
Auto-Update Module for F.R.I.D.A.Y.
Checks GitHub for new releases and updates the app automatically
"""

import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from pathlib import Path
from typing import Callable, Optional, Tuple

# GitHub repository info
GITHUB_OWNER = "Cartus121"
GITHUB_REPO = "F.R.I.D.A.Y"
RELEASES_URL = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
TAGS_URL = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/tags"

# Current version - update this when releasing
CURRENT_VERSION = "stable_v1.0.6"


def get_current_version() -> str:
    """Get current version"""
    return CURRENT_VERSION


def parse_version(version: str) -> Tuple[str, int, int, int]:
    """Parse version string into (stage, major, minor, patch)
    
    Supports:
    - alpha-v20 -> (alpha, 20, 0, 0)
    - beta-v5 -> (beta, 5, 0, 0)
    - stable_v1.0.1 -> (stable, 1, 0, 1)
    - v1.2.3 -> (release, 1, 2, 3)
    """
    version = version.lower().strip()
    
    # stable_v1.0.1 format
    if version.startswith("stable_v"):
        try:
            parts = version.replace("stable_v", "").split(".")
            major = int(parts[0]) if len(parts) > 0 else 0
            minor = int(parts[1]) if len(parts) > 1 else 0
            patch = int(parts[2]) if len(parts) > 2 else 0
            return ("stable", major, minor, patch)
        except ValueError:
            return ("stable", 1, 0, 0)
    
    # alpha-v20 format
    elif version.startswith("alpha-v"):
        try:
            num = int(version.replace("alpha-v", ""))
            return ("alpha", num, 0, 0)
        except ValueError:
            return ("alpha", 0, 0, 0)
    
    # beta-v5 format
    elif version.startswith("beta-v"):
        try:
            num = int(version.replace("beta-v", ""))
            return ("beta", num, 0, 0)
        except ValueError:
            return ("beta", 0, 0, 0)
    
    # v1.2.3 format
    elif version.startswith("v"):
        try:
            parts = version.replace("v", "").split(".")
            major = int(parts[0]) if len(parts) > 0 else 0
            minor = int(parts[1]) if len(parts) > 1 else 0
            patch = int(parts[2]) if len(parts) > 2 else 0
            return ("release", major, minor, patch)
        except ValueError:
            return ("release", 0, 0, 0)
    
    return ("unknown", 0, 0, 0)


def is_newer_version(latest: str, current: str) -> bool:
    """Check if latest version is newer than current"""
    latest_stage, latest_major, latest_minor, latest_patch = parse_version(latest)
    current_stage, current_major, current_minor, current_patch = parse_version(current)
    
    # Stage priority: stable/release > beta > alpha
    stage_order = {"alpha": 0, "beta": 1, "release": 2, "stable": 2, "unknown": -1}
    
    latest_priority = stage_order.get(latest_stage, -1)
    current_priority = stage_order.get(current_stage, -1)
    
    if latest_priority > current_priority:
        return True
    elif latest_priority < current_priority:
        return False
    else:
        # Same stage, compare version numbers
        if latest_major > current_major:
            return True
        elif latest_major < current_major:
            return False
        elif latest_minor > current_minor:
            return True
        elif latest_minor < current_minor:
            return False
        else:
            return latest_patch > current_patch


def check_for_updates() -> Optional[dict]:
    """
    Check GitHub for new releases or tags
    Returns dict with version info if update available, None otherwise
    """
    # First try releases API
    update_info = _check_releases()
    if update_info:
        return update_info
    
    # Fall back to tags API (for when releases don't exist)
    return _check_tags()


def _check_releases() -> Optional[dict]:
    """Check GitHub releases for updates"""
    try:
        request = urllib.request.Request(
            RELEASES_URL,
            headers={"User-Agent": "F.R.I.D.A.Y-Updater/1.0"}
        )
        
        with urllib.request.urlopen(request, timeout=10) as response:
            data = json.loads(response.read().decode())
        
        latest_version = data.get("tag_name", "")
        
        if is_newer_version(latest_version, CURRENT_VERSION):
            # Find the right asset for this platform
            system = platform.system().lower()
            
            download_url = None
            asset_name = None
            
            for asset in data.get("assets", []):
                name = asset.get("name", "").lower()
                
                if system == "windows" and (".exe" in name or "windows" in name):
                    download_url = asset.get("browser_download_url")
                    asset_name = asset.get("name")
                    break
                elif system == "linux" and ("linux" in name or ".appimage" in name.lower()):
                    download_url = asset.get("browser_download_url")
                    asset_name = asset.get("name")
                    break
                elif system == "darwin" and ("macos" in name or "mac" in name):
                    download_url = asset.get("browser_download_url")
                    asset_name = asset.get("name")
                    break
            
            return {
                "version": latest_version,
                "current": CURRENT_VERSION,
                "download_url": download_url,
                "asset_name": asset_name,
                "release_notes": data.get("body", ""),
                "html_url": data.get("html_url", ""),
                "source": "release"
            }
        
        return None
        
    except Exception as e:
        print(f"[Updater] Releases check: {e}")
        return None


def _check_tags() -> Optional[dict]:
    """Check GitHub tags for updates (fallback when no releases)"""
    try:
        request = urllib.request.Request(
            TAGS_URL,
            headers={"User-Agent": "F.R.I.D.A.Y-Updater/1.0"}
        )
        
        with urllib.request.urlopen(request, timeout=10) as response:
            tags = json.loads(response.read().decode())
        
        if not tags:
            return None
        
        # Tags are returned newest first, get the latest
        latest_tag = tags[0].get("name", "")
        
        if is_newer_version(latest_tag, CURRENT_VERSION):
            # No downloadable asset from tags - provide source download link
            zipball_url = f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/archive/refs/tags/{latest_tag}.zip"
            
            return {
                "version": latest_tag,
                "current": CURRENT_VERSION,
                "download_url": zipball_url,
                "asset_name": f"{GITHUB_REPO}-{latest_tag}.zip",
                "release_notes": f"New version {latest_tag} is available!\nPlease download and rebuild, or wait for an official release.",
                "html_url": f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/releases/tag/{latest_tag}",
                "source": "tag"  # Indicates this came from tag, not release
            }
        
        return None
        
    except Exception as e:
        print(f"[Updater] Tags check: {e}")
        return None


def download_update(download_url: str, progress_callback: Callable[[float], None] = None) -> Optional[str]:
    """
    Download update file
    Returns path to downloaded file, or None on failure
    """
    if not download_url:
        return None
    
    try:
        # Create temp file
        temp_dir = Path(tempfile.gettempdir()) / "friday_update"
        temp_dir.mkdir(exist_ok=True)
        
        # Get filename from URL
        filename = download_url.split("/")[-1]
        download_path = temp_dir / filename
        
        # Download with progress
        request = urllib.request.Request(
            download_url,
            headers={"User-Agent": "F.R.I.D.A.Y-Updater/1.0"}
        )
        
        with urllib.request.urlopen(request, timeout=300) as response:
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(download_path, 'wb') as f:
                while True:
                    chunk = response.read(8192)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    if progress_callback and total_size > 0:
                        progress_callback(downloaded / total_size)
        
        return str(download_path)
        
    except Exception as e:
        print(f"[Updater] Download error: {e}")
        return None


def install_update(downloaded_file: str) -> bool:
    """
    Install the update by replacing current executable and restarting
    Returns True if successful, False otherwise
    """
    if not downloaded_file or not os.path.exists(downloaded_file):
        return False
    
    try:
        system = platform.system().lower()
        
        if system == "windows":
            return _install_windows(downloaded_file)
        elif system == "linux":
            return _install_linux(downloaded_file)
        else:
            print(f"[Updater] Unsupported platform: {system}")
            return False
            
    except Exception as e:
        print(f"[Updater] Install error: {e}")
        return False


def _install_windows(downloaded_file: str) -> bool:
    """Install update on Windows - handles PyInstaller _MEI folders"""
    try:
        # Get current executable path
        if getattr(sys, 'frozen', False):
            # Running as compiled exe
            current_exe = sys.executable
            exe_dir = os.path.dirname(current_exe)
        else:
            # Running as script - just replace
            print("[Updater] Running from source, please update manually")
            return False
        
        # Create a batch script to replace the exe after we exit
        # Use a location outside the exe directory to avoid issues
        temp_dir = os.environ.get('TEMP', os.path.expanduser('~'))
        update_script = os.path.join(temp_dir, "friday_update.bat")
        new_exe_name = os.path.basename(current_exe)
        new_exe_path = os.path.join(exe_dir, new_exe_name)
        
        # More robust batch script that:
        # 1. Waits longer for app to close
        # 2. Retries deletion
        # 3. Cleans up _MEI folders
        # 4. Handles errors gracefully
        batch_content = f'''@echo off
setlocal enabledelayedexpansion
title F.R.I.D.A.Y. Update
echo.
echo ========================================
echo   F.R.I.D.A.Y. Auto-Update
echo ========================================
echo.
echo Waiting for application to close...
timeout /t 3 /nobreak >nul

REM Wait for the old process to fully exit (retry loop)
set retries=0
:waitloop
tasklist /FI "IMAGENAME eq {new_exe_name}" 2>NUL | find /I /N "{new_exe_name}">NUL
if "%ERRORLEVEL%"=="0" (
    set /a retries+=1
    if !retries! GEQ 15 (
        echo Warning: Old process still running, forcing update...
        goto :continue_update
    )
    echo Waiting for process to close... attempt !retries!/15
    timeout /t 1 /nobreak >nul
    goto :waitloop
)

:continue_update
echo.
echo Removing old version...

REM Try to delete the old exe multiple times
set del_retries=0
:del_loop
del /f /q "{current_exe}" >nul 2>&1
if exist "{current_exe}" (
    set /a del_retries+=1
    if !del_retries! GEQ 10 (
        echo Warning: Could not delete old exe, will overwrite...
        goto :copy_new
    )
    timeout /t 1 /nobreak >nul
    goto :del_loop
)

:copy_new
echo Installing new version...
copy /y "{downloaded_file}" "{new_exe_path}" >nul
if errorlevel 1 (
    echo ERROR: Failed to copy new version!
    echo Please manually copy:
    echo   From: {downloaded_file}
    echo   To: {new_exe_path}
    pause
    exit /b 1
)

echo Cleaning up...
del /f /q "{downloaded_file}" >nul 2>&1

REM Clean up old PyInstaller temp folders (older than current)
for /d %%i in ("%TEMP%\\_MEI*") do (
    rd /s /q "%%i" >nul 2>&1
)

REM Clean up friday_update folder
rd /s /q "%TEMP%\\friday_update" >nul 2>&1

echo.
echo ========================================
echo   Update complete! Starting F.R.I.D.A.Y...
echo ========================================
timeout /t 2 /nobreak >nul

REM Start the new version
start "" "{new_exe_path}"

REM Delete this script
(goto) 2>nul & del /f /q "%~f0"
'''
        
        with open(update_script, 'w') as f:
            f.write(batch_content)
        
        # Run the update script - CREATE_NEW_CONSOLE so user can see progress
        subprocess.Popen(
            ['cmd', '/c', update_script],
            creationflags=subprocess.CREATE_NEW_CONSOLE,
            close_fds=True
        )
        
        return True
        
    except Exception as e:
        print(f"[Updater] Windows install error: {e}")
        return False


def _install_linux(downloaded_file: str) -> bool:
    """Install update on Linux"""
    try:
        # Get current executable path
        if getattr(sys, 'frozen', False):
            current_exe = sys.executable
            exe_dir = os.path.dirname(current_exe)
        else:
            print("[Updater] Running from source, please update manually")
            return False
        
        # Create a shell script to replace the exe after we exit
        update_script = os.path.join(exe_dir, "_update.sh")
        new_exe_name = os.path.basename(current_exe)
        
        shell_content = f'''#!/bin/bash
sleep 2
rm -f "{current_exe}"
cp "{downloaded_file}" "{os.path.join(exe_dir, new_exe_name)}"
chmod +x "{os.path.join(exe_dir, new_exe_name)}"
rm -f "{downloaded_file}"
"{os.path.join(exe_dir, new_exe_name)}" &
rm -f "$0"
'''
        
        with open(update_script, 'w') as f:
            f.write(shell_content)
        
        os.chmod(update_script, 0o755)
        
        # Run the update script and exit
        subprocess.Popen(
            ['/bin/bash', update_script],
            close_fds=True,
            start_new_session=True
        )
        
        return True
        
    except Exception as e:
        print(f"[Updater] Linux install error: {e}")
        return False


class UpdateChecker:
    """Background update checker with GUI integration"""
    
    def __init__(self, on_update_available: Callable[[dict], None] = None):
        self.on_update_available = on_update_available
        self.update_info = None
        self.checking = False
        
    def check_async(self):
        """Check for updates in background"""
        if self.checking:
            return
        
        self.checking = True
        
        def _check():
            try:
                self.update_info = check_for_updates()
                if self.update_info and self.on_update_available:
                    self.on_update_available(self.update_info)
            finally:
                self.checking = False
        
        threading.Thread(target=_check, daemon=True).start()
    
    def download_and_install(self, progress_callback: Callable[[float], None] = None) -> bool:
        """Download and install the update"""
        if not self.update_info or not self.update_info.get("download_url"):
            return False
        
        downloaded = download_update(
            self.update_info["download_url"],
            progress_callback
        )
        
        if downloaded:
            return install_update(downloaded)
        
        return False


# For testing
if __name__ == "__main__":
    print(f"Current version: {CURRENT_VERSION}")
    print("Checking for updates...")
    
    info = check_for_updates()
    if info:
        print(f"\n✨ Update available: {info['version']}")
        print(f"Download: {info['download_url']}")
        print(f"Notes: {info['release_notes'][:200]}...")
    else:
        print("No updates available")
