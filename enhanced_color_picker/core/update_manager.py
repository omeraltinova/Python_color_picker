"""
Update manager for Enhanced Color Picker.
Handles version checking, update notifications, and automatic updates.
"""

import json
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, Optional, Tuple, Callable
import threading
import time
from datetime import datetime, timedelta
import hashlib
import zipfile
import shutil
import subprocess
import sys

from .event_bus import EventBus
from .exceptions import UpdateError
from ..__version__ import __version__, get_app_info


class UpdateManager:
    """Manages application updates and version checking."""
    
    def __init__(self, event_bus: EventBus, config_dir: Path):
        self.event_bus = event_bus
        self.config_dir = config_dir
        self.current_version = __version__
        self.update_config_file = config_dir / "update_config.json"
        self.last_check_file = config_dir / "last_update_check.json"
        
        # Update configuration
        self.update_config = self._load_update_config()
        
        # Update URLs (replace with actual URLs)
        self.version_check_url = "https://api.github.com/repos/enhanced-color-picker/enhanced-color-picker/releases/latest"
        self.download_base_url = "https://github.com/enhanced-color-picker/enhanced-color-picker/releases/download"
        
        self._setup_event_handlers()
    
    def _setup_event_handlers(self):
        """Set up event handlers."""
        self.event_bus.subscribe('app_started', self._on_app_started)
        self.event_bus.subscribe('check_updates_requested', self.check_for_updates)
    
    def _load_update_config(self) -> Dict:
        """Load update configuration."""
        default_config = {
            "auto_check": True,
            "check_interval_days": 7,
            "auto_download": False,
            "auto_install": False,
            "include_prereleases": False,
            "notify_updates": True,
            "last_notification_version": None
        }
        
        if self.update_config_file.exists():
            try:
                with open(self.update_config_file, 'r') as f:
                    config = json.load(f)
                # Merge with defaults
                default_config.update(config)
            except Exception:
                pass  # Use defaults
        
        return default_config
    
    def _save_update_config(self):
        """Save update configuration."""
        try:
            self.update_config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.update_config_file, 'w') as f:
                json.dump(self.update_config, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save update config: {e}")
    
    def _load_last_check_info(self) -> Dict:
        """Load last update check information."""
        if self.last_check_file.exists():
            try:
                with open(self.last_check_file, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        
        return {
            "last_check": None,
            "last_available_version": None,
            "last_check_result": None
        }
    
    def _save_last_check_info(self, info: Dict):
        """Save last update check information."""
        try:
            self.last_check_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.last_check_file, 'w') as f:
                json.dump(info, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save last check info: {e}")
    
    def _on_app_started(self, data=None):
        """Handle app started event."""
        if self.update_config.get("auto_check", True):
            # Check if it's time for an automatic update check
            last_check_info = self._load_last_check_info()
            last_check = last_check_info.get("last_check")
            
            if self._should_check_for_updates(last_check):
                # Run check in background thread
                threading.Thread(
                    target=self._background_update_check,
                    daemon=True
                ).start()
    
    def _should_check_for_updates(self, last_check: Optional[str]) -> bool:
        """Determine if we should check for updates."""
        if not last_check:
            return True
        
        try:
            last_check_date = datetime.fromisoformat(last_check)
            check_interval = timedelta(days=self.update_config.get("check_interval_days", 7))
            return datetime.now() - last_check_date > check_interval
        except Exception:
            return True
    
    def _background_update_check(self):
        """Perform background update check."""
        try:
            update_info = self._check_remote_version()
            if update_info and update_info.get("update_available"):
                self.event_bus.publish('update_available', update_info)
        except Exception as e:
            print(f"Background update check failed: {e}")
    
    def check_for_updates(self, manual: bool = False) -> Optional[Dict]:
        """Check for available updates."""
        try:
            update_info = self._check_remote_version()
            
            # Save check information
            check_info = {
                "last_check": datetime.now().isoformat(),
                "last_available_version": update_info.get("latest_version") if update_info else None,
                "last_check_result": "success" if update_info else "failed"
            }
            self._save_last_check_info(check_info)
            
            if manual:
                # For manual checks, always notify
                self.event_bus.publish('update_check_complete', {
                    'manual': True,
                    'update_info': update_info
                })
            elif update_info and update_info.get("update_available"):
                # For automatic checks, only notify if enabled and not already notified
                if (self.update_config.get("notify_updates", True) and 
                    self.update_config.get("last_notification_version") != update_info.get("latest_version")):
                    
                    self.event_bus.publish('update_available', update_info)
                    
                    # Mark as notified
                    self.update_config["last_notification_version"] = update_info.get("latest_version")
                    self._save_update_config()
            
            return update_info
            
        except Exception as e:
            error_info = {
                "error": str(e),
                "manual": manual
            }
            self.event_bus.publish('update_check_failed', error_info)
            return None
    
    def _check_remote_version(self) -> Optional[Dict]:
        """Check remote version information."""
        try:
            # Create request with user agent
            request = urllib.request.Request(
                self.version_check_url,
                headers={'User-Agent': f'Enhanced-Color-Picker/{self.current_version}'}
            )
            
            with urllib.request.urlopen(request, timeout=10) as response:
                data = json.loads(response.read().decode())
            
            latest_version = data.get("tag_name", "").lstrip("v")
            release_name = data.get("name", "")
            release_notes = data.get("body", "")
            release_date = data.get("published_at", "")
            prerelease = data.get("prerelease", False)
            
            # Skip prereleases if not enabled
            if prerelease and not self.update_config.get("include_prereleases", False):
                return None
            
            # Compare versions
            update_available = self._is_newer_version(latest_version, self.current_version)
            
            # Get download assets
            assets = data.get("assets", [])
            download_urls = {}
            
            for asset in assets:
                name = asset.get("name", "")
                download_url = asset.get("browser_download_url", "")
                
                if "windows" in name.lower() or name.endswith(".exe"):
                    download_urls["windows"] = download_url
                elif "macos" in name.lower() or "darwin" in name.lower() or name.endswith(".dmg"):
                    download_urls["macos"] = download_url
                elif "linux" in name.lower() or name.endswith(".tar.gz"):
                    download_urls["linux"] = download_url
                elif name.endswith(".zip") and "source" not in name.lower():
                    download_urls["source"] = download_url
            
            return {
                "update_available": update_available,
                "latest_version": latest_version,
                "current_version": self.current_version,
                "release_name": release_name,
                "release_notes": release_notes,
                "release_date": release_date,
                "prerelease": prerelease,
                "download_urls": download_urls
            }
            
        except urllib.error.URLError as e:
            raise UpdateError(f"Network error checking for updates: {e}")
        except json.JSONDecodeError as e:
            raise UpdateError(f"Invalid response from update server: {e}")
        except Exception as e:
            raise UpdateError(f"Error checking for updates: {e}")
    
    def _is_newer_version(self, remote_version: str, current_version: str) -> bool:
        """Compare version strings to determine if remote is newer."""
        try:
            # Simple version comparison (assumes semantic versioning)
            remote_parts = [int(x) for x in remote_version.split('.')]
            current_parts = [int(x) for x in current_version.split('.')]
            
            # Pad shorter version with zeros
            max_len = max(len(remote_parts), len(current_parts))
            remote_parts.extend([0] * (max_len - len(remote_parts)))
            current_parts.extend([0] * (max_len - len(current_parts)))
            
            return remote_parts > current_parts
            
        except Exception:
            # Fallback to string comparison
            return remote_version != current_version
    
    def download_update(self, update_info: Dict, progress_callback: Optional[Callable] = None) -> Optional[Path]:
        """Download update package."""
        try:
            import platform
            system = platform.system().lower()
            
            download_urls = update_info.get("download_urls", {})
            download_url = None
            
            # Select appropriate download URL
            if system == "windows" and "windows" in download_urls:
                download_url = download_urls["windows"]
            elif system == "darwin" and "macos" in download_urls:
                download_url = download_urls["macos"]
            elif system == "linux" and "linux" in download_urls:
                download_url = download_urls["linux"]
            elif "source" in download_urls:
                download_url = download_urls["source"]
            
            if not download_url:
                raise UpdateError("No suitable download URL found for this platform")
            
            # Create download directory
            download_dir = self.config_dir / "downloads"
            download_dir.mkdir(parents=True, exist_ok=True)
            
            # Determine filename
            filename = download_url.split('/')[-1]
            if not filename or '.' not in filename:
                filename = f"enhanced-color-picker-{update_info['latest_version']}.zip"
            
            download_path = download_dir / filename
            
            # Download with progress
            def download_progress_hook(block_num, block_size, total_size):
                if progress_callback and total_size > 0:
                    progress = min(100, (block_num * block_size * 100) // total_size)
                    progress_callback(progress)
            
            urllib.request.urlretrieve(
                download_url,
                download_path,
                reporthook=download_progress_hook
            )
            
            return download_path
            
        except Exception as e:
            raise UpdateError(f"Failed to download update: {e}")
    
    def install_update(self, update_package_path: Path, backup: bool = True) -> bool:
        """Install downloaded update."""
        try:
            if backup:
                self._create_backup()
            
            # Extract update package
            extract_dir = self.config_dir / "update_temp"
            if extract_dir.exists():
                shutil.rmtree(extract_dir)
            extract_dir.mkdir(parents=True)
            
            with zipfile.ZipFile(update_package_path, 'r') as zip_file:
                zip_file.extractall(extract_dir)
            
            # Find the application directory in the extracted files
            app_dirs = [d for d in extract_dir.iterdir() if d.is_dir()]
            if not app_dirs:
                raise UpdateError("No application directory found in update package")
            
            source_dir = app_dirs[0]
            target_dir = Path(sys.executable).parent  # Application directory
            
            # Copy files (excluding user data)
            self._copy_update_files(source_dir, target_dir)
            
            # Clean up
            shutil.rmtree(extract_dir)
            update_package_path.unlink()
            
            return True
            
        except Exception as e:
            raise UpdateError(f"Failed to install update: {e}")
    
    def _create_backup(self):
        """Create backup of current installation."""
        try:
            backup_dir = self.config_dir / "backups"
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{self.current_version}_{timestamp}"
            backup_path = backup_dir / backup_name
            
            # Get application directory
            app_dir = Path(sys.executable).parent
            
            # Create backup (excluding user data and cache)
            shutil.copytree(
                app_dir,
                backup_path,
                ignore=shutil.ignore_patterns(
                    "*.pyc", "__pycache__", "*.log", "cache", "logs", "temp"
                )
            )
            
            # Keep only last 5 backups
            backups = sorted(backup_dir.glob("backup_*"), key=lambda x: x.stat().st_mtime)
            for old_backup in backups[:-5]:
                shutil.rmtree(old_backup)
                
        except Exception as e:
            print(f"Warning: Could not create backup: {e}")
    
    def _copy_update_files(self, source_dir: Path, target_dir: Path):
        """Copy update files to target directory."""
        for item in source_dir.rglob("*"):
            if item.is_file():
                relative_path = item.relative_to(source_dir)
                target_path = target_dir / relative_path
                
                # Skip user data directories
                if any(part in ["cache", "logs", "settings", "palettes"] for part in relative_path.parts):
                    continue
                
                # Create parent directories
                target_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Copy file
                shutil.copy2(item, target_path)
    
    def get_update_config(self) -> Dict:
        """Get current update configuration."""
        return self.update_config.copy()
    
    def update_config_setting(self, key: str, value):
        """Update a configuration setting."""
        self.update_config[key] = value
        self._save_update_config()
    
    def get_last_check_info(self) -> Dict:
        """Get information about the last update check."""
        return self._load_last_check_info()
    
    def reset_update_notifications(self):
        """Reset update notifications (will notify again for current version)."""
        self.update_config["last_notification_version"] = None
        self._save_update_config()


class UpdateNotificationDialog:
    """Dialog for showing update notifications."""
    
    def __init__(self, parent, update_info: Dict, update_manager: UpdateManager):
        self.parent = parent
        self.update_info = update_info
        self.update_manager = update_manager
        self.dialog = None
        self.download_progress = None
    
    def show(self):
        """Show the update notification dialog."""
        import tkinter as tk
        from tkinter import ttk, messagebox
        
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Update Available")
        self.dialog.geometry("500x400")
        self.dialog.resizable(False, False)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.geometry("+%d+%d" % (
            self.parent.winfo_rootx() + 50,
            self.parent.winfo_rooty() + 50
        ))
        
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(
            main_frame,
            text="🎉 Update Available!",
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=(0, 10))
        
        # Version info
        version_frame = ttk.Frame(main_frame)
        version_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(version_frame, text="Current Version:").grid(row=0, column=0, sticky=tk.W)
        ttk.Label(version_frame, text=self.update_info["current_version"]).grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        ttk.Label(version_frame, text="Latest Version:").grid(row=1, column=0, sticky=tk.W)
        ttk.Label(version_frame, text=self.update_info["latest_version"], font=("Arial", 9, "bold")).grid(row=1, column=1, sticky=tk.W, padx=(10, 0))
        
        # Release notes
        notes_label = ttk.Label(main_frame, text="Release Notes:")
        notes_label.pack(anchor=tk.W, pady=(0, 5))
        
        notes_frame = ttk.Frame(main_frame)
        notes_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        notes_text = tk.Text(notes_frame, wrap=tk.WORD, height=8)
        notes_scrollbar = ttk.Scrollbar(notes_frame, orient=tk.VERTICAL, command=notes_text.yview)
        notes_text.configure(yscrollcommand=notes_scrollbar.set)
        
        notes_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        notes_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Insert release notes
        release_notes = self.update_info.get("release_notes", "No release notes available.")
        notes_text.insert(tk.END, release_notes)
        notes_text.config(state=tk.DISABLED)
        
        # Progress bar (initially hidden)
        self.progress_frame = ttk.Frame(main_frame)
        self.progress_label = ttk.Label(self.progress_frame, text="Downloading...")
        self.progress_bar = ttk.Progressbar(self.progress_frame, mode='determinate')
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(15, 0))
        
        ttk.Button(button_frame, text="Download & Install", command=self._download_and_install).pack(side=tk.LEFT)
        ttk.Button(button_frame, text="Download Only", command=self._download_only).pack(side=tk.LEFT, padx=(10, 0))
        ttk.Button(button_frame, text="Remind Later", command=self._remind_later).pack(side=tk.LEFT, padx=(10, 0))
        ttk.Button(button_frame, text="Skip This Version", command=self._skip_version).pack(side=tk.RIGHT)
    
    def _download_and_install(self):
        """Download and install the update."""
        self._start_download(install=True)
    
    def _download_only(self):
        """Download the update only."""
        self._start_download(install=False)
    
    def _start_download(self, install: bool = False):
        """Start the download process."""
        # Show progress
        self.progress_frame.pack(fill=tk.X, pady=(10, 0))
        self.progress_label.pack(anchor=tk.W)
        self.progress_bar.pack(fill=tk.X, pady=(5, 0))
        
        def progress_callback(progress):
            self.progress_bar['value'] = progress
            self.dialog.update_idletasks()
        
        def download_thread():
            try:
                download_path = self.update_manager.download_update(
                    self.update_info,
                    progress_callback
                )
                
                if install and download_path:
                    self.progress_label.config(text="Installing...")
                    self.progress_bar.config(mode='indeterminate')
                    self.progress_bar.start()
                    
                    success = self.update_manager.install_update(download_path)
                    
                    if success:
                        messagebox.showinfo(
                            "Update Complete",
                            "Update installed successfully! Please restart the application."
                        )
                    else:
                        messagebox.showerror(
                            "Update Failed",
                            "Failed to install update. Please try again or install manually."
                        )
                else:
                    messagebox.showinfo(
                        "Download Complete",
                        f"Update downloaded successfully to:\\n{download_path}"
                    )
                
                self.dialog.destroy()
                
            except Exception as e:
                messagebox.showerror("Download Failed", f"Failed to download update:\\n{str(e)}")
                self.dialog.destroy()
        
        import threading
        threading.Thread(target=download_thread, daemon=True).start()
    
    def _remind_later(self):
        """Remind about update later."""
        self.dialog.destroy()
    
    def _skip_version(self):
        """Skip this version."""
        self.update_manager.update_config_setting(
            "last_notification_version",
            self.update_info["latest_version"]
        )
        self.dialog.destroy()