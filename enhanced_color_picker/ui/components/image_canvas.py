"""
Enhanced Image Canvas Component

Advanced image display component with zoom, pan, pixel grid, mini-map navigation,
and pixel-perfect color picking capabilities. Optimized for performance with
large images and high zoom levels.
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Tuple, Callable, Dict, Any
import math
from PIL import Image, ImageTk
from dataclasses import dataclass
import threading

from ...models.image_data import ImageData
from ...models.color_data import ColorData
from ...core.event_bus import EventBus, EventData


@dataclass
class ViewportState:
    """Current viewport state for the image canvas."""
    zoom: float = 1.0
    offset_x: float = 0.0
    offset_y: float = 0.0
    canvas_width: int = 0
    canvas_height: int = 0
    
    def copy(self) -> 'ViewportState':
        """Create a copy of the viewport state."""
        return ViewportState(
            zoom=self.zoom,
            offset_x=self.offset_x,
            offset_y=self.offset_y,
            canvas_width=self.canvas_width,
            canvas_height=self.canvas_height
        )


class ZoomManager:
    """Manages zoom operations with cursor-centered scaling."""
    
    def __init__(self, min_zoom: float = 0.1, max_zoom: float = 50.0, zoom_step: float = 1.2):
        self.min_zoom = min_zoom
        self.max_zoom = max_zoom
        self.zoom_step = zoom_step
    
    def calculate_zoom_in(self, current_zoom: float) -> float:
        """Calculate new zoom level for zoom in operation."""
        new_zoom = current_zoom * self.zoom_step
        return min(new_zoom, self.max_zoom)
    
    def calculate_zoom_out(self, current_zoom: float) -> float:
        """Calculate new zoom level for zoom out operation."""
        new_zoom = current_zoom / self.zoom_step
        return max(new_zoom, self.min_zoom)
    
    def calculate_cursor_centered_zoom(self, current_state: ViewportState, 
                                     new_zoom: float, cursor_x: int, cursor_y: int) -> ViewportState:
        """Calculate new viewport state for cursor-centered zoom."""
        if new_zoom == current_state.zoom:
            return current_state.copy()
        
        # Calculate the point in image coordinates that the cursor is over
        image_x = (cursor_x - current_state.offset_x) / current_state.zoom
        image_y = (cursor_y - current_state.offset_y) / current_state.zoom
        
        # Calculate new offset to keep the same image point under the cursor
        new_offset_x = cursor_x - (image_x * new_zoom)
        new_offset_y = cursor_y - (image_y * new_zoom)
        
        new_state = current_state.copy()
        new_state.zoom = new_zoom
        new_state.offset_x = new_offset_x
        new_state.offset_y = new_offset_y
        
        return new_state


class PanManager:
    """Manages pan operations for image navigation."""
    
    def __init__(self):
        self.is_panning = False
        self.last_pan_x = 0
        self.last_pan_y = 0
    
    def start_pan(self, x: int, y: int):
        """Start panning operation."""
        self.is_panning = True
        self.last_pan_x = x
        self.last_pan_y = y
    
    def update_pan(self, current_state: ViewportState, x: int, y: int) -> ViewportState:
        """Update pan based on mouse movement."""
        if not self.is_panning:
            return current_state
        
        dx = x - self.last_pan_x
        dy = y - self.last_pan_y
        
        new_state = current_state.copy()
        new_state.offset_x += dx
        new_state.offset_y += dy
        
        self.last_pan_x = x
        self.last_pan_y = y
        
        return new_state
    
    def end_pan(self):
        """End panning operation."""
        self.is_panning = False


class PixelGrid:
    """Manages pixel grid display for high zoom levels."""
    
    def __init__(self, threshold_zoom: float = 8.0):
        self.threshold_zoom = threshold_zoom
        self.grid_color = "#808080"
        self.grid_width = 1
    
    def should_show_grid(self, zoom: float) -> bool:
        """Determine if pixel grid should be shown at current zoom level."""
        return zoom >= self.threshold_zoom
    
    def draw_grid(self, canvas: tk.Canvas, viewport: ViewportState, image_size: Tuple[int, int]):
        """Draw pixel grid on canvas."""
        if not self.should_show_grid(viewport.zoom):
            return
        
        canvas_width = viewport.canvas_width
        canvas_height = viewport.canvas_height
        
        # Calculate grid spacing
        grid_spacing = viewport.zoom
        
        # Calculate starting positions
        start_x = viewport.offset_x % grid_spacing
        start_y = viewport.offset_y % grid_spacing
        
        # Draw vertical lines
        x = start_x
        while x < canvas_width:
            canvas.create_line(x, 0, x, canvas_height, 
                             fill=self.grid_color, width=self.grid_width, tags="pixel_grid")
            x += grid_spacing
        
        # Draw horizontal lines
        y = start_y
        while y < canvas_height:
            canvas.create_line(0, y, canvas_width, y, 
                             fill=self.grid_color, width=self.grid_width, tags="pixel_grid")
            y += grid_spacing


class MiniMap:
    """Mini-map navigation for large images."""
    
    def __init__(self, size: Tuple[int, int] = (150, 150)):
        self.size = size
        self.enabled = False
        self.position = "bottom_right"  # bottom_right, bottom_left, top_right, top_left
        self.background_color = "#f0f0f0"
        self.viewport_color = "#ff0000"
        self.border_color = "#000000"
    
    def create_minimap_image(self, image_data: ImageData) -> ImageTk.PhotoImage:
        """Create minimap thumbnail image."""
        # Calculate thumbnail size maintaining aspect ratio
        img_width, img_height = image_data.size
        thumb_width, thumb_height = self.size
        
        # Calculate scaling to fit within minimap size
        scale_x = thumb_width / img_width
        scale_y = thumb_height / img_height
        scale = min(scale_x, scale_y)
        
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
        
        # Resize image
        thumbnail = image_data.pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(thumbnail)
    
    def get_minimap_position(self, canvas_width: int, canvas_height: int) -> Tuple[int, int]:
        """Get minimap position on canvas."""
        margin = 10
        
        if self.position == "bottom_right":
            return (canvas_width - self.size[0] - margin, canvas_height - self.size[1] - margin)
        elif self.position == "bottom_left":
            return (margin, canvas_height - self.size[1] - margin)
        elif self.position == "top_right":
            return (canvas_width - self.size[0] - margin, margin)
        else:  # top_left
            return (margin, margin)
    
    def draw_minimap(self, canvas: tk.Canvas, viewport: ViewportState, 
                    image_data: ImageData, minimap_image: ImageTk.PhotoImage):
        """Draw minimap on canvas."""
        if not self.enabled:
            return
        
        # Get minimap position
        map_x, map_y = self.get_minimap_position(viewport.canvas_width, viewport.canvas_height)
        
        # Draw minimap background
        canvas.create_rectangle(map_x, map_y, map_x + self.size[0], map_y + self.size[1],
                              fill=self.background_color, outline=self.border_color, tags="minimap")
        
        # Draw thumbnail image
        canvas.create_image(map_x + self.size[0]//2, map_y + self.size[1]//2, 
                          image=minimap_image, tags="minimap")
        
        # Draw viewport indicator
        self._draw_viewport_indicator(canvas, viewport, image_data, map_x, map_y)
    
    def _draw_viewport_indicator(self, canvas: tk.Canvas, viewport: ViewportState, 
                               image_data: ImageData, map_x: int, map_y: int):
        """Draw viewport indicator on minimap."""
        # Calculate scale factor for minimap
        img_width, img_height = image_data.size
        scale_x = self.size[0] / img_width
        scale_y = self.size[1] / img_height
        scale = min(scale_x, scale_y)
        
        # Calculate visible area in image coordinates
        visible_left = -viewport.offset_x / viewport.zoom
        visible_top = -viewport.offset_y / viewport.zoom
        visible_right = visible_left + viewport.canvas_width / viewport.zoom
        visible_bottom = visible_top + viewport.canvas_height / viewport.zoom
        
        # Clamp to image bounds
        visible_left = max(0, min(img_width, visible_left))
        visible_top = max(0, min(img_height, visible_top))
        visible_right = max(0, min(img_width, visible_right))
        visible_bottom = max(0, min(img_height, visible_bottom))
        
        # Convert to minimap coordinates
        mini_left = map_x + visible_left * scale
        mini_top = map_y + visible_top * scale
        mini_right = map_x + visible_right * scale
        mini_bottom = map_y + visible_bottom * scale
        
        # Draw viewport rectangle
        canvas.create_rectangle(mini_left, mini_top, mini_right, mini_bottom,
                              outline=self.viewport_color, width=2, fill="", tags="minimap")


class EnhancedImageCanvas(tk.Frame):
    """
    Advanced image display component with comprehensive features.
    
    Features:
    - Mouse wheel zoom with cursor-centered scaling
    - Pan with right-click drag or middle mouse button
    - Pixel grid display for high zoom levels
    - Mini-map navigation for large images
    - Pixel-perfect color picking with zoom compensation
    - Fit-to-screen functionality
    - Performance optimized rendering
    """
    
    def __init__(self, parent, event_bus: EventBus, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.event_bus = event_bus
        self.image_data: Optional[ImageData] = None
        self.display_image: Optional[ImageTk.PhotoImage] = None
        self.minimap_image: Optional[ImageTk.PhotoImage] = None
        
        # Viewport state
        self.viewport = ViewportState()
        
        # Managers
        self.zoom_manager = ZoomManager()
        self.pan_manager = PanManager()
        self.pixel_grid = PixelGrid()
        self.minimap = MiniMap()
        
        # Settings
        self.enable_pixel_grid = True
        self.enable_minimap = True
        self.background_color = "#2b2b2b"
        
        # Performance settings
        self.render_quality = Image.Resampling.LANCZOS
        self.max_render_size = (2048, 2048)  # Maximum size for rendered image
        
        # Threading for background operations
        self._render_lock = threading.Lock()
        self._pending_render = False
        
        self._setup_ui()
        self._bind_events()
        
        # Subscribe to relevant events
        self._setup_event_subscriptions()
    
    def _setup_ui(self):
        """Setup the user interface components."""
        # Create main canvas
        self.canvas = tk.Canvas(self, bg=self.background_color, highlightthickness=0)
        
        # Create scrollbars
        self.h_scrollbar = ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.v_scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.canvas.yview)
        
        # Configure canvas scrolling
        self.canvas.configure(xscrollcommand=self.h_scrollbar.set, yscrollcommand=self.v_scrollbar.set)
        
        # Layout components
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.h_scrollbar.grid(row=1, column=0, sticky="ew")
        self.v_scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Configure grid weights
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Create context menu
        self._create_context_menu()
    
    def _create_context_menu(self):
        """Create right-click context menu."""
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Fit to Screen", command=self.fit_to_screen)
        self.context_menu.add_command(label="Actual Size (100%)", command=self.actual_size)
        self.context_menu.add_separator()
        self.context_menu.add_checkbutton(label="Show Pixel Grid", 
                                        variable=tk.BooleanVar(value=self.enable_pixel_grid),
                                        command=self.toggle_pixel_grid)
        self.context_menu.add_checkbutton(label="Show Mini-map", 
                                        variable=tk.BooleanVar(value=self.enable_minimap),
                                        command=self.toggle_minimap)
    
    def _bind_events(self):
        """Bind mouse and keyboard events."""
        # Mouse wheel zoom
        self.canvas.bind("<MouseWheel>", self._on_mouse_wheel)
        self.canvas.bind("<Button-4>", self._on_mouse_wheel)  # Linux
        self.canvas.bind("<Button-5>", self._on_mouse_wheel)  # Linux
        
        # Mouse clicks
        self.canvas.bind("<Button-1>", self._on_left_click)
        self.canvas.bind("<Button-3>", self._on_right_click)
        self.canvas.bind("<Button-2>", self._on_middle_click)  # Middle mouse button
        
        # Mouse motion
        self.canvas.bind("<Motion>", self._on_mouse_motion)
        self.canvas.bind("<B3-Motion>", self._on_right_drag)  # Right mouse drag
        self.canvas.bind("<B2-Motion>", self._on_middle_drag)  # Middle mouse drag
        
        # Mouse enter/leave
        self.canvas.bind("<Enter>", self._on_mouse_enter)
        self.canvas.bind("<Leave>", self._on_mouse_leave)
        
        # Canvas resize
        self.canvas.bind("<Configure>", self._on_canvas_resize)
        
        # Keyboard shortcuts
        self.canvas.bind("<Key>", self._on_key_press)
        self.canvas.focus_set()  # Allow keyboard events
    
    def _setup_event_subscriptions(self):
        """Setup event bus subscriptions."""
        self.event_bus.subscribe("image_loaded", self._on_image_loaded)
        self.event_bus.subscribe("settings_changed", self._on_settings_changed)
    
    def display_image(self, image_data: ImageData):
        """
        Display image with current zoom and pan settings.
        
        Args:
            image_data: Image to display
        """
        self.image_data = image_data
        
        # Reset viewport for new image
        self.viewport = ViewportState()
        
        # Fit image to screen initially
        self.fit_to_screen()
        
        # Publish image displayed event
        self.event_bus.publish("image_displayed", {
            "image_data": image_data,
            "canvas": self
        }, source="image_canvas")
    
    def _render_image(self):
        """Render the current image with zoom and pan applied."""
        if not self.image_data:
            return
        
        with self._render_lock:
            try:
                # Calculate visible area
                visible_area = self._calculate_visible_area()
                if not visible_area:
                    return
                
                # Create rendered image
                rendered_image = self._create_rendered_image(visible_area)
                if not rendered_image:
                    return
                
                # Convert to PhotoImage
                self.display_image = ImageTk.PhotoImage(rendered_image)
                
                # Create minimap if enabled
                if self.enable_minimap:
                    self.minimap_image = self.minimap.create_minimap_image(self.image_data)
                
                # Update canvas
                self._update_canvas_display()
                
            except Exception as e:
                print(f"Error rendering image: {e}")
    
    def _calculate_visible_area(self) -> Optional[Tuple[int, int, int, int]]:
        """Calculate the visible area of the image in image coordinates."""
        if not self.image_data:
            return None
        
        img_width, img_height = self.image_data.size
        
        # Calculate visible area in image coordinates
        left = max(0, -self.viewport.offset_x / self.viewport.zoom)
        top = max(0, -self.viewport.offset_y / self.viewport.zoom)
        right = min(img_width, left + self.viewport.canvas_width / self.viewport.zoom)
        bottom = min(img_height, top + self.viewport.canvas_height / self.viewport.zoom)
        
        if left >= right or top >= bottom:
            return None
        
        return (int(left), int(top), int(right), int(bottom))
    
    def _create_rendered_image(self, visible_area: Tuple[int, int, int, int]) -> Optional[Image.Image]:
        """Create rendered image for the visible area."""
        if not self.image_data:
            return None
        
        left, top, right, bottom = visible_area
        
        # Crop to visible area
        cropped = self.image_data.pil_image.crop((left, top, right, bottom))
        
        # Calculate target size
        target_width = int((right - left) * self.viewport.zoom)
        target_height = int((bottom - top) * self.viewport.zoom)
        
        # Limit rendering size for performance
        if target_width > self.max_render_size[0] or target_height > self.max_render_size[1]:
            scale = min(self.max_render_size[0] / target_width, self.max_render_size[1] / target_height)
            target_width = int(target_width * scale)
            target_height = int(target_height * scale)
        
        # Resize image
        if target_width > 0 and target_height > 0:
            return cropped.resize((target_width, target_height), self.render_quality)
        
        return None
    
    def _update_canvas_display(self):
        """Update the canvas display with rendered image and overlays."""
        # Clear canvas
        self.canvas.delete("all")
        
        if self.display_image:
            # Display main image
            self.canvas.create_image(
                self.viewport.offset_x, self.viewport.offset_y,
                anchor=tk.NW, image=self.display_image, tags="main_image"
            )
        
        # Draw pixel grid if enabled
        if self.enable_pixel_grid:
            self.pixel_grid.draw_grid(self.canvas, self.viewport, self.image_data.size)
        
        # Draw minimap if enabled
        if self.enable_minimap and self.minimap_image:
            self.minimap.draw_minimap(self.canvas, self.viewport, self.image_data, self.minimap_image)
        
        # Update scroll region
        self._update_scroll_region()
    
    def _update_scroll_region(self):
        """Update canvas scroll region based on image size and zoom."""
        if not self.image_data:
            self.canvas.configure(scrollregion=(0, 0, 0, 0))
            return
        
        img_width, img_height = self.image_data.size
        zoomed_width = img_width * self.viewport.zoom
        zoomed_height = img_height * self.viewport.zoom
        
        # Calculate scroll region
        left = min(0, self.viewport.offset_x)
        top = min(0, self.viewport.offset_y)
        right = max(self.viewport.canvas_width, self.viewport.offset_x + zoomed_width)
        bottom = max(self.viewport.canvas_height, self.viewport.offset_y + zoomed_height)
        
        self.canvas.configure(scrollregion=(left, top, right, bottom))
    
    def get_color_at_position(self, canvas_x: int, canvas_y: int) -> Optional[ColorData]:
        """
        Get color at canvas position with zoom compensation.
        
        Args:
            canvas_x: X coordinate on canvas
            canvas_y: Y coordinate on canvas
            
        Returns:
            ColorData: Color at the specified position, or None if outside image
        """
        if not self.image_data:
            return None
        
        # Convert canvas coordinates to image coordinates
        image_x = (canvas_x - self.viewport.offset_x) / self.viewport.zoom
        image_y = (canvas_y - self.viewport.offset_y) / self.viewport.zoom
        
        # Check bounds
        if (image_x < 0 or image_y < 0 or 
            image_x >= self.image_data.width or image_y >= self.image_data.height):
            return None
        
        try:
            # Get pixel color from original image
            r, g, b, a = self.image_data.get_pixel_color(int(image_x), int(image_y))
            return ColorData.from_rgb(r, g, b, a / 255.0)
        except Exception:
            return None
    
    def fit_to_screen(self):
        """Fit image to screen size."""
        if not self.image_data:
            return
        
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width <= 1 or canvas_height <= 1:
            # Canvas not yet sized, schedule for later
            self.after(100, self.fit_to_screen)
            return
        
        img_width, img_height = self.image_data.size
        
        # Calculate zoom to fit
        zoom_x = canvas_width / img_width
        zoom_y = canvas_height / img_height
        zoom = min(zoom_x, zoom_y)
        
        # Center image
        offset_x = (canvas_width - img_width * zoom) / 2
        offset_y = (canvas_height - img_height * zoom) / 2
        
        # Update viewport
        self.viewport.zoom = zoom
        self.viewport.offset_x = offset_x
        self.viewport.offset_y = offset_y
        self.viewport.canvas_width = canvas_width
        self.viewport.canvas_height = canvas_height
        
        # Re-render
        self._render_image()
    
    def actual_size(self):
        """Set zoom to 100% (actual size)."""
        if not self.image_data:
            return
        
        # Center image at 100% zoom
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        img_width, img_height = self.image_data.size
        
        self.viewport.zoom = 1.0
        self.viewport.offset_x = (canvas_width - img_width) / 2
        self.viewport.offset_y = (canvas_height - img_height) / 2
        
        self._render_image()
    
    def zoom_in(self, center_x: Optional[int] = None, center_y: Optional[int] = None):
        """Zoom in at specified point or canvas center."""
        if not self.image_data:
            return
        
        if center_x is None or center_y is None:
            center_x = self.viewport.canvas_width // 2
            center_y = self.viewport.canvas_height // 2
        
        new_zoom = self.zoom_manager.calculate_zoom_in(self.viewport.zoom)
        self.viewport = self.zoom_manager.calculate_cursor_centered_zoom(
            self.viewport, new_zoom, center_x, center_y
        )
        
        self._render_image()
    
    def zoom_out(self, center_x: Optional[int] = None, center_y: Optional[int] = None):
        """Zoom out at specified point or canvas center."""
        if not self.image_data:
            return
        
        if center_x is None or center_y is None:
            center_x = self.viewport.canvas_width // 2
            center_y = self.viewport.canvas_height // 2
        
        new_zoom = self.zoom_manager.calculate_zoom_out(self.viewport.zoom)
        self.viewport = self.zoom_manager.calculate_cursor_centered_zoom(
            self.viewport, new_zoom, center_x, center_y
        )
        
        self._render_image()
    
    def toggle_pixel_grid(self):
        """Toggle pixel grid display."""
        self.enable_pixel_grid = not self.enable_pixel_grid
        self._render_image()
    
    def toggle_minimap(self):
        """Toggle minimap display."""
        self.enable_minimap = not self.enable_minimap
        self.minimap.enabled = self.enable_minimap
        self._render_image()
    
    # Event handlers
    def _on_mouse_wheel(self, event):
        """Handle mouse wheel zoom."""
        if not self.image_data:
            return
        
        # Determine zoom direction
        if event.delta > 0 or event.num == 4:
            self.zoom_in(event.x, event.y)
        else:
            self.zoom_out(event.x, event.y)
    
    def _on_left_click(self, event):
        """Handle left mouse click for color picking."""
        color = self.get_color_at_position(event.x, event.y)
        if color:
            self.event_bus.publish("color_picked", {
                "color": color,
                "position": (event.x, event.y),
                "image_position": ((event.x - self.viewport.offset_x) / self.viewport.zoom,
                                 (event.y - self.viewport.offset_y) / self.viewport.zoom)
            }, source="image_canvas")
    
    def _on_right_click(self, event):
        """Handle right mouse click."""
        # Start panning or show context menu
        if self.image_data:
            self.pan_manager.start_pan(event.x, event.y)
        else:
            self.context_menu.post(event.x_root, event.y_root)
    
    def _on_middle_click(self, event):
        """Handle middle mouse click for panning."""
        if self.image_data:
            self.pan_manager.start_pan(event.x, event.y)
    
    def _on_right_drag(self, event):
        """Handle right mouse drag for panning."""
        if self.image_data and self.pan_manager.is_panning:
            self.viewport = self.pan_manager.update_pan(self.viewport, event.x, event.y)
            self._render_image()
    
    def _on_middle_drag(self, event):
        """Handle middle mouse drag for panning."""
        if self.image_data and self.pan_manager.is_panning:
            self.viewport = self.pan_manager.update_pan(self.viewport, event.x, event.y)
            self._render_image()
    
    def _on_mouse_motion(self, event):
        """Handle mouse motion for coordinate display."""
        if not self.image_data:
            return
        
        # Calculate image coordinates
        image_x = (event.x - self.viewport.offset_x) / self.viewport.zoom
        image_y = (event.y - self.viewport.offset_y) / self.viewport.zoom
        
        # Publish mouse position event
        self.event_bus.publish("mouse_position_changed", {
            "canvas_position": (event.x, event.y),
            "image_position": (image_x, image_y),
            "zoom": self.viewport.zoom
        }, source="image_canvas")
    
    def _on_mouse_enter(self, event):
        """Handle mouse entering canvas."""
        self.canvas.focus_set()
    
    def _on_mouse_leave(self, event):
        """Handle mouse leaving canvas."""
        self.pan_manager.end_pan()
    
    def _on_canvas_resize(self, event):
        """Handle canvas resize."""
        self.viewport.canvas_width = event.width
        self.viewport.canvas_height = event.height
        
        # Re-render if image is loaded
        if self.image_data:
            self._render_image()
    
    def _on_key_press(self, event):
        """Handle keyboard shortcuts."""
        if event.keysym == "f":
            self.fit_to_screen()
        elif event.keysym == "1":
            self.actual_size()
        elif event.keysym == "g":
            self.toggle_pixel_grid()
        elif event.keysym == "m":
            self.toggle_minimap()
        elif event.keysym == "plus" or event.keysym == "equal":
            self.zoom_in()
        elif event.keysym == "minus":
            self.zoom_out()
    
    # Event bus handlers
    def _on_image_loaded(self, event_data: EventData):
        """Handle image loaded event."""
        if "image_data" in event_data.data:
            self.display_image(event_data.data["image_data"])
    
    def _on_settings_changed(self, event_data: EventData):
        """Handle settings changed event."""
        settings = event_data.data
        
        if "pixel_grid_enabled" in settings:
            self.enable_pixel_grid = settings["pixel_grid_enabled"]
        
        if "minimap_enabled" in settings:
            self.enable_minimap = settings["minimap_enabled"]
            self.minimap.enabled = self.enable_minimap
        
        if "background_color" in settings:
            self.background_color = settings["background_color"]
            self.canvas.configure(bg=self.background_color)
        
        # Re-render if needed
        if self.image_data:
            self._render_image()
    
    def get_viewport_info(self) -> Dict[str, Any]:
        """Get current viewport information."""
        return {
            "zoom": self.viewport.zoom,
            "offset": (self.viewport.offset_x, self.viewport.offset_y),
            "canvas_size": (self.viewport.canvas_width, self.viewport.canvas_height),
            "image_size": self.image_data.size if self.image_data else None,
            "pixel_grid_enabled": self.enable_pixel_grid,
            "minimap_enabled": self.enable_minimap
        }
    
    def cleanup(self):
        """Cleanup resources when component is destroyed."""
        # Cancel any pending renders
        with self._render_lock:
            self._pending_render = False
        
        # Clear images
        self.display_image = None
        self.minimap_image = None
        self.image_data = None