"""
High DPI Support Utilities

Provides comprehensive high DPI support for the Enhanced Color Picker application,
including DPI detection, scaling calculations, and font management.
"""

import tkinter as tk
from tkinter import font
from typing import Dict, Any, Optional, Tuple
import sys
import platform
from dataclasses import dataclass
from enum import Enum

from ..core.event_bus import EventBus


class DPIAwareness(Enum):
    """DPI awareness levels."""
    UNAWARE = "unaware"
    SYSTEM_AWARE = "system_aware"
    PER_MONITOR_AWARE = "per_monitor_aware"


@dataclass
class DPIInfo:
    """DPI information for a display."""
    dpi_x: float
    dpi_y: float
    scale_factor: float
    awareness: DPIAwareness
    
    @property
    def dpi(self) -> float:
        """Get average DPI."""
        return (self.dpi_x + self.dpi_y) / 2


class DPIManager:
    """
    Manages high DPI support and scaling for the application.
    
    Features:
    - Automatic DPI detection
    - Scale factor calculation
    - Font scaling
    - Widget size scaling
    - Per-monitor DPI awareness (where supported)
    """
    
    def __init__(self, root: tk.Tk, event_bus: EventBus):
        self.root = root
        self.event_bus = event_bus
        
        # DPI information
        self.dpi_info: Optional[DPIInfo] = None
        self.base_dpi = 96.0  # Standard Windows DPI
        
        # Font cache
        self.scaled_fonts: Dict[str, font.Font] = {}
        
        # Base font sizes
        self.base_font_sizes = {
            "small": 8,
            "normal": 9,
            "medium": 10,
            "large": 12,
            "extra_large": 14,
            "title": 16
        }
        
        # Initialize DPI support
        self._initialize_dpi_support()
        self._detect_dpi()
        self._setup_event_handlers()
    
    def _initialize_dpi_support(self):
        """Initialize DPI support for the platform."""
        if platform.system() == "Windows":
            self._initialize_windows_dpi()
        elif platform.system() == "Darwin":  # macOS
            self._initialize_macos_dpi()
        else:  # Linux and others
            self._initialize_linux_dpi()
    
    def _initialize_windows_dpi(self):
        """Initialize DPI support on Windows."""
        try:
            import ctypes
            from ctypes import wintypes
            
            # Try to set DPI awareness
            try:
                # Windows 10 version 1703 and later
                ctypes.windll.user32.SetProcessDpiAwarenessContext(-4)  # DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2
                awareness = DPIAwareness.PER_MONITOR_AWARE
            except:
                try:
                    # Windows 8.1 and later
                    ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
                    awareness = DPIAwareness.PER_MONITOR_AWARE
                except:
                    try:
                        # Windows Vista and later
                        ctypes.windll.user32.SetProcessDPIAware()
                        awareness = DPIAwareness.SYSTEM_AWARE
                    except:
                        awareness = DPIAwareness.UNAWARE
            
            self.dpi_awareness = awareness
            
        except ImportError:
            self.dpi_awareness = DPIAwareness.UNAWARE
    
    def _initialize_macos_dpi(self):
        """Initialize DPI support on macOS."""
        # macOS handles DPI scaling automatically
        self.dpi_awareness = DPIAwareness.PER_MONITOR_AWARE
    
    def _initialize_linux_dpi(self):
        """Initialize DPI support on Linux."""
        # Linux DPI support varies by desktop environment
        self.dpi_awareness = DPIAwareness.SYSTEM_AWARE
    
    def _detect_dpi(self):
        """Detect current DPI settings."""
        try:
            # Get DPI from Tkinter
            dpi_x = self.root.winfo_fpixels('1i')
            dpi_y = self.root.winfo_fpixels('1i')  # Tkinter doesn't distinguish X/Y DPI
            
            # Calculate scale factor
            scale_factor = dpi_x / self.base_dpi
            
            self.dpi_info = DPIInfo(
                dpi_x=dpi_x,
                dpi_y=dpi_y,
                scale_factor=scale_factor,
                awareness=getattr(self, 'dpi_awareness', DPIAwareness.UNAWARE)
            )
            
            # Publish DPI detected event
            self.event_bus.publish("dpi.detected", {
                "dpi_info": self.dpi_info
            }, source="dpi_manager")
            
        except Exception as e:
            # Fallback to default DPI
            self.dpi_info = DPIInfo(
                dpi_x=self.base_dpi,
                dpi_y=self.base_dpi,
                scale_factor=1.0,
                awareness=DPIAwareness.UNAWARE
            )
            print(f"Warning: Could not detect DPI, using defaults: {e}")
    
    def _setup_event_handlers(self):
        """Setup event handlers."""
        # Monitor for DPI changes (Windows 10 and later)
        if platform.system() == "Windows" and self.dpi_awareness == DPIAwareness.PER_MONITOR_AWARE:
            self.root.bind("<Configure>", self._on_window_configure)
    
    def get_dpi_info(self) -> DPIInfo:
        """Get current DPI information."""
        return self.dpi_info or DPIInfo(self.base_dpi, self.base_dpi, 1.0, DPIAwareness.UNAWARE)
    
    def get_scale_factor(self) -> float:
        """Get current scale factor."""
        return self.get_dpi_info().scale_factor
    
    def scale_size(self, size: int) -> int:
        """Scale a size value for current DPI."""
        return int(size * self.get_scale_factor())
    
    def scale_point(self, point: Tuple[int, int]) -> Tuple[int, int]:
        """Scale a point (x, y) for current DPI."""
        scale = self.get_scale_factor()
        return (int(point[0] * scale), int(point[1] * scale))
    
    def scale_rect(self, rect: Tuple[int, int, int, int]) -> Tuple[int, int, int, int]:
        """Scale a rectangle (x, y, width, height) for current DPI."""
        scale = self.get_scale_factor()
        return (
            int(rect[0] * scale),
            int(rect[1] * scale),
            int(rect[2] * scale),
            int(rect[3] * scale)
        )
    
    def get_scaled_font(self, family: str = "TkDefaultFont", size: str = "normal", 
                       weight: str = "normal", slant: str = "roman") -> font.Font:
        """
        Get a font scaled for current DPI.
        
        Args:
            family: Font family name
            size: Font size key or integer
            weight: Font weight (normal, bold)
            slant: Font slant (roman, italic)
            
        Returns:
            Scaled Font object
        """
        # Get base size
        if isinstance(size, str):
            base_size = self.base_font_sizes.get(size, self.base_font_sizes["normal"])
        else:
            base_size = size
        
        # Scale font size
        scaled_size = self.scale_size(base_size)
        
        # Create cache key
        cache_key = f"{family}_{scaled_size}_{weight}_{slant}"
        
        # Return cached font if available
        if cache_key in self.scaled_fonts:
            return self.scaled_fonts[cache_key]
        
        # Create new scaled font
        try:
            scaled_font = font.Font(
                family=family,
                size=scaled_size,
                weight=weight,
                slant=slant
            )
            
            # Cache the font
            self.scaled_fonts[cache_key] = scaled_font
            
            return scaled_font
            
        except Exception:
            # Fallback to default font
            return font.nametofont("TkDefaultFont")
    
    def get_system_font_size(self) -> int:
        """Get system default font size, scaled for DPI."""
        try:
            system_font = font.nametofont("TkDefaultFont")
            base_size = abs(system_font.cget("size"))  # abs() because size can be negative
            return self.scale_size(base_size)
        except:
            return self.scale_size(9)  # Fallback size
    
    def configure_widget_dpi(self, widget: tk.Widget, **options):
        """Configure a widget for current DPI scaling."""
        scaled_options = {}
        
        # Scale size-related options
        size_options = ['width', 'height', 'padx', 'pady', 'ipadx', 'ipady', 
                       'borderwidth', 'highlightthickness', 'selectborderwidth']
        
        for option, value in options.items():
            if option in size_options and isinstance(value, int):
                scaled_options[option] = self.scale_size(value)
            elif option == 'font':
                if isinstance(value, (list, tuple)) and len(value) >= 2:
                    # Font tuple: (family, size, ...)
                    family = value[0]
                    size = value[1]
                    weight = value[2] if len(value) > 2 else "normal"
                    slant = value[3] if len(value) > 3 else "roman"
                    scaled_options[option] = self.get_scaled_font(family, size, weight, slant)
                elif isinstance(value, str):
                    # Font name or size key
                    scaled_options[option] = self.get_scaled_font(size=value)
                else:
                    scaled_options[option] = value
            else:
                scaled_options[option] = value
        
        # Apply scaled options to widget
        try:
            widget.configure(**scaled_options)
        except tk.TclError as e:
            # Some options might not be valid for this widget type
            print(f"Warning: Could not configure widget option: {e}")
    
    def create_scaled_image(self, image_path: str, size: Tuple[int, int]) -> tk.PhotoImage:
        """Create a scaled image for current DPI."""
        from PIL import Image, ImageTk
        
        # Scale the target size
        scaled_size = self.scale_point(size)
        
        try:
            # Load and resize image
            pil_image = Image.open(image_path)
            pil_image = pil_image.resize(scaled_size, Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            return ImageTk.PhotoImage(pil_image)
            
        except Exception as e:
            print(f"Warning: Could not create scaled image: {e}")
            # Return a placeholder
            return tk.PhotoImage(width=scaled_size[0], height=scaled_size[1])
    
    def get_dpi_category(self) -> str:
        """Get DPI category for the current scale factor."""
        scale = self.get_scale_factor()
        
        if scale <= 1.0:
            return "normal"
        elif scale <= 1.25:
            return "high"
        elif scale <= 1.5:
            return "very_high"
        else:
            return "ultra_high"
    
    def is_high_dpi(self) -> bool:
        """Check if current display is high DPI."""
        return self.get_scale_factor() > 1.25
    
    def _on_window_configure(self, event):
        """Handle window configure event for DPI changes."""
        # Only handle root window events
        if event.widget != self.root:
            return
        
        # Re-detect DPI (in case of monitor change)
        old_dpi = self.get_dpi_info()
        self._detect_dpi()
        new_dpi = self.get_dpi_info()
        
        # Check if DPI changed significantly
        if abs(new_dpi.scale_factor - old_dpi.scale_factor) > 0.1:
            # Clear font cache
            self.scaled_fonts.clear()
            
            # Publish DPI changed event
            self.event_bus.publish("dpi.changed", {
                "old_dpi": old_dpi,
                "new_dpi": new_dpi
            }, source="dpi_manager")
    
    def apply_dpi_scaling_to_tree(self, widget: tk.Widget):
        """Apply DPI scaling to a widget and all its children."""
        # Get widget class name
        widget_class = widget.winfo_class()
        
        # Apply scaling based on widget type
        if widget_class in ['Button', 'Label', 'Entry', 'Text', 'Listbox']:
            # Scale font if widget has font option
            try:
                current_font = widget.cget('font')
                if current_font:
                    if isinstance(current_font, str):
                        scaled_font = self.get_scaled_font(size=current_font)
                    else:
                        scaled_font = self.get_scaled_font()
                    widget.configure(font=scaled_font)
            except:
                pass
        
        elif widget_class in ['Frame', 'Toplevel']:
            # Scale padding and border
            try:
                padx = widget.cget('padx')
                pady = widget.cget('pady')
                if padx:
                    widget.configure(padx=self.scale_size(padx))
                if pady:
                    widget.configure(pady=self.scale_size(pady))
            except:
                pass
        
        # Recursively apply to children
        for child in widget.winfo_children():
            self.apply_dpi_scaling_to_tree(child)
    
    def get_scaling_info(self) -> Dict[str, Any]:
        """Get comprehensive scaling information."""
        dpi_info = self.get_dpi_info()
        
        return {
            "dpi_x": dpi_info.dpi_x,
            "dpi_y": dpi_info.dpi_y,
            "scale_factor": dpi_info.scale_factor,
            "awareness": dpi_info.awareness.value,
            "category": self.get_dpi_category(),
            "is_high_dpi": self.is_high_dpi(),
            "system_font_size": self.get_system_font_size(),
            "platform": platform.system()
        }


class DPIAwareWidget:
    """
    Mixin class for creating DPI-aware widgets.
    """
    
    def __init__(self, dpi_manager: DPIManager):
        self.dpi_manager = dpi_manager
        self._original_configure = self.configure
        
        # Override configure method to apply DPI scaling
        self.configure = self._dpi_aware_configure
    
    def _dpi_aware_configure(self, **options):
        """DPI-aware configure method."""
        self.dpi_manager.configure_widget_dpi(self, **options)
    
    def scale_size(self, size: int) -> int:
        """Scale a size for current DPI."""
        return self.dpi_manager.scale_size(size)
    
    def get_scaled_font(self, **font_options) -> font.Font:
        """Get a scaled font."""
        return self.dpi_manager.get_scaled_font(**font_options)


def create_dpi_aware_widget(widget_class, dpi_manager: DPIManager):
    """
    Create a DPI-aware version of a widget class.
    
    Args:
        widget_class: The widget class to make DPI-aware
        dpi_manager: DPI manager instance
        
    Returns:
        DPI-aware widget class
    """
    class DPIAwareWidgetClass(widget_class, DPIAwareWidget):
        def __init__(self, *args, **kwargs):
            widget_class.__init__(self, *args, **kwargs)
            DPIAwareWidget.__init__(self, dpi_manager)
    
    return DPIAwareWidgetClass