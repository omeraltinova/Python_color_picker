"""
In-app help system for Enhanced Color Picker.
Provides contextual help, tooltips, and quick access to documentation.
"""

import tkinter as tk
from tkinter import ttk
import webbrowser
import os
from pathlib import Path
from typing import Dict, Optional, Callable
from ...core.event_bus import EventBus


class HelpSystem:
    """Manages in-app help functionality."""
    
    def __init__(self, parent: tk.Widget, event_bus: EventBus):
        self.parent = parent
        self.event_bus = event_bus
        self.help_window: Optional[tk.Toplevel] = None
        self.tooltip_windows: Dict[str, tk.Toplevel] = {}
        
        # Help content mapping
        self.help_topics = {
            'getting_started': {
                'title': 'Getting Started',
                'content': self._get_getting_started_content(),
                'file': 'quick-start.md'
            },
            'color_selection': {
                'title': 'Color Selection',
                'content': self._get_color_selection_content(),
                'file': 'user-manual.md#color-selection'
            },
            'palette_management': {
                'title': 'Palette Management',
                'content': self._get_palette_content(),
                'file': 'user-manual.md#palette-management'
            },
            'zoom_navigation': {
                'title': 'Zoom and Navigation',
                'content': self._get_zoom_content(),
                'file': 'user-manual.md#zoom-and-navigation'
            },
            'keyboard_shortcuts': {
                'title': 'Keyboard Shortcuts',
                'content': self._get_shortcuts_content(),
                'file': 'user-manual.md#keyboard-shortcuts'
            },
            'troubleshooting': {
                'title': 'Troubleshooting',
                'content': self._get_troubleshooting_content(),
                'file': 'troubleshooting.md'
            }
        }
        
        self._setup_event_handlers()
    
    def _setup_event_handlers(self):
        """Set up event handlers for help system."""
        self.event_bus.subscribe('help_requested', self.show_help)
        self.event_bus.subscribe('tooltip_requested', self.show_tooltip)
        self.event_bus.subscribe('tooltip_hide', self.hide_tooltip)
    
    def show_help(self, topic: str = 'getting_started'):
        """Show help window with specified topic."""
        if self.help_window and self.help_window.winfo_exists():
            self.help_window.lift()
            self._load_help_topic(topic)
            return
        
        self._create_help_window()
        self._load_help_topic(topic)
    
    def _create_help_window(self):
        """Create the main help window."""
        self.help_window = tk.Toplevel(self.parent)
        self.help_window.title("Enhanced Color Picker - Help")
        self.help_window.geometry("800x600")
        self.help_window.minsize(600, 400)
        
        # Configure window icon
        try:
            icon_path = Path(__file__).parent.parent.parent / "assets" / "icons" / "help.ico"
            if icon_path.exists():
                self.help_window.iconbitmap(str(icon_path))
        except:
            pass
        
        # Create main frame
        main_frame = ttk.Frame(self.help_window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create sidebar for topics
        sidebar_frame = ttk.Frame(main_frame, width=200)
        sidebar_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        sidebar_frame.pack_propagate(False)
        
        # Topics list
        ttk.Label(sidebar_frame, text="Help Topics", font=('Arial', 12, 'bold')).pack(pady=(0, 10))
        
        self.topics_listbox = tk.Listbox(sidebar_frame, selectmode=tk.SINGLE)
        self.topics_listbox.pack(fill=tk.BOTH, expand=True)
        
        # Populate topics
        for key, topic in self.help_topics.items():
            self.topics_listbox.insert(tk.END, topic['title'])
        
        self.topics_listbox.bind('<<ListboxSelect>>', self._on_topic_select)
        
        # Create content area
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Content title
        self.content_title = ttk.Label(content_frame, text="", font=('Arial', 14, 'bold'))
        self.content_title.pack(anchor=tk.W, pady=(0, 10))
        
        # Content text with scrollbar
        text_frame = ttk.Frame(content_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.content_text = tk.Text(text_frame, wrap=tk.WORD, padx=10, pady=10)
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.content_text.yview)
        self.content_text.configure(yscrollcommand=scrollbar.set)
        
        self.content_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Buttons frame
        buttons_frame = ttk.Frame(content_frame)
        buttons_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(buttons_frame, text="Open Full Documentation", 
                  command=self._open_full_docs).pack(side=tk.LEFT)
        ttk.Button(buttons_frame, text="Close", 
                  command=self.help_window.destroy).pack(side=tk.RIGHT)
    
    def _on_topic_select(self, event):
        """Handle topic selection from sidebar."""
        selection = self.topics_listbox.curselection()
        if selection:
            topic_keys = list(self.help_topics.keys())
            topic_key = topic_keys[selection[0]]
            self._load_help_topic(topic_key)
    
    def _load_help_topic(self, topic_key: str):
        """Load and display help topic content."""
        if topic_key not in self.help_topics:
            topic_key = 'getting_started'
        
        topic = self.help_topics[topic_key]
        self.content_title.config(text=topic['title'])
        
        # Clear and populate content
        self.content_text.delete(1.0, tk.END)
        self.content_text.insert(1.0, topic['content'])
        
        # Select corresponding topic in sidebar
        topic_keys = list(self.help_topics.keys())
        if topic_key in topic_keys:
            index = topic_keys.index(topic_key)
            self.topics_listbox.selection_clear(0, tk.END)
            self.topics_listbox.selection_set(index)
    
    def _open_full_docs(self):
        """Open full documentation in default browser or file viewer."""
        docs_path = Path(__file__).parent.parent.parent.parent / "docs"
        
        if docs_path.exists():
            # Try to open docs folder
            try:
                if os.name == 'nt':  # Windows
                    os.startfile(str(docs_path))
                elif os.name == 'posix':  # macOS and Linux
                    os.system(f'open "{docs_path}"' if os.uname().sysname == 'Darwin' 
                             else f'xdg-open "{docs_path}"')
            except:
                # Fallback: try to open README
                readme_path = docs_path / "README.md"
                if readme_path.exists():
                    webbrowser.open(f'file://{readme_path}')
    
    def show_tooltip(self, widget: tk.Widget, text: str, delay: int = 500):
        """Show tooltip for a widget."""
        def show():
            if widget.winfo_exists():
                tooltip = self._create_tooltip(widget, text)
                widget_id = str(widget)
                self.tooltip_windows[widget_id] = tooltip
        
        # Schedule tooltip display
        widget.after(delay, show)
    
    def hide_tooltip(self, widget: tk.Widget):
        """Hide tooltip for a widget."""
        widget_id = str(widget)
        if widget_id in self.tooltip_windows:
            tooltip = self.tooltip_windows[widget_id]
            if tooltip and tooltip.winfo_exists():
                tooltip.destroy()
            del self.tooltip_windows[widget_id]
    
    def _create_tooltip(self, widget: tk.Widget, text: str) -> tk.Toplevel:
        """Create a tooltip window."""
        tooltip = tk.Toplevel(widget)
        tooltip.wm_overrideredirect(True)
        tooltip.wm_attributes('-topmost', True)
        
        # Position tooltip
        x = widget.winfo_rootx() + 25
        y = widget.winfo_rooty() + 25
        tooltip.wm_geometry(f"+{x}+{y}")
        
        # Create tooltip content
        label = tk.Label(tooltip, text=text, background='#FFFFDD', 
                        relief=tk.SOLID, borderwidth=1, font=('Arial', 9))
        label.pack()
        
        return tooltip
    
    def add_help_to_widget(self, widget: tk.Widget, help_text: str):
        """Add help functionality to a widget."""
        def on_enter(event):
            self.show_tooltip(widget, help_text)
        
        def on_leave(event):
            self.hide_tooltip(widget)
        
        widget.bind('<Enter>', on_enter)
        widget.bind('<Leave>', on_leave)
    
    def _get_getting_started_content(self) -> str:
        """Get getting started help content."""
        return """Welcome to Enhanced Color Picker!

Quick Start:
1. Load an image by dragging and dropping it onto the canvas, or use File → Load Image
2. Click anywhere on the image to select a color
3. View color information in the Color Panel on the right
4. Copy color codes using the copy buttons next to each format
5. Add colors to palettes for future use

Basic Navigation:
• Mouse wheel: Zoom in/out
• Right-click + drag: Pan around the image
• Ctrl+0: Fit image to screen
• Ctrl+C: Copy selected color

The interface has several panels:
• Color Panel: Shows selected color in multiple formats
• Palette Panel: Manage your color collections
• History Panel: View recently selected colors
• Analysis Panel: Color analysis and statistics

For detailed instructions, click "Open Full Documentation" below."""
    
    def _get_color_selection_content(self) -> str:
        """Get color selection help content."""
        return """Color Selection Guide

Basic Selection:
• Click anywhere on an image to select a color
• The Color Panel shows the color in multiple formats:
  - RGB: Red, Green, Blue values (0-255)
  - HEX: Web-friendly format (#RRGGBB)
  - HSL: Hue, Saturation, Lightness
  - HSV: Hue, Saturation, Value
  - CMYK: Print colors (Cyan, Magenta, Yellow, Key)

Precision Selection:
• Zoom in using mouse wheel for pixel-perfect accuracy
• At high zoom levels, a pixel grid appears automatically
• Use coordinates display to target exact pixels
• Right-click and drag to pan around zoomed images

Multiple Colors:
• Each color selection is automatically added to history
• Hold Ctrl while clicking to compare multiple colors
• Use the History Panel to revisit previous selections

Tips:
• Colors are always picked from the original image, not the zoomed view
• The crosshair cursor helps with precise targeting
• Real-time coordinate display shows exact position"""
    
    def _get_palette_content(self) -> str:
        """Get palette management help content."""
        return """Palette Management

Creating Palettes:
• Select colors from images
• Click "Add to Palette" to add colors to your current palette
• Use File → New Palette to start a new palette
• Give your palettes descriptive names

Organizing Colors:
• Drag and drop colors to reorder them
• Right-click colors for options (edit, delete, duplicate)
• Double-click colors to edit their properties

Saving and Loading:
• File → Save Palette: Save your current palette
• File → Load Palette: Load a previously saved palette
• Auto-save option available in settings

Export Options:
• JSON: Native format with full metadata
• CSS: CSS custom properties
• SCSS: Sass variables
• Adobe ASE: For Photoshop/Illustrator
• Adobe ACO: Photoshop color swatches
• GIMP GPL: GIMP palette format

Tips:
• Save palettes frequently to avoid losing work
• Use descriptive names for easy identification
• Export in the format that matches your workflow"""
    
    def _get_zoom_content(self) -> str:
        """Get zoom and navigation help content."""
        return """Zoom and Navigation

Zoom Controls:
• Mouse wheel: Zoom in (scroll up) or out (scroll down)
• Keyboard: Ctrl+Plus (zoom in), Ctrl+Minus (zoom out)
• Toolbar: Use zoom buttons or slider
• Zoom centers on your mouse cursor position

Navigation:
• Right-click + drag: Pan around the image
• Arrow keys: Move in small increments
• Shift + Arrow keys: Move in larger steps
• Mini-map: Click to jump to specific areas

Precision Features:
• Pixel grid appears automatically at 800%+ zoom
• Grid helps identify individual pixels
• Toggle grid: View → Show Pixel Grid
• Maximum zoom: 1000% for extreme precision

Fit Options:
• Ctrl+0: Fit entire image to screen
• Ctrl+1: Show image at actual size (100%)
• Fit Width/Height: Available in View menu

Tips:
• Use high zoom levels for precise color selection
• The mini-map helps navigate large images
• Pixel grid is essential for pixel-perfect work
• Remember: colors are picked from original image resolution"""
    
    def _get_shortcuts_content(self) -> str:
        """Get keyboard shortcuts help content."""
        return """Keyboard Shortcuts

File Operations:
• Ctrl+O: Load image
• Ctrl+S: Save palette
• Ctrl+Shift+S: Save palette as
• Ctrl+N: New palette
• Ctrl+Q: Quit application

View Controls:
• Ctrl+Plus: Zoom in
• Ctrl+Minus: Zoom out
• Ctrl+0: Fit to screen
• Ctrl+1: Actual size (100%)
• F11: Toggle fullscreen

Color Operations:
• Ctrl+C: Copy selected color
• Ctrl+Shift+C: Copy all formats
• Ctrl+A: Add color to palette
• Delete: Remove selected color

Navigation:
• Arrow keys: Pan image
• Shift+Arrow: Pan faster
• Space+Drag: Pan with mouse
• Ctrl+Home: Reset view

Panels:
• F1: Toggle Color Panel
• F2: Toggle Palette Panel
• F3: Toggle History Panel
• F4: Toggle Analysis Panel

Tools:
• Ctrl+T: Color analysis
• Ctrl+B: Color blindness simulation
• Ctrl+H: Show/hide pixel grid
• Ctrl+M: Toggle mini-map

Customization:
• All shortcuts can be customized in Settings → Shortcuts
• Create your own workflow-specific shortcuts"""
    
    def _get_troubleshooting_content(self) -> str:
        """Get troubleshooting help content."""
        return """Common Issues and Solutions

Application Won't Start:
• Check Python 3.8+ is installed
• Install dependencies: pip install -r requirements.txt
• Run from command line to see error messages
• Check file permissions

Image Loading Problems:
• Verify file format is supported (PNG, JPEG, GIF, BMP, TIFF, WebP, SVG)
• Try converting unsupported formats
• For large images, try resizing before loading
• Check if file is corrupted

Color Selection Issues:
• Colors look different: Check monitor calibration
• Can't select precisely: Zoom in more, enable pixel grid
• Wrong color values: Ensure image is in RGB color space

Performance Problems:
• Application slow: Clear cache, reduce image size
• High memory usage: Enable auto-cleanup, restart application
• Zoom is jerky: Disable smooth zoom in settings

Interface Issues:
• Missing panels: View → Reset Layout
• Text too small/large: Adjust system DPI or use interface zoom
• Theme problems: Reset theme in settings

For detailed troubleshooting, click "Open Full Documentation" below.

Quick Fixes:
• Restart the application
• Clear cache (Settings → Performance)
• Reset settings to defaults
• Update to latest version"""


class HelpButton(ttk.Button):
    """A help button that shows contextual help."""
    
    def __init__(self, parent: tk.Widget, help_system: HelpSystem, 
                 topic: str = 'getting_started', **kwargs):
        super().__init__(parent, text="?", width=3, **kwargs)
        self.help_system = help_system
        self.topic = topic
        self.configure(command=self._show_help)
    
    def _show_help(self):
        """Show help for this button's topic."""
        self.help_system.show_help(self.topic)


class ContextualHelp:
    """Provides contextual help for different UI areas."""
    
    def __init__(self, help_system: HelpSystem):
        self.help_system = help_system
        self.context_map = {
            'image_canvas': 'color_selection',
            'color_panel': 'color_selection',
            'palette_panel': 'palette_management',
            'history_panel': 'color_selection',
            'analysis_panel': 'color_selection',
            'zoom_controls': 'zoom_navigation'
        }
    
    def add_context_help(self, widget: tk.Widget, context: str):
        """Add contextual help to a widget."""
        topic = self.context_map.get(context, 'getting_started')
        
        def show_context_help(event):
            if event.keysym == 'F1':
                self.help_system.show_help(topic)
        
        widget.bind('<F1>', show_context_help)
        widget.focus_set()  # Ensure widget can receive key events