"""
Accessibility Manager

Provides comprehensive accessibility features including screen reader support,
high contrast mode, font scaling, and ARIA-like functionality for Tkinter.
"""

import tkinter as tk
from tkinter import ttk, font
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from enum import Enum
import platform
import sys

from ..core.event_bus import EventBus


class AccessibilityLevel(Enum):
    """Accessibility compliance levels."""
    NONE = "none"
    A = "a"
    AA = "aa"
    AAA = "aaa"


class ContrastRatio(Enum):
    """WCAG contrast ratio requirements."""
    AA_NORMAL = 4.5
    AA_LARGE = 3.0
    AAA_NORMAL = 7.0
    AAA_LARGE = 4.5


@dataclass
class AccessibilitySettings:
    """Accessibility settings configuration."""
    high_contrast: bool = False
    large_fonts: bool = False
    screen_reader_support: bool = False
    keyboard_navigation: bool = True
    focus_indicators: bool = True
    reduced_motion: bool = False
    font_scale_factor: float = 1.0
    target_level: AccessibilityLevel = AccessibilityLevel.AA


class AccessibilityManager:
    """
    Manages accessibility features for the application.
    
    Features:
    - High contrast mode
    - Font scaling
    - Screen reader support
    - ARIA-like attributes
    - Focus management
    - Color contrast validation
    - Reduced motion support
    """
    
    def __init__(self, root: tk.Tk, event_bus: EventBus):
        self.root = root
        self.event_bus = event_bus
        
        # Settings
        self.settings = AccessibilitySettings()
        
        # Theme colors
        self.normal_colors = {
            "bg": "#f0f0f0",
            "fg": "#000000",
            "select_bg": "#0078d4",
            "select_fg": "#ffffff",
            "disabled_bg": "#e0e0e0",
            "disabled_fg": "#808080"
        }
        
        self.high_contrast_colors = {
            "bg": "#000000",
            "fg": "#ffffff",
            "select_bg": "#ffffff",
            "select_fg": "#000000",
            "disabled_bg": "#404040",
            "disabled_fg": "#c0c0c0"
        }
        
        # Font information
        self.base_fonts = {}
        self.scaled_fonts = {}
        
        # Widget accessibility information
        self.widget_info: Dict[tk.Widget, Dict[str, Any]] = {}
        
        # Screen reader support
        self.screen_reader_active = self._detect_screen_reader()
        
        # Setup
        self._initialize_fonts()
        self._setup_event_handlers()
        self._detect_system_accessibility_settings()
    
    def _initialize_fonts(self):
        """Initialize font information."""
        try:
            # Get system fonts
            self.base_fonts = {
                "default": font.nametofont("TkDefaultFont"),
                "text": font.nametofont("TkTextFont"),
                "fixed": font.nametofont("TkFixedFont"),
                "menu": font.nametofont("TkMenuFont"),
                "heading": font.nametofont("TkHeadingFont"),
                "caption": font.nametofont("TkCaptionFont"),
                "small_caption": font.nametofont("TkSmallCaptionFont"),
                "icon": font.nametofont("TkIconFont"),
                "tooltip": font.nametofont("TkTooltipFont")
            }
        except tk.TclError:
            # Fallback fonts
            self.base_fonts = {
                "default": font.Font(family="Arial", size=9),
                "text": font.Font(family="Arial", size=9),
                "fixed": font.Font(family="Courier", size=9),
                "menu": font.Font(family="Arial", size=9),
                "heading": font.Font(family="Arial", size=12, weight="bold"),
                "caption": font.Font(family="Arial", size=8),
                "small_caption": font.Font(family="Arial", size=7),
                "icon": font.Font(family="Arial", size=9),
                "tooltip": font.Font(family="Arial", size=8)
            }
    
    def _setup_event_handlers(self):
        """Setup event handlers."""
        # Subscribe to accessibility events
        self.event_bus.subscribe("accessibility.settings_changed", self._on_settings_changed)
        self.event_bus.subscribe("accessibility.high_contrast_toggle", self._on_high_contrast_toggle)
        self.event_bus.subscribe("accessibility.font_scale_changed", self._on_font_scale_changed)
        
        # Subscribe to system events
        self.root.bind("<Configure>", self._on_window_configure)
    
    def _detect_screen_reader(self) -> bool:
        """Detect if a screen reader is active."""
        if platform.system() == "Windows":
            try:
                import winreg
                # Check for common screen readers
                screen_readers = [
                    r"SOFTWARE\Freedom Scientific\JAWS",
                    r"SOFTWARE\GW Micro\Window-Eyes",
                    r"SOFTWARE\NV Access\NVDA"
                ]
                
                for reader_path in screen_readers:
                    try:
                        winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reader_path)
                        return True
                    except FileNotFoundError:
                        continue
                        
            except ImportError:
                pass
        
        # Check environment variables
        if "NVDA" in str(sys.modules) or "JAWS" in str(sys.modules):
            return True
        
        return False
    
    def _detect_system_accessibility_settings(self):
        """Detect system accessibility settings."""
        if platform.system() == "Windows":
            try:
                import winreg
                
                # Check high contrast mode
                try:
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                                       r"Control Panel\Accessibility\HighContrast")
                    flags, _ = winreg.QueryValueEx(key, "Flags")
                    self.settings.high_contrast = bool(flags & 1)
                    winreg.CloseKey(key)
                except:
                    pass
                
                # Check font scaling
                try:
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                       r"Control Panel\Desktop\WindowMetrics")
                    caption_height, _ = winreg.QueryValueEx(key, "CaptionHeight")
                    # Convert to scale factor (approximate)
                    self.settings.font_scale_factor = max(1.0, abs(caption_height) / 18.0)
                    winreg.CloseKey(key)
                except:
                    pass
                    
            except ImportError:
                pass
        
        elif platform.system() == "Darwin":  # macOS
            # macOS accessibility detection would go here
            pass
        
        else:  # Linux
            # Linux accessibility detection would go here
            pass
    
    def configure_accessibility(self, **settings):
        """Configure accessibility settings."""
        for key, value in settings.items():
            if hasattr(self.settings, key):
                setattr(self.settings, key, value)
        
        # Apply settings
        self._apply_accessibility_settings()
        
        # Publish settings changed event
        self.event_bus.publish("accessibility.settings_changed", {
            "settings": self.settings
        }, source="accessibility_manager")
    
    def enable_high_contrast(self, enabled: bool = True):
        """Enable or disable high contrast mode."""
        self.settings.high_contrast = enabled
        self._apply_high_contrast_mode()
    
    def set_font_scale(self, scale_factor: float):
        """Set font scaling factor."""
        self.settings.font_scale_factor = max(0.5, min(3.0, scale_factor))
        self._apply_font_scaling()
    
    def enable_screen_reader_support(self, enabled: bool = True):
        """Enable or disable screen reader support."""
        self.settings.screen_reader_support = enabled
        self._configure_screen_reader_support()
    
    def register_widget(self, widget: tk.Widget, **accessibility_info):
        """
        Register a widget with accessibility information.
        
        Args:
            widget: The widget to register
            **accessibility_info: Accessibility attributes (role, label, description, etc.)
        """
        self.widget_info[widget] = accessibility_info
        self._configure_widget_accessibility(widget, accessibility_info)
    
    def set_widget_label(self, widget: tk.Widget, label: str):
        """Set accessible label for a widget."""
        if widget not in self.widget_info:
            self.widget_info[widget] = {}
        
        self.widget_info[widget]["label"] = label
        self._update_widget_accessibility(widget)
    
    def set_widget_description(self, widget: tk.Widget, description: str):
        """Set accessible description for a widget."""
        if widget not in self.widget_info:
            self.widget_info[widget] = {}
        
        self.widget_info[widget]["description"] = description
        self._update_widget_accessibility(widget)
    
    def set_widget_role(self, widget: tk.Widget, role: str):
        """Set ARIA-like role for a widget."""
        if widget not in self.widget_info:
            self.widget_info[widget] = {}
        
        self.widget_info[widget]["role"] = role
        self._update_widget_accessibility(widget)
    
    def calculate_contrast_ratio(self, color1: str, color2: str) -> float:
        """
        Calculate WCAG contrast ratio between two colors.
        
        Args:
            color1: First color (hex format)
            color2: Second color (hex format)
            
        Returns:
            Contrast ratio (1.0 to 21.0)
        """
        def hex_to_rgb(hex_color):
            hex_color = hex_color.lstrip('#')
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
        def relative_luminance(rgb):
            def gamma_correct(c):
                c = c / 255.0
                return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
            
            r, g, b = [gamma_correct(c) for c in rgb]
            return 0.2126 * r + 0.7152 * g + 0.0722 * b
        
        rgb1 = hex_to_rgb(color1)
        rgb2 = hex_to_rgb(color2)
        
        lum1 = relative_luminance(rgb1)
        lum2 = relative_luminance(rgb2)
        
        # Ensure lighter color is in numerator
        if lum1 < lum2:
            lum1, lum2 = lum2, lum1
        
        return (lum1 + 0.05) / (lum2 + 0.05)
    
    def check_contrast_compliance(self, foreground: str, background: str, 
                                 font_size: int = 12, is_bold: bool = False) -> Dict[str, bool]:
        """
        Check WCAG contrast compliance for color combination.
        
        Args:
            foreground: Foreground color (hex)
            background: Background color (hex)
            font_size: Font size in points
            is_bold: Whether text is bold
            
        Returns:
            Dictionary with compliance levels
        """
        ratio = self.calculate_contrast_ratio(foreground, background)
        
        # Determine if text is "large"
        is_large_text = font_size >= 18 or (font_size >= 14 and is_bold)
        
        # Check compliance levels
        aa_threshold = ContrastRatio.AA_LARGE.value if is_large_text else ContrastRatio.AA_NORMAL.value
        aaa_threshold = ContrastRatio.AAA_LARGE.value if is_large_text else ContrastRatio.AAA_NORMAL.value
        
        return {
            "ratio": ratio,
            "aa_compliant": ratio >= aa_threshold,
            "aaa_compliant": ratio >= aaa_threshold,
            "is_large_text": is_large_text
        }
    
    def get_accessible_colors(self, base_color: str, target_level: AccessibilityLevel = None) -> Dict[str, str]:
        """
        Get accessible color combinations for a base color.
        
        Args:
            base_color: Base color (hex)
            target_level: Target accessibility level
            
        Returns:
            Dictionary with accessible color combinations
        """
        if target_level is None:
            target_level = self.settings.target_level
        
        # This is a simplified implementation
        # A full implementation would generate multiple accessible combinations
        
        if target_level == AccessibilityLevel.AAA:
            # High contrast combinations for AAA
            if self.calculate_contrast_ratio(base_color, "#000000") >= 7.0:
                return {"foreground": "#000000", "background": base_color}
            else:
                return {"foreground": "#ffffff", "background": base_color}
        else:
            # Standard combinations for AA
            if self.calculate_contrast_ratio(base_color, "#000000") >= 4.5:
                return {"foreground": "#000000", "background": base_color}
            else:
                return {"foreground": "#ffffff", "background": base_color}
    
    def _apply_accessibility_settings(self):
        """Apply all accessibility settings."""
        if self.settings.high_contrast:
            self._apply_high_contrast_mode()
        
        if self.settings.font_scale_factor != 1.0:
            self._apply_font_scaling()
        
        if self.settings.screen_reader_support:
            self._configure_screen_reader_support()
    
    def _apply_high_contrast_mode(self):
        """Apply high contrast mode styling."""
        colors = self.high_contrast_colors if self.settings.high_contrast else self.normal_colors
        
        # Apply to root window
        try:
            self.root.configure(bg=colors["bg"])
        except tk.TclError:
            pass
        
        # Configure ttk styles
        style = ttk.Style()
        
        # Configure basic styles
        style.configure(".", 
                       background=colors["bg"],
                       foreground=colors["fg"],
                       selectbackground=colors["select_bg"],
                       selectforeground=colors["select_fg"])
        
        # Configure specific widget styles
        widget_styles = [
            "TButton", "TLabel", "TEntry", "TText", "TFrame",
            "TCheckbutton", "TRadiobutton", "TCombobox", "TScale",
            "TProgressbar", "TNotebook", "TNotebook.Tab"
        ]
        
        for widget_style in widget_styles:
            try:
                style.configure(widget_style,
                              background=colors["bg"],
                              foreground=colors["fg"],
                              selectbackground=colors["select_bg"],
                              selectforeground=colors["select_fg"])
            except tk.TclError:
                pass
        
        # Special configurations
        try:
            style.configure("TEntry",
                          fieldbackground=colors["bg"],
                          bordercolor=colors["fg"],
                          lightcolor=colors["fg"],
                          darkcolor=colors["fg"])
        except tk.TclError:
            pass
    
    def _apply_font_scaling(self):
        """Apply font scaling to all fonts."""
        scale_factor = self.settings.font_scale_factor
        
        # Clear existing scaled fonts
        self.scaled_fonts.clear()
        
        # Create scaled versions of all fonts
        for font_name, base_font in self.base_fonts.items():
            try:
                # Get base font properties
                family = base_font.cget("family")
                size = base_font.cget("size")
                weight = base_font.cget("weight")
                slant = base_font.cget("slant")
                
                # Create scaled font
                scaled_size = int(abs(size) * scale_factor)
                if size < 0:  # Negative size means pixels
                    scaled_size = -scaled_size
                
                scaled_font = font.Font(
                    family=family,
                    size=scaled_size,
                    weight=weight,
                    slant=slant
                )
                
                self.scaled_fonts[font_name] = scaled_font
                
                # Update the named font
                base_font.configure(size=scaled_size)
                
            except tk.TclError:
                pass
    
    def _configure_screen_reader_support(self):
        """Configure application for screen reader support."""
        if self.settings.screen_reader_support:
            # Enable additional features for screen readers
            self.settings.focus_indicators = True
            self.settings.keyboard_navigation = True
            
            # Configure all registered widgets
            for widget, info in self.widget_info.items():
                self._configure_widget_accessibility(widget, info)
    
    def _configure_widget_accessibility(self, widget: tk.Widget, info: Dict[str, Any]):
        """Configure a widget for accessibility."""
        # Set accessible name
        if "label" in info:
            try:
                # For Tkinter, we can't set ARIA attributes directly,
                # but we can use tooltips and other mechanisms
                self._create_tooltip(widget, info["label"])
            except:
                pass
        
        # Configure focus indicators
        if self.settings.focus_indicators:
            self._add_focus_indicators(widget)
        
        # Configure for screen readers
        if self.settings.screen_reader_support:
            self._configure_widget_for_screen_reader(widget, info)
    
    def _update_widget_accessibility(self, widget: tk.Widget):
        """Update accessibility configuration for a widget."""
        if widget in self.widget_info:
            self._configure_widget_accessibility(widget, self.widget_info[widget])
    
    def _add_focus_indicators(self, widget: tk.Widget):
        """Add visual focus indicators to a widget."""
        def on_focus_in(event):
            try:
                if self.settings.high_contrast:
                    highlight_color = self.high_contrast_colors["select_bg"]
                else:
                    highlight_color = "#0078d4"
                
                widget.configure(highlightbackground=highlight_color,
                               highlightthickness=2)
            except tk.TclError:
                pass
        
        def on_focus_out(event):
            try:
                widget.configure(highlightthickness=0)
            except tk.TclError:
                pass
        
        widget.bind("<FocusIn>", on_focus_in, add=True)
        widget.bind("<FocusOut>", on_focus_out, add=True)
    
    def _configure_widget_for_screen_reader(self, widget: tk.Widget, info: Dict[str, Any]):
        """Configure widget specifically for screen reader compatibility."""
        # This is a simplified implementation
        # Real screen reader support would require platform-specific APIs
        
        widget_class = widget.winfo_class()
        
        if widget_class == "Button":
            # Ensure button has accessible text
            if "label" in info and not widget.cget("text"):
                try:
                    widget.configure(text=info["label"])
                except tk.TclError:
                    pass
        
        elif widget_class == "Entry":
            # Add placeholder or label information
            if "label" in info:
                self._create_tooltip(widget, info["label"])
    
    def _create_tooltip(self, widget: tk.Widget, text: str):
        """Create a tooltip for a widget."""
        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            
            label = tk.Label(tooltip, text=text, background="#ffffe0", 
                           relief="solid", borderwidth=1)
            label.pack()
            
            widget.tooltip = tooltip
        
        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip
        
        widget.bind("<Enter>", on_enter, add=True)
        widget.bind("<Leave>", on_leave, add=True)
    
    # Event handlers
    def _on_settings_changed(self, event_data):
        """Handle accessibility settings changed event."""
        settings = event_data.data.get("settings")
        if settings:
            self.settings = settings
            self._apply_accessibility_settings()
    
    def _on_high_contrast_toggle(self, event_data):
        """Handle high contrast toggle event."""
        enabled = event_data.data.get("enabled", not self.settings.high_contrast)
        self.enable_high_contrast(enabled)
    
    def _on_font_scale_changed(self, event_data):
        """Handle font scale changed event."""
        scale_factor = event_data.data.get("scale_factor", 1.0)
        self.set_font_scale(scale_factor)
    
    def _on_window_configure(self, event):
        """Handle window configure event."""
        # Re-apply accessibility settings if needed
        pass
    
    def get_accessibility_info(self) -> Dict[str, Any]:
        """Get comprehensive accessibility information."""
        return {
            "settings": {
                "high_contrast": self.settings.high_contrast,
                "large_fonts": self.settings.large_fonts,
                "screen_reader_support": self.settings.screen_reader_support,
                "keyboard_navigation": self.settings.keyboard_navigation,
                "focus_indicators": self.settings.focus_indicators,
                "reduced_motion": self.settings.reduced_motion,
                "font_scale_factor": self.settings.font_scale_factor,
                "target_level": self.settings.target_level.value
            },
            "system": {
                "screen_reader_detected": self.screen_reader_active,
                "platform": platform.system()
            },
            "registered_widgets": len(self.widget_info),
            "available_fonts": list(self.base_fonts.keys())
        }
    
    def cleanup(self):
        """Cleanup resources."""
        # Clear widget information
        self.widget_info.clear()
        
        # Clear scaled fonts
        self.scaled_fonts.clear()