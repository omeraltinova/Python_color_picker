"""
Main Window with Responsive Design

The main application window with adaptive layout, responsive design,
and comprehensive UI management capabilities.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict, Any, Optional, List
import os
from pathlib import Path

from ..core.event_bus import EventBus
from ..core.config import Config
from .responsive_layout import ResponsiveLayoutManager, ResponsiveFrame, ResponsivePanedWindow, LayoutMode, ResponsiveConfig
from .themes.theme_manager import ThemeManager
from .fullscreen_manager import FullscreenManager
from .dpi_support import DPIManager
from .keyboard_navigation import KeyboardNavigationManager
from .accessibility_manager import AccessibilityManager


class MainWindow:
    """
    Main application window with responsive design capabilities.
    
    Features:
    - Responsive layout that adapts to window size
    - DPI scaling support
    - Full-screen mode optimization
    - Collapsible panels for compact mode
    - Keyboard navigation support
    - Theme integration
    """
    
    def __init__(self, root: tk.Tk, event_bus: EventBus, config: Config, services: Optional[Dict[str, Any]] = None):
        self.root = root
        self.event_bus = event_bus
        self.config = config
        self.services = services or {}
        
        # UI state
        self.panels_visible = {
            "color_panel": True,
            "palette_panel": True,
            "history_panel": True,
            "analysis_panel": True,
            "settings_panel": False
        }
        
        # Responsive configuration
        responsive_config = ResponsiveConfig(
            enable_responsive=config.get('ui.responsive.enabled', True),
            enable_dpi_scaling=config.get('ui.responsive.dpi_scaling', True),
            min_window_width=config.get('ui.window.min_width', 800),
            min_window_height=config.get('ui.window.min_height', 600),
            compact_threshold_width=config.get('ui.responsive.compact_width', 1000),
            compact_threshold_height=config.get('ui.responsive.compact_height', 700),
            auto_hide_panels=config.get('ui.responsive.auto_hide_panels', True),
            collapsible_panels=config.get('ui.responsive.collapsible_panels', True)
        )
        
        # Initialize responsive layout manager
        self.layout_manager = ResponsiveLayoutManager(root, event_bus, responsive_config)
        
        # Initialize DPI manager
        self.dpi_manager = DPIManager(root, event_bus)
        
        # Initialize fullscreen manager
        self.fullscreen_manager = FullscreenManager(root, event_bus)
        
        # Initialize keyboard navigation manager
        self.keyboard_manager = KeyboardNavigationManager(root, event_bus)
        
        # Initialize accessibility manager
        self.accessibility_manager = AccessibilityManager(root, event_bus)
        
        # Initialize theme manager
        self.theme_manager = ThemeManager(event_bus, config)
        
        # UI components (will be created in setup)
        self.main_container = None
        self.toolbar = None
        self.status_bar = None
        self.main_paned = None
        self.left_panel = None
        self.center_panel = None
        self.right_panel = None
        
        # Component references
        self.image_canvas = None
        self.color_panel = None
        self.palette_panel = None
        self.history_panel = None
        self.analysis_panel = None
        self.settings_panel = None
        
        # Setup UI
        self._setup_window()
        self._setup_ui()
        self._setup_menu()
        self._setup_keyboard_shortcuts()
        self._setup_event_handlers()
        
        # Apply initial theme
        self.theme_manager.apply_theme()
        
        # Register UI elements with fullscreen manager
        self._register_fullscreen_elements()
        
        # Setup keyboard navigation
        self._setup_keyboard_navigation()
        
        # Setup accessibility features
        self._setup_accessibility()
        
        # Apply DPI scaling
        self._apply_dpi_scaling()
        
        # Register for responsive updates
        self.layout_manager.register_responsive_component("main_window", self._on_layout_update)
    
    def _setup_window(self):
        """Setup main window properties."""
        # Window title
        self.root.title("Enhanced Color Picker")
        
        # Window size and position
        width = self.config.get('ui.window.width', 1200)
        height = self.config.get('ui.window.height', 800)
        self.root.geometry(f"{width}x{height}")
        
        # Minimum size
        min_width = self.layout_manager.config.min_window_width
        min_height = self.layout_manager.config.min_window_height
        self.root.minsize(min_width, min_height)
        
        # Window icon
        self._set_window_icon()
        
        # Window state
        if self.config.get('ui.window.maximized', False):
            self.root.state('zoomed')
    
    def _set_window_icon(self):
        """Set window icon if available."""
        try:
            icon_path = Path(__file__).parent.parent / "assets" / "icons" / "app_icon.ico"
            if icon_path.exists():
                self.root.iconbitmap(str(icon_path))
        except Exception:
            pass  # Icon not critical
    
    def _setup_ui(self):
        """Setup the main user interface."""
        # Main container
        self.main_container = ResponsiveFrame(self.root, self.layout_manager)
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        # Configure responsive padding
        self.main_container.configure_responsive(
            padding={"compact": 2, "normal": 5, "expanded": 8}
        )
        
        # Create toolbar
        self._create_toolbar()
        
        # Create main content area
        self._create_main_content()
        
        # Create status bar
        self._create_status_bar()
    
    def _create_toolbar(self):
        """Create the main toolbar."""
        self.toolbar = ResponsiveFrame(self.main_container, self.layout_manager)
        self.toolbar.pack(fill=tk.X, pady=(0, 5))
        
        # Configure responsive behavior
        self.toolbar.configure_responsive(
            padding={"compact": 2, "normal": 5, "expanded": 8}
        )
        
        # File operations
        file_frame = ttk.Frame(self.toolbar)
        file_frame.pack(side=tk.LEFT, padx=(0, 10))
        
        self.load_button = ttk.Button(file_frame, text="Load Image", 
                                     command=self._load_image)
        self.load_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.clear_button = ttk.Button(file_frame, text="Clear", 
                                      command=self._clear_image)
        self.clear_button.pack(side=tk.LEFT)
        
        # View controls
        view_frame = ttk.Frame(self.toolbar)
        view_frame.pack(side=tk.LEFT, padx=(0, 10))
        
        self.fit_button = ttk.Button(view_frame, text="Fit to Screen", 
                                    command=self._fit_to_screen)
        self.fit_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.actual_size_button = ttk.Button(view_frame, text="100%", 
                                           command=self._actual_size)
        self.actual_size_button.pack(side=tk.LEFT)
        
        # Panel toggles (will be hidden in compact mode)
        self.panel_frame = ttk.Frame(self.toolbar)
        self.panel_frame.pack(side=tk.RIGHT)
        
        self._create_panel_toggles()
        
        # Fullscreen toggle
        self.fullscreen_button = ttk.Button(self.toolbar, text="Fullscreen", 
                                          command=self._toggle_fullscreen)
        self.fullscreen_button.pack(side=tk.RIGHT, padx=(10, 0))
    
    def _create_panel_toggles(self):
        """Create panel visibility toggle buttons."""
        panels = [
            ("Color", "color_panel"),
            ("Palette", "palette_panel"),
            ("History", "history_panel"),
            ("Analysis", "analysis_panel")
        ]
        
        for label, panel_id in panels:
            var = tk.BooleanVar(value=self.panels_visible[panel_id])
            btn = ttk.Checkbutton(self.panel_frame, text=label, variable=var,
                                 command=lambda p=panel_id, v=var: self._toggle_panel(p, v))
            btn.pack(side=tk.LEFT, padx=2)
            
            # Store reference
            setattr(self, f"{panel_id}_toggle", btn)
            setattr(self, f"{panel_id}_var", var)
    
    def _create_main_content(self):
        """Create the main content area with responsive paned windows."""
        # Main paned window (horizontal by default, vertical in compact mode)
        self.main_paned = ResponsivePanedWindow(self.main_container, 
                                              self.layout_manager, 
                                              orient=tk.HORIZONTAL)
        self.main_paned.pack(fill=tk.BOTH, expand=True)
        
        # Configure responsive behavior
        self.main_paned.configure_responsive(
            compact_orient=tk.VERTICAL,
            sash_positions={
                "compact": [200],
                "normal": [250, 950],
                "expanded": [300, 1100]
            }
        )
        
        # Left panel (tools and controls)
        self._create_left_panel()
        
        # Center panel (main image canvas)
        self._create_center_panel()
        
        # Right panel (information and analysis)
        self._create_right_panel()
    
    def _create_left_panel(self):
        """Create the left panel with color and palette controls."""
        self.left_panel = ResponsiveFrame(self.main_paned, self.layout_manager)
        self.main_paned.add(self.left_panel, minsize=200)
        
        # Left panel notebook for multiple tabs
        self.left_notebook = ttk.Notebook(self.left_panel)
        self.left_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Color panel tab
        self._create_color_panel_tab()
        
        # Palette panel tab
        self._create_palette_panel_tab()
    
    def _create_color_panel_tab(self):
        """Create the color panel tab."""
        color_frame = ResponsiveFrame(self.left_notebook, self.layout_manager)
        self.left_notebook.add(color_frame, text="Color")
        
        # Placeholder for color panel component
        # This will be replaced with actual ColorPanel component
        placeholder = ttk.Label(color_frame, text="Color Panel\n(To be implemented)")
        placeholder.pack(expand=True)
    
    def _create_palette_panel_tab(self):
        """Create the palette panel tab."""
        palette_frame = ResponsiveFrame(self.left_notebook, self.layout_manager)
        self.left_notebook.add(palette_frame, text="Palette")
        
        # Placeholder for palette panel component
        # This will be replaced with actual PalettePanel component
        placeholder = ttk.Label(palette_frame, text="Palette Panel\n(To be implemented)")
        placeholder.pack(expand=True)
    
    def _create_center_panel(self):
        """Create the center panel with image canvas."""
        self.center_panel = ResponsiveFrame(self.main_paned, self.layout_manager)
        self.main_paned.add(self.center_panel, minsize=400)
        
        # Placeholder for image canvas component
        # This will be replaced with actual ImageCanvas component
        canvas_placeholder = tk.Canvas(self.center_panel, bg="#2b2b2b")
        canvas_placeholder.pack(fill=tk.BOTH, expand=True)
        
        # Add some placeholder text
        canvas_placeholder.create_text(200, 150, text="Image Canvas\n(Enhanced with responsive features)", 
                                     fill="white", font=("Arial", 12))
    
    def _create_right_panel(self):
        """Create the right panel with history and analysis."""
        self.right_panel = ResponsiveFrame(self.main_paned, self.layout_manager)
        self.main_paned.add(self.right_panel, minsize=200)
        
        # Right panel notebook
        self.right_notebook = ttk.Notebook(self.right_panel)
        self.right_notebook.pack(fill=tk.BOTH, expand=True)
        
        # History panel tab
        self._create_history_panel_tab()
        
        # Analysis panel tab
        self._create_analysis_panel_tab()
    
    def _create_history_panel_tab(self):
        """Create the history panel tab."""
        history_frame = ResponsiveFrame(self.right_notebook, self.layout_manager)
        self.right_notebook.add(history_frame, text="History")
        
        # Placeholder for history panel component
        placeholder = ttk.Label(history_frame, text="History Panel\n(To be implemented)")
        placeholder.pack(expand=True)
    
    def _create_analysis_panel_tab(self):
        """Create the analysis panel tab."""
        analysis_frame = ResponsiveFrame(self.right_notebook, self.layout_manager)
        self.right_notebook.add(analysis_frame, text="Analysis")
        
        # Placeholder for analysis panel component
        placeholder = ttk.Label(analysis_frame, text="Analysis Panel\n(To be implemented)")
        placeholder.pack(expand=True)
    
    def _create_status_bar(self):
        """Create the status bar."""
        self.status_bar = ResponsiveFrame(self.main_container, self.layout_manager)
        self.status_bar.pack(fill=tk.X, pady=(5, 0))
        
        # Configure responsive padding
        self.status_bar.configure_responsive(
            padding={"compact": 2, "normal": 3, "expanded": 5}
        )
        
        # Status labels
        self.status_label = ttk.Label(self.status_bar, text="Ready")
        self.status_label.pack(side=tk.LEFT)
        
        # Layout mode indicator
        self.layout_mode_label = ttk.Label(self.status_bar, text="Normal")
        self.layout_mode_label.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Window size indicator
        self.size_label = ttk.Label(self.status_bar, text="1200x800")
        self.size_label.pack(side=tk.RIGHT, padx=(10, 0))
    
    def _setup_menu(self):
        """Setup the main menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Load Image...", command=self._load_image, accelerator="Ctrl+O")
        file_menu.add_command(label="Clear Image", command=self._clear_image, accelerator="Ctrl+N")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._exit_application, accelerator="Ctrl+Q")
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Fit to Screen", command=self._fit_to_screen, accelerator="F")
        view_menu.add_command(label="Actual Size", command=self._actual_size, accelerator="1")
        view_menu.add_separator()
        view_menu.add_command(label="Toggle Fullscreen", command=self._toggle_fullscreen, accelerator="F11")
        view_menu.add_separator()
        
        # Panel visibility submenu
        panels_menu = tk.Menu(view_menu, tearoff=0)
        view_menu.add_cascade(label="Panels", menu=panels_menu)
        panels_menu.add_checkbutton(label="Color Panel", variable=self.color_panel_var)
        panels_menu.add_checkbutton(label="Palette Panel", variable=self.palette_panel_var)
        panels_menu.add_checkbutton(label="History Panel", variable=self.history_panel_var)
        panels_menu.add_checkbutton(label="Analysis Panel", variable=self.analysis_panel_var)
        
        # Settings menu
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_command(label="Preferences...", command=self._show_preferences)
        
        # Theme submenu
        theme_menu = tk.Menu(settings_menu, tearoff=0)
        settings_menu.add_cascade(label="Theme", menu=theme_menu)
        theme_menu.add_command(label="Light", command=lambda: self._change_theme("light"))
        theme_menu.add_command(label="Dark", command=lambda: self._change_theme("dark"))
        theme_menu.add_command(label="Auto", command=lambda: self._change_theme("auto"))
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about)
    
    def _setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts."""
        # File operations
        self.root.bind("<Control-o>", lambda e: self._load_image())
        self.root.bind("<Control-n>", lambda e: self._clear_image())
        self.root.bind("<Control-q>", lambda e: self._exit_application())
        
        # View operations
        self.root.bind("<KeyPress-f>", lambda e: self._fit_to_screen())
        self.root.bind("<KeyPress-1>", lambda e: self._actual_size())
        self.root.bind("<F11>", lambda e: self._toggle_fullscreen())
        
        # Panel toggles
        self.root.bind("<Control-1>", lambda e: self._toggle_panel("color_panel"))
        self.root.bind("<Control-2>", lambda e: self._toggle_panel("palette_panel"))
        self.root.bind("<Control-3>", lambda e: self._toggle_panel("history_panel"))
        self.root.bind("<Control-4>", lambda e: self._toggle_panel("analysis_panel"))
        
        # Settings
        self.root.bind("<Control-comma>", lambda e: self._show_preferences())
    
    def _setup_event_handlers(self):
        """Setup event handlers."""
        # Subscribe to relevant events
        self.event_bus.subscribe("image.loaded", self._on_image_loaded)
        self.event_bus.subscribe("color.picked", self._on_color_picked)
        self.event_bus.subscribe("theme.changed", self._on_theme_changed)
        self.event_bus.subscribe("window.fullscreen_changed", self._on_fullscreen_changed)
    
    def _on_layout_update(self, layout_info):
        """Handle responsive layout updates."""
        layout_mode = layout_info["layout_mode"]
        window_info = layout_info["window_info"]
        
        # Update status bar
        self.layout_mode_label.config(text=layout_mode.value.title())
        self.size_label.config(text=f"{window_info['width']}x{window_info['height']}")
        
        # Handle compact mode
        if layout_mode == LayoutMode.COMPACT:
            self._enter_compact_mode()
        else:
            self._exit_compact_mode()
        
        # Update panel visibility based on layout
        self._update_panel_visibility_for_layout(layout_mode)
    
    def _enter_compact_mode(self):
        """Enter compact mode layout."""
        # Hide panel toggle buttons in compact mode
        if hasattr(self, 'panel_frame'):
            self.panel_frame.pack_forget()
        
        # Adjust toolbar layout
        self._adjust_toolbar_for_compact()
    
    def _exit_compact_mode(self):
        """Exit compact mode layout."""
        # Show panel toggle buttons
        if hasattr(self, 'panel_frame'):
            self.panel_frame.pack(side=tk.RIGHT)
        
        # Restore toolbar layout
        self._restore_toolbar_layout()
    
    def _adjust_toolbar_for_compact(self):
        """Adjust toolbar layout for compact mode."""
        # Make buttons smaller or hide some in compact mode
        pass
    
    def _restore_toolbar_layout(self):
        """Restore normal toolbar layout."""
        pass
    
    def _update_panel_visibility_for_layout(self, layout_mode: LayoutMode):
        """Update panel visibility based on layout mode."""
        if not self.layout_manager.config.auto_hide_panels:
            return
        
        if layout_mode == LayoutMode.COMPACT:
            # In compact mode, hide some panels by default
            self._set_panel_visibility("analysis_panel", False)
        else:
            # Restore panels in normal/expanded mode
            self._set_panel_visibility("analysis_panel", True)
    
    def _set_panel_visibility(self, panel_id: str, visible: bool):
        """Set panel visibility."""
        self.panels_visible[panel_id] = visible
        
        # Update toggle button
        var = getattr(self, f"{panel_id}_var", None)
        if var:
            var.set(visible)
        
        # Apply visibility (implementation depends on actual panel components)
        # This is a placeholder for the actual panel visibility logic
    
    def _toggle_panel(self, panel_id: str, var: tk.BooleanVar = None):
        """Toggle panel visibility."""
        if var is None:
            var = getattr(self, f"{panel_id}_var", None)
        
        if var:
            visible = var.get()
            self._set_panel_visibility(panel_id, visible)
    
    # Command handlers
    def _load_image(self):
        """Load an image file."""
        filetypes = [
            ("All Images", "*.png *.jpg *.jpeg *.gif *.bmp *.tiff *.webp *.svg"),
            ("PNG files", "*.png"),
            ("JPEG files", "*.jpg *.jpeg"),
            ("GIF files", "*.gif"),
            ("BMP files", "*.bmp"),
            ("TIFF files", "*.tiff"),
            ("WebP files", "*.webp"),
            ("SVG files", "*.svg"),
            ("All files", "*.*")
        ]
        
        filename = filedialog.askopenfilename(
            title="Load Image",
            filetypes=filetypes
        )
        
        if filename:
            self.event_bus.publish("image.load_requested", {
                "file_path": filename
            }, source="main_window")
            
            self.status_label.config(text=f"Loading: {os.path.basename(filename)}")
    
    def _clear_image(self):
        """Clear the current image."""
        self.event_bus.publish("image.clear_requested", source="main_window")
        self.status_label.config(text="Image cleared")
    
    def _fit_to_screen(self):
        """Fit image to screen."""
        self.event_bus.publish("image.fit_to_screen", source="main_window")
    
    def _actual_size(self):
        """Show image at actual size."""
        self.event_bus.publish("image.actual_size", source="main_window")
    
    def _toggle_fullscreen(self):
        """Toggle fullscreen mode."""
        self.fullscreen_manager.toggle_fullscreen()
    
    def _show_preferences(self):
        """Show preferences dialog."""
        self.event_bus.publish("preferences.show", source="main_window")
    
    def _change_theme(self, theme_name: str):
        """Change application theme."""
        self.theme_manager.set_theme(theme_name)
    
    def _show_about(self):
        """Show about dialog."""
        messagebox.showinfo("About", 
                          "Enhanced Color Picker\n"
                          "Version 1.0\n\n"
                          "A professional color picking tool with advanced features.")
    
    def _exit_application(self):
        """Exit the application."""
        self.event_bus.publish("app.exit_requested", source="main_window")
    
    # Event handlers
    def _on_image_loaded(self, event_data):
        """Handle image loaded event."""
        image_info = event_data.data
        filename = image_info.get("file_path", "Unknown")
        self.status_label.config(text=f"Loaded: {os.path.basename(filename)}")
    
    def _on_color_picked(self, event_data):
        """Handle color picked event."""
        color_info = event_data.data
        color = color_info.get("color")
        if color:
            self.status_label.config(text=f"Color: {color.hex}")
    
    def _on_theme_changed(self, event_data):
        """Handle theme changed event."""
        theme_name = event_data.data.get("theme", "unknown")
        self.status_label.config(text=f"Theme changed to: {theme_name}")
    
    def _on_fullscreen_changed(self, event_data):
        """Handle fullscreen mode change."""
        is_fullscreen = event_data.data.get("fullscreen", False)
        
        if is_fullscreen:
            self.fullscreen_button.config(text="Exit Fullscreen")
            # Hide menu bar in fullscreen
            self.root.config(menu="")
        else:
            self.fullscreen_button.config(text="Fullscreen")
            # Restore menu bar
            menubar = self.root.nametowidget(self.root['menu']) if self.root['menu'] else None
            if menubar:
                self.root.config(menu=menubar)
    
    def get_window_state(self) -> Dict[str, Any]:
        """Get current window state for saving."""
        return {
            "width": self.root.winfo_width(),
            "height": self.root.winfo_height(),
            "x": self.root.winfo_x(),
            "y": self.root.winfo_y(),
            "maximized": self.root.state() == "zoomed",
            "panels_visible": self.panels_visible.copy(),
            "layout_mode": self.layout_manager.get_layout_mode().value
        }
    
    def restore_window_state(self, state: Dict[str, Any]):
        """Restore window state from saved data."""
        if "width" in state and "height" in state:
            width = state["width"]
            height = state["height"]
            x = state.get("x", 100)
            y = state.get("y", 100)
            self.root.geometry(f"{width}x{height}+{x}+{y}")
        
        if state.get("maximized", False):
            self.root.state("zoomed")
        
        if "panels_visible" in state:
            self.panels_visible.update(state["panels_visible"])
            # Update toggle buttons
            for panel_id, visible in self.panels_visible.items():
                var = getattr(self, f"{panel_id}_var", None)
                if var:
                    var.set(visible)
    
    def _register_fullscreen_elements(self):
        """Register UI elements with fullscreen manager."""
        # Register toolbar
        if hasattr(self, 'toolbar'):
            self.fullscreen_manager.register_ui_element(
                "toolbar", self.toolbar,
                hide_in_fullscreen=True,
                pack_options={"fill": tk.X, "pady": (0, 5)}
            )
        
        # Register status bar
        if hasattr(self, 'status_bar'):
            self.fullscreen_manager.register_ui_element(
                "statusbar", self.status_bar,
                hide_in_fullscreen=False,  # Keep status bar visible
                pack_options={"fill": tk.X, "pady": (5, 0)}
            )
        
        # Register panels
        panels = ["left_panel", "right_panel"]
        for panel_name in panels:
            if hasattr(self, panel_name):
                panel = getattr(self, panel_name)
                self.fullscreen_manager.register_ui_element(
                    "panel", panel,
                    panel_id=panel_name,
                    hide_in_fullscreen=False,
                    restore_after_fullscreen=True
                )
    
    def _apply_dpi_scaling(self):
        """Apply DPI scaling to the entire UI."""
        # Apply DPI scaling to the widget tree
        self.dpi_manager.apply_dpi_scaling_to_tree(self.root)
        
        # Configure specific elements for DPI
        if hasattr(self, 'toolbar'):
            self.dpi_manager.configure_widget_dpi(
                self.toolbar,
                padx=5, pady=5
            )
        
        if hasattr(self, 'status_bar'):
            self.dpi_manager.configure_widget_dpi(
                self.status_bar,
                padx=3, pady=3
            )
    
    def get_dpi_info(self) -> Dict[str, Any]:
        """Get DPI information."""
        return self.dpi_manager.get_scaling_info()
    
    def get_fullscreen_info(self) -> Dict[str, Any]:
        """Get fullscreen information."""
        return self.fullscreen_manager.get_fullscreen_info()
    
    def _setup_keyboard_navigation(self):
        """Setup keyboard navigation for all UI elements."""
        # Register main UI components as focusable
        
        # Toolbar buttons
        if hasattr(self, 'load_button'):
            self.keyboard_manager.register_focusable_widget(
                self.load_button, group="toolbar", tab_order=0
            )
        
        if hasattr(self, 'clear_button'):
            self.keyboard_manager.register_focusable_widget(
                self.clear_button, group="toolbar", tab_order=1
            )
        
        if hasattr(self, 'fit_button'):
            self.keyboard_manager.register_focusable_widget(
                self.fit_button, group="toolbar", tab_order=2
            )
        
        if hasattr(self, 'actual_size_button'):
            self.keyboard_manager.register_focusable_widget(
                self.actual_size_button, group="toolbar", tab_order=3
            )
        
        # Panel toggle buttons
        for panel_id in ["color_panel", "palette_panel", "history_panel", "analysis_panel"]:
            toggle_button = getattr(self, f"{panel_id}_toggle", None)
            if toggle_button:
                self.keyboard_manager.register_focusable_widget(
                    toggle_button, group="toolbar", tab_order=10 + hash(panel_id) % 10
                )
        
        # Notebooks (left and right panels)
        if hasattr(self, 'left_notebook'):
            self.keyboard_manager.register_focusable_widget(
                self.left_notebook, group="panels", tab_order=0
            )
        
        if hasattr(self, 'right_notebook'):
            self.keyboard_manager.register_focusable_widget(
                self.right_notebook, group="panels", tab_order=1
            )
        
        # Register custom keyboard shortcuts
        self._register_custom_shortcuts()
    
    def _register_custom_shortcuts(self):
        """Register custom keyboard shortcuts."""
        # File operations
        self.keyboard_manager.register_key_binding(
            "Ctrl+O", self._load_image, "Load image file"
        )
        self.keyboard_manager.register_key_binding(
            "Ctrl+N", self._clear_image, "Clear current image"
        )
        
        # View operations
        self.keyboard_manager.register_key_binding(
            "Ctrl+0", self._fit_to_screen, "Fit image to screen"
        )
        self.keyboard_manager.register_key_binding(
            "Ctrl+1", self._actual_size, "Show image at actual size"
        )
        
        # Panel toggles
        self.keyboard_manager.register_key_binding(
            "Ctrl+Shift+1", lambda: self._toggle_panel("color_panel"), "Toggle color panel"
        )
        self.keyboard_manager.register_key_binding(
            "Ctrl+Shift+2", lambda: self._toggle_panel("palette_panel"), "Toggle palette panel"
        )
        self.keyboard_manager.register_key_binding(
            "Ctrl+Shift+3", lambda: self._toggle_panel("history_panel"), "Toggle history panel"
        )
        self.keyboard_manager.register_key_binding(
            "Ctrl+Shift+4", lambda: self._toggle_panel("analysis_panel"), "Toggle analysis panel"
        )
        
        # Accessibility shortcuts
        self.keyboard_manager.register_key_binding(
            "Ctrl+Alt+H", self._toggle_high_contrast, "Toggle high contrast mode"
        )
        self.keyboard_manager.register_key_binding(
            "Ctrl+Alt+Plus", self._increase_font_size, "Increase font size"
        )
        self.keyboard_manager.register_key_binding(
            "Ctrl+Alt+Minus", self._decrease_font_size, "Decrease font size"
        )
        self.keyboard_manager.register_key_binding(
            "Ctrl+Alt+0", self._reset_font_size, "Reset font size"
        )
    
    def _setup_accessibility(self):
        """Setup accessibility features for all UI elements."""
        # Register main window components with accessibility manager
        
        # Toolbar buttons with labels
        if hasattr(self, 'load_button'):
            self.accessibility_manager.register_widget(
                self.load_button,
                role="button",
                label="Load Image",
                description="Load an image file to pick colors from"
            )
        
        if hasattr(self, 'clear_button'):
            self.accessibility_manager.register_widget(
                self.clear_button,
                role="button",
                label="Clear Image",
                description="Clear the currently loaded image"
            )
        
        if hasattr(self, 'fit_button'):
            self.accessibility_manager.register_widget(
                self.fit_button,
                role="button",
                label="Fit to Screen",
                description="Fit the image to the screen size"
            )
        
        if hasattr(self, 'actual_size_button'):
            self.accessibility_manager.register_widget(
                self.actual_size_button,
                role="button",
                label="Actual Size",
                description="Show the image at its actual size (100%)"
            )
        
        # Panel toggle buttons
        panel_descriptions = {
            "color_panel": "Show or hide the color information panel",
            "palette_panel": "Show or hide the color palette panel",
            "history_panel": "Show or hide the color history panel",
            "analysis_panel": "Show or hide the color analysis panel"
        }
        
        for panel_id, description in panel_descriptions.items():
            toggle_button = getattr(self, f"{panel_id}_toggle", None)
            if toggle_button:
                self.accessibility_manager.register_widget(
                    toggle_button,
                    role="checkbox",
                    label=f"Toggle {panel_id.replace('_', ' ').title()}",
                    description=description
                )
        
        # Notebooks
        if hasattr(self, 'left_notebook'):
            self.accessibility_manager.register_widget(
                self.left_notebook,
                role="tablist",
                label="Left Panel Tabs",
                description="Tabs for color and palette controls"
            )
        
        if hasattr(self, 'right_notebook'):
            self.accessibility_manager.register_widget(
                self.right_notebook,
                role="tablist",
                label="Right Panel Tabs",
                description="Tabs for history and analysis information"
            )
        
        # Status bar elements
        if hasattr(self, 'status_label'):
            self.accessibility_manager.register_widget(
                self.status_label,
                role="status",
                label="Application Status",
                description="Current application status and messages"
            )
        
        if hasattr(self, 'layout_mode_label'):
            self.accessibility_manager.register_widget(
                self.layout_mode_label,
                role="status",
                label="Layout Mode",
                description="Current responsive layout mode"
            )
        
        if hasattr(self, 'size_label'):
            self.accessibility_manager.register_widget(
                self.size_label,
                role="status",
                label="Window Size",
                description="Current window dimensions"
            )
    
    def _toggle_high_contrast(self):
        """Toggle high contrast mode."""
        current_mode = self.accessibility_manager.settings.high_contrast
        self.accessibility_manager.enable_high_contrast(not current_mode)
        
        # Update status
        mode_text = "enabled" if not current_mode else "disabled"
        self.status_label.config(text=f"High contrast mode {mode_text}")
    
    def _increase_font_size(self):
        """Increase font size."""
        current_scale = self.accessibility_manager.settings.font_scale_factor
        new_scale = min(3.0, current_scale + 0.1)
        self.accessibility_manager.set_font_scale(new_scale)
        
        self.status_label.config(text=f"Font size: {int(new_scale * 100)}%")
    
    def _decrease_font_size(self):
        """Decrease font size."""
        current_scale = self.accessibility_manager.settings.font_scale_factor
        new_scale = max(0.5, current_scale - 0.1)
        self.accessibility_manager.set_font_scale(new_scale)
        
        self.status_label.config(text=f"Font size: {int(new_scale * 100)}%")
    
    def _reset_font_size(self):
        """Reset font size to normal."""
        self.accessibility_manager.set_font_scale(1.0)
        self.status_label.config(text="Font size reset to normal")
    
    def get_keyboard_navigation_info(self) -> Dict[str, Any]:
        """Get keyboard navigation information."""
        return self.keyboard_manager.get_accessibility_info()
    
    def get_accessibility_info(self) -> Dict[str, Any]:
        """Get accessibility information."""
        return self.accessibility_manager.get_accessibility_info()
    
    def cleanup(self):
        """Cleanup resources when window is closed."""
        # Unregister from responsive updates
        self.layout_manager.unregister_responsive_component("main_window")
        
        # Save window state
        window_state = self.get_window_state()
        self.config.set('ui.window.state', window_state)
        
        # Cleanup managers
        if self.theme_manager:
            self.theme_manager.cleanup()
        
        if self.fullscreen_manager:
            self.fullscreen_manager.cleanup()
        
        if self.keyboard_manager:
            self.keyboard_manager.cleanup()
        
        if self.accessibility_manager:
            self.accessibility_manager.cleanup()