"""
AppSettings class for application configuration management.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from .enums import ColorFormat


@dataclass
class AppSettings:
    """
    Application settings data structure for user preferences and configuration.
    
    Manages all user-configurable options with sensible defaults.
    """
    
    # Theme and appearance
    theme: str = "dark"
    language: str = "tr"
    
    # Color preferences
    default_color_format: ColorFormat = ColorFormat.HEX
    show_alpha_channel: bool = True
    
    # Palette settings
    auto_save_palettes: bool = True
    max_palette_colors: int = 100
    
    # History settings
    max_history_items: int = 50
    save_history_on_exit: bool = True
    
    # Image display settings
    zoom_sensitivity: float = 1.1
    enable_pixel_grid: bool = True
    pixel_grid_threshold: float = 8.0
    fit_image_on_load: bool = True
    
    # Performance settings
    max_image_size: int = 4096  # Maximum width/height in pixels
    enable_image_caching: bool = True
    max_cache_size_mb: int = 100
    
    # UI settings
    show_minimap: bool = True
    show_color_info_panel: bool = True
    show_palette_panel: bool = True
    show_history_panel: bool = True
    show_analysis_panel: bool = False
    
    # Export settings
    default_export_format: str = "json"
    include_metadata_in_export: bool = True
    
    # Accessibility settings
    high_contrast_mode: bool = False
    large_fonts: bool = False
    keyboard_navigation_hints: bool = True
    
    # Advanced settings
    enable_debug_mode: bool = False
    auto_check_updates: bool = True
    send_usage_statistics: bool = False
    
    # Custom settings (for extensions or user-defined options)
    custom_settings: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize settings after creation."""
        if not self.custom_settings:
            self.custom_settings = {}
        
        # Validate settings
        self._validate_settings()
    
    def _validate_settings(self):
        """Validate and correct invalid settings."""
        # Validate theme
        if self.theme not in ["light", "dark", "auto"]:
            self.theme = "dark"
        
        # Validate language
        if self.language not in ["tr", "en"]:
            self.language = "tr"
        
        # Validate numeric ranges
        self.zoom_sensitivity = max(1.01, min(2.0, self.zoom_sensitivity))
        self.pixel_grid_threshold = max(1.0, min(50.0, self.pixel_grid_threshold))
        self.max_history_items = max(10, min(1000, self.max_history_items))
        self.max_palette_colors = max(5, min(500, self.max_palette_colors))
        self.max_image_size = max(512, min(16384, self.max_image_size))
        self.max_cache_size_mb = max(10, min(1000, self.max_cache_size_mb))
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a setting value by key."""
        if hasattr(self, key):
            return getattr(self, key)
        return self.custom_settings.get(key, default)
    
    def set_setting(self, key: str, value: Any) -> None:
        """Set a setting value by key."""
        if hasattr(self, key):
            setattr(self, key, value)
        else:
            self.custom_settings[key] = value
        
        # Re-validate after changes
        self._validate_settings()
    
    def get_custom_setting(self, key: str, default: Any = None) -> Any:
        """Get a custom setting value."""
        return self.custom_settings.get(key, default)
    
    def set_custom_setting(self, key: str, value: Any) -> None:
        """Set a custom setting value."""
        self.custom_settings[key] = value
    
    def remove_custom_setting(self, key: str) -> bool:
        """Remove a custom setting. Returns True if removed."""
        if key in self.custom_settings:
            del self.custom_settings[key]
            return True
        return False
    
    def reset_to_defaults(self) -> None:
        """Reset all settings to default values."""
        default_settings = AppSettings()
        
        # Copy all default values
        for field_name in self.__dataclass_fields__:
            if field_name != 'custom_settings':
                setattr(self, field_name, getattr(default_settings, field_name))
        
        # Clear custom settings
        self.custom_settings.clear()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary for serialization."""
        result = {}
        
        # Add all standard fields
        for field_name in self.__dataclass_fields__:
            value = getattr(self, field_name)
            if isinstance(value, ColorFormat):
                result[field_name] = value.value
            else:
                result[field_name] = value
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AppSettings':
        """Create settings from dictionary."""
        # Handle ColorFormat enum
        if 'default_color_format' in data:
            format_value = data['default_color_format']
            if isinstance(format_value, str):
                try:
                    data['default_color_format'] = ColorFormat(format_value)
                except ValueError:
                    data['default_color_format'] = ColorFormat.HEX
        
        # Filter out unknown fields
        valid_fields = set(cls.__dataclass_fields__.keys())
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        
        return cls(**filtered_data)
    
    def copy(self) -> 'AppSettings':
        """Create a copy of the settings."""
        return AppSettings.from_dict(self.to_dict())
    
    def __str__(self) -> str:
        """String representation of the settings."""
        return f"AppSettings(theme={self.theme}, language={self.language}, format={self.default_color_format.value})"