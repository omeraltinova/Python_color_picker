# Internationalization (I18n) System

The Enhanced Color Picker includes a comprehensive internationalization system that supports multiple languages with dynamic switching, parameter substitution, and validation features.

## Features

- **JSON-based translations**: Easy to edit and maintain translation files
- **Dynamic language switching**: Change language at runtime without restart
- **Parameter substitution**: Support for dynamic values in translations
- **Fallback mechanism**: Graceful handling of missing translations
- **Translation validation**: Tools to find missing keys and validate completeness
- **UI integration helpers**: Base classes and utilities for UI components

## Quick Start

### Basic Usage

```python
from enhanced_color_picker.localization import init_i18n, t, set_language

# Initialize the I18n system
init_i18n(default_language="tr")

# Translate text
title = t('ui.main_window.title')  # "Gelişmiş Renk Seçici"

# Switch language
set_language("en")
title = t('ui.main_window.title')  # "Enhanced Color Picker"

# Use parameters
message = t('messages.success.color_copied', color='#FF5733')
```

### UI Integration

```python
from enhanced_color_picker.localization import get_language_manager
from enhanced_color_picker.localization.ui_integration_example import I18nAwareWidget

class MyPanel(ttk.Frame, I18nAwareWidget):
    def __init__(self, parent):
        ttk.Frame.__init__(self, parent)
        I18nAwareWidget.__init__(self)
        
        # Create widgets
        self.title_label = ttk.Label(self)
        
        # Register for automatic translation updates
        self.register_translatable_widget(
            self.title_label, 
            'ui.my_panel.title'
        )
```

## Translation Files

Translation files are stored in `enhanced_color_picker/localization/translations/` as JSON files named with language codes (e.g., `tr.json`, `en.json`).

### Structure

```json
{
  "ui": {
    "main_window": {
      "title": "Enhanced Color Picker",
      "load_image": "Load Image"
    }
  },
  "messages": {
    "success": {
      "color_copied": "Color code copied: {color}"
    }
  }
}
```

### Key Naming Convention

- Use dot notation for nested keys: `ui.main_window.title`
- Group related translations: `ui.*`, `messages.*`, `tooltips.*`
- Use descriptive names: `load_image` instead of `btn1`

## Supported Languages

Currently supported languages:

- **Turkish (tr)**: Türkçe - Default language
- **English (en)**: English

## API Reference

### Core Functions

#### `init_i18n(default_language="tr", translations_dir=None)`
Initialize the I18n system.

#### `t(key, **kwargs)`
Translate a key with optional parameters.

#### `set_language(language)`
Change the current language.

#### `get_current_language()`
Get the current language code.

### I18nService Class

The main service class providing all I18n functionality.

```python
from enhanced_color_picker.localization import I18nService

i18n = I18nService(default_language="tr")

# Basic translation
text = i18n.translate('ui.main_window.title')

# With parameters
text = i18n.translate('messages.success.color_copied', color='#FF5733')

# Language management
i18n.set_language('en')
languages = i18n.get_available_languages()

# Validation
is_valid = i18n.is_key_valid('ui.main_window.title')
missing = i18n.get_missing_keys()
```

### LanguageManager Class

High-level language management with UI integration features.

```python
from enhanced_color_picker.localization import get_language_manager

lang_manager = get_language_manager()

# Get supported languages for UI
languages = lang_manager.get_supported_languages()  # {'tr': 'Türkçe', 'en': 'English'}

# Register for language change notifications
def on_language_change(new_language):
    print(f"Language changed to: {new_language}")

lang_manager.register_language_change_callback(on_language_change)

# Get menu items for language selection UI
menu_items = lang_manager.get_language_menu_items()

# Translation statistics
stats = lang_manager.get_translation_stats()
```

## Adding New Languages

1. Create a new JSON file in `translations/` directory (e.g., `fr.json`)
2. Copy the structure from an existing translation file
3. Translate all text values
4. Add the language to `LanguageManager._supported_languages`
5. Test with validation tools

## Translation Guidelines

### Best Practices

1. **Keep it concise**: UI text should be brief and clear
2. **Context matters**: Consider where the text will appear
3. **Consistency**: Use consistent terminology throughout
4. **Cultural adaptation**: Adapt to local conventions, not just literal translation

### Parameter Usage

Use parameters for dynamic content:

```json
{
  "messages": {
    "success": {
      "file_saved": "File saved: {filename}",
      "colors_found": "Found {count} colors in image"
    }
  }
}
```

### Pluralization

Handle plural forms appropriately:

```json
{
  "ui": {
    "palette_panel": {
      "color_count_single": "1 color",
      "color_count_plural": "{count} colors"
    }
  }
}
```

## Validation and Maintenance

### Finding Missing Keys

```python
from enhanced_color_picker.localization import get_language_manager

lang_manager = get_language_manager()
missing_keys = lang_manager.validate_translations()

for language, keys in missing_keys.items():
    if keys:
        print(f"Language '{language}' missing {len(keys)} keys:")
        for key in keys:
            print(f"  - {key}")
```

### Translation Statistics

```python
stats = lang_manager.get_translation_stats()
for lang_code, stat in stats.items():
    completion = stat['completion_percentage']
    print(f"{lang_code}: {completion:.1f}% complete")
```

## Integration with Application

The I18n system is designed to integrate seamlessly with the Enhanced Color Picker application:

1. **Initialization**: Call `init_i18n()` and `init_language_manager()` during app startup
2. **UI Components**: Extend `I18nAwareWidget` for automatic translation updates
3. **Settings**: Store language preference in application settings
4. **Event System**: Use language change callbacks to update UI components

## Performance Considerations

- Translation files are loaded once at startup
- Translations are cached in memory for fast access
- Language switching is immediate (no file I/O required)
- Minimal overhead for translation lookups

## Error Handling

The system includes robust error handling:

- Missing translation keys fall back to the key name
- Invalid language codes are rejected gracefully
- File loading errors are logged but don't crash the application
- Parameter substitution errors are handled safely

## Testing

The system includes comprehensive testing capabilities:

- Key validation
- Translation completeness checking
- Parameter substitution testing
- Language switching verification

See `ui_integration_example.py` for a complete working example of UI integration.