"""
Configuration management system for Enhanced Color Picker.

This module provides centralized configuration management with support for
default values, validation, persistence, and environment-specific overrides.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union, List
from dataclasses import dataclass, asdict, field
from enum import Enum

from .exceptions import ConfigurationError, ValidationError


class ColorFormat(Enum):
    """Supported color formats."""
    RGB = "rgb"
    HEX = "hex"
    HSL = "hsl"
    HSV = "hsv"
    CMYK = "cmyk"


class Theme(Enum):
    """Available themes."""
    DARK = "dark"
    LIGHT = "light"
    AUTO = "auto"


class Language(Enum):
    """Supported languages."""
    TURKISH = "tr"
    ENGLISH = "en"


@dataclass
class UISettings:
    """UI-related configuration settings."""
    theme: Theme = Theme.DARK
    language: Language = Language.TURKISH
    window_width: int = 1200
    window_height: int = 800
    window_maximized: bool = False
    panel_width: int = 360
    enable_tooltips: bool = True
    show_coordinates: bool = True


@dataclass
class PerformanceSettings:
    """Performance-related configuration settings."""
    enable_profiling: bool = True
    enable_auto_optimization: bool = True
    image_cache_size: int = 100 * 1024 * 1024  # 100MB
    max_workers: int = 4
    optimization_interval: int = 300  # 5 minutes
    memory_warning_threshold: int = 80  # 80%
    memory_critical_threshold: int = 90  # 90%
    cpu_warning_threshold: int = 80  # 80%
    function_time_warning: float = 0.1  # 100ms
    function_time_critical: float = 0.5  # 500ms
    ui_freeze_threshold: float = 0.05  # 50ms
    enable_memory_monitoring: bool = True
    enable_cpu_monitoring: bool = True
    gc_threshold_multiplier: float = 1.5
    show_zoom_info: bool = True


@dataclass
class ColorSettings:
    """Color-related configuration settings."""
    default_format: ColorFormat = ColorFormat.HEX
    copy_format: ColorFormat = ColorFormat.HEX
    show_all_formats: bool = True
    enable_color_history: bool = True
    max_history_items: int = 50
    enable_favorites: bool = True
    max_favorite_items: int = 100


@dataclass
class ImageSettings:
    """Image processing configuration settings."""
    max_image_size: int = 50 * 1024 * 1024  # 50MB
    supported_formats: List[str] = field(default_factory=lambda: [
        ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp", ".svg"
    ])
    enable_image_cache: bool = True
    cache_size_mb: int = 100
    zoom_sensitivity: float = 1.1
    min_zoom: float = 0.1
    max_zoom: float = 10.0
    enable_pixel_grid: bool = True
    pixel_grid_threshold: float = 8.0



@dataclass
class AccessibilitySettings:
    """Accessibility configuration settings."""
    enable_wcag_checking: bool = True
    enable_color_blindness_simulation: bool = True
    high_contrast_mode: bool = False
    large_fonts: bool = False
    keyboard_navigation: bool = True
    screen_reader_support: bool = True


@dataclass
class ExportSettings:
    """Export-related configuration settings."""
    default_export_format: str = "json"
    include_metadata: bool = True
    compress_exports: bool = False
    export_directory: Optional[str] = None


@dataclass
class AppConfig:
    """Main application configuration."""
    ui: UISettings = field(default_factory=UISettings)
    color: ColorSettings = field(default_factory=ColorSettings)
    image: ImageSettings = field(default_factory=ImageSettings)
    performance: PerformanceSettings = field(default_factory=PerformanceSettings)
    accessibility: AccessibilitySettings = field(default_factory=AccessibilitySettings)
    export: ExportSettings = field(default_factory=ExportSettings)
    
    # Application metadata
    version: str = "1.0.0"
    first_run: bool = True
    last_update_check: Optional[str] = None


class Config:
    """
    Configuration manager for Enhanced Color Picker.
    
    This class handles loading, saving, and managing application configuration
    with support for validation, defaults, and environment-specific overrides.
    """
    
    def __init__(self, config_dir: Optional[Union[str, Path]] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_dir: Directory to store configuration files.
                       If None, uses default user config directory.
        """
        self._config_dir = self._get_config_directory(config_dir)
        self._config_file = self._config_dir / "config.json"
        self._backup_file = self._config_dir / "config.backup.json"
        
        # Initialize with default configuration
        self._config = AppConfig()
        
        # Ensure config directory exists
        self._config_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing configuration
        self.load()
    
    def _get_config_directory(self, config_dir: Optional[Union[str, Path]]) -> Path:
        """Get the configuration directory path."""
        if config_dir:
            return Path(config_dir)
        
        # Use platform-appropriate config directory
        if os.name == 'nt':  # Windows
            config_base = Path(os.environ.get('APPDATA', Path.home() / 'AppData' / 'Roaming'))
        else:  # Unix-like systems
            config_base = Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config'))
        
        return config_base / 'enhanced_color_picker'
    
    def load(self) -> None:
        """
        Load configuration from file.
        
        Raises:
            ConfigurationError: If configuration loading fails
        """
        try:
            if self._config_file.exists():
                with open(self._config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # Validate and merge with defaults
                self._config = self._merge_config(config_data)
                self._validate_config()
            else:
                # First run - save default configuration
                self.save()
                
        except json.JSONDecodeError as e:
            raise ConfigurationError(
                f"Invalid JSON in configuration file: {e}",
                config_key="json_format"
            )
        except Exception as e:
            raise ConfigurationError(
                f"Failed to load configuration: {e}",
                details=str(e)
            )
    
    def save(self) -> None:
        """
        Save configuration to file.
        
        Raises:
            ConfigurationError: If configuration saving fails
        """
        try:
            # Create backup of existing config
            if self._config_file.exists():
                self._config_file.rename(self._backup_file)
            
            # Save current configuration
            config_data = self._serialize_config()
            with open(self._config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            # Remove backup on successful save
            if self._backup_file.exists():
                self._backup_file.unlink()
                
        except Exception as e:
            # Restore backup if save failed
            if self._backup_file.exists():
                self._backup_file.rename(self._config_file)
            
            raise ConfigurationError(
                f"Failed to save configuration: {e}",
                details=str(e)
            )
    
    def _merge_config(self, config_data: Dict[str, Any]) -> AppConfig:
        """
        Merge loaded configuration with defaults.
        
        Args:
            config_data: Configuration data from file
            
        Returns:
            AppConfig: Merged configuration
        """
        try:
            # Start with default config
            merged_config = AppConfig()
            
            # Update with loaded data
            if 'ui' in config_data:
                ui_data = config_data['ui']
                merged_config.ui = UISettings(
                    theme=Theme(ui_data.get('theme', merged_config.ui.theme.value)),
                    language=Language(ui_data.get('language', merged_config.ui.language.value)),
                    window_width=ui_data.get('window_width', merged_config.ui.window_width),
                    window_height=ui_data.get('window_height', merged_config.ui.window_height),
                    window_maximized=ui_data.get('window_maximized', merged_config.ui.window_maximized),
                    panel_width=ui_data.get('panel_width', merged_config.ui.panel_width),
                    enable_tooltips=ui_data.get('enable_tooltips', merged_config.ui.enable_tooltips),
                    show_coordinates=ui_data.get('show_coordinates', merged_config.ui.show_coordinates),
                    show_zoom_info=ui_data.get('show_zoom_info', merged_config.ui.show_zoom_info)
                )
            
            if 'color' in config_data:
                color_data = config_data['color']
                merged_config.color = ColorSettings(
                    default_format=ColorFormat(color_data.get('default_format', merged_config.color.default_format.value)),
                    copy_format=ColorFormat(color_data.get('copy_format', merged_config.color.copy_format.value)),
                    show_all_formats=color_data.get('show_all_formats', merged_config.color.show_all_formats),
                    enable_color_history=color_data.get('enable_color_history', merged_config.color.enable_color_history),
                    max_history_items=color_data.get('max_history_items', merged_config.color.max_history_items),
                    enable_favorites=color_data.get('enable_favorites', merged_config.color.enable_favorites),
                    max_favorite_items=color_data.get('max_favorite_items', merged_config.color.max_favorite_items)
                )
            
            if 'image' in config_data:
                image_data = config_data['image']
                merged_config.image = ImageSettings(
                    max_image_size=image_data.get('max_image_size', merged_config.image.max_image_size),
                    supported_formats=image_data.get('supported_formats', merged_config.image.supported_formats),
                    enable_image_cache=image_data.get('enable_image_cache', merged_config.image.enable_image_cache),
                    cache_size_mb=image_data.get('cache_size_mb', merged_config.image.cache_size_mb),
                    zoom_sensitivity=image_data.get('zoom_sensitivity', merged_config.image.zoom_sensitivity),
                    min_zoom=image_data.get('min_zoom', merged_config.image.min_zoom),
                    max_zoom=image_data.get('max_zoom', merged_config.image.max_zoom),
                    enable_pixel_grid=image_data.get('enable_pixel_grid', merged_config.image.enable_pixel_grid),
                    pixel_grid_threshold=image_data.get('pixel_grid_threshold', merged_config.image.pixel_grid_threshold)
                )
            
            # Update other sections similarly...
            merged_config.version = config_data.get('version', merged_config.version)
            merged_config.first_run = config_data.get('first_run', merged_config.first_run)
            merged_config.last_update_check = config_data.get('last_update_check', merged_config.last_update_check)
            
            return merged_config
            
        except (ValueError, KeyError) as e:
            raise ConfigurationError(
                f"Invalid configuration value: {e}",
                details=str(e)
            )
    
    def _serialize_config(self) -> Dict[str, Any]:
        """
        Serialize configuration to JSON-compatible format.
        
        Returns:
            Dict[str, Any]: Serialized configuration data
        """
        def convert_enums(obj):
            """Convert enum values to strings recursively."""
            if isinstance(obj, Enum):
                return obj.value
            elif isinstance(obj, dict):
                return {k: convert_enums(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_enums(item) for item in obj]
            else:
                return obj
        
        config_dict = asdict(self._config)
        return convert_enums(config_dict)
    
    def _validate_config(self) -> None:
        """
        Validate configuration values.
        
        Raises:
            ValidationError: If configuration values are invalid
        """
        # Validate UI settings
        if self._config.ui.window_width < 800:
            raise ValidationError("Window width must be at least 800 pixels", 
                                field_name="ui.window_width", 
                                field_value=self._config.ui.window_width)
        
        if self._config.ui.window_height < 600:
            raise ValidationError("Window height must be at least 600 pixels",
                                field_name="ui.window_height",
                                field_value=self._config.ui.window_height)
        
        # Validate color settings
        if self._config.color.max_history_items < 1:
            raise ValidationError("Max history items must be at least 1",
                                field_name="color.max_history_items",
                                field_value=self._config.color.max_history_items)
        
        # Validate image settings
        if self._config.image.min_zoom >= self._config.image.max_zoom:
            raise ValidationError("Min zoom must be less than max zoom",
                                field_name="image.zoom_range")
        
        if self._config.image.cache_size_mb < 10:
            raise ValidationError("Cache size must be at least 10MB",
                                field_name="image.cache_size_mb",
                                field_value=self._config.image.cache_size_mb)
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key.
        
        Args:
            key: Configuration key in dot notation (e.g., 'ui.theme')
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        try:
            keys = key.split('.')
            value = self._config
            
            for k in keys:
                if hasattr(value, k):
                    value = getattr(value, k)
                else:
                    return default
            
            # Convert enum values to their string representation
            if isinstance(value, Enum):
                return value.value
            
            return value
            
        except Exception:
            return default
    
    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value by key.
        
        Args:
            key: Configuration key in dot notation
            value: Value to set
            
        Raises:
            ConfigurationError: If key is invalid or value cannot be set
        """
        try:
            keys = key.split('.')
            if len(keys) < 2:
                raise ConfigurationError(f"Invalid configuration key: {key}")
            
            section = getattr(self._config, keys[0])
            if not section:
                raise ConfigurationError(f"Invalid configuration section: {keys[0]}")
            
            # Handle enum conversions
            field_name = keys[1]
            if hasattr(section, field_name):
                current_value = getattr(section, field_name)
                if isinstance(current_value, Enum):
                    # Convert string value to enum
                    enum_class = type(current_value)
                    value = enum_class(value)
            
            setattr(section, field_name, value)
            
        except Exception as e:
            raise ConfigurationError(
                f"Failed to set configuration value for key '{key}': {e}",
                config_key=key,
                details=str(e)
            )
    
    def reset_to_defaults(self) -> None:
        """Reset configuration to default values."""
        self._config = AppConfig()
        self.save()
    
    def get_config_file_path(self) -> Path:
        """Get the path to the configuration file."""
        return self._config_file
    
    def export_config(self, file_path: Union[str, Path]) -> None:
        """
        Export configuration to a file.
        
        Args:
            file_path: Path to export file
            
        Raises:
            ConfigurationError: If export fails
        """
        try:
            export_path = Path(file_path)
            config_data = self._serialize_config()
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            raise ConfigurationError(
                f"Failed to export configuration: {e}",
                details=str(e)
            )
    
    def import_config(self, file_path: Union[str, Path]) -> None:
        """
        Import configuration from a file.
        
        Args:
            file_path: Path to import file
            
        Raises:
            ConfigurationError: If import fails
        """
        try:
            import_path = Path(file_path)
            if not import_path.exists():
                raise ConfigurationError(f"Configuration file not found: {import_path}")
            
            with open(import_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            self._config = self._merge_config(config_data)
            self._validate_config()
            self.save()
            
        except Exception as e:
            raise ConfigurationError(
                f"Failed to import configuration: {e}",
                details=str(e)
            )
    
    @property
    def config(self) -> AppConfig:
        """Get the current configuration object."""
        return self._config