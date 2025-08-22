"""
Fullscreen Mode Manager

Manages fullscreen mode functionality with optimized layouts and user experience.
"""

import tkinter as tk
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum

from ..core.event_bus import EventBus


class FullscreenMode(Enum):
    """Fullscreen mode types."""
    WINDOWED = "windowed"
    FULLSCREEN = "fullscreen"
    MAXIMIZED = "maximized"


@dataclass
class WindowState:
    """Stores window state for restoration."""
    geometry: str
    state: str
    attributes: Dict[str, Any]
    menu_visible: bool
    toolbar_visible: bool
    statusbar_visible: bool


class FullscreenManager:
    """
    Manages fullscreen mode with optimized UI layout.
    
    Features:
    - True fullscreen mode
    - Maximized window mode
    - UI element hiding/showing
    - Smooth transitions
    - Keyboard shortcuts
    - Multi-monitor support
    """
    
    def __init__(self, root: tk.Tk, event_bus: EventBus):
        self.root = root
        self.event_bus = event_bus
        
        # Current state
        self.current_mode = FullscreenMode.WINDOWED
        self.saved_state: Optional[WindowState] = None
        
        # UI element references (to be set by main window)
        self.ui_elements = {
            "menubar": None,
            "toolbar": None,
            "statusbar": None,
            "panels": {}
        }
        
        # Fullscreen settings
        self.hide_cursor_in_fullscreen = False
        self.auto_hide_ui_delay = 3000  # ms
        self.ui_fade_enabled = True
        
        # Auto-hide timer
        self._auto_hide_timer = None
        self._ui_visible = True
        
        # Setup event handlers
        self._setup_event_handlers()
    
    def _setup_event_handlers(self):
        """Setup event handlers."""
        # Keyboard shortcuts
        self.root.bind("<F11>", self._on_f11_pressed)
        self.root.bind("<Escape>", self._on_escape_pressed)
        self.root.bind("<Alt-Return>", self._on_alt_enter_pressed)
        
        # Mouse movement for auto-hide
        self.root.bind("<Motion>", self._on_mouse_motion)
        
        # Subscribe to events
        self.event_bus.subscribe("fullscreen.toggle", self._on_toggle_fullscreen)
        self.event_bus.subscribe("fullscreen.enter", self._on_enter_fullscreen)
        self.event_bus.subscribe("fullscreen.exit", self._on_exit_fullscreen)
    
    def register_ui_element(self, element_type: str, element, **options):
        """
        Register a UI element for fullscreen management.
        
        Args:
            element_type: Type of element (menubar, toolbar, statusbar, panel)
            element: The UI element widget
            **options: Additional options for the element
        """
        if element_type in ["menubar", "toolbar", "statusbar"]:
            self.ui_elements[element_type] = {
                "widget": element,
                "options": options
            }
        elif element_type == "panel":
            panel_id = options.get("panel_id", f"panel_{len(self.ui_elements['panels'])}")
            self.ui_elements["panels"][panel_id] = {
                "widget": element,
                "options": options
            }
    
    def get_current_mode(self) -> FullscreenMode:
        """Get current fullscreen mode."""
        return self.current_mode
    
    def is_fullscreen(self) -> bool:
        """Check if currently in fullscreen mode."""
        return self.current_mode == FullscreenMode.FULLSCREEN
    
    def is_maximized(self) -> bool:
        """Check if window is maximized."""
        return self.current_mode == FullscreenMode.MAXIMIZED
    
    def toggle_fullscreen(self):
        """Toggle between windowed and fullscreen mode."""
        if self.current_mode == FullscreenMode.FULLSCREEN:
            self.exit_fullscreen()
        else:
            self.enter_fullscreen()
    
    def enter_fullscreen(self):
        """Enter fullscreen mode."""
        if self.current_mode == FullscreenMode.FULLSCREEN:
            return
        
        # Save current window state
        self._save_window_state()
        
        # Enter fullscreen
        self.root.attributes('-fullscreen', True)
        self.current_mode = FullscreenMode.FULLSCREEN
        
        # Optimize UI for fullscreen
        self._optimize_ui_for_fullscreen()
        
        # Start auto-hide timer if enabled
        if self.auto_hide_ui_delay > 0:
            self._start_auto_hide_timer()
        
        # Hide cursor if enabled
        if self.hide_cursor_in_fullscreen:
            self.root.config(cursor="none")
        
        # Publish event
        self.event_bus.publish("fullscreen.entered", {
            "mode": self.current_mode.value
        }, source="fullscreen_manager")
    
    def exit_fullscreen(self):
        """Exit fullscreen mode."""
        if self.current_mode == FullscreenMode.WINDOWED:
            return
        
        # Exit fullscreen
        self.root.attributes('-fullscreen', False)
        
        # Restore window state
        self._restore_window_state()
        
        # Restore UI elements
        self._restore_ui_elements()
        
        # Stop auto-hide timer
        self._stop_auto_hide_timer()
        
        # Restore cursor
        self.root.config(cursor="")
        
        # Update mode
        self.current_mode = FullscreenMode.WINDOWED
        
        # Publish event
        self.event_bus.publish("fullscreen.exited", {
            "mode": self.current_mode.value
        }, source="fullscreen_manager")
    
    def toggle_maximize(self):
        """Toggle window maximized state."""
        if self.current_mode == FullscreenMode.MAXIMIZED:
            self.restore_window()
        else:
            self.maximize_window()
    
    def maximize_window(self):
        """Maximize the window."""
        if self.current_mode == FullscreenMode.FULLSCREEN:
            self.exit_fullscreen()
        
        # Save current state if not already saved
        if self.current_mode == FullscreenMode.WINDOWED:
            self._save_window_state()
        
        # Maximize window
        self.root.state('zoomed')
        self.current_mode = FullscreenMode.MAXIMIZED
        
        # Publish event
        self.event_bus.publish("window.maximized", {
            "mode": self.current_mode.value
        }, source="fullscreen_manager")
    
    def restore_window(self):
        """Restore window to normal size."""
        if self.current_mode == FullscreenMode.FULLSCREEN:
            self.exit_fullscreen()
            return
        
        # Restore window state
        self.root.state('normal')
        self._restore_window_state()
        
        self.current_mode = FullscreenMode.WINDOWED
        
        # Publish event
        self.event_bus.publish("window.restored", {
            "mode": self.current_mode.value
        }, source="fullscreen_manager")
    
    def _save_window_state(self):
        """Save current window state."""
        if self.saved_state is not None:
            return  # Already saved
        
        # Get current geometry
        geometry = self.root.geometry()
        state = self.root.state()
        
        # Get window attributes
        attributes = {}
        try:
            attributes['topmost'] = self.root.attributes('-topmost')
            attributes['alpha'] = self.root.attributes('-alpha')
        except:
            pass
        
        # Check UI element visibility
        menu_visible = bool(self.root.cget('menu'))
        toolbar_visible = self._is_ui_element_visible("toolbar")
        statusbar_visible = self._is_ui_element_visible("statusbar")
        
        self.saved_state = WindowState(
            geometry=geometry,
            state=state,
            attributes=attributes,
            menu_visible=menu_visible,
            toolbar_visible=toolbar_visible,
            statusbar_visible=statusbar_visible
        )
    
    def _restore_window_state(self):
        """Restore saved window state."""
        if self.saved_state is None:
            return
        
        # Restore geometry and state
        if self.saved_state.state == 'normal':
            self.root.geometry(self.saved_state.geometry)
        self.root.state(self.saved_state.state)
        
        # Restore attributes
        for attr, value in self.saved_state.attributes.items():
            try:
                self.root.attributes(f'-{attr}', value)
            except:
                pass
        
        # Clear saved state
        self.saved_state = None
    
    def _optimize_ui_for_fullscreen(self):
        """Optimize UI layout for fullscreen mode."""
        # Hide menu bar
        self.root.config(menu="")
        
        # Hide or minimize UI elements based on configuration
        self._hide_ui_elements_for_fullscreen()
        
        # Adjust layout for fullscreen
        self._adjust_layout_for_fullscreen()
    
    def _hide_ui_elements_for_fullscreen(self):
        """Hide UI elements in fullscreen mode."""
        # Hide toolbar if configured
        toolbar_info = self.ui_elements.get("toolbar")
        if toolbar_info and toolbar_info["options"].get("hide_in_fullscreen", True):
            self._hide_ui_element("toolbar")
        
        # Hide status bar if configured
        statusbar_info = self.ui_elements.get("statusbar")
        if statusbar_info and statusbar_info["options"].get("hide_in_fullscreen", True):
            self._hide_ui_element("statusbar")
        
        # Hide panels if configured
        for panel_id, panel_info in self.ui_elements["panels"].items():
            if panel_info["options"].get("hide_in_fullscreen", False):
                self._hide_ui_element("panel", panel_id)
    
    def _restore_ui_elements(self):
        """Restore UI elements when exiting fullscreen."""
        # Restore menu bar
        if self.saved_state and self.saved_state.menu_visible:
            # Menu restoration is handled by main window
            pass
        
        # Restore toolbar
        if self.saved_state and self.saved_state.toolbar_visible:
            self._show_ui_element("toolbar")
        
        # Restore status bar
        if self.saved_state and self.saved_state.statusbar_visible:
            self._show_ui_element("statusbar")
        
        # Restore panels
        for panel_id, panel_info in self.ui_elements["panels"].items():
            if panel_info["options"].get("restore_after_fullscreen", True):
                self._show_ui_element("panel", panel_id)
    
    def _adjust_layout_for_fullscreen(self):
        """Adjust layout for fullscreen mode."""
        # Publish layout adjustment event
        self.event_bus.publish("layout.fullscreen_optimize", {
            "fullscreen": True
        }, source="fullscreen_manager")
    
    def _hide_ui_element(self, element_type: str, element_id: str = None):
        """Hide a UI element."""
        if element_type in ["toolbar", "statusbar"]:
            element_info = self.ui_elements.get(element_type)
            if element_info and element_info["widget"]:
                element_info["widget"].pack_forget()
        elif element_type == "panel" and element_id:
            panel_info = self.ui_elements["panels"].get(element_id)
            if panel_info and panel_info["widget"]:
                panel_info["widget"].pack_forget()
    
    def _show_ui_element(self, element_type: str, element_id: str = None):
        """Show a UI element."""
        if element_type in ["toolbar", "statusbar"]:
            element_info = self.ui_elements.get(element_type)
            if element_info and element_info["widget"]:
                # Restore original packing
                pack_options = element_info["options"].get("pack_options", {})
                element_info["widget"].pack(**pack_options)
        elif element_type == "panel" and element_id:
            panel_info = self.ui_elements["panels"].get(element_id)
            if panel_info and panel_info["widget"]:
                pack_options = panel_info["options"].get("pack_options", {})
                panel_info["widget"].pack(**pack_options)
    
    def _is_ui_element_visible(self, element_type: str, element_id: str = None) -> bool:
        """Check if a UI element is visible."""
        if element_type in ["toolbar", "statusbar"]:
            element_info = self.ui_elements.get(element_type)
            if element_info and element_info["widget"]:
                try:
                    return element_info["widget"].winfo_viewable()
                except:
                    return False
        elif element_type == "panel" and element_id:
            panel_info = self.ui_elements["panels"].get(element_id)
            if panel_info and panel_info["widget"]:
                try:
                    return panel_info["widget"].winfo_viewable()
                except:
                    return False
        return False
    
    def _start_auto_hide_timer(self):
        """Start auto-hide timer for UI elements."""
        self._stop_auto_hide_timer()
        self._auto_hide_timer = self.root.after(self.auto_hide_ui_delay, self._auto_hide_ui)
    
    def _stop_auto_hide_timer(self):
        """Stop auto-hide timer."""
        if self._auto_hide_timer:
            self.root.after_cancel(self._auto_hide_timer)
            self._auto_hide_timer = None
    
    def _auto_hide_ui(self):
        """Auto-hide UI elements after inactivity."""
        if not self.is_fullscreen():
            return
        
        # Hide UI elements with fade effect if enabled
        if self.ui_fade_enabled:
            self._fade_out_ui()
        else:
            self._hide_ui_instantly()
        
        self._ui_visible = False
    
    def _show_ui_on_activity(self):
        """Show UI elements on user activity."""
        if not self.is_fullscreen() or self._ui_visible:
            return
        
        # Show UI elements with fade effect if enabled
        if self.ui_fade_enabled:
            self._fade_in_ui()
        else:
            self._show_ui_instantly()
        
        self._ui_visible = True
        
        # Restart auto-hide timer
        self._start_auto_hide_timer()
    
    def _fade_out_ui(self):
        """Fade out UI elements."""
        # Simple implementation - could be enhanced with gradual alpha changes
        self._hide_ui_instantly()
    
    def _fade_in_ui(self):
        """Fade in UI elements."""
        # Simple implementation - could be enhanced with gradual alpha changes
        self._show_ui_instantly()
    
    def _hide_ui_instantly(self):
        """Hide UI elements instantly."""
        # Hide cursor
        if self.hide_cursor_in_fullscreen:
            self.root.config(cursor="none")
        
        # Hide other UI elements as configured
        pass
    
    def _show_ui_instantly(self):
        """Show UI elements instantly."""
        # Show cursor
        self.root.config(cursor="")
        
        # Show other UI elements as configured
        pass
    
    # Event handlers
    def _on_f11_pressed(self, event):
        """Handle F11 key press."""
        self.toggle_fullscreen()
    
    def _on_escape_pressed(self, event):
        """Handle Escape key press."""
        if self.is_fullscreen():
            self.exit_fullscreen()
    
    def _on_alt_enter_pressed(self, event):
        """Handle Alt+Enter key press."""
        self.toggle_fullscreen()
    
    def _on_mouse_motion(self, event):
        """Handle mouse motion for auto-hide functionality."""
        if self.is_fullscreen() and not self._ui_visible:
            self._show_ui_on_activity()
    
    def _on_toggle_fullscreen(self, event_data):
        """Handle toggle fullscreen event."""
        self.toggle_fullscreen()
    
    def _on_enter_fullscreen(self, event_data):
        """Handle enter fullscreen event."""
        self.enter_fullscreen()
    
    def _on_exit_fullscreen(self, event_data):
        """Handle exit fullscreen event."""
        self.exit_fullscreen()
    
    def get_fullscreen_info(self) -> Dict[str, Any]:
        """Get fullscreen mode information."""
        return {
            "mode": self.current_mode.value,
            "is_fullscreen": self.is_fullscreen(),
            "is_maximized": self.is_maximized(),
            "ui_visible": self._ui_visible,
            "auto_hide_enabled": self.auto_hide_ui_delay > 0,
            "cursor_hidden": self.hide_cursor_in_fullscreen,
            "fade_enabled": self.ui_fade_enabled
        }
    
    def configure_fullscreen(self, **options):
        """Configure fullscreen behavior."""
        if "hide_cursor" in options:
            self.hide_cursor_in_fullscreen = options["hide_cursor"]
        
        if "auto_hide_delay" in options:
            self.auto_hide_ui_delay = options["auto_hide_delay"]
        
        if "ui_fade" in options:
            self.ui_fade_enabled = options["ui_fade"]
        
        # Apply changes if currently in fullscreen
        if self.is_fullscreen():
            if "hide_cursor" in options:
                cursor = "none" if self.hide_cursor_in_fullscreen else ""
                self.root.config(cursor=cursor)
            
            if "auto_hide_delay" in options:
                if self.auto_hide_ui_delay > 0:
                    self._start_auto_hide_timer()
                else:
                    self._stop_auto_hide_timer()
    
    def cleanup(self):
        """Cleanup resources."""
        self._stop_auto_hide_timer()
        
        if self.is_fullscreen():
            self.exit_fullscreen()