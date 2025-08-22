"""
Example of how to integrate the I18n system with UI components.

This demonstrates best practices for using translations in the Enhanced Color Picker UI.
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Any

from . import t, get_language_manager


class I18nAwareWidget:
    """
    Base class for widgets that support internationalization.
    
    Provides common functionality for UI components that need to update
    their text when the language changes.
    """
    
    def __init__(self):
        self.language_manager = get_language_manager()
        self.translatable_widgets: Dict[str, Any] = {}
        
        # Register for language change notifications
        self.language_manager.register_language_change_callback(self._on_language_change)
    
    def _on_language_change(self, new_language: str) -> None:
        """Called when the language changes."""
        self.update_translations()
    
    def update_translations(self) -> None:
        """Update all translatable widgets. Override in subclasses."""
        pass
    
    def register_translatable_widget(self, widget: Any, translation_key: str, 
                                   attribute: str = 'text', **format_params) -> None:
        """
        Register a widget for automatic translation updates.
        
        Args:
            widget: The widget to update
            translation_key: Translation key to use
            attribute: Widget attribute to update (e.g., 'text', 'title')
            **format_params: Parameters for string formatting
        """
        self.translatable_widgets[id(widget)] = {
            'widget': widget,
            'key': translation_key,
            'attribute': attribute,
            'params': format_params
        }
        
        # Set initial translation
        self._update_widget_translation(widget, translation_key, attribute, format_params)
    
    def _update_widget_translation(self, widget: Any, key: str, attribute: str, params: Dict[str, Any]) -> None:
        """Update a single widget's translation."""
        try:
            translated_text = t(key, **params)
            
            if hasattr(widget, 'config'):
                # Tkinter widget
                widget.config(**{attribute: translated_text})
            else:
                # Other widget types
                setattr(widget, attribute, translated_text)
        except Exception as e:
            print(f"Error updating translation for key '{key}': {e}")
    
    def update_translations(self) -> None:
        """Update all registered translatable widgets."""
        for widget_info in self.translatable_widgets.values():
            self._update_widget_translation(
                widget_info['widget'],
                widget_info['key'],
                widget_info['attribute'],
                widget_info['params']
            )


class ExampleColorPanel(ttk.Frame, I18nAwareWidget):
    """
    Example color panel that demonstrates I18n integration.
    """
    
    def __init__(self, parent):
        ttk.Frame.__init__(self, parent)
        I18nAwareWidget.__init__(self)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the UI components with translations."""
        # Title label
        self.title_label = ttk.Label(self, font=('Arial', 12, 'bold'))
        self.title_label.pack(pady=5)
        self.register_translatable_widget(self.title_label, 'ui.color_panel.title')
        
        # Color format labels
        self.rgb_label = ttk.Label(self)
        self.rgb_label.pack(anchor='w', padx=10)
        self.register_translatable_widget(self.rgb_label, 'ui.color_panel.rgb_label')
        
        self.hex_label = ttk.Label(self)
        self.hex_label.pack(anchor='w', padx=10)
        self.register_translatable_widget(self.hex_label, 'ui.color_panel.hex_label')
        
        # Copy button
        self.copy_button = ttk.Button(self, command=self.copy_color)
        self.copy_button.pack(pady=5)
        self.register_translatable_widget(self.copy_button, 'ui.color_panel.copy_button')
        
        # Language selection
        self.language_frame = ttk.Frame(self)
        self.language_frame.pack(pady=10)
        
        ttk.Label(self.language_frame, text="Language:").pack(side='left')
        
        self.language_var = tk.StringVar()
        self.language_combo = ttk.Combobox(
            self.language_frame, 
            textvariable=self.language_var,
            state='readonly',
            width=10
        )
        self.language_combo.pack(side='left', padx=5)
        self.language_combo.bind('<<ComboboxSelected>>', self.on_language_selected)
        
        # Populate language options
        self.update_language_options()
    
    def update_language_options(self):
        """Update the language combobox options."""
        menu_items = self.language_manager.get_language_menu_items()
        
        values = []
        current_value = None
        
        for item in menu_items:
            values.append(item['name'])
            if item['current']:
                current_value = item['name']
        
        self.language_combo['values'] = values
        if current_value:
            self.language_var.set(current_value)
    
    def on_language_selected(self, event=None):
        """Handle language selection."""
        selected_name = self.language_var.get()
        
        # Find the language code for the selected name
        supported = self.language_manager.get_supported_languages()
        for code, name in supported.items():
            if name == selected_name:
                self.language_manager.change_language(code)
                break
    
    def copy_color(self):
        """Simulate copying a color."""
        # This would normally copy the actual color
        color = "#FF5733"
        print(t('messages.success.color_copied', color=color))
    
    def update_translations(self):
        """Override to update language options as well."""
        super().update_translations()
        self.update_language_options()


def create_example_window():
    """Create an example window demonstrating I18n integration."""
    root = tk.Tk()
    root.title("I18n Integration Example")
    root.geometry("300x250")
    
    # Create the example panel
    panel = ExampleColorPanel(root)
    panel.pack(fill='both', expand=True, padx=10, pady=10)
    
    return root


if __name__ == "__main__":
    # Initialize I18n system
    from . import init_i18n, init_language_manager
    
    init_i18n(default_language="tr")
    init_language_manager()
    
    # Create and run example
    root = create_example_window()
    root.mainloop()