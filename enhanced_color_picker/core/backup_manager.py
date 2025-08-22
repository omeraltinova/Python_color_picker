"""
Backup and restore manager for Enhanced Color Picker.
Handles user data backup, restore, and migration functionality.
"""

import json
import shutil
import zipfile
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Callable
import threading
import os

from .event_bus import EventBus
from .exceptions import BackupError


class BackupManager:
    """Manages backup and restore operations for user data."""
    
    def __init__(self, event_bus: EventBus, user_data_dir: Path):
        self.event_bus = event_bus
        self.user_data_dir = user_data_dir
        self.backup_dir = user_data_dir / "backups"
        self.backup_config_file = user_data_dir / "backup_config.json"
        
        # Ensure backup directory exists
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Load backup configuration
        self.backup_config = self._load_backup_config()
        
        self._setup_event_handlers()
    
    def _setup_event_handlers(self):
        """Set up event handlers."""
        self.event_bus.subscribe('app_closing', self._on_app_closing)
        self.event_bus.subscribe('palette_saved', self._on_palette_saved)
        self.event_bus.subscribe('settings_changed', self._on_settings_changed)
    
    def _load_backup_config(self) -> Dict:
        """Load backup configuration."""
        default_config = {
            "auto_backup": True,
            "backup_on_exit": True,
            "backup_interval_hours": 24,
            "max_backups": 10,
            "backup_palettes": True,
            "backup_settings": True,
            "backup_history": True,
            "backup_cache": False,
            "compress_backups": True,
            "last_backup": None
        }
        
        if self.backup_config_file.exists():
            try:
                with open(self.backup_config_file, 'r') as f:
                    config = json.load(f)
                default_config.update(config)
            except Exception:
                pass  # Use defaults
        
        return default_config
    
    def _save_backup_config(self):
        """Save backup configuration."""
        try:
            with open(self.backup_config_file, 'w') as f:
                json.dump(self.backup_config, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save backup config: {e}")
    
    def _on_app_closing(self, data=None):
        """Handle app closing event."""
        if self.backup_config.get("backup_on_exit", True):
            try:
                self.create_backup("exit_backup", include_cache=False)
            except Exception as e:
                print(f"Warning: Exit backup failed: {e}")
    
    def _on_palette_saved(self, data=None):
        """Handle palette saved event."""
        if self.backup_config.get("auto_backup", True):
            # Create incremental backup of palettes
            try:
                self._create_incremental_backup("palettes")
            except Exception as e:
                print(f"Warning: Palette backup failed: {e}")
    
    def _on_settings_changed(self, data=None):
        """Handle settings changed event."""
        if self.backup_config.get("auto_backup", True):
            # Create incremental backup of settings
            try:
                self._create_incremental_backup("settings")
            except Exception as e:
                print(f"Warning: Settings backup failed: {e}")
    
    def create_backup(self, backup_name: Optional[str] = None, 
                     include_cache: bool = False,
                     progress_callback: Optional[Callable] = None) -> Path:
        """Create a full backup of user data."""
        if not backup_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{timestamp}"
        
        backup_path = self.backup_dir / f"{backup_name}.zip"
        
        try:
            # Collect files to backup
            files_to_backup = self._collect_backup_files(include_cache)
            
            # Create backup archive
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as backup_zip:
                total_files = len(files_to_backup)
                
                for i, (file_path, archive_name) in enumerate(files_to_backup):
                    if file_path.exists():
                        backup_zip.write(file_path, archive_name)
                    
                    if progress_callback:
                        progress = int((i + 1) * 100 / total_files)
                        progress_callback(progress)
            
            # Update backup config
            self.backup_config["last_backup"] = datetime.now().isoformat()
            self._save_backup_config()
            
            # Clean up old backups
            self._cleanup_old_backups()
            
            # Publish backup created event
            self.event_bus.publish('backup_created', {
                'backup_path': backup_path,
                'backup_name': backup_name
            })
            
            return backup_path
            
        except Exception as e:
            if backup_path.exists():
                backup_path.unlink()  # Clean up partial backup
            raise BackupError(f"Failed to create backup: {e}")
    
    def _collect_backup_files(self, include_cache: bool = False) -> List[tuple]:
        """Collect files to include in backup."""
        files_to_backup = []
        
        # Palettes
        if self.backup_config.get("backup_palettes", True):
            palettes_dir = self.user_data_dir / "palettes"
            if palettes_dir.exists():
                for palette_file in palettes_dir.rglob("*.json"):
                    archive_name = f"palettes/{palette_file.relative_to(palettes_dir)}"
                    files_to_backup.append((palette_file, archive_name))
        
        # Settings
        if self.backup_config.get("backup_settings", True):
            settings_dir = self.user_data_dir / "settings"
            if settings_dir.exists():
                for settings_file in settings_dir.rglob("*.json"):
                    archive_name = f"settings/{settings_file.relative_to(settings_dir)}"
                    files_to_backup.append((settings_file, archive_name))
        
        # History
        if self.backup_config.get("backup_history", True):
            history_files = [
                self.user_data_dir / "color_history.json",
                self.user_data_dir / "favorites.json"
            ]
            for history_file in history_files:
                if history_file.exists():
                    files_to_backup.append((history_file, history_file.name))
        
        # Cache (if requested)
        if include_cache and self.backup_config.get("backup_cache", False):
            cache_dir = self.user_data_dir / "cache"
            if cache_dir.exists():
                for cache_file in cache_dir.rglob("*"):
                    if cache_file.is_file():
                        archive_name = f"cache/{cache_file.relative_to(cache_dir)}"
                        files_to_backup.append((cache_file, archive_name))
        
        # Backup configuration itself
        if self.backup_config_file.exists():
            files_to_backup.append((self.backup_config_file, "backup_config.json"))
        
        return files_to_backup
    
    def _create_incremental_backup(self, data_type: str):
        """Create incremental backup for specific data type."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"incremental_{data_type}_{timestamp}"
        backup_path = self.backup_dir / f"{backup_name}.zip"
        
        try:
            files_to_backup = []
            
            if data_type == "palettes":
                palettes_dir = self.user_data_dir / "palettes"
                if palettes_dir.exists():
                    for palette_file in palettes_dir.rglob("*.json"):
                        archive_name = f"palettes/{palette_file.relative_to(palettes_dir)}"
                        files_to_backup.append((palette_file, archive_name))
            
            elif data_type == "settings":
                settings_dir = self.user_data_dir / "settings"
                if settings_dir.exists():
                    for settings_file in settings_dir.rglob("*.json"):
                        archive_name = f"settings/{settings_file.relative_to(settings_dir)}"
                        files_to_backup.append((settings_file, archive_name))
            
            if files_to_backup:
                with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as backup_zip:
                    for file_path, archive_name in files_to_backup:
                        if file_path.exists():
                            backup_zip.write(file_path, archive_name)
                
                # Keep only recent incremental backups
                self._cleanup_incremental_backups(data_type)
        
        except Exception as e:
            if backup_path.exists():
                backup_path.unlink()
            raise BackupError(f"Failed to create incremental backup: {e}")
    
    def restore_backup(self, backup_path: Path, 
                      restore_palettes: bool = True,
                      restore_settings: bool = True,
                      restore_history: bool = True,
                      progress_callback: Optional[Callable] = None) -> bool:
        """Restore data from backup."""
        if not backup_path.exists():
            raise BackupError(f"Backup file not found: {backup_path}")
        
        try:
            # Create restore point before restoring
            restore_point = self.create_backup("pre_restore_backup")
            
            with zipfile.ZipFile(backup_path, 'r') as backup_zip:
                file_list = backup_zip.namelist()
                total_files = len(file_list)
                
                for i, file_name in enumerate(file_list):
                    # Determine if we should restore this file
                    should_restore = False
                    
                    if file_name.startswith("palettes/") and restore_palettes:
                        should_restore = True
                    elif file_name.startswith("settings/") and restore_settings:
                        should_restore = True
                    elif file_name in ["color_history.json", "favorites.json"] and restore_history:
                        should_restore = True
                    elif file_name == "backup_config.json":
                        should_restore = True
                    
                    if should_restore:
                        # Extract file
                        target_path = self.user_data_dir / file_name
                        target_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        with backup_zip.open(file_name) as source:
                            with open(target_path, 'wb') as target:
                                shutil.copyfileobj(source, target)
                    
                    if progress_callback:
                        progress = int((i + 1) * 100 / total_files)
                        progress_callback(progress)
            
            # Publish restore completed event
            self.event_bus.publish('backup_restored', {
                'backup_path': backup_path,
                'restore_point': restore_point
            })
            
            return True
            
        except Exception as e:
            raise BackupError(f"Failed to restore backup: {e}")
    
    def list_backups(self) -> List[Dict]:
        """List available backups."""
        backups = []
        
        for backup_file in self.backup_dir.glob("*.zip"):
            try:
                stat = backup_file.stat()
                backup_info = {
                    "name": backup_file.stem,
                    "path": backup_file,
                    "size": stat.st_size,
                    "created": datetime.fromtimestamp(stat.st_mtime),
                    "type": self._determine_backup_type(backup_file.stem)
                }
                
                # Try to get additional info from backup
                try:
                    with zipfile.ZipFile(backup_file, 'r') as backup_zip:
                        backup_info["file_count"] = len(backup_zip.namelist())
                        backup_info["contains_palettes"] = any(f.startswith("palettes/") for f in backup_zip.namelist())
                        backup_info["contains_settings"] = any(f.startswith("settings/") for f in backup_zip.namelist())
                        backup_info["contains_history"] = any(f in ["color_history.json", "favorites.json"] for f in backup_zip.namelist())
                except:
                    pass
                
                backups.append(backup_info)
                
            except Exception:
                continue  # Skip corrupted backup files
        
        # Sort by creation date (newest first)
        backups.sort(key=lambda x: x["created"], reverse=True)
        
        return backups
    
    def _determine_backup_type(self, backup_name: str) -> str:
        """Determine backup type from name."""
        if backup_name.startswith("incremental_"):
            return "incremental"
        elif backup_name.startswith("exit_backup"):
            return "exit"
        elif backup_name.startswith("pre_restore"):
            return "restore_point"
        else:
            return "manual"
    
    def delete_backup(self, backup_path: Path) -> bool:
        """Delete a backup file."""
        try:
            if backup_path.exists():
                backup_path.unlink()
                
                self.event_bus.publish('backup_deleted', {
                    'backup_path': backup_path
                })
                
                return True
            return False
            
        except Exception as e:
            raise BackupError(f"Failed to delete backup: {e}")
    
    def _cleanup_old_backups(self):
        """Clean up old backups based on configuration."""
        max_backups = self.backup_config.get("max_backups", 10)
        
        # Get all full backups (exclude incremental)
        full_backups = []
        for backup_file in self.backup_dir.glob("backup_*.zip"):
            if not backup_file.stem.startswith("incremental_"):
                full_backups.append(backup_file)
        
        # Sort by modification time (oldest first)
        full_backups.sort(key=lambda x: x.stat().st_mtime)
        
        # Remove excess backups
        while len(full_backups) > max_backups:
            old_backup = full_backups.pop(0)
            try:
                old_backup.unlink()
            except Exception:
                pass  # Ignore errors when cleaning up
    
    def _cleanup_incremental_backups(self, data_type: str, max_keep: int = 5):
        """Clean up old incremental backups."""
        pattern = f"incremental_{data_type}_*.zip"
        incremental_backups = list(self.backup_dir.glob(pattern))
        
        # Sort by modification time (oldest first)
        incremental_backups.sort(key=lambda x: x.stat().st_mtime)
        
        # Remove excess incremental backups
        while len(incremental_backups) > max_keep:
            old_backup = incremental_backups.pop(0)
            try:
                old_backup.unlink()
            except Exception:
                pass
    
    def export_backup(self, backup_path: Path, export_path: Path) -> bool:
        """Export backup to external location."""
        try:
            shutil.copy2(backup_path, export_path)
            return True
        except Exception as e:
            raise BackupError(f"Failed to export backup: {e}")
    
    def import_backup(self, external_backup_path: Path) -> Path:
        """Import backup from external location."""
        try:
            # Validate backup file
            if not zipfile.is_zipfile(external_backup_path):
                raise BackupError("Invalid backup file format")
            
            # Generate unique name
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"imported_{timestamp}.zip"
            backup_path = self.backup_dir / backup_name
            
            # Copy to backup directory
            shutil.copy2(external_backup_path, backup_path)
            
            return backup_path
            
        except Exception as e:
            raise BackupError(f"Failed to import backup: {e}")
    
    def get_backup_config(self) -> Dict:
        """Get current backup configuration."""
        return self.backup_config.copy()
    
    def update_backup_config(self, config_updates: Dict):
        """Update backup configuration."""
        self.backup_config.update(config_updates)
        self._save_backup_config()
    
    def get_backup_statistics(self) -> Dict:
        """Get backup statistics."""
        backups = self.list_backups()
        
        total_size = sum(backup["size"] for backup in backups)
        backup_types = {}
        
        for backup in backups:
            backup_type = backup["type"]
            if backup_type not in backup_types:
                backup_types[backup_type] = {"count": 0, "size": 0}
            backup_types[backup_type]["count"] += 1
            backup_types[backup_type]["size"] += backup["size"]
        
        return {
            "total_backups": len(backups),
            "total_size": total_size,
            "backup_types": backup_types,
            "last_backup": self.backup_config.get("last_backup"),
            "backup_directory": str(self.backup_dir)
        }


class BackupRestoreDialog:
    """Dialog for backup and restore operations."""
    
    def __init__(self, parent, backup_manager: BackupManager):
        self.parent = parent
        self.backup_manager = backup_manager
        self.dialog = None
    
    def show(self):
        """Show the backup/restore dialog."""
        import tkinter as tk
        from tkinter import ttk, messagebox, filedialog
        
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Backup & Restore")
        self.dialog.geometry("600x500")
        self.dialog.resizable(True, True)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Create notebook for tabs
        notebook = ttk.Notebook(self.dialog)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Backup tab
        backup_frame = ttk.Frame(notebook)
        notebook.add(backup_frame, text="Create Backup")
        self._create_backup_tab(backup_frame)
        
        # Restore tab
        restore_frame = ttk.Frame(notebook)
        notebook.add(restore_frame, text="Restore Backup")
        self._create_restore_tab(restore_frame)
        
        # Settings tab
        settings_frame = ttk.Frame(notebook)
        notebook.add(settings_frame, text="Settings")
        self._create_settings_tab(settings_frame)
    
    def _create_backup_tab(self, parent):
        """Create backup tab content."""
        import tkinter as tk
        from tkinter import ttk
        
        # Backup options
        options_frame = ttk.LabelFrame(parent, text="Backup Options", padding="10")
        options_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.backup_palettes_var = tk.BooleanVar(value=True)
        self.backup_settings_var = tk.BooleanVar(value=True)
        self.backup_history_var = tk.BooleanVar(value=True)
        self.backup_cache_var = tk.BooleanVar(value=False)
        
        ttk.Checkbutton(options_frame, text="Include Palettes", variable=self.backup_palettes_var).pack(anchor=tk.W)
        ttk.Checkbutton(options_frame, text="Include Settings", variable=self.backup_settings_var).pack(anchor=tk.W)
        ttk.Checkbutton(options_frame, text="Include History", variable=self.backup_history_var).pack(anchor=tk.W)
        ttk.Checkbutton(options_frame, text="Include Cache", variable=self.backup_cache_var).pack(anchor=tk.W)
        
        # Backup name
        name_frame = ttk.Frame(options_frame)
        name_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(name_frame, text="Backup Name:").pack(side=tk.LEFT)
        self.backup_name_var = tk.StringVar()
        ttk.Entry(name_frame, textvariable=self.backup_name_var, width=30).pack(side=tk.LEFT, padx=(10, 0))
        
        # Progress bar
        self.backup_progress_frame = ttk.Frame(parent)
        self.backup_progress_label = ttk.Label(self.backup_progress_frame, text="Creating backup...")
        self.backup_progress_bar = ttk.Progressbar(self.backup_progress_frame, mode='determinate')
        
        # Buttons
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="Create Backup", command=self._create_backup).pack(side=tk.LEFT)
        ttk.Button(button_frame, text="Export Backup", command=self._export_backup).pack(side=tk.LEFT, padx=(10, 0))
    
    def _create_restore_tab(self, parent):
        """Create restore tab content."""
        import tkinter as tk
        from tkinter import ttk
        
        # Backup list
        list_frame = ttk.LabelFrame(parent, text="Available Backups", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Treeview for backups
        columns = ("Name", "Date", "Size", "Type")
        self.backup_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=8)
        
        for col in columns:
            self.backup_tree.heading(col, text=col)
            self.backup_tree.column(col, width=120)
        
        backup_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.backup_tree.yview)
        self.backup_tree.configure(yscrollcommand=backup_scrollbar.set)
        
        self.backup_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        backup_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Restore options
        restore_options_frame = ttk.LabelFrame(parent, text="Restore Options", padding="10")
        restore_options_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.restore_palettes_var = tk.BooleanVar(value=True)
        self.restore_settings_var = tk.BooleanVar(value=True)
        self.restore_history_var = tk.BooleanVar(value=True)
        
        ttk.Checkbutton(restore_options_frame, text="Restore Palettes", variable=self.restore_palettes_var).pack(anchor=tk.W)
        ttk.Checkbutton(restore_options_frame, text="Restore Settings", variable=self.restore_settings_var).pack(anchor=tk.W)
        ttk.Checkbutton(restore_options_frame, text="Restore History", variable=self.restore_history_var).pack(anchor=tk.W)
        
        # Progress bar
        self.restore_progress_frame = ttk.Frame(parent)
        self.restore_progress_label = ttk.Label(self.restore_progress_frame, text="Restoring backup...")
        self.restore_progress_bar = ttk.Progressbar(self.restore_progress_frame, mode='determinate')
        
        # Buttons
        restore_button_frame = ttk.Frame(parent)
        restore_button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(restore_button_frame, text="Restore Selected", command=self._restore_backup).pack(side=tk.LEFT)
        ttk.Button(restore_button_frame, text="Import Backup", command=self._import_backup).pack(side=tk.LEFT, padx=(10, 0))
        ttk.Button(restore_button_frame, text="Delete Selected", command=self._delete_backup).pack(side=tk.LEFT, padx=(10, 0))
        ttk.Button(restore_button_frame, text="Refresh", command=self._refresh_backup_list).pack(side=tk.RIGHT)
        
        # Load backup list
        self._refresh_backup_list()
    
    def _create_settings_tab(self, parent):
        """Create settings tab content."""
        import tkinter as tk
        from tkinter import ttk
        
        config = self.backup_manager.get_backup_config()
        
        # Auto backup settings
        auto_frame = ttk.LabelFrame(parent, text="Automatic Backup", padding="10")
        auto_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.auto_backup_var = tk.BooleanVar(value=config.get("auto_backup", True))
        self.backup_on_exit_var = tk.BooleanVar(value=config.get("backup_on_exit", True))
        
        ttk.Checkbutton(auto_frame, text="Enable automatic backups", variable=self.auto_backup_var).pack(anchor=tk.W)
        ttk.Checkbutton(auto_frame, text="Backup on application exit", variable=self.backup_on_exit_var).pack(anchor=tk.W)
        
        # Backup limits
        limits_frame = ttk.LabelFrame(parent, text="Backup Limits", padding="10")
        limits_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(limits_frame, text="Maximum backups to keep:").pack(anchor=tk.W)
        self.max_backups_var = tk.IntVar(value=config.get("max_backups", 10))
        ttk.Spinbox(limits_frame, from_=1, to=50, textvariable=self.max_backups_var, width=10).pack(anchor=tk.W, pady=(5, 0))
        
        # Statistics
        stats_frame = ttk.LabelFrame(parent, text="Backup Statistics", padding="10")
        stats_frame.pack(fill=tk.X, padx=10, pady=10)
        
        stats = self.backup_manager.get_backup_statistics()
        
        ttk.Label(stats_frame, text=f"Total backups: {stats['total_backups']}").pack(anchor=tk.W)
        ttk.Label(stats_frame, text=f"Total size: {stats['total_size'] / (1024*1024):.1f} MB").pack(anchor=tk.W)
        ttk.Label(stats_frame, text=f"Backup directory: {stats['backup_directory']}").pack(anchor=tk.W)
        
        # Save button
        ttk.Button(parent, text="Save Settings", command=self._save_settings).pack(pady=20)
    
    def _create_backup(self):
        """Create a new backup."""
        import threading
        
        # Show progress
        self.backup_progress_frame.pack(fill=tk.X, padx=10, pady=10)
        self.backup_progress_label.pack(anchor=tk.W)
        self.backup_progress_bar.pack(fill=tk.X, pady=(5, 0))
        
        def progress_callback(progress):
            self.backup_progress_bar['value'] = progress
            self.dialog.update_idletasks()
        
        def backup_thread():
            try:
                backup_name = self.backup_name_var.get().strip() or None
                include_cache = self.backup_cache_var.get()
                
                backup_path = self.backup_manager.create_backup(
                    backup_name=backup_name,
                    include_cache=include_cache,
                    progress_callback=progress_callback
                )
                
                self.backup_progress_frame.pack_forget()
                
                from tkinter import messagebox
                messagebox.showinfo("Backup Complete", f"Backup created successfully:\\n{backup_path}")
                
                # Refresh backup list if restore tab is visible
                self._refresh_backup_list()
                
            except Exception as e:
                self.backup_progress_frame.pack_forget()
                from tkinter import messagebox
                messagebox.showerror("Backup Failed", f"Failed to create backup:\\n{str(e)}")
        
        threading.Thread(target=backup_thread, daemon=True).start()
    
    def _restore_backup(self):
        """Restore selected backup."""
        selection = self.backup_tree.selection()
        if not selection:
            from tkinter import messagebox
            messagebox.showwarning("No Selection", "Please select a backup to restore.")
            return
        
        # Get selected backup path
        item = self.backup_tree.item(selection[0])
        backup_name = item['values'][0]
        backup_path = self.backup_manager.backup_dir / f"{backup_name}.zip"
        
        # Confirm restore
        from tkinter import messagebox
        if not messagebox.askyesno("Confirm Restore", 
                                  f"This will restore data from backup '{backup_name}'.\\n"
                                  "Current data will be backed up first.\\n\\n"
                                  "Continue?"):
            return
        
        # Show progress
        self.restore_progress_frame.pack(fill=tk.X, padx=10, pady=10)
        self.restore_progress_label.pack(anchor=tk.W)
        self.restore_progress_bar.pack(fill=tk.X, pady=(5, 0))
        
        def progress_callback(progress):
            self.restore_progress_bar['value'] = progress
            self.dialog.update_idletasks()
        
        def restore_thread():
            try:
                success = self.backup_manager.restore_backup(
                    backup_path=backup_path,
                    restore_palettes=self.restore_palettes_var.get(),
                    restore_settings=self.restore_settings_var.get(),
                    restore_history=self.restore_history_var.get(),
                    progress_callback=progress_callback
                )
                
                self.restore_progress_frame.pack_forget()
                
                if success:
                    messagebox.showinfo("Restore Complete", 
                                      "Backup restored successfully!\\n"
                                      "Please restart the application to see changes.")
                
            except Exception as e:
                self.restore_progress_frame.pack_forget()
                messagebox.showerror("Restore Failed", f"Failed to restore backup:\\n{str(e)}")
        
        import threading
        threading.Thread(target=restore_thread, daemon=True).start()
    
    def _refresh_backup_list(self):
        """Refresh the backup list."""
        # Clear existing items
        for item in self.backup_tree.get_children():
            self.backup_tree.delete(item)
        
        # Load backups
        backups = self.backup_manager.list_backups()
        
        for backup in backups:
            size_mb = backup["size"] / (1024 * 1024)
            date_str = backup["created"].strftime("%Y-%m-%d %H:%M")
            
            self.backup_tree.insert("", tk.END, values=(
                backup["name"],
                date_str,
                f"{size_mb:.1f} MB",
                backup["type"].title()
            ))
    
    def _export_backup(self):
        """Export selected backup."""
        from tkinter import filedialog, messagebox
        
        selection = self.backup_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a backup to export.")
            return
        
        # Get selected backup
        item = self.backup_tree.item(selection[0])
        backup_name = item['values'][0]
        backup_path = self.backup_manager.backup_dir / f"{backup_name}.zip"
        
        # Choose export location
        export_path = filedialog.asksaveasfilename(
            title="Export Backup",
            defaultextension=".zip",
            filetypes=[("Zip files", "*.zip"), ("All files", "*.*")],
            initialvalue=f"{backup_name}.zip"
        )
        
        if export_path:
            try:
                self.backup_manager.export_backup(backup_path, Path(export_path))
                messagebox.showinfo("Export Complete", f"Backup exported to:\\n{export_path}")
            except Exception as e:
                messagebox.showerror("Export Failed", f"Failed to export backup:\\n{str(e)}")
    
    def _import_backup(self):
        """Import external backup."""
        from tkinter import filedialog, messagebox
        
        backup_file = filedialog.askopenfilename(
            title="Import Backup",
            filetypes=[("Zip files", "*.zip"), ("All files", "*.*")]
        )
        
        if backup_file:
            try:
                imported_path = self.backup_manager.import_backup(Path(backup_file))
                messagebox.showinfo("Import Complete", f"Backup imported successfully:\\n{imported_path}")
                self._refresh_backup_list()
            except Exception as e:
                messagebox.showerror("Import Failed", f"Failed to import backup:\\n{str(e)}")
    
    def _delete_backup(self):
        """Delete selected backup."""
        from tkinter import messagebox
        
        selection = self.backup_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a backup to delete.")
            return
        
        # Get selected backup
        item = self.backup_tree.item(selection[0])
        backup_name = item['values'][0]
        backup_path = self.backup_manager.backup_dir / f"{backup_name}.zip"
        
        # Confirm deletion
        if messagebox.askyesno("Confirm Delete", f"Delete backup '{backup_name}'?\\n\\nThis cannot be undone."):
            try:
                self.backup_manager.delete_backup(backup_path)
                messagebox.showinfo("Delete Complete", "Backup deleted successfully.")
                self._refresh_backup_list()
            except Exception as e:
                messagebox.showerror("Delete Failed", f"Failed to delete backup:\\n{str(e)}")
    
    def _save_settings(self):
        """Save backup settings."""
        config_updates = {
            "auto_backup": self.auto_backup_var.get(),
            "backup_on_exit": self.backup_on_exit_var.get(),
            "max_backups": self.max_backups_var.get()
        }
        
        self.backup_manager.update_backup_config(config_updates)
        
        from tkinter import messagebox
        messagebox.showinfo("Settings Saved", "Backup settings saved successfully.")