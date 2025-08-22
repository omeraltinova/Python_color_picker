"""
Comprehensive Settings Panel for Enhanced Color Picker.

Provides a categorized settings interface with theme management,
keyboard shortcuts, performance settings, and more.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict, Any, Optional
import json

from ...core.event_bus import EventBus
from ...models.app_settings import AppSettings
from ...models.enums import ColorFormat
from ...storage.settings_storage import SettingsStorage
from ...ui.themes.theme_manager import ThemeManager, ThemeMode
from ...localization.i18n_service import I18nService


class SettingsPanel(ttk.Frame):
    """
    Comprehensive settings panel with categorized options.
    
    Features:
    - Theme management with preview
    - Keyboard shortcut customization
    - Default color format selection
    - Performance and cache settings
    - Language selection
    - Import/export settings
    """
    
    def __init__(self, parent, event_bus: EventBus, settings_storage: SettingsStorage, 
                 theme_manager: ThemeManager, i18n_service: I18nService):
        """Initialize settings panel."""
        super().__init__(parent)
        
        self.event_bus = event_bus
        self.settings_storage = settings_storage
        self.theme_manager = theme_manager
        self.i18n_service = i18n_service
        
        # Current settings (working copy)
        self.current_settings = self.settings_storage.load_settings()
        self.original_settings = self.current_settings.copy()
        
        # Keyboard shortcuts
        self.keyboard_shortcuts = self._load_default_shortcuts()
        
        # Theme preview
        self.theme_preview_frame = None
        
        # Setup UI
        self._setup_ui()
        self._load_current_settings()
        
        # Register for theme changes
        self.event_bus.subscribe("theme_changed", self._on_theme_changed)
    
    def _setup_ui(self):
        """Setup the settings panel UI."""
        # Create notebook for categories
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create tab frames
        self.appearance_frame = ttk.Frame(self.notebook)
        self.behavior_frame = ttk.Frame(self.notebook)
        self.performance_frame = ttk.Frame(self.notebook)
        self.shortcuts_frame = ttk.Frame(self.notebook)
        self.advanced_frame = ttk.Frame(self.notebook)
        
        # Add tabs
        self.notebook.add(self.appearance_frame, text="Appearance")
        self.notebook.add(self.behavior_frame, text="Behavior")
        self.notebook.add(self.performance_frame, text="Performance")
        self.notebook.add(self.shortcuts_frame, text="Shortcuts")
        self.notebook.add(self.advanced_frame, text="Advanced")
        
        # Create settings sections
        self._create_appearance_settings()
        self._create_behavior_settings()
        self._create_performance_settings()
        self._create_keyboard_shortcuts()
        self._create_advanced_settings()
        
        # Create action buttons
        self._create_action_buttons()
    
    def _create_appearance_settings(self):
        """Create appearance settings section."""
        # Theme settings
        theme_group = ttk.LabelFrame(self.appearance_frame, text="Theme")
        theme_group.pack(fill="x", padx=10, pady=5)
        
        # Theme selection
        ttk.Label(theme_group, text="Theme Mode:").pack(anchor="w", padx=10, pady=5)
        
        self.theme_var = tk.StringVar(value=self.current_settings.theme)
        theme_frame = ttk.Frame(theme_group)
        theme_frame.pack(fill="x", padx=10, pady=5)
        
        for theme_mode in ThemeMode:
            ttk.Radiobutton(
                theme_frame,
                text=theme_mode.value.title(),
                variable=self.theme_var,
                value=theme_mode.value,
                command=self._on_theme_selection_changed
            ).pack(side="left", padx=5)
        
        # Language settings
        language_group = ttk.LabelFrame(self.appearance_frame, text="Language")
        language_group.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(language_group, text="Interface Language:").pack(anchor="w", padx=10, pady=5)
        
        self.language_var = tk.StringVar(value=self.current_settings.language)
        language_combo = ttk.Combobox(
            language_group,
            textvariable=self.language_var,
            values=["tr", "en"],
            state="readonly"
        )
        language_combo.pack(anchor="w", padx=10, pady=5)
        language_combo.bind("<<ComboboxSelected>>", self._on_setting_changed)
        
        # Display settings
        display_group = ttk.LabelFrame(self.appearance_frame, text="Display")
        display_group.pack(fill="x", padx=10, pady=5)
        
        self.high_contrast_var = tk.BooleanVar(value=self.current_settings.high_contrast_mode)
        ttk.Checkbutton(
            display_group,
            text="High Contrast Mode",
            variable=self.high_contrast_var,
            command=self._on_setting_changed
        ).pack(anchor="w", padx=10, pady=2)
        
        self.large_fonts_var = tk.BooleanVar(value=self.current_settings.large_fonts)
        ttk.Checkbutton(
            display_group,
            text="Large Fonts",
            variable=self.large_fonts_var,
            command=self._on_setting_changed
        ).pack(anchor="w", padx=10, pady=2)
    
    def _create_behavior_settings(self):
        """Create behavior settings section."""
        # Color format settings
        format_group = ttk.LabelFrame(self.behavior_frame, text="Color Format")
        format_group.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(format_group, text="Default Color Format:").pack(anchor="w", padx=10, pady=5)
        
        self.color_format_var = tk.StringVar(value=self.current_settings.default_color_format.value)
        format_combo = ttk.Combobox(
            format_group,
            textvariable=self.color_format_var,
            values=[fmt.value for fmt in ColorFormat],
            state="readonly"
        )
        format_combo.pack(anchor="w", padx=10, pady=5)
        format_combo.bind("<<ComboboxSelected>>", self._on_setting_changed)
        
        # Image display settings
        image_group = ttk.LabelFrame(self.behavior_frame, text="Image Display")
        image_group.pack(fill="x", padx=10, pady=5)
        
        self.fit_image_var = tk.BooleanVar(value=self.current_settings.fit_image_on_load)
        ttk.Checkbutton(
            image_group,
            text="Fit Image on Load",
            variable=self.fit_image_var,
            command=self._on_setting_changed
        ).pack(anchor="w", padx=10, pady=2)
        
        self.pixel_grid_var = tk.BooleanVar(value=self.current_settings.enable_pixel_grid)
        ttk.Checkbutton(
            image_group,
            text="Enable Pixel Grid",
            variable=self.pixel_grid_var,
            command=self._on_setting_changed
        ).pack(anchor="w", padx=10, pady=2)
        
        # Zoom sensitivity
        zoom_frame = ttk.Frame(image_group)
        zoom_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(zoom_frame, text="Zoom Sensitivity:").pack(side="left")
        
        self.zoom_sensitivity_var = tk.DoubleVar(value=self.current_settings.zoom_sensitivity)
        zoom_scale = ttk.Scale(
            zoom_frame,
            from_=1.01,
            to=2.0,
            variable=self.zoom_sensitivity_var,
            orient="horizontal",
            command=self._on_setting_changed
        )
        zoom_scale.pack(side="left", fill="x", expand=True, padx=10)
        
        self.zoom_label = ttk.Label(zoom_frame, text=f"{self.zoom_sensitivity_var.get():.2f}")
        self.zoom_label.pack(side="right")
    
    def _create_performance_settings(self):
        """Create performance settings section."""
        # Cache settings
        cache_group = ttk.LabelFrame(self.performance_frame, text="Cache")
        cache_group.pack(fill="x", padx=10, pady=5)
        
        self.enable_caching_var = tk.BooleanVar(value=self.current_settings.enable_image_caching)
        ttk.Checkbutton(
            cache_group,
            text="Enable Image Caching",
            variable=self.enable_caching_var,
            command=self._on_setting_changed
        ).pack(anchor="w", padx=10, pady=2)
        
        # Max cache size
        cache_size_frame = ttk.Frame(cache_group)
        cache_size_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(cache_size_frame, text="Max Cache Size (MB):").pack(side="left")
        
        self.max_cache_size_var = tk.IntVar(value=self.current_settings.max_cache_size_mb)
        cache_size_scale = ttk.Scale(
            cache_size_frame,
            from_=10,
            to=1000,
            variable=self.max_cache_size_var,
            orient="horizontal",
            command=self._on_setting_changed
        )
        cache_size_scale.pack(side="left", fill="x", expand=True, padx=10)
        
        self.cache_size_label = ttk.Label(cache_size_frame, text=f"{self.max_cache_size_var.get()} MB")
        self.cache_size_label.pack(side="right")
        
        # History settings
        history_group = ttk.LabelFrame(self.performance_frame, text="History")
        history_group.pack(fill="x", padx=10, pady=5)
        
        # Max history items
        history_frame = ttk.Frame(history_group)
        history_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(history_frame, text="Max History Items:").pack(side="left")
        
        self.max_history_var = tk.IntVar(value=self.current_settings.max_history_items)
        history_scale = ttk.Scale(
            history_frame,
            from_=10,
            to=1000,
            variable=self.max_history_var,
            orient="horizontal",
            command=self._on_setting_changed
        )
        history_scale.pack(side="left", fill="x", expand=True, padx=10)
        
        self.history_label = ttk.Label(history_frame, text=f"{self.max_history_var.get()}")
        self.history_label.pack(side="right")
    
    def _create_keyboard_shortcuts(self):
        """Create keyboard shortcuts customization section."""
        # Instructions
        instructions = ttk.Label(
            self.shortcuts_frame,
            text="Keyboard shortcuts can be customized here. Click Edit to modify a shortcut.",
            wraplength=400
        )
        instructions.pack(anchor="w", padx=10, pady=10)
        
        # Shortcuts list
        shortcuts_frame = ttk.Frame(self.shortcuts_frame)
        shortcuts_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Create treeview for shortcuts
        columns = ("action", "shortcut")
        self.shortcuts_tree = ttk.Treeview(shortcuts_frame, columns=columns, show="headings", height=10)
        
        self.shortcuts_tree.heading("action", text="Action")
        self.shortcuts_tree.heading("shortcut", text="Shortcut")
        
        self.shortcuts_tree.column("action", width=300)
        self.shortcuts_tree.column("shortcut", width=150)
        
        # Scrollbar for shortcuts
        shortcuts_scrollbar = ttk.Scrollbar(shortcuts_frame, orient="vertical", command=self.shortcuts_tree.yview)
        self.shortcuts_tree.configure(yscrollcommand=shortcuts_scrollbar.set)
        
        self.shortcuts_tree.pack(side="left", fill="both", expand=True)
        shortcuts_scrollbar.pack(side="right", fill="y")
        
        # Populate shortcuts
        self._populate_shortcuts_tree()
        
        # Shortcut editing buttons
        edit_frame = ttk.Frame(self.shortcuts_frame)
        edit_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Button(
            edit_frame,
            text="Edit Shortcut",
            command=self._edit_shortcut
        ).pack(side="left", padx=5)
        
        ttk.Button(
            edit_frame,
            text="Reset All",
            command=self._reset_shortcuts
        ).pack(side="left", padx=5)
    
    def _create_advanced_settings(self):
        """Create advanced settings section."""
        # Debug settings
        debug_group = ttk.LabelFrame(self.advanced_frame, text="Debug")
        debug_group.pack(fill="x", padx=10, pady=5)
        
        self.debug_mode_var = tk.BooleanVar(value=self.current_settings.enable_debug_mode)
        ttk.Checkbutton(
            debug_group,
            text="Enable Debug Mode",
            variable=self.debug_mode_var,
            command=self._on_setting_changed
        ).pack(anchor="w", padx=10, pady=2)
        
        # Export/Import settings
        backup_group = ttk.LabelFrame(self.advanced_frame, text="Backup & Restore")
        backup_group.pack(fill="x", padx=10, pady=5)
        
        backup_frame = ttk.Frame(backup_group)
        backup_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Button(
            backup_frame,
            text="Export Settings",
            command=self._export_settings
        ).pack(side="left", padx=5)
        
        ttk.Button(
            backup_frame,
            text="Import Settings",
            command=self._import_settings
        ).pack(side="left", padx=5)
        
        ttk.Button(
            backup_frame,
            text="Reset All",
            command=self._reset_all_settings
        ).pack(side="left", padx=5)
    
    def _create_action_buttons(self):
        """Create action buttons for the settings panel."""
        button_frame = ttk.Frame(self)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Button(
            button_frame,
            text="OK",
            command=self._ok_settings
        ).pack(side="right", padx=5)
        
        ttk.Button(
            button_frame,
            text="Cancel",
            command=self._cancel_settings
        ).pack(side="right", padx=5)
        
        ttk.Button(
            button_frame,
            text="Apply",
            command=self._apply_settings
        ).pack(side="right", padx=5)
    
    def _load_default_shortcuts(self) -> Dict[str, str]:
        """Load default keyboard shortcuts."""
        return {
            "Open Image": "Ctrl+O",
            "Save Palette": "Ctrl+S",
            "Copy Color": "Ctrl+C",
            "Zoom In": "Ctrl+Plus",
            "Zoom Out": "Ctrl+Minus",
            "Fit to Screen": "Ctrl+0",
            "Toggle Pixel Grid": "G",
            "Settings": "Ctrl+Comma",
            "Help": "F1",
            "Quit": "Ctrl+Q"
        }
    
    def _populate_shortcuts_tree(self):
        """Populate the shortcuts tree with current shortcuts."""
        # Clear existing items
        for item in self.shortcuts_tree.get_children():
            self.shortcuts_tree.delete(item)
        
        # Add shortcuts
        for action, shortcut in self.keyboard_shortcuts.items():
            self.shortcuts_tree.insert("", "end", values=(action, shortcut))
    
    def _load_current_settings(self):
        """Load current settings into UI controls."""
        self._update_scale_labels()
    
    def _update_scale_labels(self):
        """Update scale labels with current values."""
        if hasattr(self, 'zoom_label'):
            self.zoom_label.config(text=f"{self.zoom_sensitivity_var.get():.2f}")
        if hasattr(self, 'cache_size_label'):
            self.cache_size_label.config(text=f"{self.max_cache_size_var.get()} MB")
        if hasattr(self, 'history_label'):
            self.history_label.config(text=f"{self.max_history_var.get()}")
    
    def _on_theme_selection_changed(self):
        """Handle theme selection change."""
        theme_mode = ThemeMode(self.theme_var.get())
        self.theme_manager.set_theme_mode(theme_mode, animate=True)
    
    def _on_theme_changed(self, event_data):
        """Handle theme change event."""
        pass  # Theme manager handles the visual updates
    
    def _on_setting_changed(self, event=None):
        """Handle setting change."""
        self._update_scale_labels()
    
    def _edit_shortcut(self):
        """Edit selected keyboard shortcut."""
        selection = self.shortcuts_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a shortcut to edit.")
            return
        
        messagebox.showinfo("Edit Shortcut", "Shortcut editing will be implemented in a future version.")
    
    def _reset_shortcuts(self):
        """Reset all shortcuts to defaults."""
        if messagebox.askyesno("Reset Shortcuts", "Reset all shortcuts to default values?"):
            self.keyboard_shortcuts = self._load_default_shortcuts()
            self._populate_shortcuts_tree()
    
    def _export_settings(self):
        """Export settings to file."""
        file_path = filedialog.asksaveasfilename(
            title="Export Settings",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                settings_data = {
                    'settings': self.current_settings.to_dict(),
                    'shortcuts': self.keyboard_shortcuts,
                    'version': '1.0'
                }
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(settings_data, f, indent=2, ensure_ascii=False)
                
                messagebox.showinfo("Success", "Settings exported successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export settings: {e}")
    
    def _import_settings(self):
        """Import settings from file."""
        file_path = filedialog.askopenfilename(
            title="Import Settings",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    settings_data = json.load(f)
                
                if 'settings' in settings_data:
                    self.current_settings = AppSettings.from_dict(settings_data['settings'])
                
                if 'shortcuts' in settings_data:
                    self.keyboard_shortcuts = settings_data['shortcuts']
                    self._populate_shortcuts_tree()
                
                self._load_current_settings()
                messagebox.showinfo("Success", "Settings imported successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to import settings: {e}")
    
    def _reset_all_settings(self):
        """Reset all settings to defaults."""
        if messagebox.askyesno("Reset All", "Reset all settings to default values? This cannot be undone."):
            self.current_settings.reset_to_defaults()
            self.keyboard_shortcuts = self._load_default_shortcuts()
            self._load_current_settings()
            self._populate_shortcuts_tree()
    
    def _apply_settings(self):
        """Apply current settings."""
        self._save_current_settings()
        messagebox.showinfo("Applied", "Settings have been applied!")
    
    def _cancel_settings(self):
        """Cancel settings changes."""
        self.current_settings = self.original_settings.copy()
        self._load_current_settings()
        self.event_bus.publish("settings_cancelled", {})
    
    def _ok_settings(self):
        """Apply settings and close panel."""
        self._save_current_settings()
        self.event_bus.publish("settings_applied", {"settings": self.current_settings})
    
    def _save_current_settings(self):
        """Save current settings to storage."""
        # Update settings from UI controls
        self.current_settings.theme = self.theme_var.get()
        self.current_settings.language = self.language_var.get()
        self.current_settings.default_color_format = ColorFormat(self.color_format_var.get())
        self.current_settings.fit_image_on_load = self.fit_image_var.get()
        self.current_settings.enable_pixel_grid = self.pixel_grid_var.get()
        self.current_settings.zoom_sensitivity = self.zoom_sensitivity_var.get()
        self.current_settings.enable_image_caching = self.enable_caching_var.get()
        self.current_settings.max_cache_size_mb = self.max_cache_size_var.get()
        self.current_settings.max_history_items = self.max_history_var.get()
        self.current_settings.high_contrast_mode = self.high_contrast_var.get()
        self.current_settings.large_fonts = self.large_fonts_var.get()
        self.current_settings.enable_debug_mode = self.debug_mode_var.get()
        
        # Save to storage
        self.settings_storage.save_settings(self.current_settings)
        
        # Update original settings
        self.original_settings = self.current_settings.copy()
    
    def cleanup(self):
        """Cleanup settings panel resources."""
        self.event_bus.unsubscribe("theme_changed", self._on_theme_changed)