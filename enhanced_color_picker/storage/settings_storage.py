"""
Settings storage system for Enhanced Color Picker.

This module provides persistent storage for user settings with JSON format,
validation, migration support, and change notifications through the event bus.
"""

import json
import os
import shutil
import threading
from pathlib import Path
from typing import Any, Dict, Optional, Callable, List
from datetime import datetime
import logging

from ..models.app_settings import AppSettings
from ..core.event_bus import EventBus, get_global_event_bus
from ..core.exceptions import ColorPickerError


class SettingsStorageError(ColorPickerError):
    """Raised when settings storage operations fail."""
    pass


class SettingsMigrationError(SettingsStorageError):
    """Raised when settings migration fails."""
    pass


class SettingsStorage:
    """
    Manages persistent storage of application settings.
    
    Features:
    - JSON-based storage with human-readable format
    - Automatic backup creation before changes
    - Settings validation and migration support
    - Change notifications through event bus
    - Thread-safe operations
    - Default settings fallback mechanism
    """
    
    # Current settings version for migration support
    CURRENT_VERSION = "1.0.0"
    
    def __init__(self, settings_dir: Optional[Path] = None, 
                 event_bus: Optional[EventBus] = None,
                 auto_save: bool = True,
                 backup_count: int = 5):
        """
        Initialize settings storage.
        
        Args:
            settings_dir: Directory to store settings files (default: user config dir)
            event_bus: Event bus for change notifications
            auto_save: Enable automatic saving on changes
            backup_count: Number of backup files to keep
        """
        self._settings_dir = settings_dir or self._get_default_settings_dir()
        self._event_bus = event_bus or get_global_event_bus()
        self._auto_save = auto_save
        self._backup_count = backup_count
        self._lock = threading.RLock()
        self._logger = logging.getLogger(__name__)
        
        # Current settings instance
        self._current_settings: Optional[AppSettings] = None
        
        # Settings file paths
        self._settings_file = self._settings_dir / "settings.json"
        self._backup_dir = self._settings_dir / "backups"
        
        # Migration handlers
        self._migration_handlers: Dict[str, Callable[[Dict], Dict]] = {
            "0.9.0": self._migrate_from_0_9_0,
            "1.0.0": self._migrate_from_1_0_0,
        }
        
        # Ensure directories exist
        self._ensure_directories()
        
        # Load settings on initialization
        self._load_settings()
    
    def _get_default_settings_dir(self) -> Path:
        """Get the default settings directory based on the operating system."""
        if os.name == 'nt':  # Windows
            base_dir = Path(os.environ.get('APPDATA', Path.home() / 'AppData' / 'Roaming'))
        elif os.name == 'posix':  # Linux/macOS
            if 'XDG_CONFIG_HOME' in os.environ:
                base_dir = Path(os.environ['XDG_CONFIG_HOME'])
            else:
                base_dir = Path.home() / '.config'
        else:
            base_dir = Path.home() / '.enhanced_color_picker'
        
        return base_dir / 'enhanced_color_picker'
    
    def _ensure_directories(self) -> None:
        """Ensure settings and backup directories exist."""
        try:
            self._settings_dir.mkdir(parents=True, exist_ok=True)
            self._backup_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise SettingsStorageError(f"Failed to create settings directory: {e}")
    
    def _load_settings(self) -> None:
        """Load settings from file or create defaults."""
        try:
            if self._settings_file.exists():
                self._current_settings = self._load_from_file()
            else:
                self._current_settings = AppSettings()
                self._save_to_file(self._current_settings)
                self._logger.info("Created default settings file")
        except Exception as e:
            self._logger.error(f"Failed to load settings: {e}")
            self._current_settings = AppSettings()
    
    def _load_from_file(self) -> AppSettings:
        """Load settings from JSON file with migration support."""
        try:
            with open(self._settings_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Check if migration is needed
            file_version = data.get('_version', '0.9.0')
            if file_version != self.CURRENT_VERSION:
                data = self._migrate_settings(data, file_version)
            
            # Remove metadata fields
            settings_data = {k: v for k, v in data.items() if not k.startswith('_')}
            
            return AppSettings.from_dict(settings_data)
            
        except json.JSONDecodeError as e:
            raise SettingsStorageError(f"Invalid JSON in settings file: {e}")
        except Exception as e:
            raise SettingsStorageError(f"Failed to load settings: {e}")
    
    def _migrate_settings(self, data: Dict[str, Any], from_version: str) -> Dict[str, Any]:
        """
        Migrate settings from older version to current version.
        
        Args:
            data: Settings data to migrate
            from_version: Version to migrate from
            
        Returns:
            Dict[str, Any]: Migrated settings data
        """
        self._logger.info(f"Migrating settings from version {from_version} to {self.CURRENT_VERSION}")
        
        # Create backup before migration
        self._create_backup(f"pre_migration_{from_version}")
        
        try:
            # Apply migration handlers in sequence
            current_data = data.copy()
            
            # Get all versions between from_version and current
            versions_to_migrate = self._get_migration_path(from_version, self.CURRENT_VERSION)
            
            for version in versions_to_migrate:
                if version in self._migration_handlers:
                    current_data = self._migration_handlers[version](current_data)
                    self._logger.debug(f"Applied migration for version {version}")
            
            # Update version
            current_data['_version'] = self.CURRENT_VERSION
            current_data['_migrated_at'] = datetime.now().isoformat()
            current_data['_migrated_from'] = from_version
            
            # Save migrated settings
            with open(self._settings_file, 'w', encoding='utf-8') as f:
                json.dump(current_data, f, indent=2, ensure_ascii=False)
            
            self._logger.info(f"Settings migration completed successfully")
            return current_data
            
        except Exception as e:
            raise SettingsMigrationError(f"Settings migration failed: {e}")
    
    def _get_migration_path(self, from_version: str, to_version: str) -> List[str]:
        """Get the list of versions to migrate through."""
        # For now, simple version comparison
        # In a real implementation, you'd have proper version parsing
        available_versions = sorted(self._migration_handlers.keys())
        
        # Find versions between from_version and to_version
        migration_path = []
        for version in available_versions:
            if version > from_version and version <= to_version:
                migration_path.append(version)
        
        return migration_path
    
    def _migrate_from_0_9_0(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate settings from version 0.9.0."""
        # Example migration: rename old field names
        migrated = data.copy()
        
        # Rename old fields if they exist
        if 'color_format' in migrated:
            migrated['default_color_format'] = migrated.pop('color_format')
        
        if 'max_history' in migrated:
            migrated['max_history_items'] = migrated.pop('max_history')
        
        # Add new fields with defaults
        migrated.setdefault('enable_pixel_grid', True)
        migrated.setdefault('pixel_grid_threshold', 8.0)
        migrated.setdefault('high_contrast_mode', False)
        
        return migrated
    
    def _migrate_from_1_0_0(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate settings from version 1.0.0 (no changes needed)."""
        return data
    
    def _save_to_file(self, settings: AppSettings) -> None:
        """Save settings to JSON file."""
        try:
            # Create backup before saving
            if self._settings_file.exists():
                self._create_backup()
            
            # Prepare data for saving
            data = settings.to_dict()
            data['_version'] = self.CURRENT_VERSION
            data['_saved_at'] = datetime.now().isoformat()
            
            # Write to temporary file first, then rename (atomic operation)
            temp_file = self._settings_file.with_suffix('.tmp')
            
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Atomic rename
            temp_file.replace(self._settings_file)
            
            self._logger.debug("Settings saved successfully")
            
        except Exception as e:
            # Clean up temp file if it exists
            temp_file = self._settings_file.with_suffix('.tmp')
            if temp_file.exists():
                temp_file.unlink()
            
            raise SettingsStorageError(f"Failed to save settings: {e}")
    
    def _create_backup(self, suffix: str = None) -> None:
        """Create a backup of the current settings file."""
        if not self._settings_file.exists():
            return
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"settings_{timestamp}"
            
            if suffix:
                backup_name += f"_{suffix}"
            
            backup_name += ".json"
            backup_path = self._backup_dir / backup_name
            
            shutil.copy2(self._settings_file, backup_path)
            
            # Clean up old backups
            self._cleanup_old_backups()
            
            self._logger.debug(f"Created settings backup: {backup_name}")
            
        except Exception as e:
            self._logger.warning(f"Failed to create settings backup: {e}")
    
    def _cleanup_old_backups(self) -> None:
        """Remove old backup files, keeping only the most recent ones."""
        try:
            backup_files = list(self._backup_dir.glob("settings_*.json"))
            backup_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            
            # Remove excess backups
            for backup_file in backup_files[self._backup_count:]:
                backup_file.unlink()
                self._logger.debug(f"Removed old backup: {backup_file.name}")
                
        except Exception as e:
            self._logger.warning(f"Failed to cleanup old backups: {e}")
    
    def get_settings(self) -> AppSettings:
        """
        Get the current settings.
        
        Returns:
            AppSettings: Current application settings
        """
        with self._lock:
            if self._current_settings is None:
                self._load_settings()
            return self._current_settings.copy()
    
    def save_settings(self, settings: AppSettings) -> None:
        """
        Save settings to persistent storage.
        
        Args:
            settings: Settings to save
            
        Raises:
            SettingsStorageError: If saving fails
        """
        with self._lock:
            # Validate settings
            settings._validate_settings()
            
            # Save to file
            self._save_to_file(settings)
            
            # Update current settings
            old_settings = self._current_settings
            self._current_settings = settings.copy()
            
            # Publish change event
            self._event_bus.publish(
                'settings_changed',
                {
                    'old_settings': old_settings.to_dict() if old_settings else None,
                    'new_settings': settings.to_dict(),
                    'timestamp': datetime.now().isoformat()
                },
                source='settings_storage'
            )
    
    def update_setting(self, key: str, value: Any) -> None:
        """
        Update a single setting value.
        
        Args:
            key: Setting key to update
            value: New value for the setting
        """
        with self._lock:
            current = self.get_settings()
            old_value = current.get_setting(key)
            
            current.set_setting(key, value)
            
            if self._auto_save:
                self.save_settings(current)
            else:
                self._current_settings = current
            
            # Publish specific setting change event
            self._event_bus.publish(
                'setting_changed',
                {
                    'key': key,
                    'old_value': old_value,
                    'new_value': value,
                    'timestamp': datetime.now().isoformat()
                },
                source='settings_storage'
            )
    
    def reset_to_defaults(self) -> None:
        """Reset all settings to default values."""
        with self._lock:
            # Create backup before reset
            self._create_backup("before_reset")
            
            default_settings = AppSettings()
            self.save_settings(default_settings)
            
            self._event_bus.publish(
                'settings_reset',
                {
                    'timestamp': datetime.now().isoformat()
                },
                source='settings_storage'
            )
    
    def export_settings(self, file_path: Path) -> None:
        """
        Export settings to a file.
        
        Args:
            file_path: Path to export settings to
        """
        try:
            settings = self.get_settings()
            data = settings.to_dict()
            data['_exported_at'] = datetime.now().isoformat()
            data['_version'] = self.CURRENT_VERSION
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            self._logger.info(f"Settings exported to: {file_path}")
            
        except Exception as e:
            raise SettingsStorageError(f"Failed to export settings: {e}")
    
    def import_settings(self, file_path: Path) -> None:
        """
        Import settings from a file.
        
        Args:
            file_path: Path to import settings from
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Remove metadata fields
            settings_data = {k: v for k, v in data.items() if not k.startswith('_')}
            
            # Create settings object and validate
            imported_settings = AppSettings.from_dict(settings_data)
            
            # Create backup before import
            self._create_backup("before_import")
            
            # Save imported settings
            self.save_settings(imported_settings)
            
            self._logger.info(f"Settings imported from: {file_path}")
            
        except Exception as e:
            raise SettingsStorageError(f"Failed to import settings: {e}")
    
    def get_backup_files(self) -> List[Path]:
        """
        Get list of available backup files.
        
        Returns:
            List[Path]: List of backup file paths, sorted by modification time (newest first)
        """
        try:
            backup_files = list(self._backup_dir.glob("settings_*.json"))
            backup_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            return backup_files
        except Exception as e:
            self._logger.warning(f"Failed to get backup files: {e}")
            return []
    
    def restore_from_backup(self, backup_path: Path) -> None:
        """
        Restore settings from a backup file.
        
        Args:
            backup_path: Path to backup file to restore from
        """
        try:
            # Create backup of current settings before restore
            self._create_backup("before_restore")
            
            # Load backup file
            with open(backup_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Check if migration is needed
            file_version = data.get('_version', '0.9.0')
            if file_version != self.CURRENT_VERSION:
                data = self._migrate_settings(data, file_version)
            
            # Remove metadata fields
            settings_data = {k: v for k, v in data.items() if not k.startswith('_')}
            
            # Create and save settings
            restored_settings = AppSettings.from_dict(settings_data)
            self.save_settings(restored_settings)
            
            self._logger.info(f"Settings restored from backup: {backup_path.name}")
            
        except Exception as e:
            raise SettingsStorageError(f"Failed to restore from backup: {e}")
    
    def get_settings_info(self) -> Dict[str, Any]:
        """
        Get information about the settings storage.
        
        Returns:
            Dict[str, Any]: Settings storage information
        """
        info = {
            'settings_file': str(self._settings_file),
            'settings_dir': str(self._settings_dir),
            'backup_dir': str(self._backup_dir),
            'backup_count': self._backup_count,
            'auto_save': self._auto_save,
            'current_version': self.CURRENT_VERSION,
            'file_exists': self._settings_file.exists(),
        }
        
        if self._settings_file.exists():
            stat = self._settings_file.stat()
            info.update({
                'file_size': stat.st_size,
                'last_modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            })
        
        # Backup information
        backup_files = self.get_backup_files()
        info['backup_files'] = [
            {
                'name': f.name,
                'size': f.stat().st_size,
                'modified': datetime.fromtimestamp(f.stat().st_mtime).isoformat()
            }
            for f in backup_files
        ]
        
        return info
    
    def cleanup(self) -> None:
        """Clean up resources and perform maintenance."""
        with self._lock:
            self._cleanup_old_backups()
            self._logger.debug("Settings storage cleanup completed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()


# Global settings storage instance
_global_settings_storage: Optional[SettingsStorage] = None


def get_global_settings_storage() -> SettingsStorage:
    """
    Get the global settings storage instance.
    
    Returns:
        SettingsStorage: Global settings storage instance
    """
    global _global_settings_storage
    if _global_settings_storage is None:
        _global_settings_storage = SettingsStorage()
    return _global_settings_storage


def set_global_settings_storage(storage: SettingsStorage) -> None:
    """
    Set the global settings storage instance.
    
    Args:
        storage: SettingsStorage instance to use as global
    """
    global _global_settings_storage
    _global_settings_storage = storage