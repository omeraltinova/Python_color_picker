"""
Color Blindness Panel for simulating and testing color blindness effects.

This panel provides:
- Real-time color blindness simulation
- Color blindness type selection
- Palette accessibility testing
- Color blindness-safe recommendations
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, List, Dict, Any
import threading
from PIL import Image, ImageTk

from ...models.color_data import ColorData
from ...models.enums import ColorBlindnessType
from ...models.palette import Palette
from ...services.color_blindness_service import (
    ColorBlindnessService, ColorBlindnessSimulation, PaletteAccessibilityAnalysis
)
from ...core.event_bus import EventBus


class ColorBlindnessPanel(ttk.Frame):
    """Panel for color blindness simulation and accessibility testing"""
    
    def __init__(self, parent, event_bus: EventBus):
        super().__init__(parent)
        self.event_bus = event_bus
        self.color_blindness_service = ColorBlindnessService()
        
        # Current state
        self.current_color: Optional[ColorData] = None
        self.current_image: Optional[Image.Image] = None
        self.current_palette: Optional[List[ColorData]] = None
        self.selected_blindness_type = tk.StringVar(value="PROTANOPIA")
        self.severity_var = tk.DoubleVar(value=1.0)
        self.real_time_enabled = tk.BooleanVar(value=True)
        
        # Simulation results
        self.current_simulation: Optional[ColorBlindnessSimulation] = None
        self.current_palette_analysis: Optional[PaletteAccessibilityAnalysis] = None
        
        self._setup_ui()
        self._setup_event_handlers()
    
    def _setup_ui(self):
        """Setup the color blindness panel UI"""
        # Main title
        title_label = ttk.Label(self, text="Color Blindness Simulation", 
                               font=('Arial', 12, 'bold'))
        title_label.pack(pady=(0, 10), anchor='w')
        
        # Color blindness type selection
        self._create_blindness_type_selection()
        
        # Severity control
        self._create_severity_control()
        
        # Real-time simulation toggle
        self._create_realtime_toggle()
        
        # Color simulation display
        self._create_color_simulation_display()
        
        # Image simulation controls
        self._create_image_simulation_controls()
        
        # Palette accessibility testing
        self._create_palette_testing()
        
        # Information and recommendations
        self._create_info_display()
    
    def _create_blindness_type_selection(self):
        """Create color blindness type selection"""
        type_frame = ttk.LabelFrame(self, text="Color Blindness Type", padding=10)
        type_frame.pack(fill='x', pady=(0, 10))
        
        # Get all blindness types with info
        blindness_info = self.color_blindness_service.get_all_blindness_types_info()
        
        # Create radio buttons for each type
        for i, (blindness_type, info) in enumerate(blindness_info.items()):
            radio_frame = ttk.Frame(type_frame)
            radio_frame.pack(fill='x', pady=2)
            
            radio = ttk.Radiobutton(
                radio_frame,
                text=f"{info['name']} ({info['prevalence']})",
                variable=self.selected_blindness_type,
                value=blindness_type.value,
                command=self._on_blindness_type_changed
            )
            radio.pack(side='left')
            
            # Info button
            info_btn = ttk.Button(
                radio_frame, 
                text="ℹ️", 
                width=3,
                command=lambda t=blindness_type: self._show_blindness_info(t)
            )
            info_btn.pack(side='right')
    
    def _create_severity_control(self):
        """Create severity control for partial color blindness"""
        severity_frame = ttk.LabelFrame(self, text="Severity", padding=10)
        severity_frame.pack(fill='x', pady=(0, 10))
        
        # Severity scale
        severity_scale = ttk.Scale(
            severity_frame,
            from_=0.0,
            to=1.0,
            orient='horizontal',
            variable=self.severity_var,
            command=self._on_severity_changed
        )
        severity_scale.pack(fill='x', pady=(0, 5))
        
        # Severity label
        self.severity_label = ttk.Label(severity_frame, text="Severity: 100%")
        self.severity_label.pack()
        
        # Update label initially
        self._update_severity_label()
    
    def _create_realtime_toggle(self):
        """Create real-time simulation toggle"""
        realtime_frame = ttk.Frame(self)
        realtime_frame.pack(fill='x', pady=(0, 10))
        
        realtime_check = ttk.Checkbutton(
            realtime_frame,
            text="Real-time simulation",
            variable=self.real_time_enabled,
            command=self._on_realtime_toggled
        )
        realtime_check.pack(side='left')
        
        # Manual update button (for when real-time is disabled)
        self.update_btn = ttk.Button(
            realtime_frame,
            text="Update Simulation",
            command=self._update_simulation,
            state='disabled'
        )
        self.update_btn.pack(side='right')
    
    def _create_color_simulation_display(self):
        """Create color simulation display"""
        color_frame = ttk.LabelFrame(self, text="Color Simulation", padding=10)
        color_frame.pack(fill='x', pady=(0, 10))
        
        # Original vs Simulated comparison
        comparison_frame = ttk.Frame(color_frame)
        comparison_frame.pack(fill='x')
        
        # Original color
        original_frame = ttk.Frame(comparison_frame)
        original_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))
        
        ttk.Label(original_frame, text="Original", font=('Arial', 10, 'bold')).pack()
        self.original_color_canvas = tk.Canvas(original_frame, width=100, height=60,
                                              relief='solid', borderwidth=1)
        self.original_color_canvas.pack(pady=5)
        self.original_color_label = ttk.Label(original_frame, text="No color selected")
        self.original_color_label.pack()
        
        # Arrow
        arrow_frame = ttk.Frame(comparison_frame)
        arrow_frame.pack(side='left', padx=10)
        ttk.Label(arrow_frame, text="→", font=('Arial', 20)).pack(pady=20)
        
        # Simulated color
        simulated_frame = ttk.Frame(comparison_frame)
        simulated_frame.pack(side='left', fill='both', expand=True, padx=(5, 0))
        
        ttk.Label(simulated_frame, text="Simulated", font=('Arial', 10, 'bold')).pack()
        self.simulated_color_canvas = tk.Canvas(simulated_frame, width=100, height=60,
                                               relief='solid', borderwidth=1)
        self.simulated_color_canvas.pack(pady=5)
        self.simulated_color_label = ttk.Label(simulated_frame, text="No simulation")
        self.simulated_color_label.pack()
        
        # Distinguishability indicator
        self.distinguishable_label = ttk.Label(color_frame, text="", 
                                              font=('Arial', 10, 'bold'))
        self.distinguishable_label.pack(pady=(10, 0))
    
    def _create_image_simulation_controls(self):
        """Create image simulation controls"""
        image_frame = ttk.LabelFrame(self, text="Image Simulation", padding=10)
        image_frame.pack(fill='x', pady=(0, 10))
        
        # Image simulation button
        ttk.Button(image_frame, text="Simulate Current Image",
                  command=self._simulate_current_image).pack(side='left')
        
        # Reset image button
        ttk.Button(image_frame, text="Reset Image",
                  command=self._reset_image_simulation).pack(side='left', padx=(10, 0))
        
        # Status label
        self.image_status_label = ttk.Label(image_frame, text="No image loaded")
        self.image_status_label.pack(side='right')
    
    def _create_palette_testing(self):
        """Create palette accessibility testing"""
        palette_frame = ttk.LabelFrame(self, text="Palette Accessibility", padding=10)
        palette_frame.pack(fill='x', pady=(0, 10))
        
        # Test current palette button
        ttk.Button(palette_frame, text="Test Current Palette",
                  command=self._test_current_palette).pack(side='left')
        
        # Clear results button
        ttk.Button(palette_frame, text="Clear Results",
                  command=self._clear_palette_results).pack(side='left', padx=(10, 0))
        
        # Accessibility score
        self.accessibility_score_label = ttk.Label(palette_frame, text="Score: N/A")
        self.accessibility_score_label.pack(side='right')
        
        # Results display
        self.palette_results_text = tk.Text(palette_frame, height=4, wrap='word',
                                           font=('Arial', 9))
        palette_scrollbar = ttk.Scrollbar(palette_frame, orient='vertical',
                                         command=self.palette_results_text.yview)
        self.palette_results_text.configure(yscrollcommand=palette_scrollbar.set)
        
        self.palette_results_text.pack(fill='x', pady=(10, 0))
        palette_scrollbar.pack(side='right', fill='y')
    
    def _create_info_display(self):
        """Create information and recommendations display"""
        info_frame = ttk.LabelFrame(self, text="Information & Tips", padding=10)
        info_frame.pack(fill='both', expand=True)
        
        # Info text widget
        self.info_text = tk.Text(info_frame, height=6, wrap='word',
                                font=('Arial', 9), state='disabled')
        info_scrollbar = ttk.Scrollbar(info_frame, orient='vertical',
                                      command=self.info_text.yview)
        self.info_text.configure(yscrollcommand=info_scrollbar.set)
        
        self.info_text.pack(side='left', fill='both', expand=True)
        info_scrollbar.pack(side='right', fill='y')
        
        # Load initial info
        self._update_info_display()
    
    def _setup_event_handlers(self):
        """Setup event handlers"""
        self.event_bus.subscribe('color_selected', self._on_color_selected)
        self.event_bus.subscribe('image_loaded', self._on_image_loaded)
        self.event_bus.subscribe('palette_changed', self._on_palette_changed)
    
    def _on_color_selected(self, color_data: ColorData):
        """Handle color selection events"""
        self.current_color = color_data
        self._update_color_display()
        
        if self.real_time_enabled.get():
            self._update_simulation()
    
    def _on_image_loaded(self, image_data):
        """Handle image loading events"""
        if hasattr(image_data, 'pil_image'):
            self.current_image = image_data.pil_image
            self.image_status_label.configure(text="Image loaded")
        else:
            self.current_image = image_data
            self.image_status_label.configure(text="Image loaded")
    
    def _on_palette_changed(self, palette_data):
        """Handle palette change events"""
        if isinstance(palette_data, list):
            self.current_palette = palette_data
        elif hasattr(palette_data, 'colors'):
            self.current_palette = palette_data.colors
    
    def _on_blindness_type_changed(self):
        """Handle blindness type selection change"""
        if self.real_time_enabled.get():
            self._update_simulation()
        self._update_info_display()
    
    def _on_severity_changed(self, value):
        """Handle severity change"""
        self._update_severity_label()
        if self.real_time_enabled.get():
            self._update_simulation()
    
    def _update_severity_label(self):
        """Update severity label"""
        severity_percent = int(self.severity_var.get() * 100)
        self.severity_label.configure(text=f"Severity: {severity_percent}%")
    
    def _on_realtime_toggled(self):
        """Handle real-time toggle"""
        if self.real_time_enabled.get():
            self.update_btn.configure(state='disabled')
            self._update_simulation()
        else:
            self.update_btn.configure(state='normal')
    
    def _update_color_display(self):
        """Update color display"""
        if self.current_color:
            self.original_color_canvas.configure(bg=self.current_color.hex)
            self.original_color_label.configure(text=self.current_color.hex)
        else:
            self.original_color_canvas.configure(bg='white')
            self.original_color_label.configure(text="No color selected")
    
    def _update_simulation(self):
        """Update color blindness simulation"""
        if not self.current_color:
            self._clear_simulation_display()
            return
        
        # Run simulation in background thread
        threading.Thread(target=self._perform_color_simulation, daemon=True).start()
    
    def _perform_color_simulation(self):
        """Perform color simulation in background thread"""
        try:
            blindness_type = ColorBlindnessType(self.selected_blindness_type.get())
            severity = self.severity_var.get()
            
            simulation = self.color_blindness_service.simulate_color_blindness(
                self.current_color, blindness_type, severity
            )
            
            # Update UI in main thread
            self.after(0, lambda: self._update_simulation_display(simulation))
            
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Simulation Error",
                                                      f"Failed to simulate color blindness: {str(e)}"))
    
    def _update_simulation_display(self, simulation: ColorBlindnessSimulation):
        """Update simulation display with results"""
        self.current_simulation = simulation
        
        # Update simulated color display
        simulated_color = simulation.simulated_color
        self.simulated_color_canvas.configure(bg=simulated_color.hex)
        self.simulated_color_label.configure(text=simulated_color.hex)
        
        # Update distinguishability indicator
        if simulation.is_distinguishable:
            self.distinguishable_label.configure(
                text="✅ Colors are distinguishable",
                foreground='green'
            )
        else:
            self.distinguishable_label.configure(
                text="⚠️ Colors may be hard to distinguish",
                foreground='red'
            )
    
    def _clear_simulation_display(self):
        """Clear simulation display"""
        self.simulated_color_canvas.configure(bg='white')
        self.simulated_color_label.configure(text="No simulation")
        self.distinguishable_label.configure(text="")
        self.current_simulation = None
    
    def _simulate_current_image(self):
        """Simulate color blindness for current image"""
        if not self.current_image:
            messagebox.showwarning("No Image", "Please load an image first")
            return
        
        # Run image simulation in background thread
        threading.Thread(target=self._perform_image_simulation, daemon=True).start()
    
    def _perform_image_simulation(self):
        """Perform image simulation in background thread"""
        try:
            blindness_type = ColorBlindnessType(self.selected_blindness_type.get())
            severity = self.severity_var.get()
            
            simulated_image = self.color_blindness_service.simulate_image_color_blindness(
                self.current_image, blindness_type, severity
            )
            
            # Publish simulated image
            self.after(0, lambda: self.event_bus.publish('image_simulated', simulated_image))
            self.after(0, lambda: self.image_status_label.configure(text="Simulation applied"))
            
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Image Simulation Error",
                                                      f"Failed to simulate image: {str(e)}"))
    
    def _reset_image_simulation(self):
        """Reset image simulation"""
        if self.current_image:
            self.event_bus.publish('image_reset_requested', None)
            self.image_status_label.configure(text="Image reset")
    
    def _test_current_palette(self):
        """Test current palette for accessibility"""
        if not self.current_palette:
            messagebox.showwarning("No Palette", "Please create or load a palette first")
            return
        
        # Run palette analysis in background thread
        threading.Thread(target=self._perform_palette_analysis, daemon=True).start()
    
    def _perform_palette_analysis(self):
        """Perform palette analysis in background thread"""
        try:
            analysis = self.color_blindness_service.analyze_palette_accessibility(
                self.current_palette
            )
            
            # Update UI in main thread
            self.after(0, lambda: self._update_palette_analysis_display(analysis))
            
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Analysis Error",
                                                      f"Failed to analyze palette: {str(e)}"))
    
    def _update_palette_analysis_display(self, analysis: PaletteAccessibilityAnalysis):
        """Update palette analysis display"""
        self.current_palette_analysis = analysis
        
        # Update accessibility score
        score_percent = int(analysis.accessibility_score * 100)
        score_color = 'green' if score_percent >= 80 else 'orange' if score_percent >= 60 else 'red'
        self.accessibility_score_label.configure(
            text=f"Score: {score_percent}%",
            foreground=score_color
        )
        
        # Update results text
        self.palette_results_text.configure(state='normal')
        self.palette_results_text.delete('1.0', tk.END)
        
        results_text = f"Accessibility Analysis Results:\n\n"
        results_text += f"Total colors: {len(analysis.original_palette)}\n"
        results_text += f"Problematic pairs: {len(analysis.problematic_pairs)}\n"
        results_text += f"Accessibility score: {score_percent}%\n\n"
        
        results_text += "Recommendations:\n"
        for rec in analysis.recommendations:
            results_text += f"• {rec}\n"
        
        if analysis.problematic_pairs:
            results_text += f"\nProblematic color pairs:\n"
            for i, j in analysis.problematic_pairs:
                color1 = analysis.original_palette[i]
                color2 = analysis.original_palette[j]
                results_text += f"• {color1.hex} ↔ {color2.hex}\n"
        
        self.palette_results_text.insert('1.0', results_text)
        self.palette_results_text.configure(state='disabled')
    
    def _clear_palette_results(self):
        """Clear palette analysis results"""
        self.current_palette_analysis = None
        self.accessibility_score_label.configure(text="Score: N/A", foreground='black')
        
        self.palette_results_text.configure(state='normal')
        self.palette_results_text.delete('1.0', tk.END)
        self.palette_results_text.configure(state='disabled')
    
    def _show_blindness_info(self, blindness_type: ColorBlindnessType):
        """Show detailed information about a color blindness type"""
        info = self.color_blindness_service.get_color_blindness_info(blindness_type)
        
        info_window = tk.Toplevel(self)
        info_window.title(f"{info['name']} Information")
        info_window.geometry("400x300")
        
        # Info content
        info_frame = ttk.Frame(info_window)
        info_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        ttk.Label(info_frame, text=info['name'], 
                 font=('Arial', 14, 'bold')).pack(anchor='w', pady=(0, 10))
        
        ttk.Label(info_frame, text=f"Description: {info['description']}",
                 wraplength=350, justify='left').pack(anchor='w', pady=2)
        
        ttk.Label(info_frame, text=f"Prevalence: {info['prevalence']}",
                 wraplength=350, justify='left').pack(anchor='w', pady=2)
        
        ttk.Label(info_frame, text=f"Affected Colors: {info['affected_colors']}",
                 wraplength=350, justify='left').pack(anchor='w', pady=2)
        
        ttk.Label(info_frame, text=f"Severity: {info['severity']}",
                 wraplength=350, justify='left').pack(anchor='w', pady=2)
        
        # Close button
        ttk.Button(info_window, text="Close",
                  command=info_window.destroy).pack(pady=10)
    
    def _update_info_display(self):
        """Update information display"""
        blindness_type = ColorBlindnessType(self.selected_blindness_type.get())
        info = self.color_blindness_service.get_color_blindness_info(blindness_type)
        
        info_text = f"Current Type: {info['name']}\n"
        info_text += f"Description: {info['description']}\n"
        info_text += f"Prevalence: {info['prevalence']}\n"
        info_text += f"Affected Colors: {info['affected_colors']}\n\n"
        
        info_text += "Tips for Accessibility:\n"
        info_text += "• Use sufficient contrast between colors\n"
        info_text += "• Don't rely solely on color to convey information\n"
        info_text += "• Consider using patterns, shapes, or text labels\n"
        info_text += "• Test your designs with simulation tools\n"
        info_text += "• Use color-blind safe palettes when possible"
        
        self.info_text.configure(state='normal')
        self.info_text.delete('1.0', tk.END)
        self.info_text.insert('1.0', info_text)
        self.info_text.configure(state='disabled')
    
    def get_current_simulation(self) -> Optional[ColorBlindnessSimulation]:
        """Get current color simulation"""
        return self.current_simulation
    
    def get_current_palette_analysis(self) -> Optional[PaletteAccessibilityAnalysis]:
        """Get current palette analysis"""
        return self.current_palette_analysis