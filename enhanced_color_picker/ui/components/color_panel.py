"""
Comprehensive Color Panel Component

Advanced color information display and controls with multi-format support,
copy functionality, CSS/programming language formats, and WCAG compliance information.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Dict, List, Callable, Any
import pyperclip
from enum import Enum

from ...models.color_data import ColorData
from ...models.enums import ColorFormat
from ...core.event_bus import EventBus, EventData
from ...services.color_service import ColorService


class CopyFormat(Enum):
    """Available copy formats for colors."""
    HEX = "hex"
    RGB = "rgb"
    HSL = "hsl"
    HSV = "hsv"
    CMYK = "cmyk"
    CSS_HEX = "css_hex"
    CSS_RGB = "css_rgb"
    CSS_HSL = "css_hsl"
    PYTHON_TUPLE = "python_tuple"
    PYTHON_DICT = "python_dict"
    JAVASCRIPT_HEX = "javascript_hex"
    JAVASCRIPT_RGB = "javascript_rgb"
    JAVA_COLOR = "java_color"
    CSHARP_COLOR = "csharp_color"


class ColorFormatConverter:
    """Converts colors to various programming language formats."""
    
    @staticmethod
    def to_css_hex(color: ColorData) -> str:
        """Convert to CSS hex format."""
        return f"color: {color.hex};"
    
    @staticmethod
    def to_css_rgb(color: ColorData) -> str:
        """Convert to CSS RGB format."""
        if color.alpha < 1.0:
            return f"color: rgba({color.r}, {color.g}, {color.b}, {color.alpha:.2f});"
        return f"color: rgb({color.r}, {color.g}, {color.b});"
    
    @staticmethod
    def to_css_hsl(color: ColorData) -> str:
        """Convert to CSS HSL format."""
        h, s, l = color.hsl
        if color.alpha < 1.0:
            return f"color: hsla({h:.0f}, {s:.0f}%, {l:.0f}%, {color.alpha:.2f});"
        return f"color: hsl({h:.0f}, {s:.0f}%, {l:.0f}%);"
    
    @staticmethod
    def to_python_tuple(color: ColorData) -> str:
        """Convert to Python tuple format."""
        if color.alpha < 1.0:
            return f"({color.r}, {color.g}, {color.b}, {color.alpha:.2f})"
        return f"({color.r}, {color.g}, {color.b})"
    
    @staticmethod
    def to_python_dict(color: ColorData) -> str:
        """Convert to Python dictionary format."""
        if color.alpha < 1.0:
            return f"{{'r': {color.r}, 'g': {color.g}, 'b': {color.b}, 'a': {color.alpha:.2f}}}"
        return f"{{'r': {color.r}, 'g': {color.g}, 'b': {color.b}}}"
    
    @staticmethod
    def to_javascript_hex(color: ColorData) -> str:
        """Convert to JavaScript hex format."""
        return f'const color = "{color.hex}";'
    
    @staticmethod
    def to_javascript_rgb(color: ColorData) -> str:
        """Convert to JavaScript RGB format."""
        if color.alpha < 1.0:
            return f"const color = `rgba({color.r}, {color.g}, {color.b}, {color.alpha:.2f})`;"
        return f"const color = `rgb({color.r}, {color.g}, {color.b})`;"
    
    @staticmethod
    def to_java_color(color: ColorData) -> str:
        """Convert to Java Color format."""
        if color.alpha < 1.0:
            return f"new Color({color.r}, {color.g}, {color.b}, {int(color.alpha * 255)})"
        return f"new Color({color.r}, {color.g}, {color.b})"
    
    @staticmethod
    def to_csharp_color(color: ColorData) -> str:
        """Convert to C# Color format."""
        if color.alpha < 1.0:
            return f"Color.FromArgb({int(color.alpha * 255)}, {color.r}, {color.g}, {color.b})"
        return f"Color.FromArgb({color.r}, {color.g}, {color.b})"


class WCAGComplianceChecker:
    """WCAG compliance checker for color accessibility."""
    
    @staticmethod
    def calculate_contrast_ratio(color1: ColorData, color2: ColorData) -> float:
        """Calculate WCAG contrast ratio between two colors."""
        l1 = color1.get_luminance()
        l2 = color2.get_luminance()
        
        # Ensure l1 is the lighter color
        if l1 < l2:
            l1, l2 = l2, l1
        
        return (l1 + 0.05) / (l2 + 0.05)
    
    @staticmethod
    def get_compliance_level(contrast_ratio: float) -> str:
        """Get WCAG compliance level for contrast ratio."""
        if contrast_ratio >= 7.0:
            return "AAA"
        elif contrast_ratio >= 4.5:
            return "AA"
        elif contrast_ratio >= 3.0:
            return "AA Large"
        else:
            return "Fail"
    
    @staticmethod
    def get_compliance_info(color: ColorData, background: ColorData) -> Dict[str, Any]:
        """Get comprehensive compliance information."""
        contrast_ratio = WCAGComplianceChecker.calculate_contrast_ratio(color, background)
        compliance_level = WCAGComplianceChecker.get_compliance_level(contrast_ratio)
        
        return {
            "contrast_ratio": contrast_ratio,
            "compliance_level": compliance_level,
            "passes_aa": contrast_ratio >= 4.5,
            "passes_aaa": contrast_ratio >= 7.0,
            "passes_aa_large": contrast_ratio >= 3.0,
            "recommendations": WCAGComplianceChecker._get_recommendations(contrast_ratio)
        }
    
    @staticmethod
    def _get_recommendations(contrast_ratio: float) -> List[str]:
        """Get accessibility recommendations based on contrast ratio."""
        recommendations = []
        
        if contrast_ratio < 3.0:
            recommendations.append("Contrast too low for any text use")
            recommendations.append("Consider using a different color combination")
        elif contrast_ratio < 4.5:
            recommendations.append("Suitable only for large text (18pt+ or 14pt+ bold)")
            recommendations.append("Not suitable for normal text")
        elif contrast_ratio < 7.0:
            recommendations.append("Meets AA standard for all text sizes")
            recommendations.append("Consider higher contrast for better accessibility")
        else:
            recommendations.append("Excellent contrast - meets AAA standard")
            recommendations.append("Suitable for all text sizes and users")
        
        return recommendations


class ColorDisplayWidget(tk.Frame):
    """Widget for displaying a single color format with copy functionality."""
    
    def __init__(self, parent, format_name: str, copy_format: CopyFormat, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.format_name = format_name
        self.copy_format = copy_format
        self.current_color: Optional[ColorData] = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the widget UI."""
        # Format label
        self.label = ttk.Label(self, text=f"{self.format_name}:", width=8, anchor="w")
        self.label.grid(row=0, column=0, sticky="w", padx=(0, 5))
        
        # Value entry (read-only)
        self.value_var = tk.StringVar()
        self.value_entry = ttk.Entry(self, textvariable=self.value_var, state="readonly", width=25)
        self.value_entry.grid(row=0, column=1, sticky="ew", padx=(0, 5))
        
        # Copy button
        self.copy_button = ttk.Button(self, text="Copy", width=6, command=self._copy_value)
        self.copy_button.grid(row=0, column=2)
        
        # Configure grid
        self.grid_columnconfigure(1, weight=1)
    
    def update_color(self, color: ColorData):
        """Update the displayed color value."""
        self.current_color = color
        
        # Get formatted value
        formatted_value = self._format_color_value(color)
        self.value_var.set(formatted_value)
    
    def _format_color_value(self, color: ColorData) -> str:
        """Format color value based on the copy format."""
        if self.copy_format == CopyFormat.HEX:
            return color.hex
        elif self.copy_format == CopyFormat.RGB:
            return f"rgb({color.r}, {color.g}, {color.b})"
        elif self.copy_format == CopyFormat.HSL:
            h, s, l = color.hsl
            return f"hsl({h:.0f}, {s:.0f}%, {l:.0f}%)"
        elif self.copy_format == CopyFormat.HSV:
            h, s, v = color.hsv
            return f"hsv({h:.0f}, {s:.0f}%, {v:.0f}%)"
        elif self.copy_format == CopyFormat.CMYK:
            c, m, y, k = color.cmyk
            return f"cmyk({c:.0f}%, {m:.0f}%, {y:.0f}%, {k:.0f}%)"
        else:
            return color.hex
    
    def _copy_value(self):
        """Copy the formatted value to clipboard."""
        if not self.current_color:
            return
        
        try:
            # Get the copy value based on format
            copy_value = self._get_copy_value(self.current_color)
            
            # Copy to clipboard
            pyperclip.copy(copy_value)
            
            # Show feedback
            self._show_copy_feedback()
            
        except Exception as e:
            messagebox.showerror("Copy Error", f"Failed to copy color: {str(e)}")
    
    def _get_copy_value(self, color: ColorData) -> str:
        """Get the value to copy based on copy format."""
        converter = ColorFormatConverter()
        
        format_map = {
            CopyFormat.HEX: lambda c: c.hex,
            CopyFormat.RGB: lambda c: f"rgb({c.r}, {c.g}, {c.b})",
            CopyFormat.HSL: lambda c: f"hsl({c.hsl[0]:.0f}, {c.hsl[1]:.0f}%, {c.hsl[2]:.0f}%)",
            CopyFormat.HSV: lambda c: f"hsv({c.hsv[0]:.0f}, {c.hsv[1]:.0f}%, {c.hsv[2]:.0f}%)",
            CopyFormat.CMYK: lambda c: f"cmyk({c.cmyk[0]:.0f}%, {c.cmyk[1]:.0f}%, {c.cmyk[2]:.0f}%, {c.cmyk[3]:.0f}%)",
            CopyFormat.CSS_HEX: converter.to_css_hex,
            CopyFormat.CSS_RGB: converter.to_css_rgb,
            CopyFormat.CSS_HSL: converter.to_css_hsl,
            CopyFormat.PYTHON_TUPLE: converter.to_python_tuple,
            CopyFormat.PYTHON_DICT: converter.to_python_dict,
            CopyFormat.JAVASCRIPT_HEX: converter.to_javascript_hex,
            CopyFormat.JAVASCRIPT_RGB: converter.to_javascript_rgb,
            CopyFormat.JAVA_COLOR: converter.to_java_color,
            CopyFormat.CSHARP_COLOR: converter.to_csharp_color,
        }
        
        formatter = format_map.get(self.copy_format, lambda c: c.hex)
        return formatter(color)
    
    def _show_copy_feedback(self):
        """Show visual feedback that value was copied."""
        original_text = self.copy_button.cget("text")
        self.copy_button.configure(text="Copied!")
        self.after(1000, lambda: self.copy_button.configure(text=original_text))


class ColorPreviewWidget(tk.Frame):
    """Widget for displaying color preview with swatch."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.current_color: Optional[ColorData] = None
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the widget UI."""
        # Color swatch
        self.swatch = tk.Canvas(self, width=80, height=80, highlightthickness=1, highlightbackground="#ccc")
        self.swatch.grid(row=0, column=0, rowspan=3, padx=(0, 10), pady=5)
        
        # Color name/description
        self.name_label = ttk.Label(self, text="No color selected", font=("TkDefaultFont", 10, "bold"))
        self.name_label.grid(row=0, column=1, sticky="w")
        
        # Coordinates info
        self.coords_label = ttk.Label(self, text="", font=("TkDefaultFont", 8))
        self.coords_label.grid(row=1, column=1, sticky="w")
        
        # Additional info
        self.info_label = ttk.Label(self, text="", font=("TkDefaultFont", 8))
        self.info_label.grid(row=2, column=1, sticky="w")
    
    def update_color(self, color: ColorData, position: Optional[Tuple[int, int]] = None):
        """Update the color preview."""
        self.current_color = color
        
        # Update swatch
        self._update_swatch(color)
        
        # Update labels
        self.name_label.configure(text=f"Color: {color.hex}")
        
        if position:
            self.coords_label.configure(text=f"Position: ({position[0]:.0f}, {position[1]:.0f})")
        else:
            self.coords_label.configure(text="")
        
        # Show luminance info
        luminance = color.get_luminance()
        brightness = "Light" if luminance > 0.5 else "Dark"
        self.info_label.configure(text=f"Luminance: {luminance:.3f} ({brightness})")
    
    def _update_swatch(self, color: ColorData):
        """Update the color swatch."""
        self.swatch.delete("all")
        
        # Create color rectangle
        hex_color = color.hex
        self.swatch.create_rectangle(2, 2, 78, 78, fill=hex_color, outline="#000", width=1)
        
        # Add transparency pattern if color has alpha
        if color.alpha < 1.0:
            self._draw_transparency_pattern()
            # Overlay with alpha
            alpha_color = f"#{color.r:02x}{color.g:02x}{color.b:02x}"
            # Note: Tkinter doesn't support alpha directly, so we simulate it
            self.swatch.create_rectangle(2, 2, 78, 78, fill=alpha_color, outline="#000", width=1, stipple="gray50")
    
    def _draw_transparency_pattern(self):
        """Draw transparency checkerboard pattern."""
        # Draw checkerboard pattern
        for x in range(2, 78, 8):
            for y in range(2, 78, 8):
                if (x // 8 + y // 8) % 2 == 0:
                    self.swatch.create_rectangle(x, y, x+8, y+8, fill="#ffffff", outline="")
                else:
                    self.swatch.create_rectangle(x, y, x+8, y+8, fill="#cccccc", outline="")


class WCAGComplianceWidget(tk.Frame):
    """Widget for displaying WCAG compliance information."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.current_color: Optional[ColorData] = None
        self.background_color = ColorData.from_rgb(255, 255, 255)  # Default white background
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the widget UI."""
        # Title
        title_label = ttk.Label(self, text="WCAG Compliance", font=("TkDefaultFont", 10, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 5))
        
        # Background color selector
        bg_frame = ttk.Frame(self)
        bg_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 5))
        
        ttk.Label(bg_frame, text="Background:").grid(row=0, column=0, sticky="w")
        self.bg_button = ttk.Button(bg_frame, text="White", width=10, command=self._select_background)
        self.bg_button.grid(row=0, column=1, padx=(5, 0))
        
        # Contrast ratio
        self.contrast_label = ttk.Label(self, text="Contrast Ratio: -")
        self.contrast_label.grid(row=2, column=0, columnspan=2, sticky="w")
        
        # Compliance level
        self.compliance_label = ttk.Label(self, text="Compliance: -")
        self.compliance_label.grid(row=3, column=0, columnspan=2, sticky="w")
        
        # Pass/fail indicators
        self.aa_label = ttk.Label(self, text="AA: -")
        self.aa_label.grid(row=4, column=0, sticky="w")
        
        self.aaa_label = ttk.Label(self, text="AAA: -")
        self.aaa_label.grid(row=4, column=1, sticky="w")
        
        # Recommendations
        self.recommendations_text = tk.Text(self, height=4, width=40, wrap=tk.WORD, 
                                          font=("TkDefaultFont", 8), state=tk.DISABLED)
        self.recommendations_text.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(5, 0))
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
    
    def update_color(self, color: ColorData):
        """Update WCAG compliance information for the color."""
        self.current_color = color
        self._update_compliance_info()
    
    def _update_compliance_info(self):
        """Update the compliance information display."""
        if not self.current_color:
            return
        
        # Get compliance info
        compliance_info = WCAGComplianceChecker.get_compliance_info(
            self.current_color, self.background_color
        )
        
        # Update labels
        contrast_ratio = compliance_info["contrast_ratio"]
        self.contrast_label.configure(text=f"Contrast Ratio: {contrast_ratio:.2f}:1")
        
        compliance_level = compliance_info["compliance_level"]
        self.compliance_label.configure(text=f"Compliance: {compliance_level}")
        
        # Update pass/fail indicators
        aa_status = "✓ Pass" if compliance_info["passes_aa"] else "✗ Fail"
        aaa_status = "✓ Pass" if compliance_info["passes_aaa"] else "✗ Fail"
        
        self.aa_label.configure(text=f"AA: {aa_status}")
        self.aaa_label.configure(text=f"AAA: {aaa_status}")
        
        # Update recommendations
        self.recommendations_text.configure(state=tk.NORMAL)
        self.recommendations_text.delete(1.0, tk.END)
        
        recommendations = compliance_info["recommendations"]
        for i, rec in enumerate(recommendations):
            if i > 0:
                self.recommendations_text.insert(tk.END, "\n")
            self.recommendations_text.insert(tk.END, f"• {rec}")
        
        self.recommendations_text.configure(state=tk.DISABLED)
    
    def _select_background(self):
        """Open background color selection dialog."""
        # For now, cycle through common backgrounds
        backgrounds = [
            (ColorData.from_rgb(255, 255, 255), "White"),
            (ColorData.from_rgb(0, 0, 0), "Black"),
            (ColorData.from_rgb(128, 128, 128), "Gray"),
            (ColorData.from_rgb(240, 240, 240), "Light Gray"),
        ]
        
        # Find current background and select next
        current_index = 0
        for i, (bg_color, name) in enumerate(backgrounds):
            if (bg_color.r == self.background_color.r and 
                bg_color.g == self.background_color.g and 
                bg_color.b == self.background_color.b):
                current_index = i
                break
        
        next_index = (current_index + 1) % len(backgrounds)
        self.background_color, bg_name = backgrounds[next_index]
        
        self.bg_button.configure(text=bg_name)
        self._update_compliance_info()


class ComprehensiveColorPanel(ttk.Frame):
    """
    Comprehensive color panel with multi-format display, copy functionality,
    and WCAG compliance information.
    """
    
    def __init__(self, parent, event_bus: EventBus, color_service: Optional[ColorService] = None, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.event_bus = event_bus
        self.color_service = color_service or ColorService()
        self.current_color: Optional[ColorData] = None
        
        self._setup_ui()
        self._setup_event_subscriptions()
    
    def _setup_ui(self):
        """Setup the user interface."""
        # Create notebook for organized display
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Basic formats tab
        self.basic_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.basic_frame, text="Basic Formats")
        self._setup_basic_formats_tab()
        
        # Programming formats tab
        self.programming_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.programming_frame, text="Programming")
        self._setup_programming_formats_tab()
        
        # Accessibility tab
        self.accessibility_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.accessibility_frame, text="Accessibility")
        self._setup_accessibility_tab()
    
    def _setup_basic_formats_tab(self):
        """Setup the basic color formats tab."""
        # Color preview
        self.color_preview = ColorPreviewWidget(self.basic_frame)
        self.color_preview.pack(fill=tk.X, padx=5, pady=5)
        
        # Separator
        ttk.Separator(self.basic_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=5, pady=5)
        
        # Color format displays
        formats_frame = ttk.Frame(self.basic_frame)
        formats_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Basic color formats
        self.format_widgets = {}
        
        formats = [
            ("HEX", CopyFormat.HEX),
            ("RGB", CopyFormat.RGB),
            ("HSL", CopyFormat.HSL),
            ("HSV", CopyFormat.HSV),
            ("CMYK", CopyFormat.CMYK),
        ]
        
        for i, (name, copy_format) in enumerate(formats):
            widget = ColorDisplayWidget(formats_frame, name, copy_format)
            widget.pack(fill=tk.X, pady=2)
            self.format_widgets[name] = widget
        
        # Bulk copy buttons
        bulk_frame = ttk.Frame(self.basic_frame)
        bulk_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(bulk_frame, text="Copy All Formats", command=self._copy_all_formats).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(bulk_frame, text="Copy as CSS", command=self._copy_as_css).pack(side=tk.LEFT)
    
    def _setup_programming_formats_tab(self):
        """Setup the programming formats tab."""
        # Language selection
        lang_frame = ttk.Frame(self.programming_frame)
        lang_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(lang_frame, text="Language:").pack(side=tk.LEFT)
        
        self.language_var = tk.StringVar(value="CSS")
        self.language_combo = ttk.Combobox(lang_frame, textvariable=self.language_var, 
                                         values=["CSS", "Python", "JavaScript", "Java", "C#"],
                                         state="readonly", width=15)
        self.language_combo.pack(side=tk.LEFT, padx=(5, 0))
        self.language_combo.bind("<<ComboboxSelected>>", self._on_language_changed)
        
        # Programming format displays
        self.prog_formats_frame = ttk.Frame(self.programming_frame)
        self.prog_formats_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.prog_format_widgets = {}
        self._update_programming_formats()
    
    def _setup_accessibility_tab(self):
        """Setup the accessibility tab."""
        # WCAG compliance widget
        self.wcag_widget = WCAGComplianceWidget(self.accessibility_frame)
        self.wcag_widget.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def _setup_event_subscriptions(self):
        """Setup event bus subscriptions."""
        self.event_bus.subscribe("color_picked", self._on_color_picked)
        self.event_bus.subscribe("color_changed", self._on_color_changed)
    
    def display_color(self, color: ColorData, position: Optional[Tuple[int, int]] = None):
        """
        Display color information in all formats.
        
        Args:
            color: Color to display
            position: Optional position where color was picked
        """
        self.current_color = color
        
        # Update color preview
        self.color_preview.update_color(color, position)
        
        # Update basic format widgets
        for widget in self.format_widgets.values():
            widget.update_color(color)
        
        # Update programming format widgets
        for widget in self.prog_format_widgets.values():
            widget.update_color(color)
        
        # Update accessibility information
        self.wcag_widget.update_color(color)
        
        # Publish color displayed event
        self.event_bus.publish("color_displayed", {
            "color": color,
            "position": position
        }, source="color_panel")
    
    def _update_programming_formats(self):
        """Update programming format widgets based on selected language."""
        # Clear existing widgets
        for widget in self.prog_format_widgets.values():
            widget.destroy()
        self.prog_format_widgets.clear()
        
        language = self.language_var.get()
        
        # Define formats for each language
        language_formats = {
            "CSS": [
                ("Hex", CopyFormat.CSS_HEX),
                ("RGB", CopyFormat.CSS_RGB),
                ("HSL", CopyFormat.CSS_HSL),
            ],
            "Python": [
                ("Tuple", CopyFormat.PYTHON_TUPLE),
                ("Dict", CopyFormat.PYTHON_DICT),
            ],
            "JavaScript": [
                ("Hex", CopyFormat.JAVASCRIPT_HEX),
                ("RGB", CopyFormat.JAVASCRIPT_RGB),
            ],
            "Java": [
                ("Color", CopyFormat.JAVA_COLOR),
            ],
            "C#": [
                ("Color", CopyFormat.CSHARP_COLOR),
            ],
        }
        
        formats = language_formats.get(language, [])
        
        for name, copy_format in formats:
            widget = ColorDisplayWidget(self.prog_formats_frame, name, copy_format)
            widget.pack(fill=tk.X, pady=2)
            self.prog_format_widgets[name] = widget
            
            # Update with current color if available
            if self.current_color:
                widget.update_color(self.current_color)
    
    def _copy_all_formats(self):
        """Copy all basic formats to clipboard."""
        if not self.current_color:
            return
        
        color = self.current_color
        
        formats_text = [
            f"HEX: {color.hex}",
            f"RGB: rgb({color.r}, {color.g}, {color.b})",
            f"HSL: hsl({color.hsl[0]:.0f}, {color.hsl[1]:.0f}%, {color.hsl[2]:.0f}%)",
            f"HSV: hsv({color.hsv[0]:.0f}, {color.hsv[1]:.0f}%, {color.hsv[2]:.0f}%)",
            f"CMYK: cmyk({color.cmyk[0]:.0f}%, {color.cmyk[1]:.0f}%, {color.cmyk[2]:.0f}%, {color.cmyk[3]:.0f}%)",
        ]
        
        try:
            pyperclip.copy("\n".join(formats_text))
            messagebox.showinfo("Copied", "All color formats copied to clipboard!")
        except Exception as e:
            messagebox.showerror("Copy Error", f"Failed to copy formats: {str(e)}")
    
    def _copy_as_css(self):
        """Copy color as CSS variables."""
        if not self.current_color:
            return
        
        color = self.current_color
        converter = ColorFormatConverter()
        
        css_text = [
            ":root {",
            f"  --color-hex: {color.hex};",
            f"  --color-rgb: rgb({color.r}, {color.g}, {color.b});",
            f"  --color-hsl: hsl({color.hsl[0]:.0f}, {color.hsl[1]:.0f}%, {color.hsl[2]:.0f}%);",
            "}"
        ]
        
        try:
            pyperclip.copy("\n".join(css_text))
            messagebox.showinfo("Copied", "CSS variables copied to clipboard!")
        except Exception as e:
            messagebox.showerror("Copy Error", f"Failed to copy CSS: {str(e)}")
    
    def _on_language_changed(self, event=None):
        """Handle language selection change."""
        self._update_programming_formats()
    
    # Event handlers
    def _on_color_picked(self, event_data: EventData):
        """Handle color picked event."""
        data = event_data.data
        if "color" in data:
            position = data.get("image_position")
            self.display_color(data["color"], position)
    
    def _on_color_changed(self, event_data: EventData):
        """Handle color changed event."""
        data = event_data.data
        if "color" in data:
            self.display_color(data["color"])
    
    def get_current_color(self) -> Optional[ColorData]:
        """Get the currently displayed color."""
        return self.current_color
    
    def clear_display(self):
        """Clear the color display."""
        self.current_color = None
        
        # Clear preview
        self.color_preview.name_label.configure(text="No color selected")
        self.color_preview.coords_label.configure(text="")
        self.color_preview.info_label.configure(text="")
        self.color_preview.swatch.delete("all")
        
        # Clear format widgets
        for widget in self.format_widgets.values():
            widget.value_var.set("")
        
        for widget in self.prog_format_widgets.values():
            widget.value_var.set("")