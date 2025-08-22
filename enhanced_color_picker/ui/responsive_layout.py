"""
Responsive Layout Manager

Provides responsive design capabilities for the Enhanced Color Picker application,
including adaptive layouts, DPI scaling, and window size management.
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, Optional, Callable, List, Tuple
from enum import Enum
from dataclasses import dataclass
import math

from ..core.event_bus import EventBus


class LayoutMode(Enum):
    """Layout modes for different screen sizes."""
    COMPACT = "compact"
    NORMAL = "normal"
    EXPANDED = "expanded"


class DPIScale(Enum):
    """DPI scaling levels."""
    SMALL = 0.8
    NORMAL = 1.0
    LARGE = 1.2
    EXTRA_LARGE = 1.5


@dataclass
class BreakPoint:
    """Responsive breakpoint definition."""
    name: str
    min_width: int
    min_height: int
    layout_mode: LayoutMode
    
    def matches(self, width: int, height: int) -> bool:
        """Check if dimensions match this breakpoint."""
        return width >= self.min_width and height >= self.min_height


@dataclass
class ResponsiveConfig:
    """Configuration for responsive behavior."""
    enable_responsive: bool = True
    enable_dpi_scaling: bool = True
    min_window_width: int = 800
    min_window_height: int = 600
    compact_threshold_width: int = 1000
    compact_threshold_height: int = 700
    auto_hide_panels: bool = True
    collapsible_panels: bool = True


class ResponsiveLayoutManager:
    """
    Manages responsive layout behavior for the application.
    
    Features:
    - Automatic layout mode switching based on window size
    - DPI scaling support
    - Panel visibility management
    - Breakpoint-based responsive behavior
    - Full-screen mode optimization
    """
    
    def __init__(self, root: tk.Tk, event_bus: EventBus, config: ResponsiveConfig = None):
        self.root = root
        self.event_bus = event_bus
        self.config = config or ResponsiveConfig()
        
        # Current state
        self.current_layout_mode = LayoutMode.NORMAL
        self.current_dpi_scale = DPIScale.NORMAL
        self.is_fullscreen = False
        self.window_state = "normal"
        
        # Breakpoints
        self.breakpoints = [
            BreakPoint("compact", 0, 0, LayoutMode.COMPACT),
            BreakPoint("normal", self.config.compact_threshold_width, 
                      self.config.compact_threshold_height, LayoutMode.NORMAL),
            BreakPoint("expanded", 1400, 900, LayoutMode.EXPANDED)
        ]
        
        # Registered components for responsive updates
        self.responsive_components: Dict[str, Callable] = {}
        
        # DPI detection
        self._detect_dpi_scale()
        
        # Setup event handlers
        self._setup_event_handlers()
        
        # Initial layout update
        self.root.after(100, self._update_layout)
    
    def _detect_dpi_scale(self):
        """Detect system DPI scaling."""
        try:
            # Get DPI from Tkinter
            dpi = self.root.winfo_fpixels('1i')
            
            # Standard DPI is 96
            scale_factor = dpi / 96.0
            
            if scale_factor <= 0.9:
                self.current_dpi_scale = DPIScale.SMALL
            elif scale_factor <= 1.1:
                self.current_dpi_scale = DPIScale.NORMAL
            elif scale_factor <= 1.3:
                self.current_dpi_scale = DPIScale.LARGE
            else:
                self.current_dpi_scale = DPIScale.EXTRA_LARGE
                
        except Exception:
            # Fallback to normal scaling
            self.current_dpi_scale = DPIScale.NORMAL
    
    def _setup_event_handlers(self):
        """Setup event handlers for window events."""
        self.root.bind("<Configure>", self._on_window_configure)
        self.root.bind("<Map>", self._on_window_map)
        self.root.bind("<Unmap>", self._on_window_unmap)
        
        # Subscribe to relevant events
        self.event_bus.subscribe("window.fullscreen_toggle", self._on_fullscreen_toggle)
        self.event_bus.subscribe("settings.dpi_scale_changed", self._on_dpi_scale_changed)
    
    def register_responsive_component(self, name: str, update_callback: Callable):
        """
        Register a component for responsive updates.
        
        Args:
            name: Component identifier
            update_callback: Function to call when layout changes
        """
        self.responsive_components[name] = update_callback
    
    def unregister_responsive_component(self, name: str):
        """Unregister a responsive component."""
        self.responsive_components.pop(name, None)
    
    def get_current_breakpoint(self) -> BreakPoint:
        """Get the current active breakpoint."""
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        
        # Find the largest matching breakpoint
        matching_breakpoints = [bp for bp in self.breakpoints if bp.matches(width, height)]
        
        if matching_breakpoints:
            return max(matching_breakpoints, key=lambda bp: bp.min_width * bp.min_height)
        
        # Fallback to compact mode
        return self.breakpoints[0]
    
    def get_layout_mode(self) -> LayoutMode:
        """Get current layout mode."""
        return self.current_layout_mode
    
    def get_dpi_scale(self) -> DPIScale:
        """Get current DPI scale."""
        return self.current_dpi_scale
    
    def is_compact_mode(self) -> bool:
        """Check if currently in compact mode."""
        return self.current_layout_mode == LayoutMode.COMPACT
    
    def is_expanded_mode(self) -> bool:
        """Check if currently in expanded mode."""
        return self.current_layout_mode == LayoutMode.EXPANDED
    
    def toggle_fullscreen(self):
        """Toggle fullscreen mode."""
        self.is_fullscreen = not self.is_fullscreen
        
        if self.is_fullscreen:
            self.root.attributes('-fullscreen', True)
            self.window_state = "fullscreen"
        else:
            self.root.attributes('-fullscreen', False)
            self.window_state = "normal"
        
        # Publish fullscreen event
        self.event_bus.publish("window.fullscreen_changed", {
            "fullscreen": self.is_fullscreen
        }, source="responsive_layout")
        
        # Update layout
        self._update_layout()
    
    def set_dpi_scale(self, scale: DPIScale):
        """Set DPI scaling manually."""
        if scale != self.current_dpi_scale:
            self.current_dpi_scale = scale
            self._update_layout()
    
    def get_scaled_size(self, size: int) -> int:
        """Get size scaled for current DPI."""
        if not self.config.enable_dpi_scaling:
            return size
        
        return int(size * self.current_dpi_scale.value)
    
    def get_scaled_font_size(self, base_size: int) -> int:
        """Get font size scaled for current DPI."""
        return self.get_scaled_size(base_size)
    
    def get_window_info(self) -> Dict[str, Any]:
        """Get current window information."""
        return {
            "width": self.root.winfo_width(),
            "height": self.root.winfo_height(),
            "layout_mode": self.current_layout_mode.value,
            "dpi_scale": self.current_dpi_scale.value,
            "fullscreen": self.is_fullscreen,
            "window_state": self.window_state,
            "breakpoint": self.get_current_breakpoint().name
        }
    
    def _update_layout(self):
        """Update layout based on current window size and settings."""
        if not self.config.enable_responsive:
            return
        
        # Get current breakpoint
        current_breakpoint = self.get_current_breakpoint()
        new_layout_mode = current_breakpoint.layout_mode
        
        # Check if layout mode changed
        layout_changed = new_layout_mode != self.current_layout_mode
        
        if layout_changed:
            self.current_layout_mode = new_layout_mode
            
            # Publish layout change event
            self.event_bus.publish("layout.mode_changed", {
                "old_mode": self.current_layout_mode.value if not layout_changed else None,
                "new_mode": new_layout_mode.value,
                "breakpoint": current_breakpoint.name,
                "window_info": self.get_window_info()
            }, source="responsive_layout")
        
        # Update all registered components
        self._update_responsive_components()
    
    def _update_responsive_components(self):
        """Update all registered responsive components."""
        layout_info = {
            "layout_mode": self.current_layout_mode,
            "dpi_scale": self.current_dpi_scale,
            "window_info": self.get_window_info(),
            "is_fullscreen": self.is_fullscreen
        }
        
        for name, callback in self.responsive_components.items():
            try:
                callback(layout_info)
            except Exception as e:
                print(f"Error updating responsive component '{name}': {e}")
    
    def _on_window_configure(self, event):
        """Handle window configure event."""
        # Only handle root window events
        if event.widget != self.root:
            return
        
        # Update layout after a short delay to avoid excessive updates
        self.root.after_cancel(getattr(self, '_layout_update_id', None))
        self._layout_update_id = self.root.after(100, self._update_layout)
    
    def _on_window_map(self, event):
        """Handle window map event."""
        if event.widget == self.root:
            self._update_layout()
    
    def _on_window_unmap(self, event):
        """Handle window unmap event."""
        pass
    
    def _on_fullscreen_toggle(self, event_data):
        """Handle fullscreen toggle event."""
        self.toggle_fullscreen()
    
    def _on_dpi_scale_changed(self, event_data):
        """Handle DPI scale change event."""
        scale_value = event_data.data.get("scale", 1.0)
        
        # Find matching DPI scale
        for scale in DPIScale:
            if abs(scale.value - scale_value) < 0.1:
                self.set_dpi_scale(scale)
                break


class ResponsiveFrame(ttk.Frame):
    """
    A frame that adapts to responsive layout changes.
    """
    
    def __init__(self, parent, layout_manager: ResponsiveLayoutManager, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.layout_manager = layout_manager
        self.responsive_config = {}
        
        # Register for responsive updates
        component_id = f"frame_{id(self)}"
        self.layout_manager.register_responsive_component(component_id, self._on_layout_update)
        
        # Store component ID for cleanup
        self._component_id = component_id
    
    def configure_responsive(self, **config):
        """Configure responsive behavior for this frame."""
        self.responsive_config.update(config)
    
    def _on_layout_update(self, layout_info):
        """Handle layout updates."""
        layout_mode = layout_info["layout_mode"]
        dpi_scale = layout_info["dpi_scale"]
        
        # Apply responsive configuration
        if "padding" in self.responsive_config:
            padding_config = self.responsive_config["padding"]
            
            if layout_mode == LayoutMode.COMPACT:
                padding = padding_config.get("compact", 5)
            elif layout_mode == LayoutMode.EXPANDED:
                padding = padding_config.get("expanded", 15)
            else:
                padding = padding_config.get("normal", 10)
            
            # Scale padding for DPI
            scaled_padding = self.layout_manager.get_scaled_size(padding)
            self.configure(padding=scaled_padding)
    
    def destroy(self):
        """Cleanup when frame is destroyed."""
        if hasattr(self, '_component_id'):
            self.layout_manager.unregister_responsive_component(self._component_id)
        super().destroy()


class ResponsivePanedWindow(ttk.PanedWindow):
    """
    A paned window that adapts to responsive layout changes.
    """
    
    def __init__(self, parent, layout_manager: ResponsiveLayoutManager, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.layout_manager = layout_manager
        self.responsive_config = {}
        self.original_orient = kwargs.get('orient', tk.HORIZONTAL)
        
        # Register for responsive updates
        component_id = f"paned_{id(self)}"
        self.layout_manager.register_responsive_component(component_id, self._on_layout_update)
        
        # Store component ID for cleanup
        self._component_id = component_id
    
    def configure_responsive(self, **config):
        """Configure responsive behavior for this paned window."""
        self.responsive_config.update(config)
    
    def _on_layout_update(self, layout_info):
        """Handle layout updates."""
        layout_mode = layout_info["layout_mode"]
        
        # Change orientation in compact mode if configured
        if "compact_orient" in self.responsive_config:
            if layout_mode == LayoutMode.COMPACT:
                new_orient = self.responsive_config["compact_orient"]
            else:
                new_orient = self.original_orient
            
            if self.cget('orient') != new_orient:
                self.configure(orient=new_orient)
        
        # Adjust sash positions
        if "sash_positions" in self.responsive_config:
            positions = self.responsive_config["sash_positions"]
            
            if layout_mode.value in positions:
                target_positions = positions[layout_mode.value]
                
                # Apply sash positions after a short delay
                self.after(10, lambda: self._apply_sash_positions(target_positions))
    
    def _apply_sash_positions(self, positions):
        """Apply sash positions."""
        try:
            for i, pos in enumerate(positions):
                if i < len(self.panes()):
                    self.sash_place(i, pos, 0)
        except Exception:
            pass  # Ignore errors in sash positioning
    
    def destroy(self):
        """Cleanup when paned window is destroyed."""
        if hasattr(self, '_component_id'):
            self.layout_manager.unregister_responsive_component(self._component_id)
        super().destroy()