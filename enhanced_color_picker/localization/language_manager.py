"""
Language manager for Enhanced Color Picker.

Provides high-level language management functionality and integration
with the application's event system.
"""

from typing import Dict, List, Optional, Callable
from .i18n_service import I18nService, get_i18n


class LanguageManager:
    """
    High-level language manager that integrates with the application.
    
    Features:
    - Language change notifications
    - UI update callbacks
    - Language preference persistence
    - Validation and error handling
    """
    
    def __init__(self, i18n_service: Optional[I18nService] = None):
        """
        Initialize the language manager.
        
        Args:
            i18n_service: I18n service instance (uses global if None)
        """
        self.i18n = i18n_service or get_i18n()
        self._language_change_callbacks: List[Callable[[str], None]] = []
        self._supported_languages = {
            'tr': 'Türkçe',
            'en': 'English'
        }
    
    def get_supported_languages(self) -> Dict[str, str]:
        """
        Get dictionary of supported languages.
        
        Returns:
            Dictionary mapping language codes to display names
        """
        return self._supported_languages.copy()
    
    def get_current_language_name(self) -> str:
        """
        Get the display name of the current language.
        
        Returns:
            Display name of current language
        """
        current_code = self.i18n.get_current_language()
        return self._supported_languages.get(current_code, current_code)
    
    def change_language(self, language_code: str) -> bool:
        """
        Change the application language and notify callbacks.
        
        Args:
            language_code: Language code to switch to
            
        Returns:
            True if language was changed successfully
        """
        if language_code not in self._supported_languages:
            print(f"Warning: Unsupported language '{language_code}'")
            return False
        
        old_language = self.i18n.get_current_language()
        success = self.i18n.set_language(language_code)
        
        if success and old_language != language_code:
            # Notify all registered callbacks
            for callback in self._language_change_callbacks:
                try:
                    callback(language_code)
                except Exception as e:
                    print(f"Error in language change callback: {e}")
        
        return success
    
    def register_language_change_callback(self, callback: Callable[[str], None]) -> None:
        """
        Register a callback to be called when language changes.
        
        Args:
            callback: Function to call with new language code
        """
        if callback not in self._language_change_callbacks:
            self._language_change_callbacks.append(callback)
    
    def unregister_language_change_callback(self, callback: Callable[[str], None]) -> None:
        """
        Unregister a language change callback.
        
        Args:
            callback: Function to remove from callbacks
        """
        if callback in self._language_change_callbacks:
            self._language_change_callbacks.remove(callback)
    
    def get_language_menu_items(self) -> List[Dict[str, str]]:
        """
        Get language menu items for UI creation.
        
        Returns:
            List of dictionaries with 'code' and 'name' keys
        """
        current_lang = self.i18n.get_current_language()
        items = []
        
        for code, name in self._supported_languages.items():
            items.append({
                'code': code,
                'name': name,
                'current': code == current_lang
            })
        
        return items
    
    def validate_translations(self) -> Dict[str, List[str]]:
        """
        Validate all translations and return missing keys.
        
        Returns:
            Dictionary of missing keys per language
        """
        return self.i18n.get_missing_keys()
    
    def get_translation_stats(self) -> Dict[str, Dict[str, int]]:
        """
        Get translation statistics for each language.
        
        Returns:
            Dictionary with translation statistics
        """
        stats = {}
        missing_keys = self.validate_translations()
        
        # Get total keys from default language (Turkish)
        all_keys = self.i18n._get_all_keys(self.i18n._translations.get('tr', {}))
        total_keys = len(all_keys)
        
        for lang_code in self._supported_languages:
            missing_count = len(missing_keys.get(lang_code, []))
            translated_count = total_keys - missing_count
            
            stats[lang_code] = {
                'total_keys': total_keys,
                'translated_keys': translated_count,
                'missing_keys': missing_count,
                'completion_percentage': (translated_count / total_keys * 100) if total_keys > 0 else 0
            }
        
        return stats
    
    def export_missing_keys_template(self, language_code: str) -> Optional[str]:
        """
        Export a template file with missing keys for translation.
        
        Args:
            language_code: Language to export missing keys for
            
        Returns:
            JSON string with missing keys template or None if no missing keys
        """
        missing_keys = self.validate_translations().get(language_code, [])
        
        if not missing_keys:
            return None
        
        import json
        
        template = {}
        for key in missing_keys:
            # Create nested structure
            keys = key.split('.')
            current = template
            
            for k in keys[:-1]:
                if k not in current:
                    current[k] = {}
                current = current[k]
            
            # Add placeholder for translation
            current[keys[-1]] = f"[TRANSLATE: {key}]"
        
        return json.dumps(template, indent=2, ensure_ascii=False)


# Global language manager instance
_language_manager: Optional[LanguageManager] = None


def get_language_manager() -> LanguageManager:
    """Get the global language manager instance."""
    global _language_manager
    if _language_manager is None:
        _language_manager = LanguageManager()
    return _language_manager


def init_language_manager(i18n_service: Optional[I18nService] = None) -> LanguageManager:
    """
    Initialize the global language manager.
    
    Args:
        i18n_service: I18n service instance
        
    Returns:
        Initialized language manager instance
    """
    global _language_manager
    _language_manager = LanguageManager(i18n_service)
    return _language_manager