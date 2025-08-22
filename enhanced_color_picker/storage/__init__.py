"""
Storage module for Enhanced Color Picker.

Contains storage and persistence functionality for user settings,
palette data, and caching systems.
"""

from .settings_storage import (
    SettingsStorage,
    SettingsStorageError,
    SettingsMigrationError,
    get_global_settings_storage,
    set_global_settings_storage
)

from .cache_storage import (
    CacheManager,
    ImageCache,
    LRUCache,
    CacheError,
    CacheEntry,
    get_global_cache_manager,
    set_global_cache_manager
)

__all__ = [
    'SettingsStorage',
    'SettingsStorageError', 
    'SettingsMigrationError',
    'get_global_settings_storage',
    'set_global_settings_storage',
    'CacheManager',
    'ImageCache',
    'LRUCache',
    'CacheError',
    'CacheEntry',
    'get_global_cache_manager',
    'set_global_cache_manager'
]