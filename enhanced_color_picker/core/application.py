"""
Main application controller for Enhanced Color Picker.

This module contains the main application class that coordinates all services,
manages the application lifecycle, and provides the entry point for the application.
"""

import sys
import logging
import threading
from pathlib import Path
from typing import Dict, Any, Optional

# Import tkinter conditionally to avoid issues in headless environments
try:
    import tkinter as tk
    from tkinter import messagebox
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False
    tk = None
    messagebox = None

from .config import Config
from .event_bus import EventBus, EventPriority
from .exceptions import ColorPickerError, ConfigurationError, handle_error, format_error_for_user


class EnhancedColorPickerApp:
    """
    Main application controller for Enhanced Color Picker.
    
    This class manages the application lifecycle, coordinates services,
    handles initialization and shutdown, and provides the main entry point.
    """
    
    def __init__(self, config_dir: Optional[str] = None, debug: bool = False):
        """
        Initialize the Enhanced Color Picker application.
        
        Args:
            config_dir: Optional custom configuration directory
            debug: Enable debug logging and features
        """
        self.debug = debug
        self._setup_logging()
        
        # Check if GUI is available
        if not TKINTER_AVAILABLE:
            raise ColorPickerError("Tkinter is not available. GUI functionality requires tkinter.")
        
        # Core components
        self.config: Optional[Config] = None
        self.event_bus: Optional[EventBus] = None
        self.root: Optional[tk.Tk] = None
        
        # Services (will be initialized later)
        self.services: Dict[str, Any] = {}
        
        # UI components
        self.main_window: Optional[Any] = None
        
        # Application state
        self._initialized = False
        self._running = False
        self._shutdown_requested = False
        
        # Initialize core components
        try:
            self._initialize_core(config_dir)
            self._setup_event_handlers()
            self.setup_error_boundaries()
            self._initialized = True
            
            self.logger.info("Enhanced Color Picker application initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize application: {e}")
            self._handle_initialization_error(e)
            raise
    
    def _setup_logging(self) -> None:
        """Setup application logging."""
        log_level = logging.DEBUG if self.debug else logging.INFO
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                # File handler will be added after config is loaded
            ]
        )
        
        self.logger = logging.getLogger(__name__)
    
    def _initialize_core(self, config_dir: Optional[str]) -> None:
        """Initialize core application components."""
        # Initialize configuration
        try:
            self.config = Config(config_dir)
            self.logger.info(f"Configuration loaded from: {self.config.get_config_file_path()}")
        except Exception as e:
            raise ConfigurationError(f"Failed to initialize configuration: {e}")
        
        # Initialize event bus
        self.event_bus = EventBus(enable_logging=self.debug)
        self.logger.info("Event bus initialized")
        
        # Initialize Tkinter root
        self.root = tk.Tk()
        self.root.withdraw()  # Hide initially
        
        # Configure root window
        self._configure_root_window()
        
        # Setup error handling
        self.root.report_callback_exception = self._handle_tk_error
    
    def _configure_root_window(self) -> None:
        """Configure the main Tkinter window."""
        if not self.root or not self.config:
            return
        
        # Set window properties from config
        ui_config = self.config.config.ui
        
        self.root.title("Enhanced Color Picker")
        self.root.geometry(f"{ui_config.window_width}x{ui_config.window_height}")
        self.root.minsize(800, 600)
        
        # Set window icon if available
        try:
            icon_path = Path(__file__).parent.parent / "assets" / "icons" / "app_icon.ico"
            if icon_path.exists():
                self.root.iconbitmap(str(icon_path))
        except Exception:
            pass  # Icon not critical
        
        # Configure window closing
        self.root.protocol("WM_DELETE_WINDOW", self._on_window_close)
        
        # Apply theme
        self._apply_theme()
    
    def _apply_theme(self) -> None:
        """Apply the current theme to the application."""
        if not self.config:
            return
        
        theme = self.config.get('ui.theme', 'dark')
        
        # Basic theme colors
        if theme == 'dark':
            bg_color = '#1e1e1e'
            fg_color = '#ffffff'
        else:
            bg_color = '#f5f6f7'
            fg_color = '#1e1e1e'
        
        if self.root:
            self.root.configure(bg=bg_color)
    
    def _setup_event_handlers(self) -> None:
        """Setup application-level event handlers."""
        if not self.event_bus:
            return
        
        # Subscribe to application events
        self.event_bus.subscribe('app.shutdown', self._on_shutdown_event, priority=EventPriority.HIGH)
        self.event_bus.subscribe('app.error', self._on_error_event, priority=EventPriority.HIGH)
        self.event_bus.subscribe('config.changed', self._on_config_changed, priority=EventPriority.NORMAL)
        
        # Subscribe to service events
        self.event_bus.subscribe('image.load_requested', self._on_image_load_requested, priority=EventPriority.NORMAL)
        self.event_bus.subscribe('image.clear_requested', self._on_image_clear_requested, priority=EventPriority.NORMAL)
        self.event_bus.subscribe('color.pick_requested', self._on_color_pick_requested, priority=EventPriority.NORMAL)
        self.event_bus.subscribe('palette.save_requested', self._on_palette_save_requested, priority=EventPriority.NORMAL)
        self.event_bus.subscribe('preferences.show', self._on_show_preferences, priority=EventPriority.NORMAL)
        self.event_bus.subscribe('app.exit_requested', self._on_exit_requested, priority=EventPriority.HIGH)
        
        self.logger.debug("Application event handlers setup complete")
    
    def _setup_service_event_handlers(self) -> None:
        """Setup event handlers for service integration."""
        if not self.event_bus:
            return
        
        # Memory management events
        self.event_bus.subscribe('memory.warning', self._on_memory_warning, priority=EventPriority.HIGH)
        self.event_bus.subscribe('memory.critical', self._on_memory_critical, priority=EventPriority.HIGH)
        
        # Task management events
        self.event_bus.subscribe('task.completed', self._on_task_completed, priority=EventPriority.NORMAL)
        self.event_bus.subscribe('task.failed', self._on_task_failed, priority=EventPriority.NORMAL)
        
        # Service error events
        self.event_bus.subscribe('service.error', self._on_service_error, priority=EventPriority.HIGH)
        
        self.logger.debug("Service event handlers setup complete")
    
    def _initialize_services(self) -> None:
        """Initialize application services."""
        try:
            self.logger.info("Initializing application services...")
            
            # Import services
            from ..services import (
                ImageService, ColorService, PaletteService, AnalysisService,
                AccessibilityService, ColorBlindnessService, ExportService, BatchService
            )
            from ..localization.i18n_service import I18nService
            from ..storage.settings_storage import SettingsStorage
            from ..storage.cache_storage import CacheStorage
            from ..core.task_manager import TaskManager
            from ..core.memory_manager import MemoryManager
            from ..core.error_handler import ErrorHandler
            
            # Initialize core services first
            self.services['error_handler'] = ErrorHandler(self.event_bus, self.config)
            self.services['task_manager'] = TaskManager(self.event_bus, max_workers=4)
            self.services['memory_manager'] = MemoryManager(self.event_bus, self.config)
            
            # Initialize performance monitoring
            from .performance_profiler import PerformanceProfiler
            from .optimization_manager import OptimizationManager
            
            enable_profiling = self.config.get('performance.enable_profiling', True)
            self.services['profiler'] = PerformanceProfiler(self.event_bus, enable_profiling)
            self.services['optimizer'] = OptimizationManager(
                self.event_bus, 
                self.services['profiler'],
                self.config.get('performance.optimization', {})
            )
            
            # Initialize storage services
            self.services['settings_storage'] = SettingsStorage(self.config)
            self.services['cache_storage'] = CacheStorage(self.config)
            
            # Initialize localization service
            self.services['i18n'] = I18nService(
                default_language=self.config.get('ui.language', 'tr'),
                translations_dir=Path(__file__).parent.parent / "localization" / "translations"
            )
            
            # Initialize image service
            cache_size = self.config.get('performance.image_cache_size', 100 * 1024 * 1024)
            max_workers = self.config.get('performance.max_workers', 4)
            self.services['image'] = ImageService(cache_size=cache_size, max_workers=max_workers)
            
            # Initialize color service
            self.services['color'] = ColorService()
            
            # Initialize palette service
            palettes_dir = self.config.get_user_data_dir() / "palettes"
            self.services['palette'] = PaletteService(palettes_directory=str(palettes_dir))
            
            # Initialize analysis service
            self.services['analysis'] = AnalysisService(
                image_service=self.services['image'],
                color_service=self.services['color']
            )
            
            # Initialize accessibility service
            self.services['accessibility'] = AccessibilityService(
                color_service=self.services['color']
            )
            
            # Initialize color blindness service
            self.services['color_blindness'] = ColorBlindnessService(
                color_service=self.services['color']
            )
            
            # Initialize export service
            self.services['export'] = ExportService(
                palette_service=self.services['palette'],
                color_service=self.services['color']
            )
            
            # Initialize batch service
            self.services['batch'] = BatchService(
                color_service=self.services['color'],
                palette_service=self.services['palette'],
                export_service=self.services['export'],
                task_manager=self.services['task_manager']
            )
            
            # Setup service event handlers
            self._setup_service_event_handlers()
            
            # Start background services
            self.services['task_manager'].start()
            self.services['memory_manager'].start_monitoring()
            
            # Start performance monitoring
            if 'profiler' in self.services:
                self.services['profiler'].start_monitoring()
            
            # Start auto-optimization
            if 'optimizer' in self.services:
                self.services['optimizer'].start_auto_optimization()
            
            self.logger.info(f"Successfully initialized {len(self.services)} services")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize services: {e}")
            raise ConfigurationError(f"Service initialization failed: {e}")
    
    def _initialize_ui(self) -> None:
        """Initialize the user interface."""
        try:
            from ..ui.main_window import MainWindow
            
            # Create main window with services
            self.main_window = MainWindow(
                root=self.root,
                event_bus=self.event_bus,
                config=self.config,
                services=self.services
            )
            self.logger.info("Main window initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize UI: {e}")
            raise
    
    def run(self) -> None:
        """
        Start the application main loop.
        
        This method initializes services and UI, then starts the Tkinter main loop.
        """
        if not self._initialized:
            raise ColorPickerError("Application not properly initialized")
        
        if self._running:
            self.logger.warning("Application is already running")
            return
        
        try:
            self.logger.info("Starting Enhanced Color Picker application")
            
            # Initialize services
            self._initialize_services()
            
            # Initialize UI
            self._initialize_ui()
            
            # Show main window
            if self.root:
                self.root.deiconify()  # Show window
                
                # Center window on screen
                self._center_window()
                
                # Set running state
                self._running = True
                
                # Execute startup procedures
                self._execute_startup_procedures()
                
                # Publish application started event
                if self.event_bus:
                    self.event_bus.publish('app.started', source='application')
                
                # Start main loop
                self.logger.info("Starting Tkinter main loop")
                self.root.mainloop()
            
        except Exception as e:
            self.logger.error(f"Error during application startup: {e}")
            self._handle_runtime_error(e)
            raise
        finally:
            self._running = False
            self.logger.info("Application main loop ended")
    
    def _center_window(self) -> None:
        """Center the main window on the screen."""
        if not self.root:
            return
        
        self.root.update_idletasks()
        
        # Get window dimensions
        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()
        
        # Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Calculate position
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    def shutdown(self, save_config: bool = True) -> None:
        """
        Shutdown the application gracefully.
        
        Args:
            save_config: Whether to save configuration before shutdown
        """
        if self._shutdown_requested:
            return
        
        self._shutdown_requested = True
        self.logger.info("Application shutdown requested")
        
        try:
            # Execute shutdown procedures
            self._execute_shutdown_procedures()
            
            # Publish shutdown event
            if self.event_bus:
                self.event_bus.publish('app.shutdown', source='application')
            
            # Save configuration
            if save_config and self.config:
                try:
                    self.config.save()
                    self.logger.info("Configuration saved")
                except Exception as e:
                    self.logger.error(f"Failed to save configuration: {e}")
            
            # Cleanup services
            self._cleanup_services()
            
            # Cleanup event bus
            if self.event_bus:
                self.event_bus.shutdown()
            
            # Close main window
            if self.root:
                self.root.quit()
                self.root.destroy()
            
            self.logger.info("Application shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")
    
    def _cleanup_services(self) -> None:
        """Cleanup application services."""
        self.logger.info("Cleaning up application services...")
        
        # Shutdown services in reverse order of initialization
        service_shutdown_order = [
            'batch', 'export', 'color_blindness', 'accessibility', 'analysis',
            'palette', 'color', 'image', 'i18n', 'cache_storage', 'settings_storage',
            'optimizer', 'profiler', 'memory_manager', 'task_manager', 'error_handler'
        ]
        
        for service_name in service_shutdown_order:
            if service_name in self.services:
                service = self.services[service_name]
                try:
                    if hasattr(service, 'shutdown'):
                        service.shutdown()
                    elif hasattr(service, 'stop'):
                        service.stop()
                    elif hasattr(service, 'cleanup'):
                        service.cleanup()
                    self.logger.debug(f"Service '{service_name}' cleaned up")
                except Exception as e:
                    self.logger.error(f"Error cleaning up service '{service_name}': {e}")
        
        # Clear all services
        self.services.clear()
        self.logger.info("All services cleaned up")
    
    def _on_window_close(self) -> None:
        """Handle main window close event."""
        self.shutdown()
    
    def _on_shutdown_event(self, event_data) -> None:
        """Handle application shutdown event."""
        self.logger.debug("Received shutdown event")
        # Additional shutdown logic can be added here
    
    def _on_error_event(self, event_data) -> None:
        """Handle application error event."""
        error = event_data.data
        self.logger.error(f"Application error event: {error}")
        
        # Show error dialog to user
        if isinstance(error, ColorPickerError):
            error_message = format_error_for_user(error)
        else:
            error_message = "Beklenmeyen bir hata oluştu. Lütfen uygulamayı yeniden başlatın."
        
        if self.root:
            messagebox.showerror("Hata", error_message)
    
    def _on_config_changed(self, event_data) -> None:
        """Handle configuration change event."""
        self.logger.debug("Configuration changed, applying updates")
        
        # Reapply theme if theme changed
        if 'ui.theme' in str(event_data.data):
            self._apply_theme()
    
    def _on_image_load_requested(self, event_data) -> None:
        """Handle image load request."""
        file_path = event_data.data.get('file_path')
        if file_path and 'image' in self.services:
            try:
                # Load image asynchronously
                task_id = self.services['image'].load_image_async(
                    file_path,
                    progress_callback=lambda current, total, msg: self.event_bus.publish(
                        'image.load_progress', {'current': current, 'total': total, 'message': msg}
                    ),
                    completion_callback=lambda image_data: self.event_bus.publish(
                        'image.loaded', {'image_data': image_data, 'file_path': file_path}
                    ),
                    error_callback=lambda error: self.event_bus.publish(
                        'image.load_error', {'error': error, 'file_path': file_path}
                    )
                )
                self.logger.info(f"Started loading image: {file_path} (task: {task_id})")
            except Exception as e:
                self.logger.error(f"Failed to start image loading: {e}")
                self.event_bus.publish('image.load_error', {'error': e, 'file_path': file_path})
    
    def _on_image_clear_requested(self, event_data) -> None:
        """Handle image clear request."""
        self.event_bus.publish('image.cleared', source='application')
        self.logger.debug("Image cleared")
    
    def _on_color_pick_requested(self, event_data) -> None:
        """Handle color pick request."""
        image_data = event_data.data.get('image_data')
        x = event_data.data.get('x')
        y = event_data.data.get('y')
        
        if image_data and x is not None and y is not None and 'image' in self.services:
            try:
                color = self.services['image'].get_pixel_color(image_data, x, y)
                self.event_bus.publish('color.picked', {
                    'color': color, 'x': x, 'y': y, 'image_data': image_data
                })
                self.logger.debug(f"Color picked: {color.hex} at ({x}, {y})")
            except Exception as e:
                self.logger.error(f"Failed to pick color: {e}")
                self.event_bus.publish('color.pick_error', {'error': e})
    
    def _on_palette_save_requested(self, event_data) -> None:
        """Handle palette save request."""
        palette = event_data.data.get('palette')
        if palette and 'palette' in self.services:
            try:
                file_path = self.services['palette'].save_palette(palette)
                self.event_bus.publish('palette.saved', {
                    'palette': palette, 'file_path': file_path
                })
                self.logger.info(f"Palette saved: {palette.name}")
            except Exception as e:
                self.logger.error(f"Failed to save palette: {e}")
                self.event_bus.publish('palette.save_error', {'error': e, 'palette': palette})
    
    def _on_show_preferences(self, event_data) -> None:
        """Handle show preferences request."""
        try:
            from ..ui.dialogs.settings_dialog import SettingsDialog
            if self.root:
                dialog = SettingsDialog(self.root, self.config, self.event_bus)
                dialog.show()
        except ImportError:
            self.logger.warning("Settings dialog not available")
            if self.root:
                messagebox.showinfo("Settings", "Settings dialog will be available in a future update.")
    
    def _on_exit_requested(self, event_data) -> None:
        """Handle application exit request."""
        self.logger.info("Exit requested by user")
        self.shutdown()
    
    def _on_memory_warning(self, event_data) -> None:
        """Handle memory warning."""
        memory_info = event_data.data
        self.logger.warning(f"Memory warning: {memory_info}")
        
        # Clear image cache if memory usage is high
        if 'image' in self.services:
            self.services['image'].clear_cache()
            self.logger.info("Cleared image cache due to memory warning")
    
    def _on_memory_critical(self, event_data) -> None:
        """Handle critical memory situation."""
        memory_info = event_data.data
        self.logger.error(f"Critical memory situation: {memory_info}")
        
        # Aggressive cleanup
        if 'image' in self.services:
            self.services['image'].clear_cache()
        if 'cache_storage' in self.services:
            self.services['cache_storage'].clear_all()
        
        # Show warning to user
        if self.root:
            messagebox.showwarning(
                "Memory Warning",
                "Memory usage is critically high. Some caches have been cleared to free memory."
            )
    
    def _on_task_completed(self, event_data) -> None:
        """Handle task completion."""
        task_info = event_data.data
        self.logger.debug(f"Task completed: {task_info.get('task_id', 'unknown')}")
    
    def _on_task_failed(self, event_data) -> None:
        """Handle task failure."""
        task_info = event_data.data
        error = task_info.get('error', 'Unknown error')
        self.logger.error(f"Task failed: {task_info.get('task_id', 'unknown')} - {error}")
    
    def _on_service_error(self, event_data) -> None:
        """Handle service errors."""
        error_info = event_data.data
        service_name = error_info.get('service', 'unknown')
        error = error_info.get('error', 'Unknown error')
        self.logger.error(f"Service error in {service_name}: {error}")
        
        # Show user-friendly error message
        if self.root:
            messagebox.showerror("Service Error", f"An error occurred in {service_name}: {error}")
    
    def _handle_initialization_error(self, error: Exception) -> None:
        """Handle errors during application initialization."""
        error_msg = f"Uygulama başlatılamadı: {error}"
        
        # Try to show error dialog
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Başlatma Hatası", error_msg)
            root.destroy()
        except Exception:
            # If GUI fails, print to console
            print(f"FATAL ERROR: {error_msg}")
    
    def _handle_runtime_error(self, error: Exception) -> None:
        """Handle errors during application runtime."""
        app_error = handle_error(error, "Runtime error")
        
        if self.event_bus:
            self.event_bus.publish('app.error', app_error, source='application')
    
    def _handle_tk_error(self, exc_type, exc_value, exc_traceback) -> None:
        """Handle Tkinter callback exceptions with error boundary."""
        import traceback
        
        error_msg = f"Tkinter error: {exc_type.__name__}: {exc_value}"
        self.logger.error(error_msg)
        self.logger.error("Traceback: " + "".join(traceback.format_exception(exc_type, exc_value, exc_traceback)))
        
        # Convert to application error and publish
        app_error = handle_error(exc_value, "Tkinter callback error")
        
        if self.event_bus:
            self.event_bus.publish('app.error', app_error, source='tkinter')
        
        # Try to recover from the error
        self._attempt_error_recovery(exc_type, exc_value)
    
    def _attempt_error_recovery(self, exc_type, exc_value) -> None:
        """Attempt to recover from errors."""
        try:
            # Clear any pending operations
            if 'task_manager' in self.services:
                self.services['task_manager'].cancel_all_tasks()
            
            # Clear caches to free memory
            if 'image' in self.services:
                self.services['image'].clear_cache()
            
            # Force garbage collection
            import gc
            gc.collect()
            
            self.logger.info("Attempted error recovery")
            
        except Exception as recovery_error:
            self.logger.error(f"Error recovery failed: {recovery_error}")
    
    def _execute_startup_procedures(self) -> None:
        """Execute application startup procedures."""
        try:
            self.logger.info("Executing startup procedures...")
            
            # Load user settings
            if 'settings_storage' in self.services:
                try:
                    user_settings = self.services['settings_storage'].load_settings()
                    if user_settings:
                        self.config.update_from_dict(user_settings)
                        self.logger.debug("User settings loaded")
                except Exception as e:
                    self.logger.warning(f"Failed to load user settings: {e}")
            
            # Restore window state if available
            if self.main_window and hasattr(self.main_window, 'restore_window_state'):
                try:
                    window_state = self.config.get('ui.window_state', {})
                    if window_state:
                        self.main_window.restore_window_state(window_state)
                        self.logger.debug("Window state restored")
                except Exception as e:
                    self.logger.warning(f"Failed to restore window state: {e}")
            
            # Initialize cache if needed
            if 'cache_storage' in self.services:
                try:
                    self.services['cache_storage'].initialize()
                    self.logger.debug("Cache storage initialized")
                except Exception as e:
                    self.logger.warning(f"Failed to initialize cache: {e}")
            
            # Apply user preferences
            self._apply_user_preferences()
            
            # Check for updates (if enabled)
            if self.config.get('app.check_updates_on_startup', False):
                self._check_for_updates()
            
            # Run initial performance optimization
            if 'optimizer' in self.services:
                try:
                    context = {
                        'trigger': 'startup',
                        'services': self.services
                    }
                    self.services['optimizer'].run_optimization('Memory Optimization', context)
                    self.logger.debug("Initial performance optimization completed")
                except Exception as e:
                    self.logger.warning(f"Initial optimization failed: {e}")
            
            self.logger.info("Startup procedures completed successfully")
            
        except Exception as e:
            self.logger.error(f"Error during startup procedures: {e}")
            # Don't fail startup for non-critical errors
    
    def _apply_user_preferences(self) -> None:
        """Apply user preferences from configuration."""
        try:
            # Apply theme
            theme = self.config.get('ui.theme', 'dark')
            if self.main_window and hasattr(self.main_window, 'theme_manager'):
                self.main_window.theme_manager.set_theme(theme)
            
            # Apply language
            language = self.config.get('ui.language', 'tr')
            if 'i18n' in self.services:
                self.services['i18n'].set_language(language)
            
            # Apply performance settings
            if 'image' in self.services:
                cache_size = self.config.get('performance.image_cache_size', 100 * 1024 * 1024)
                # Update cache size if needed
            
            self.logger.debug("User preferences applied")
            
        except Exception as e:
            self.logger.warning(f"Failed to apply user preferences: {e}")
    
    def _check_for_updates(self) -> None:
        """Check for application updates."""
        # Placeholder for update checking functionality
        self.logger.debug("Update checking not implemented yet")
    
    def _execute_shutdown_procedures(self) -> None:
        """Execute application shutdown procedures."""
        try:
            self.logger.info("Executing shutdown procedures...")
            
            # Save window state
            if self.main_window and hasattr(self.main_window, 'get_window_state'):
                try:
                    window_state = self.main_window.get_window_state()
                    self.config.set('ui.window_state', window_state)
                    self.logger.debug("Window state saved")
                except Exception as e:
                    self.logger.warning(f"Failed to save window state: {e}")
            
            # Save user settings
            if 'settings_storage' in self.services:
                try:
                    user_settings = self.config.get_user_settings()
                    self.services['settings_storage'].save_settings(user_settings)
                    self.logger.debug("User settings saved")
                except Exception as e:
                    self.logger.warning(f"Failed to save user settings: {e}")
            
            # Cancel any running tasks
            if 'task_manager' in self.services:
                try:
                    self.services['task_manager'].cancel_all_tasks()
                    self.logger.debug("All tasks cancelled")
                except Exception as e:
                    self.logger.warning(f"Failed to cancel tasks: {e}")
            
            # Clear temporary files
            self._cleanup_temporary_files()
            
            # Final memory cleanup
            if 'memory_manager' in self.services:
                try:
                    self.services['memory_manager'].force_cleanup()
                    self.logger.debug("Memory cleanup completed")
                except Exception as e:
                    self.logger.warning(f"Failed to cleanup memory: {e}")
            
            self.logger.info("Shutdown procedures completed successfully")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown procedures: {e}")
    
    def _cleanup_temporary_files(self) -> None:
        """Clean up temporary files created during application run."""
        try:
            import tempfile
            import shutil
            
            # Clean up any temporary files in the app's temp directory
            temp_dir = Path(tempfile.gettempdir()) / "enhanced_color_picker"
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
                self.logger.debug("Temporary files cleaned up")
                
        except Exception as e:
            self.logger.warning(f"Failed to cleanup temporary files: {e}")
    
    def setup_error_boundaries(self) -> None:
        """Setup comprehensive error boundaries."""
        # Set up global exception handler
        import sys
        sys.excepthook = self._global_exception_handler
        
        # Set up thread exception handler (Python 3.8+)
        try:
            import threading
            threading.excepthook = self._thread_exception_handler
        except AttributeError:
            pass  # Not available in older Python versions
    
    def _global_exception_handler(self, exc_type, exc_value, exc_traceback) -> None:
        """Handle uncaught exceptions."""
        import traceback
        
        if issubclass(exc_type, KeyboardInterrupt):
            # Handle Ctrl+C gracefully
            self.logger.info("Application interrupted by user")
            self.shutdown()
            return
        
        error_msg = f"Uncaught exception: {exc_type.__name__}: {exc_value}"
        self.logger.critical(error_msg)
        self.logger.critical("Traceback: " + "".join(traceback.format_exception(exc_type, exc_value, exc_traceback)))
        
        # Try to show error dialog
        try:
            if self.root and not self._shutdown_requested:
                messagebox.showerror(
                    "Critical Error",
                    f"A critical error occurred:\n\n{exc_value}\n\nThe application will attempt to continue, but you may want to save your work and restart."
                )
        except Exception:
            pass
        
        # Attempt recovery
        self._attempt_error_recovery(exc_type, exc_value)
    
    def _thread_exception_handler(self, args) -> None:
        """Handle exceptions in threads."""
        exc_type, exc_value, exc_traceback, thread = args
        
        error_msg = f"Thread exception in {thread.name}: {exc_type.__name__}: {exc_value}"
        self.logger.error(error_msg)
        
        if self.event_bus:
            self.event_bus.publish('thread.error', {
                'thread_name': thread.name,
                'error': exc_value,
                'error_type': exc_type.__name__
            }, source='application')
    
    @property
    def is_initialized(self) -> bool:
        """Check if application is properly initialized."""
        return self._initialized
    
    @property
    def is_running(self) -> bool:
        """Check if application is currently running."""
        return self._running
    
    @property
    def is_shutdown_requested(self) -> bool:
        """Check if shutdown has been requested."""
        return self._shutdown_requested
    
    def get_service(self, service_name: str) -> Optional[Any]:
        """Get a service by name."""
        return self.services.get(service_name)
    
    def get_all_services(self) -> Dict[str, Any]:
        """Get all services."""
        return self.services.copy()
    
    def is_service_available(self, service_name: str) -> bool:
        """Check if a service is available."""
        return service_name in self.services


def main(config_dir: Optional[str] = None, debug: bool = False) -> None:
    """
    Main entry point for the Enhanced Color Picker application.
    
    Args:
        config_dir: Optional custom configuration directory
        debug: Enable debug mode
    """
    try:
        app = EnhancedColorPickerApp(config_dir=config_dir, debug=debug)
        app.run()
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced Color Picker")
    parser.add_argument("--config-dir", help="Custom configuration directory")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    main(config_dir=args.config_dir, debug=args.debug)