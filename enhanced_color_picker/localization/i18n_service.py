"""
Internationalization service for Enhanced Color Picker.

Provides translation functionality with JSON-based translations,
dynamic language switching, and fallback mechanisms.
"""

import json
import os
from typing import Dict, List, Optional, Any
from pathlib import Path


class I18nService:
    """
    Internationalization service for managing translations and language switching.
    
    Features:
    - JSON-based translation files
    - Dynamic language switching
    - Translation key validation
    - Fallback to default language
    - Parameter substitution in translations
    """
    
    def __init__(self, default_language: str = "tr", translations_dir: Optional[str] = None):
        """
        Initialize the I18n service.
        
        Args:
            default_language: Default language code (e.g., 'tr', 'en')
            translations_dir: Directory containing translation files
        """
        self.default_language = default_language
        self.current_language = default_language
        
        # Set translations directory
        if translations_dir is None:
            self.translations_dir = Path(__file__).parent / "translations"
        else:
            self.translations_dir = Path(translations_dir)
            
        # Storage for loaded translations
        self._translations: Dict[str, Dict[str, Any]] = {}
        self._available_languages: List[str] = []
        
        # Load available translations
        self._load_available_languages()
        self._load_translations()
    
    def _load_available_languages(self) -> None:
        """Discover available language files."""
        if not self.translations_dir.exists():
            self.translations_dir.mkdir(parents=True, exist_ok=True)
            return
            
        self._available_languages = []
        for file_path in self.translations_dir.glob("*.json"):
            language_code = file_path.stem
            self._available_languages.append(language_code)
        
        # Ensure default language is available
        if self.default_language not in self._available_languages:
            self._available_languages.append(self.default_language)
    
    def _load_translations(self) -> None:
        """Load all translation files."""
        self._translations = {}
        
        for language in self._available_languages:
            translation_file = self.translations_dir / f"{language}.json"
            
            if translation_file.exists():
                try:
                    with open(translation_file, 'r', encoding='utf-8') as f:
                        self._translations[language] = json.load(f)
                except (json.JSONDecodeError, IOError) as e:
                    print(f"Warning: Failed to load translation file {translation_file}: {e}")
                    self._translations[language] = {}
            else:
                self._translations[language] = {}
    
    def _get_nested_value(self, data: Dict[str, Any], key_path: str) -> Optional[str]:
        """
        Get nested value from dictionary using dot notation.
        
        Args:
            data: Dictionary to search in
            key_path: Dot-separated key path (e.g., 'ui.main_window.title')
            
        Returns:
            Translation string or None if not found
        """
        keys = key_path.split('.')
        current = data
        
        try:
            for key in keys:
                current = current[key]
            return current if isinstance(current, str) else None
        except (KeyError, TypeError):
            return None
    
    def translate(self, key: str, **kwargs) -> str:
        """
        Translate a key to the current language with parameter substitution.
        
        Args:
            key: Translation key in dot notation (e.g., 'ui.main_window.title')
            **kwargs: Parameters for string formatting
            
        Returns:
            Translated string with parameters substituted
        """
        # Try current language first
        translation = self._get_translation_for_language(key, self.current_language)
        
        # Fallback to default language if not found
        if translation is None and self.current_language != self.default_language:
            translation = self._get_translation_for_language(key, self.default_language)
        
        # Final fallback to the key itself
        if translation is None:
            translation = key
            print(f"Warning: Translation not found for key '{key}'")
        
        # Substitute parameters
        try:
            return translation.format(**kwargs)
        except (KeyError, ValueError) as e:
            print(f"Warning: Parameter substitution failed for key '{key}': {e}")
            return translation
    
    def _get_translation_for_language(self, key: str, language: str) -> Optional[str]:
        """Get translation for specific language."""
        if language not in self._translations:
            return None
        
        return self._get_nested_value(self._translations[language], key)
    
    def set_language(self, language: str) -> bool:
        """
        Change the current language.
        
        Args:
            language: Language code to switch to
            
        Returns:
            True if language was changed successfully, False otherwise
        """
        if language in self._available_languages:
            self.current_language = language
            return True
        else:
            print(f"Warning: Language '{language}' is not available")
            return False
    
    def get_current_language(self) -> str:
        """Get the current language code."""
        return self.current_language
    
    def get_available_languages(self) -> List[str]:
        """Get list of available language codes."""
        return self._available_languages.copy()
    
    def is_key_valid(self, key: str, language: Optional[str] = None) -> bool:
        """
        Check if a translation key exists.
        
        Args:
            key: Translation key to validate
            language: Language to check (current language if None)
            
        Returns:
            True if key exists, False otherwise
        """
        check_language = language or self.current_language
        
        if check_language not in self._translations:
            return False
        
        return self._get_nested_value(self._translations[check_language], key) is not None
    
    def get_missing_keys(self, reference_language: Optional[str] = None) -> Dict[str, List[str]]:
        """
        Find missing translation keys compared to a reference language.
        
        Args:
            reference_language: Language to use as reference (default language if None)
            
        Returns:
            Dictionary mapping language codes to lists of missing keys
        """
        ref_lang = reference_language or self.default_language
        
        if ref_lang not in self._translations:
            return {}
        
        ref_keys = self._get_all_keys(self._translations[ref_lang])
        missing_keys = {}
        
        for language in self._available_languages:
            if language == ref_lang:
                continue
                
            if language not in self._translations:
                missing_keys[language] = ref_keys
                continue
            
            lang_keys = self._get_all_keys(self._translations[language])
            missing_keys[language] = [key for key in ref_keys if key not in lang_keys]
        
        return missing_keys
    
    def _get_all_keys(self, data: Dict[str, Any], prefix: str = "") -> List[str]:
        """
        Recursively get all keys from nested dictionary.
        
        Args:
            data: Dictionary to extract keys from
            prefix: Current key prefix
            
        Returns:
            List of all keys in dot notation
        """
        keys = []
        
        for key, value in data.items():
            full_key = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, dict):
                keys.extend(self._get_all_keys(value, full_key))
            else:
                keys.append(full_key)
        
        return keys
    
    def reload_translations(self) -> None:
        """Reload all translation files from disk."""
        self._load_available_languages()
        self._load_translations()
    
    def add_translation(self, language: str, key: str, value: str) -> None:
        """
        Add or update a translation programmatically.
        
        Args:
            language: Language code
            key: Translation key in dot notation
            value: Translation value
        """
        if language not in self._translations:
            self._translations[language] = {}
            if language not in self._available_languages:
                self._available_languages.append(language)
        
        # Navigate to the correct nested location
        keys = key.split('.')
        current = self._translations[language]
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value


# Global instance for easy access
_i18n_instance: Optional[I18nService] = None


def get_i18n() -> I18nService:
    """Get the global I18n service instance."""
    global _i18n_instance
    if _i18n_instance is None:
        _i18n_instance = I18nService()
    return _i18n_instance


def init_i18n(default_language: str = "tr", translations_dir: Optional[str] = None) -> I18nService:
    """
    Initialize the global I18n service.
    
    Args:
        default_language: Default language code
        translations_dir: Directory containing translation files
        
    Returns:
        Initialized I18n service instance
    """
    global _i18n_instance
    _i18n_instance = I18nService(default_language, translations_dir)
    return _i18n_instance


# Convenience functions
def t(key: str, **kwargs) -> str:
    """Shorthand for translate function."""
    return get_i18n().translate(key, **kwargs)


def set_language(language: str) -> bool:
    """Shorthand for setting language."""
    return get_i18n().set_language(language)


def get_current_language() -> str:
    """Shorthand for getting current language."""
    return get_i18n().get_current_language()