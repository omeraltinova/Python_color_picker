"""
Enhanced Color Picker - Secure Configuration Manager

This module provides secure configuration management with safe defaults,
input sanitization, and security validation.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
import tempfile
import shutil
from dataclasses import dataclass, asdict
from enum import Enum

from .exceptions import ValidationError, FileOperationError
from ..utils.validation_utils import get_file_validator, get_input_validator
from ..models.enums import ColorFormat


class ConfigSecurity(Enum):
    """Configuration security levels"""
    STRICT = "strict"      # Maximum security, minimal features
    BALANCED = "balanced"  # Balance between security and functionality
    PERMISSIVE = "permissive"  # More features, reduced security


@dataclass
class SecuritySettings:
    """Security-related configuration settings"""
    max_file_size_mb: int = 100
    max_memory_mb: int = 1024
    allow_network_access: bool = False
    enable_file_validation: bool = True
    security_level: ConfigSecurity = ConfigSecurity.BALANCED
    allowed_directories: List[str] = None
    
    def __post_init__(self):
        if self.allowed_directories is None:
            self.allowed_directories = [
                str(Path.home()),
                str(Path.cwd()),
                str(tempfile.gettempdir())
            ]


@dataclass
class AppConfiguration:
    """Main application configuration with secure defaults"""
    
    # UI Settings
    theme: str = "dark"
    language: str = "en"
    window_width: int = 1200
    window_height: int = 800
    window_maximized: bool = False
    
    # Color Settings
    default_color_format: ColorFormat = ColorFormat.HEX
    show_alpha_channel: bool = True
    precision_digits: int = 2
    
    # Palette Settings
    auto_save_palettes: bool = True
    max_palette_colors: int = 100
    palette_backup_count: int = 5
    
    # History Settings
    max_history_items: int = 50
    save_history_on_exit: bool = True
    
    # Performance Settings
    zoom_sensitivity: float = 1.1
    enable_pixel_grid: bool = True
    pixel_grid_threshold: float = 8.0
    cache_size_mb: int = 100
    max_image_size_mb: int = 50
    
    # Security Settings
    security: SecuritySettings = None
    
    def __post_init__(self):
        if self.security is None:
            self.security = SecuritySettings()
            
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        config_dict = asdict(self)
        # Convert enums to their values
        config_dict['default_color_format'] = self.default_color_format.value
        config_dict['security']['security_level'] = self.security.security_level.value
        return config_dict
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AppConfiguration':
        """Create configuration from dictionary"""
        # Handle enum conversions
        if 'default_color_format' in data:
            data['default_color_format'] = ColorFormat(data['default_color_format'])
            
        if 'security' in data and 'security_level' in data['security']:
            data['security']['security_level'] = ConfigSecurity(data['security']['security_level'])
            
        # Create security settings if not present
        if 'security' not in data:
            data['security'] = SecuritySettings()
        elif isinstance(data['security'], dict):
            data['security'] = SecuritySettings(**data['security'])
            
        return cls(**data)


class SecureConfigManager:
    """
    Secure configuration manager with validation and safe defaults.
    
    Provides secure loading, saving, and validation of application configuration
    with protection against malicious configuration files.
    """
    
    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or self._get_default_config_dir()
        self.config_file = self.config_dir / "config.json"
        self.backup_dir = self.config_dir / "backups"
        
        self.file_validator = get_file_validator()
        self.input_validator = get_input_validator()
        
        # Ensure directories exist
        self._ensure_directories()
        
        # Load or create configuration
        self.config = self._load_or_create_config()
        
    def _get_default_config_dir(self) -> Path:
        """Get default configuration directory"""
        if os.name == 'nt':  # Windows
            config_dir = Path(os.environ.get('APPDATA', Path.home())) / "EnhancedColorPicker"
        else:  # Unix-like
            config_dir = Path.home() / ".config" / "enhanced_color_picker"
            
        return config_dir
        
    def _ensure_directories(self):
        """Ensure configuration directories exist"""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Set appropriate permissions (Unix-like systems)
            if os.name != 'nt':
                os.chmod(self.config_dir, 0o700)  # Owner read/write/execute only
                os.chmod(self.backup_dir, 0o700)
                
        except Exception as e:
            raise FileOperationError(
                "directory_creation",
                str(self.config_dir),
                f"Failed to create configuration directory: {e}"
            )
            
    def _load_or_create_config(self) -> AppConfiguration:
        """Load existing configuration or create default"""
        if self.config_file.exists():
            try:
                return self._load_config()
            except Exception as e:
                # If loading fails, backup the corrupted file and create new
                self._backup_corrupted_config()
                return self._create_default_config()
        else:
            return self._create_default_config()
            
    def _load_config(self) -> AppConfiguration:
        """Load configuration from file with validation"""
        # Validate file before loading
        validation_result = self.file_validator.validate_config_file(self.config_file)
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                
            # Validate configuration data
            validated_data = self._validate_config_data(config_data)
            
            return AppConfiguration.from_dict(validated_data)
            
        except json.JSONDecodeError as e:
            raise ValidationError(
                "config_json",
                str(self.config_file),
                f"Invalid JSON in configuration file: {e}"
            )
        except Exception as e:
            raise FileOperationError(
                "config_load",
                str(self.config_file),
                f"Failed to load configuration: {e}"
            )
            
    def _create_default_config(self) -> AppConfiguration:
        """Create default configuration"""
        config = AppConfiguration()
        
        # Apply security-based defaults
        if config.security.security_level == ConfigSecurity.STRICT:
            config.max_image_size_mb = 10
            config.cache_size_mb = 50
            config.security.max_file_size_mb = 10
            config.security.max_memory_mb = 512
            config.security.allow_network_access = False
        elif config.security.security_level == ConfigSecurity.PERMISSIVE:
            config.max_image_size_mb = 200
            config.cache_size_mb = 500
            config.security.max_file_size_mb = 200
            config.security.max_memory_mb = 2048
            config.security.allow_network_access = True
            
        # Save default configuration
        self.save_config(config)
        
        return config
        
    def _validate_config_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate configuration data and apply safe defaults"""
        validated = {}
        defaults = AppConfiguration()
        
        # Validate each field with safe defaults
        validated['theme'] = self._validate_theme(data.get('theme', defaults.theme))
        validated['language'] = self._validate_language(data.get('language', defaults.language))
        
        # Window settings
        validated['window_width'] = self._validate_dimension(
            data.get('window_width', defaults.window_width), 400, 4000
        )
        validated['window_height'] = self._validate_dimension(
            data.get('window_height', defaults.window_height), 300, 3000
        )
        validated['window_maximized'] = bool(data.get('window_maximized', defaults.window_maximized))
        
        # Color settings
        validated['default_color_format'] = self._validate_color_format(
            data.get('default_color_format', defaults.default_color_format.value)
        )
        validated['show_alpha_channel'] = bool(data.get('show_alpha_channel', defaults.show_alpha_channel))
        validated['precision_digits'] = self._validate_range(
            data.get('precision_digits', defaults.precision_digits), 0, 10
        )
        
        # Palette settings
        validated['auto_save_palettes'] = bool(data.get('auto_save_palettes', defaults.auto_save_palettes))
        validated['max_palette_colors'] = self._validate_range(
            data.get('max_palette_colors', defaults.max_palette_colors), 1, 10000
        )
        validated['palette_backup_count'] = self._validate_range(
            data.get('palette_backup_count', defaults.palette_backup_count), 0, 50
        )
        
        # History settings
        validated['max_history_items'] = self._validate_range(
            data.get('max_history_items', defaults.max_history_items), 0, 1000
        )
        validated['save_history_on_exit'] = bool(data.get('save_history_on_exit', defaults.save_history_on_exit))
        
        # Performance settings
        validated['zoom_sensitivity'] = self._validate_range(
            data.get('zoom_sensitivity', defaults.zoom_sensitivity), 1.01, 3.0
        )
        validated['enable_pixel_grid'] = bool(data.get('enable_pixel_grid', defaults.enable_pixel_grid))
        validated['pixel_grid_threshold'] = self._validate_range(
            data.get('pixel_grid_threshold', defaults.pixel_grid_threshold), 1.0, 50.0
        )
        validated['cache_size_mb'] = self._validate_range(
            data.get('cache_size_mb', defaults.cache_size_mb), 10, 2000
        )
        validated['max_image_size_mb'] = self._validate_range(
            data.get('max_image_size_mb', defaults.max_image_size_mb), 1, 500
        )
        
        # Security settings
        security_data = data.get('security', {})
        validated['security'] = self._validate_security_settings(security_data, defaults.security)
        
        return validated
        
    def _validate_theme(self, theme: Any) -> str:
        """Validate theme setting"""
        valid_themes = {'light', 'dark', 'auto'}
        if isinstance(theme, str) and theme in valid_themes:
            return theme
        return 'dark'  # Safe default
        
    def _validate_language(self, language: Any) -> str:
        """Validate language setting"""
        valid_languages = {'en', 'tr'}
        if isinstance(language, str) and language in valid_languages:
            return language
        return 'en'  # Safe default
        
    def _validate_dimension(self, value: Any, min_val: int, max_val: int) -> int:
        """Validate window dimension"""
        if isinstance(value, (int, float)) and min_val <= value <= max_val:
            return int(value)
        return min_val  # Safe default
        
    def _validate_color_format(self, format_value: Any) -> ColorFormat:
        """Validate color format setting"""
        if isinstance(format_value, str):
            try:
                return ColorFormat(format_value)
            except ValueError:
                pass
        return ColorFormat.HEX  # Safe default
        
    def _validate_range(self, value: Any, min_val: Union[int, float], max_val: Union[int, float]) -> Union[int, float]:
        """Validate numeric value within range"""
        if isinstance(value, (int, float)) and min_val <= value <= max_val:
            return type(min_val)(value)  # Return same type as min_val
        return min_val  # Safe default
        
    def _validate_security_settings(self, security_data: Dict[str, Any], defaults: SecuritySettings) -> Dict[str, Any]:
        """Validate security settings"""
        validated = {}
        
        validated['max_file_size_mb'] = self._validate_range(
            security_data.get('max_file_size_mb', defaults.max_file_size_mb), 1, 1000
        )
        validated['max_memory_mb'] = self._validate_range(
            security_data.get('max_memory_mb', defaults.max_memory_mb), 128, 8192
        )
        validated['allow_network_access'] = bool(
            security_data.get('allow_network_access', defaults.allow_network_access)
        )
        validated['enable_file_validation'] = bool(
            security_data.get('enable_file_validation', defaults.enable_file_validation)
        )
        
        # Validate security level
        security_level = security_data.get('security_level', defaults.security_level.value)
        try:
            validated['security_level'] = ConfigSecurity(security_level)
        except ValueError:
            validated['security_level'] = ConfigSecurity.BALANCED
            
        # Validate allowed directories
        allowed_dirs = security_data.get('allowed_directories', defaults.allowed_directories)
        if isinstance(allowed_dirs, list):
            validated['allowed_directories'] = [
                str(Path(d).resolve()) for d in allowed_dirs 
                if isinstance(d, (str, Path)) and Path(d).exists()
            ]
        else:
            validated['allowed_directories'] = defaults.allowed_directories
            
        return validated
        
    def save_config(self, config: Optional[AppConfiguration] = None):
        """Save configuration to file with backup"""
        if config is None:
            config = self.config
            
        # Create backup if file exists
        if self.config_file.exists():
            self._create_backup()
            
        # Write configuration atomically
        temp_file = self.config_file.with_suffix('.tmp')
        
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(config.to_dict(), f, indent=2, ensure_ascii=False)
                
            # Atomic move
            shutil.move(str(temp_file), str(self.config_file))
            
            # Set appropriate permissions
            if os.name != 'nt':
                os.chmod(self.config_file, 0o600)  # Owner read/write only
                
            self.config = config
            
        except Exception as e:
            # Clean up temp file if it exists
            if temp_file.exists():
                temp_file.unlink()
                
            raise FileOperationError(
                "config_save",
                str(self.config_file),
                f"Failed to save configuration: {e}"
            )
            
    def _create_backup(self):
        """Create backup of current configuration"""
        if not self.config_file.exists():
            return
            
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"config_backup_{timestamp}.json"
        
        try:
            shutil.copy2(self.config_file, backup_file)
            
            # Clean up old backups (keep only the most recent ones)
            self._cleanup_old_backups()
            
        except Exception as e:
            # Backup failure shouldn't prevent saving new config
            pass
            
    def _backup_corrupted_config(self):
        """Backup corrupted configuration file"""
        if not self.config_file.exists():
            return
            
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        corrupted_file = self.backup_dir / f"config_corrupted_{timestamp}.json"
        
        try:
            shutil.move(str(self.config_file), str(corrupted_file))
        except Exception:
            pass
            
    def _cleanup_old_backups(self):
        """Clean up old backup files"""
        try:
            backup_files = list(self.backup_dir.glob("config_backup_*.json"))
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Keep only the most recent backups
            max_backups = self.config.palette_backup_count
            for old_backup in backup_files[max_backups:]:
                old_backup.unlink()
                
        except Exception:
            pass
            
    def get_config(self) -> AppConfiguration:
        """Get current configuration"""
        return self.config
        
    def update_config(self, **kwargs):
        """Update configuration with new values"""
        config_dict = self.config.to_dict()
        config_dict.update(kwargs)
        
        # Validate updated configuration
        validated_data = self._validate_config_data(config_dict)
        new_config = AppConfiguration.from_dict(validated_data)
        
        self.save_config(new_config)
        
    def reset_to_defaults(self):
        """Reset configuration to safe defaults"""
        self.config = self._create_default_config()
        
    def is_path_allowed(self, file_path: Union[str, Path]) -> bool:
        """Check if file path is in allowed directories"""
        file_path = Path(file_path).resolve()
        
        for allowed_dir in self.config.security.allowed_directories:
            try:
                allowed_path = Path(allowed_dir).resolve()
                if file_path.is_relative_to(allowed_path):
                    return True
            except (ValueError, OSError):
                continue
                
        return False
        
    def get_safe_temp_dir(self) -> Path:
        """Get safe temporary directory for file operations"""
        temp_dir = self.config_dir / "temp"
        temp_dir.mkdir(exist_ok=True)
        
        if os.name != 'nt':
            os.chmod(temp_dir, 0o700)
            
        return temp_dir


# Global configuration manager instance
_config_manager: Optional[SecureConfigManager] = None


def get_config_manager() -> SecureConfigManager:
    """Get global configuration manager instance"""
    global _config_manager
    if _config_manager is None:
        _config_manager = SecureConfigManager()
    return _config_manager


def initialize_config_manager(config_dir: Optional[Path] = None):
    """Initialize global configuration manager"""
    global _config_manager
    _config_manager = SecureConfigManager(config_dir)