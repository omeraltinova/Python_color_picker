"""
Color Analysis Panel Component

Advanced color analysis panel with dominant colors display, color histogram visualization,
color distribution statistics, and color palette extraction from images.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, List, Dict, Any, Tuple
import numpy as np
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import threading
from collections import Counter

from ...models.color_data import ColorData
from ...models.image_data import ImageData
from ...core.event_bus import EventBus, EventData
from ...services.analysis_service import AnalysisService


class DominantColorsWidget(tk.Frame):
    """Widget for displaying dominant colors from image analysis."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.dominant_colors: List[Tuple[ColorData, float]] = []  # (color, percentage)
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the widget UI."""
        # Title
        title_label = ttk.Label(self, text="Dominant Colors", font=("TkDefaultFont", 10, "bold"))
        title_label.pack(anchor="w", pady=(0, 5))
        
        # Colors frame
        self.colors_frame = tk.Frame(self, bg="white", relief=tk.SUNKEN, borderwidth=1)
        self.colors_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        # Info label
        self.info_label = ttk.Label(self, text="No image loaded", font=("TkDefaultFont", 8))
        self.info_label.pack(anchor="w")
    
    def update_dominant_colors(self, colors_with_percentages: List[Tuple[ColorData, float]]):
        """Update the dominant colors display."""
        self.dominant_colors = colors_with_percentages
        
        # Clear existing widgets
        for widget in self.colors_frame.winfo_children():
            widget.destroy()
        
        if not colors_with_percentages:
            no_data_label = tk.Label(self.colors_frame, text="No dominant colors found", 
                                   bg="white", fg="gray")
            no_data_label.pack(expand=True)
            self.info_label.configure(text="No data")
            return
        
        # Create color swatches with percentages
        for i, (color, percentage) in enumerate(colors_with_percentages):
            color_frame = tk.Frame(self.colors_frame, bg="white")
            color_frame.pack(fill=tk.X, padx=5, pady=2)
            
            # Color swatch
            swatch = tk.Canvas(color_frame, width=30, height=30, highlightthickness=0)
            swatch.pack(side=tk.LEFT, padx=(0, 10))
            swatch.create_rectangle(0, 0, 30, 30, fill=color.hex, outline="#ccc")
            
            # Color info
            info_frame = tk.Frame(color_frame, bg="white")
            info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            # Hex and percentage
            hex_label = tk.Label(info_frame, text=color.hex, font=("TkDefaultFont", 9, "bold"), bg="white")
            hex_label.pack(anchor="w")
            
            rgb_text = f"RGB({color.r}, {color.g}, {color.b}) • {percentage:.1f}%"
            rgb_label = tk.Label(info_frame, text=rgb_text, font=("TkDefaultFont", 8), bg="white", fg="gray")
            rgb_label.pack(anchor="w")
            
            # Percentage bar
            bar_frame = tk.Frame(color_frame, bg="white")
            bar_frame.pack(side=tk.RIGHT, padx=(10, 0))
            
            bar_width = int(percentage * 2)  # Scale for display
            bar_canvas = tk.Canvas(bar_frame, width=100, height=10, highlightthickness=0, bg="white")
            bar_canvas.pack()
            
            # Background bar
            bar_canvas.create_rectangle(0, 2, 100, 8, fill="#e0e0e0", outline="")
            # Percentage bar
            bar_canvas.create_rectangle(0, 2, bar_width, 8, fill=color.hex, outline="")
            
            # Bind click event
            def on_color_click(c=color):
                self._on_color_selected(c)
            
            swatch.bind("<Button-1>", lambda e, c=color: self._on_color_selected(c))
            hex_label.bind("<Button-1>", lambda e, c=color: self._on_color_selected(c))
        
        # Update info
        total_colors = len(colors_with_percentages)
        coverage = sum(percentage for _, percentage in colors_with_percentages)
        self.info_label.configure(text=f"{total_colors} colors • {coverage:.1f}% coverage")
    
    def _on_color_selected(self, color: ColorData):
        """Handle color selection."""
        # This would typically publish an event or call a callback
        print(f"Dominant color selected: {color.hex}")


class ColorHistogramWidget(tk.Frame):
    """Widget for displaying color histogram visualization."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.current_image: Optional[ImageData] = None
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the widget UI."""
        # Title
        title_label = ttk.Label(self, text="Color Histogram", font=("TkDefaultFont", 10, "bold"))
        title_label.pack(anchor="w", pady=(0, 5))
        
        # Create matplotlib figure
        self.figure = Figure(figsize=(6, 3), dpi=80, facecolor='white')
        self.canvas = FigureCanvasTkAgg(self.figure, self)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Controls frame
        controls_frame = ttk.Frame(self)
        controls_frame.pack(fill=tk.X, pady=(5, 0))
        
        # Histogram type selection
        ttk.Label(controls_frame, text="Type:").pack(side=tk.LEFT)
        
        self.histogram_type = tk.StringVar(value="rgb")
        type_combo = ttk.Combobox(controls_frame, textvariable=self.histogram_type,
                                values=["rgb", "hue", "saturation", "brightness"],
                                state="readonly", width=10)
        type_combo.pack(side=tk.LEFT, padx=(5, 10))
        type_combo.bind("<<ComboboxSelected>>", self._on_type_changed)
        
        # Refresh button
        ttk.Button(controls_frame, text="Refresh", command=self._update_histogram).pack(side=tk.LEFT)
        
        # Show initial empty state
        self._show_empty_state()
    
    def _show_empty_state(self):
        """Show empty state when no image is loaded."""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.text(0.5, 0.5, 'No image loaded', ha='center', va='center', 
                transform=ax.transAxes, fontsize=12, color='gray')
        ax.set_xticks([])
        ax.set_yticks([])
        self.canvas.draw()
    
    def update_image(self, image_data: ImageData):
        """Update histogram with new image data."""
        self.current_image = image_data
        self._update_histogram()
    
    def _update_histogram(self):
        """Update the histogram display."""
        if not self.current_image:
            self._show_empty_state()
            return
        
        # Run histogram calculation in background thread
        def calculate_histogram():
            try:
                histogram_type = self.histogram_type.get()
                
                if histogram_type == "rgb":
                    self._create_rgb_histogram()
                elif histogram_type == "hue":
                    self._create_hue_histogram()
                elif histogram_type == "saturation":
                    self._create_saturation_histogram()
                elif histogram_type == "brightness":
                    self._create_brightness_histogram()
                
                # Update canvas on main thread
                self.after(0, lambda: self.canvas.draw())
                
            except Exception as e:
                print(f"Error creating histogram: {e}")
                self.after(0, self._show_empty_state)
        
        # Start background thread
        thread = threading.Thread(target=calculate_histogram, daemon=True)
        thread.start()
    
    def _create_rgb_histogram(self):
        """Create RGB histogram."""
        self.figure.clear()
        
        # Convert image to numpy array
        img_array = np.array(self.current_image.pil_image)
        
        # Handle different image modes
        if len(img_array.shape) == 3 and img_array.shape[2] >= 3:
            # RGB or RGBA image
            r_channel = img_array[:, :, 0].flatten()
            g_channel = img_array[:, :, 1].flatten()
            b_channel = img_array[:, :, 2].flatten()
        else:
            # Grayscale image
            gray_channel = img_array.flatten()
            r_channel = g_channel = b_channel = gray_channel
        
        # Create histogram
        ax = self.figure.add_subplot(111)
        
        bins = 50
        alpha = 0.7
        
        ax.hist(r_channel, bins=bins, color='red', alpha=alpha, label='Red', density=True)
        ax.hist(g_channel, bins=bins, color='green', alpha=alpha, label='Green', density=True)
        ax.hist(b_channel, bins=bins, color='blue', alpha=alpha, label='Blue', density=True)
        
        ax.set_xlabel('Pixel Value')
        ax.set_ylabel('Density')
        ax.set_title('RGB Histogram')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        self.figure.tight_layout()
    
    def _create_hue_histogram(self):
        """Create hue histogram."""
        self.figure.clear()
        
        # Convert to HSV
        hsv_image = self.current_image.pil_image.convert('HSV')
        hsv_array = np.array(hsv_image)
        
        # Extract hue channel (0-255 in PIL, convert to 0-360)
        hue_channel = hsv_array[:, :, 0].flatten()
        hue_degrees = (hue_channel / 255.0) * 360
        
        # Create histogram
        ax = self.figure.add_subplot(111)
        
        n, bins, patches = ax.hist(hue_degrees, bins=36, density=True, edgecolor='black', alpha=0.7)
        
        # Color the bars with corresponding hues
        for i, (patch, bin_center) in enumerate(zip(patches, (bins[:-1] + bins[1:]) / 2)):
            # Convert hue to RGB for coloring
            hue_normalized = bin_center / 360.0
            rgb = plt.cm.hsv(hue_normalized)
            patch.set_facecolor(rgb)
        
        ax.set_xlabel('Hue (degrees)')
        ax.set_ylabel('Density')
        ax.set_title('Hue Histogram')
        ax.set_xlim(0, 360)
        ax.grid(True, alpha=0.3)
        
        self.figure.tight_layout()
    
    def _create_saturation_histogram(self):
        """Create saturation histogram."""
        self.figure.clear()
        
        # Convert to HSV
        hsv_image = self.current_image.pil_image.convert('HSV')
        hsv_array = np.array(hsv_image)
        
        # Extract saturation channel
        saturation_channel = hsv_array[:, :, 1].flatten()
        
        # Create histogram
        ax = self.figure.add_subplot(111)
        
        ax.hist(saturation_channel, bins=50, color='purple', alpha=0.7, density=True, edgecolor='black')
        
        ax.set_xlabel('Saturation (0-255)')
        ax.set_ylabel('Density')
        ax.set_title('Saturation Histogram')
        ax.grid(True, alpha=0.3)
        
        self.figure.tight_layout()
    
    def _create_brightness_histogram(self):
        """Create brightness (value) histogram."""
        self.figure.clear()
        
        # Convert to grayscale for brightness
        gray_image = self.current_image.pil_image.convert('L')
        gray_array = np.array(gray_image).flatten()
        
        # Create histogram
        ax = self.figure.add_subplot(111)
        
        ax.hist(gray_array, bins=50, color='gray', alpha=0.7, density=True, edgecolor='black')
        
        ax.set_xlabel('Brightness (0-255)')
        ax.set_ylabel('Density')
        ax.set_title('Brightness Histogram')
        ax.grid(True, alpha=0.3)
        
        self.figure.tight_layout()
    
    def _on_type_changed(self, event=None):
        """Handle histogram type change."""
        self._update_histogram()


class ColorStatisticsWidget(tk.Frame):
    """Widget for displaying color distribution statistics."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.current_stats: Optional[Dict[str, Any]] = None
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the widget UI."""
        # Title
        title_label = ttk.Label(self, text="Color Statistics", font=("TkDefaultFont", 10, "bold"))
        title_label.pack(anchor="w", pady=(0, 5))
        
        # Statistics frame
        self.stats_frame = ttk.Frame(self)
        self.stats_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create statistics labels
        self.stats_labels = {}
        
        stats_info = [
            ("total_colors", "Unique Colors:"),
            ("average_color", "Average Color:"),
            ("brightness_avg", "Avg Brightness:"),
            ("saturation_avg", "Avg Saturation:"),
            ("hue_range", "Hue Range:"),
            ("contrast_ratio", "Contrast Ratio:"),
            ("color_temperature", "Color Temperature:"),
            ("dominant_hue", "Dominant Hue:")
        ]
        
        for i, (key, label) in enumerate(stats_info):
            row = i // 2
            col = (i % 2) * 2
            
            # Label
            ttk.Label(self.stats_frame, text=label).grid(row=row, column=col, sticky="w", padx=(0, 5), pady=2)
            
            # Value
            value_label = ttk.Label(self.stats_frame, text="-", font=("TkDefaultFont", 9, "bold"))
            value_label.grid(row=row, column=col+1, sticky="w", padx=(0, 20), pady=2)
            
            self.stats_labels[key] = value_label
        
        # Configure grid
        for i in range(4):
            self.stats_frame.grid_columnconfigure(i, weight=1 if i % 2 == 1 else 0)
    
    def update_statistics(self, stats: Dict[str, Any]):
        """Update the statistics display."""
        self.current_stats = stats
        
        # Update labels
        for key, label in self.stats_labels.items():
            if key in stats:
                value = stats[key]
                
                if key == "average_color" and isinstance(value, ColorData):
                    label.configure(text=value.hex)
                elif key in ["brightness_avg", "saturation_avg"]:
                    label.configure(text=f"{value:.1f}")
                elif key == "hue_range":
                    if isinstance(value, tuple):
                        label.configure(text=f"{value[0]:.0f}°-{value[1]:.0f}°")
                    else:
                        label.configure(text=f"{value:.0f}°")
                elif key == "contrast_ratio":
                    label.configure(text=f"{value:.2f}:1")
                elif key == "color_temperature":
                    label.configure(text=f"{value:.0f}K")
                elif key == "dominant_hue":
                    label.configure(text=f"{value:.0f}°")
                else:
                    label.configure(text=str(value))
            else:
                label.configure(text="-")


class PaletteExtractionWidget(tk.Frame):
    """Widget for extracting and displaying color palettes from images."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.extracted_palette: List[ColorData] = []
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the widget UI."""
        # Title and controls
        header_frame = ttk.Frame(self)
        header_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(header_frame, text="Palette Extraction", font=("TkDefaultFont", 10, "bold")).pack(side=tk.LEFT)
        
        # Controls
        controls_frame = ttk.Frame(self)
        controls_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(controls_frame, text="Colors:").pack(side=tk.LEFT)
        
        self.color_count_var = tk.StringVar(value="8")
        color_count_spin = ttk.Spinbox(controls_frame, from_=3, to=20, width=5, 
                                     textvariable=self.color_count_var)
        color_count_spin.pack(side=tk.LEFT, padx=(5, 10))
        
        ttk.Label(controls_frame, text="Method:").pack(side=tk.LEFT)
        
        self.method_var = tk.StringVar(value="kmeans")
        method_combo = ttk.Combobox(controls_frame, textvariable=self.method_var,
                                  values=["kmeans", "quantize", "dominant"],
                                  state="readonly", width=10)
        method_combo.pack(side=tk.LEFT, padx=(5, 10))
        
        ttk.Button(controls_frame, text="Extract", command=self._extract_palette).pack(side=tk.LEFT, padx=(10, 0))
        ttk.Button(controls_frame, text="Save Palette", command=self._save_palette).pack(side=tk.LEFT, padx=5)
        
        # Palette display
        self.palette_frame = tk.Frame(self, bg="white", relief=tk.SUNKEN, borderwidth=1, height=80)
        self.palette_frame.pack(fill=tk.X, pady=(0, 5))
        self.palette_frame.pack_propagate(False)
        
        # Info label
        self.palette_info_label = ttk.Label(self, text="No palette extracted", font=("TkDefaultFont", 8))
        self.palette_info_label.pack(anchor="w")
    
    def set_image(self, image_data: ImageData):
        """Set the image for palette extraction."""
        self.current_image = image_data
    
    def _extract_palette(self):
        """Extract color palette from current image."""
        if not hasattr(self, 'current_image') or not self.current_image:
            messagebox.showwarning("No Image", "No image loaded for palette extraction.")
            return
        
        try:
            color_count = int(self.color_count_var.get())
            method = self.method_var.get()
            
            # Extract palette using different methods
            if method == "kmeans":
                self.extracted_palette = self._extract_kmeans_palette(color_count)
            elif method == "quantize":
                self.extracted_palette = self._extract_quantize_palette(color_count)
            else:  # dominant
                self.extracted_palette = self._extract_dominant_palette(color_count)
            
            self._update_palette_display()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to extract palette: {str(e)}")
    
    def _extract_kmeans_palette(self, color_count: int) -> List[ColorData]:
        """Extract palette using K-means clustering."""
        try:
            from sklearn.cluster import KMeans
        except ImportError:
            messagebox.showerror("Error", "scikit-learn is required for K-means palette extraction.")
            return []
        
        # Convert image to RGB array
        img_rgb = self.current_image.pil_image.convert('RGB')
        img_array = np.array(img_rgb)
        
        # Reshape to list of pixels
        pixels = img_array.reshape(-1, 3)
        
        # Sample pixels for performance (use max 10000 pixels)
        if len(pixels) > 10000:
            indices = np.random.choice(len(pixels), 10000, replace=False)
            pixels = pixels[indices]
        
        # Apply K-means
        kmeans = KMeans(n_clusters=color_count, random_state=42, n_init=10)
        kmeans.fit(pixels)
        
        # Get cluster centers as colors
        colors = []
        for center in kmeans.cluster_centers_:
            r, g, b = center.astype(int)
            colors.append(ColorData.from_rgb(r, g, b))
        
        return colors
    
    def _extract_quantize_palette(self, color_count: int) -> List[ColorData]:
        """Extract palette using PIL quantization."""
        # Convert to RGB and quantize
        img_rgb = self.current_image.pil_image.convert('RGB')
        quantized = img_rgb.quantize(colors=color_count)
        
        # Get palette colors
        palette = quantized.getpalette()
        colors = []
        
        for i in range(color_count):
            r = palette[i * 3]
            g = palette[i * 3 + 1]
            b = palette[i * 3 + 2]
            colors.append(ColorData.from_rgb(r, g, b))
        
        return colors
    
    def _extract_dominant_palette(self, color_count: int) -> List[ColorData]:
        """Extract palette using dominant color analysis."""
        # Convert to RGB
        img_rgb = self.current_image.pil_image.convert('RGB')
        img_array = np.array(img_rgb)
        
        # Flatten to list of pixels
        pixels = img_array.reshape(-1, 3)
        
        # Count color frequencies
        unique_colors, counts = np.unique(pixels, axis=0, return_counts=True)
        
        # Sort by frequency
        sorted_indices = np.argsort(counts)[::-1]
        
        # Get top colors
        colors = []
        for i in range(min(color_count, len(unique_colors))):
            idx = sorted_indices[i]
            r, g, b = unique_colors[idx]
            colors.append(ColorData.from_rgb(int(r), int(g), int(b)))
        
        return colors
    
    def _update_palette_display(self):
        """Update the palette display."""
        # Clear existing widgets
        for widget in self.palette_frame.winfo_children():
            widget.destroy()
        
        if not self.extracted_palette:
            no_data_label = tk.Label(self.palette_frame, text="No palette extracted", 
                                   bg="white", fg="gray")
            no_data_label.pack(expand=True)
            self.palette_info_label.configure(text="No palette")
            return
        
        # Create color swatches
        swatch_width = min(60, 400 // len(self.extracted_palette))
        
        for i, color in enumerate(self.extracted_palette):
            swatch = tk.Canvas(self.palette_frame, width=swatch_width, height=60, 
                             highlightthickness=1, highlightbackground="#ccc")
            swatch.pack(side=tk.LEFT, padx=1, pady=5)
            
            # Draw color
            swatch.create_rectangle(0, 0, swatch_width, 60, fill=color.hex, outline="")
            
            # Add click handler
            def on_click(c=color):
                self._on_palette_color_click(c)
            
            swatch.bind("<Button-1>", lambda e, c=color: self._on_palette_color_click(c))
        
        # Update info
        self.palette_info_label.configure(text=f"{len(self.extracted_palette)} colors extracted")
    
    def _on_palette_color_click(self, color: ColorData):
        """Handle palette color click."""
        print(f"Palette color selected: {color.hex}")
        # This would typically publish an event or call a callback
    
    def _save_palette(self):
        """Save the extracted palette."""
        if not self.extracted_palette:
            messagebox.showwarning("No Palette", "No palette to save. Extract a palette first.")
            return
        
        # This would typically integrate with the palette service
        messagebox.showinfo("Save Palette", "Palette saving functionality would be implemented here.")


class ColorAnalysisPanel(ttk.Frame):
    """
    Comprehensive color analysis panel with multiple analysis tools.
    
    Features:
    - Dominant colors display with percentages
    - Color histogram visualization (RGB, HSV channels)
    - Color distribution statistics
    - Color palette extraction from images
    """
    
    def __init__(self, parent, event_bus: EventBus, analysis_service: Optional[AnalysisService] = None, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.event_bus = event_bus
        self.analysis_service = analysis_service or AnalysisService()
        self.current_image: Optional[ImageData] = None
        
        self._setup_ui()
        self._setup_event_subscriptions()
    
    def _setup_ui(self):
        """Setup the user interface."""
        # Create notebook for different analysis views
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Dominant colors tab
        self.dominant_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.dominant_frame, text="Dominant Colors")
        
        self.dominant_widget = DominantColorsWidget(self.dominant_frame)
        self.dominant_widget.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Histogram tab
        self.histogram_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.histogram_frame, text="Histogram")
        
        self.histogram_widget = ColorHistogramWidget(self.histogram_frame)
        self.histogram_widget.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Statistics tab
        self.statistics_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.statistics_frame, text="Statistics")
        
        self.statistics_widget = ColorStatisticsWidget(self.statistics_frame)
        self.statistics_widget.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Palette extraction tab
        self.palette_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.palette_frame, text="Palette Extraction")
        
        self.palette_widget = PaletteExtractionWidget(self.palette_frame)
        self.palette_widget.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def _setup_event_subscriptions(self):
        """Setup event bus subscriptions."""
        self.event_bus.subscribe("image_loaded", self._on_image_loaded)
        self.event_bus.subscribe("image_displayed", self._on_image_displayed)
    
    def analyze_image(self, image_data: ImageData):
        """Analyze the given image and update all displays."""
        self.current_image = image_data
        
        # Start analysis in background thread
        def run_analysis():
            try:
                # Get dominant colors
                dominant_colors = self.analysis_service.extract_dominant_colors(image_data, count=8)
                
                # Calculate color statistics
                stats = self.analysis_service.calculate_color_statistics(image_data)
                
                # Update UI on main thread
                self.after(0, lambda: self._update_analysis_results(dominant_colors, stats))
                
            except Exception as e:
                print(f"Error analyzing image: {e}")
                self.after(0, lambda: messagebox.showerror("Analysis Error", f"Failed to analyze image: {str(e)}"))
        
        # Start background thread
        thread = threading.Thread(target=run_analysis, daemon=True)
        thread.start()
        
        # Update histogram and palette extraction widgets immediately
        self.histogram_widget.update_image(image_data)
        self.palette_widget.set_image(image_data)
    
    def _update_analysis_results(self, dominant_colors: List[ColorData], stats: Dict[str, Any]):
        """Update analysis results on UI thread."""
        # Convert dominant colors to format expected by widget
        # For now, we'll assign equal percentages - this should be calculated properly
        if dominant_colors:
            total_colors = len(dominant_colors)
            colors_with_percentages = [(color, 100.0 / total_colors) for color in dominant_colors]
            self.dominant_widget.update_dominant_colors(colors_with_percentages)
        
        # Update statistics
        self.statistics_widget.update_statistics(stats)
    
    # Event handlers
    def _on_image_loaded(self, event_data: EventData):
        """Handle image loaded event."""
        data = event_data.data
        if "image_data" in data:
            self.analyze_image(data["image_data"])
    
    def _on_image_displayed(self, event_data: EventData):
        """Handle image displayed event."""
        data = event_data.data
        if "image_data" in data:
            self.analyze_image(data["image_data"])
    
    def get_current_analysis(self) -> Optional[Dict[str, Any]]:
        """Get current analysis results."""
        if not self.current_image:
            return None
        
        return {
            "image": self.current_image,
            "dominant_colors": self.dominant_widget.dominant_colors,
            "statistics": self.statistics_widget.current_stats,
            "extracted_palette": self.palette_widget.extracted_palette
        }
    
    def clear_analysis(self):
        """Clear all analysis results."""
        self.current_image = None
        self.dominant_widget.update_dominant_colors([])
        self.statistics_widget.update_statistics({})
        self.histogram_widget._show_empty_state()
        self.palette_widget._update_palette_display()