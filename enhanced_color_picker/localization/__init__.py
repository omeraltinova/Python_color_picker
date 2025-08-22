"""
Localization module for Enhanced Color Picker.

Contains internationalization support and translation files.
"""

from .i18n_service import (
    I18nService,
    get_i18n,
    init_i18n,
    t,
    set_language,
    get_current_language
)
from .language_manager import (
    LanguageManager,
    get_language_manager,
    init_language_manager
)

__all__ = [
    'I18nService',
    'get_i18n',
    'init_i18n',
    't',
    'set_language',
    'get_current_language',
    'LanguageManager',
    'get_language_manager',
    'init_language_manager'
]