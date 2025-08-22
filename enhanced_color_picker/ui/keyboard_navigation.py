"""
Keyboard Navigation Manager

Provides comprehensive keyboard navigation support for the Enhanced Color Picker,
including focus management, keyboard shortcuts, and accessibility features.
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, Optional, List, Callable, Union
from dataclasses import dataclass
from enum import Enum
import re

from ..core.event_bus import EventBus


class NavigationMode(Enum):
    """Navigation modes."""
    NORMAL = "normal"
    MODAL = "modal"
    DISABLED = "disabled"


class FocusDirection(Enum):
    """Focus movement directions."""
    NEXT = "next"
    PREVIOUS = "previous"
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"
    FIRST = "first"
    LAST = "last"


@dataclass
class KeyBinding:
    """Keyboard shortcut binding."""
    key_sequence: str
    callback: Callable
    description: str
    context: str = "global"
    enabled: bool = True


@dataclass
class FocusableWidget:
    """Information about a focusable widget."""
    widget: tk.Widget
    tab_order: int
    group: str
    can_receive_focus: Callable[[], bool] = lambda: True
    on_focus_in: Optional[Callable] = None
    on_focus_out: Optional[Callable] = None


class KeyboardNavigationManager:
    """
    Manages keyboard navigation and accessibility features.
    
    Features:
    - Tab order management
    - Custom keyboard shortcuts
    - Focus management
    - Screen reader support
    - High contrast mode
    - Keyboard-only operation
    """
    
    def __init__(self, root: tk.Tk, event_bus: EventBus):
        self.root = root
        self.event_bus = event_bus
        
        # Navigation state
        self.navigation_mode = NavigationMode.NORMAL
        self.current_focus_group = "main"
        
        # Focus management
        self.focusable_widgets: Dict[str, List[FocusableWidget]] = {}
        self.focus_history: List[tk.Widget] = []
        self.max_focus_history = 10
        
        # Keyboard shortcuts
        self.key_bindings: Dict[str, KeyBinding] = {}
        self.context_stack: List[str] = ["global"]
        
        # Accessibility settings
        self.high_contrast_mode = False
        self.screen_reader_mode = False
        self.keyboard_only_mode = False
        self.focus_indicators_enabled = True
        
        # Visual feedback
        self.focus_ring_color = "#0078d4"
        self.focus_ring_width = 2
        
        # Setup
        self._setup_default_bindings()
        self._setup_focus_management()
        self._setup_event_handlers()
    
    def _setup_default_bindings(self):
        """Setup default keyboard bindings."""
        # Navigation
        self.register_key_binding("Tab", self._focus_next, "Move to next focusable element")
        self.register_key_binding("Shift+Tab", self._focus_previous, "Move to previous focusable element")
        self.register_key_binding("F6", self._cycle_focus_groups, "Cycle between focus groups")
        self.register_key_binding("Shift+F6", self._cycle_focus_groups_reverse, "Cycle between focus groups (reverse)")
        
        # Application shortcuts
        self.register_key_binding("Alt+F4", self._close_application, "Close application")
        self.register_key_binding("F1", self._show_help, "Show help")
        self.register_key_binding("F10", self._activate_menu, "Activate menu bar")
        
        # Accessibility
        self.register_key_binding("Alt+Shift+H", self._toggle_high_contrast, "Toggle high contrast mode")
        self.register_key_binding("Alt+Shift+K", self._toggle_keyboard_mode, "Toggle keyboard-only mode")
        
        # Focus management
        self.register_key_binding("Ctrl+Home", self._focus_first, "Move to first focusable element")
        self.register_key_binding("Ctrl+End", self._focus_last, "Move to last focusable element")
        self.register_key_binding("Alt+Left", self._focus_previous_in_history, "Go back in focus history")
    
    def _setup_focus_management(self):
        """Setup focus management system."""
        # Bind focus events to root
        self.root.bind_all("<FocusIn>", self._on_focus_in)
        self.root.bind_all("<FocusOut>", self._on_focus_out)
        
        # Setup focus groups
        self.focusable_widgets = {
            "main": [],
            "toolbar": [],
            "panels": [],
            "dialogs": []
        }
    
    def _setup_event_handlers(self):
        """Setup event handlers."""
        # Subscribe to accessibility events
        self.event_bus.subscribe("accessibility.high_contrast_toggle", self._on_high_contrast_toggle)
        self.event_bus.subscribe("accessibility.screen_reader_toggle", self._on_screen_reader_toggle)
        self.event_bus.subscribe("accessibility.keyboard_mode_toggle", self._on_keyboard_mode_toggle)
        
        # Subscribe to UI events
        self.event_bus.subscribe("ui.modal_opened", self._on_modal_opened)
        self.event_bus.subscribe("ui.modal_closed", self._on_modal_closed)
    
    def register_key_binding(self, key_sequence: str, callback: Callable, 
                           description: str, context: str = "global"):
        """
        Register a keyboard shortcut.
        
        Args:
            key_sequence: Key sequence (e.g., "Ctrl+O", "F1", "Alt+Shift+S")
            callback: Function to call when shortcut is pressed
            description: Human-readable description
            context: Context where shortcut is active
        """
        # Normalize key sequence
        normalized_key = self._normalize_key_sequence(key_sequence)
        
        # Create binding
        binding = KeyBinding(
            key_sequence=normalized_key,
            callback=callback,
            description=description,
            context=context
        )
        
        # Store binding
        self.key_bindings[normalized_key] = binding
        
        # Bind to Tkinter
        try:
            self.root.bind_all(f"<{normalized_key}>", self._handle_key_press)
        except tk.TclError:
            print(f"Warning: Could not bind key sequence: {key_sequence}")
    
    def unregister_key_binding(self, key_sequence: str):
        """Unregister a keyboard shortcut."""
        normalized_key = self._normalize_key_sequence(key_sequence)
        
        if normalized_key in self.key_bindings:
            # Remove binding
            del self.key_bindings[normalized_key]
            
            # Unbind from Tkinter
            try:
                self.root.unbind_all(f"<{normalized_key}>")
            except tk.TclError:
                pass
    
    def register_focusable_widget(self, widget: tk.Widget, group: str = "main", 
                                 tab_order: int = None, **options):
        """
        Register a widget as focusable.
        
        Args:
            widget: The widget to register
            group: Focus group name
            tab_order: Tab order within group (auto-assigned if None)
            **options: Additional options (can_receive_focus, on_focus_in, on_focus_out)
        """
        if group not in self.focusable_widgets:
            self.focusable_widgets[group] = []
        
        # Auto-assign tab order if not provided
        if tab_order is None:
            tab_order = len(self.focusable_widgets[group])
        
        # Create focusable widget info
        focusable = FocusableWidget(
            widget=widget,
            tab_order=tab_order,
            group=group,
            can_receive_focus=options.get("can_receive_focus", lambda: True),
            on_focus_in=options.get("on_focus_in"),
            on_focus_out=options.get("on_focus_out")
        )
        
        # Add to group
        self.focusable_widgets[group].append(focusable)
        
        # Sort by tab order
        self.focusable_widgets[group].sort(key=lambda x: x.tab_order)
        
        # Configure widget for accessibility
        self._configure_widget_accessibility(widget)
    
    def unregister_focusable_widget(self, widget: tk.Widget):
        """Unregister a focusable widget."""
        for group_widgets in self.focusable_widgets.values():
            group_widgets[:] = [fw for fw in group_widgets if fw.widget != widget]
    
    def set_focus_group(self, group: str):
        """Set the current focus group."""
        if group in self.focusable_widgets:
            self.current_focus_group = group
            
            # Focus first widget in group
            self._focus_first_in_group(group)
    
    def get_focusable_widgets_in_group(self, group: str) -> List[FocusableWidget]:
        """Get all focusable widgets in a group."""
        return [fw for fw in self.focusable_widgets.get(group, []) 
                if fw.can_receive_focus()]
    
    def focus_widget(self, widget: tk.Widget):
        """Focus a specific widget."""
        try:
            widget.focus_set()
            self._add_to_focus_history(widget)
        except tk.TclError:
            pass
    
    def get_current_focus(self) -> Optional[tk.Widget]:
        """Get currently focused widget."""
        try:
            return self.root.focus_get()
        except:
            return None
    
    def push_context(self, context: str):
        """Push a new keyboard context."""
        self.context_stack.append(context)
    
    def pop_context(self) -> Optional[str]:
        """Pop the current keyboard context."""
        if len(self.context_stack) > 1:
            return self.context_stack.pop()
        return None
    
    def get_current_context(self) -> str:
        """Get the current keyboard context."""
        return self.context_stack[-1] if self.context_stack else "global"
    
    def enable_high_contrast_mode(self, enabled: bool = True):
        """Enable or disable high contrast mode."""
        self.high_contrast_mode = enabled
        
        # Apply high contrast styling
        self._apply_high_contrast_styling()
        
        # Publish event
        self.event_bus.publish("accessibility.high_contrast_changed", {
            "enabled": enabled
        }, source="keyboard_navigation")
    
    def enable_screen_reader_mode(self, enabled: bool = True):
        """Enable or disable screen reader mode."""
        self.screen_reader_mode = enabled
        
        # Configure for screen readers
        self._configure_screen_reader_support()
        
        # Publish event
        self.event_bus.publish("accessibility.screen_reader_changed", {
            "enabled": enabled
        }, source="keyboard_navigation")
    
    def enable_keyboard_only_mode(self, enabled: bool = True):
        """Enable or disable keyboard-only mode."""
        self.keyboard_only_mode = enabled
        
        # Configure keyboard-only features
        self._configure_keyboard_only_mode()
        
        # Publish event
        self.event_bus.publish("accessibility.keyboard_only_changed", {
            "enabled": enabled
        }, source="keyboard_navigation")
    
    def get_key_bindings_for_context(self, context: str = None) -> List[KeyBinding]:
        """Get key bindings for a specific context."""
        if context is None:
            context = self.get_current_context()
        
        return [binding for binding in self.key_bindings.values() 
                if binding.context == context or binding.context == "global"]
    
    def _normalize_key_sequence(self, key_sequence: str) -> str:
        """Normalize key sequence format."""
        # Convert common variations
        key_sequence = key_sequence.replace("Ctrl", "Control")
        key_sequence = key_sequence.replace("Cmd", "Command")  # macOS
        
        return key_sequence
    
    def _handle_key_press(self, event):
        """Handle key press events."""
        # Get key sequence from event
        key_sequence = self._event_to_key_sequence(event)
        
        # Find matching binding
        binding = self.key_bindings.get(key_sequence)
        
        if binding and binding.enabled:
            # Check context
            current_context = self.get_current_context()
            if binding.context == "global" or binding.context == current_context:
                try:
                    # Call the callback
                    result = binding.callback()
                    
                    # If callback returns True, prevent default handling
                    if result is True:
                        return "break"
                        
                except Exception as e:
                    print(f"Error executing key binding {key_sequence}: {e}")
    
    def _event_to_key_sequence(self, event) -> str:
        """Convert Tkinter event to key sequence string."""
        modifiers = []
        
        if event.state & 0x4:  # Control
            modifiers.append("Control")
        if event.state & 0x8:  # Alt
            modifiers.append("Alt")
        if event.state & 0x1:  # Shift
            modifiers.append("Shift")
        
        key = event.keysym
        
        if modifiers:
            return "+".join(modifiers + [key])
        else:
            return key
    
    def _configure_widget_accessibility(self, widget: tk.Widget):
        """Configure a widget for accessibility."""
        # Add focus indicators if enabled
        if self.focus_indicators_enabled:
            self._add_focus_indicators(widget)
        
        # Configure for screen readers
        if self.screen_reader_mode:
            self._configure_widget_for_screen_reader(widget)
    
    def _add_focus_indicators(self, widget: tk.Widget):
        """Add visual focus indicators to a widget."""
        def on_focus_in(event):
            try:
                widget.configure(highlightbackground=self.focus_ring_color,
                               highlightthickness=self.focus_ring_width)
            except tk.TclError:
                pass
        
        def on_focus_out(event):
            try:
                widget.configure(highlightthickness=0)
            except tk.TclError:
                pass
        
        widget.bind("<FocusIn>", on_focus_in)
        widget.bind("<FocusOut>", on_focus_out)
    
    def _configure_widget_for_screen_reader(self, widget: tk.Widget):
        """Configure widget for screen reader compatibility."""
        # Add ARIA-like attributes where possible
        widget_class = widget.winfo_class()
        
        if widget_class == "Button":
            # Ensure button has accessible name
            text = widget.cget("text") if hasattr(widget, "cget") else ""
            if not text:
                # Try to get text from other sources
                pass
        
        elif widget_class == "Entry":
            # Add role information
            pass
        
        elif widget_class == "Canvas":
            # Add canvas description
            pass
    
    def _apply_high_contrast_styling(self):
        """Apply high contrast styling to the application."""
        if self.high_contrast_mode:
            # High contrast colors
            bg_color = "#000000"
            fg_color = "#ffffff"
            select_bg = "#ffffff"
            select_fg = "#000000"
            
            # Apply to root
            try:
                self.root.configure(bg=bg_color, fg=fg_color)
            except tk.TclError:
                pass
            
            # Configure ttk styles
            style = ttk.Style()
            style.configure(".", background=bg_color, foreground=fg_color)
            style.configure("TButton", background=bg_color, foreground=fg_color)
            style.configure("TLabel", background=bg_color, foreground=fg_color)
            style.configure("TEntry", fieldbackground=bg_color, foreground=fg_color)
            
        else:
            # Restore normal styling
            # This would typically restore from theme
            pass
    
    def _configure_screen_reader_support(self):
        """Configure application for screen reader support."""
        if self.screen_reader_mode:
            # Enable additional accessibility features
            self.focus_indicators_enabled = True
            
            # Configure widgets for better screen reader support
            for group_widgets in self.focusable_widgets.values():
                for focusable in group_widgets:
                    self._configure_widget_for_screen_reader(focusable.widget)
    
    def _configure_keyboard_only_mode(self):
        """Configure application for keyboard-only operation."""
        if self.keyboard_only_mode:
            # Ensure all interactive elements are keyboard accessible
            self.focus_indicators_enabled = True
            
            # Disable mouse-only features
            # This would be implemented based on specific UI components
            pass
    
    def _add_to_focus_history(self, widget: tk.Widget):
        """Add widget to focus history."""
        # Remove widget if already in history
        if widget in self.focus_history:
            self.focus_history.remove(widget)
        
        # Add to front of history
        self.focus_history.insert(0, widget)
        
        # Limit history size
        if len(self.focus_history) > self.max_focus_history:
            self.focus_history = self.focus_history[:self.max_focus_history]
    
    # Navigation methods
    def _focus_next(self):
        """Focus next widget in tab order."""
        current_widget = self.get_current_focus()
        focusable_widgets = self.get_focusable_widgets_in_group(self.current_focus_group)
        
        if not focusable_widgets:
            return
        
        # Find current widget index
        current_index = -1
        for i, fw in enumerate(focusable_widgets):
            if fw.widget == current_widget:
                current_index = i
                break
        
        # Move to next widget
        next_index = (current_index + 1) % len(focusable_widgets)
        next_widget = focusable_widgets[next_index].widget
        
        self.focus_widget(next_widget)
        return True
    
    def _focus_previous(self):
        """Focus previous widget in tab order."""
        current_widget = self.get_current_focus()
        focusable_widgets = self.get_focusable_widgets_in_group(self.current_focus_group)
        
        if not focusable_widgets:
            return
        
        # Find current widget index
        current_index = -1
        for i, fw in enumerate(focusable_widgets):
            if fw.widget == current_widget:
                current_index = i
                break
        
        # Move to previous widget
        prev_index = (current_index - 1) % len(focusable_widgets)
        prev_widget = focusable_widgets[prev_index].widget
        
        self.focus_widget(prev_widget)
        return True
    
    def _focus_first(self):
        """Focus first widget in current group."""
        self._focus_first_in_group(self.current_focus_group)
        return True
    
    def _focus_last(self):
        """Focus last widget in current group."""
        focusable_widgets = self.get_focusable_widgets_in_group(self.current_focus_group)
        if focusable_widgets:
            self.focus_widget(focusable_widgets[-1].widget)
        return True
    
    def _focus_first_in_group(self, group: str):
        """Focus first widget in specified group."""
        focusable_widgets = self.get_focusable_widgets_in_group(group)
        if focusable_widgets:
            self.focus_widget(focusable_widgets[0].widget)
    
    def _cycle_focus_groups(self):
        """Cycle to next focus group."""
        groups = list(self.focusable_widgets.keys())
        if not groups:
            return
        
        current_index = groups.index(self.current_focus_group) if self.current_focus_group in groups else 0
        next_index = (current_index + 1) % len(groups)
        
        self.set_focus_group(groups[next_index])
        return True
    
    def _cycle_focus_groups_reverse(self):
        """Cycle to previous focus group."""
        groups = list(self.focusable_widgets.keys())
        if not groups:
            return
        
        current_index = groups.index(self.current_focus_group) if self.current_focus_group in groups else 0
        prev_index = (current_index - 1) % len(groups)
        
        self.set_focus_group(groups[prev_index])
        return True
    
    def _focus_previous_in_history(self):
        """Focus previous widget in focus history."""
        if len(self.focus_history) > 1:
            # Skip current widget (index 0) and focus previous (index 1)
            prev_widget = self.focus_history[1]
            self.focus_widget(prev_widget)
        return True
    
    # Application shortcuts
    def _close_application(self):
        """Close the application."""
        self.event_bus.publish("app.close_requested", source="keyboard_navigation")
        return True
    
    def _show_help(self):
        """Show help dialog."""
        self.event_bus.publish("help.show", source="keyboard_navigation")
        return True
    
    def _activate_menu(self):
        """Activate the menu bar."""
        self.event_bus.publish("menu.activate", source="keyboard_navigation")
        return True
    
    # Accessibility toggles
    def _toggle_high_contrast(self):
        """Toggle high contrast mode."""
        self.enable_high_contrast_mode(not self.high_contrast_mode)
        return True
    
    def _toggle_keyboard_mode(self):
        """Toggle keyboard-only mode."""
        self.enable_keyboard_only_mode(not self.keyboard_only_mode)
        return True
    
    # Event handlers
    def _on_focus_in(self, event):
        """Handle focus in event."""
        widget = event.widget
        
        # Find focusable widget info
        for group_widgets in self.focusable_widgets.values():
            for fw in group_widgets:
                if fw.widget == widget:
                    # Call custom focus in handler
                    if fw.on_focus_in:
                        fw.on_focus_in()
                    break
        
        # Add to focus history
        self._add_to_focus_history(widget)
    
    def _on_focus_out(self, event):
        """Handle focus out event."""
        widget = event.widget
        
        # Find focusable widget info
        for group_widgets in self.focusable_widgets.values():
            for fw in group_widgets:
                if fw.widget == widget:
                    # Call custom focus out handler
                    if fw.on_focus_out:
                        fw.on_focus_out()
                    break
    
    def _on_high_contrast_toggle(self, event_data):
        """Handle high contrast toggle event."""
        enabled = event_data.data.get("enabled", not self.high_contrast_mode)
        self.enable_high_contrast_mode(enabled)
    
    def _on_screen_reader_toggle(self, event_data):
        """Handle screen reader toggle event."""
        enabled = event_data.data.get("enabled", not self.screen_reader_mode)
        self.enable_screen_reader_mode(enabled)
    
    def _on_keyboard_mode_toggle(self, event_data):
        """Handle keyboard mode toggle event."""
        enabled = event_data.data.get("enabled", not self.keyboard_only_mode)
        self.enable_keyboard_only_mode(enabled)
    
    def _on_modal_opened(self, event_data):
        """Handle modal dialog opened."""
        self.navigation_mode = NavigationMode.MODAL
        self.push_context("modal")
    
    def _on_modal_closed(self, event_data):
        """Handle modal dialog closed."""
        self.navigation_mode = NavigationMode.NORMAL
        self.pop_context()
    
    def get_accessibility_info(self) -> Dict[str, Any]:
        """Get accessibility information."""
        return {
            "high_contrast_mode": self.high_contrast_mode,
            "screen_reader_mode": self.screen_reader_mode,
            "keyboard_only_mode": self.keyboard_only_mode,
            "focus_indicators_enabled": self.focus_indicators_enabled,
            "navigation_mode": self.navigation_mode.value,
            "current_focus_group": self.current_focus_group,
            "registered_shortcuts": len(self.key_bindings),
            "focusable_widgets": {group: len(widgets) for group, widgets in self.focusable_widgets.items()}
        }
    
    def cleanup(self):
        """Cleanup resources."""
        # Clear all key bindings
        for key_sequence in list(self.key_bindings.keys()):
            self.unregister_key_binding(key_sequence)
        
        # Clear focus history
        self.focus_history.clear()
        
        # Clear focusable widgets
        self.focusable_widgets.clear()