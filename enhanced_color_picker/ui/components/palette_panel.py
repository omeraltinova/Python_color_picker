"""
Palette Management Panel Component

Advanced palette creation, editing, and management interface with drag-and-drop
color organization, save/load functionality, and multi-format export capabilities.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from typing import Optional, List, Dict, Any, Callable
import os
from datetime import datetime
import json

from ...models.color_data import ColorData
from ...models.palette import Palette
from ...models.enums import ExportFormat
from ...core.event_bus import EventBus, EventData
from ...services.palette_service import PaletteService


class ColorSwatchWidget(tk.Frame):
    """Individual color swatch widget with drag-and-drop support."""
    
    def __init__(self, parent, color: ColorData, index: int, 
                 on_click: Optional[Callable] = None,
                 on_right_click: Optional[Callable] = None,
                 on_drag_start: Optional[Callable] = None,
                 on_drag_end: Optional[Callable] = None,
                 **kwargs):
        super().__init__(parent, **kwargs)
        
        self.color = color
        self.index = index
        self.on_click = on_click
        self.on_right_click = on_right_click
        self.on_drag_start = on_drag_start
        self.on_drag_end = on_drag_end
        
        self.is_selected = False
        self.is_dragging = False
        self.drag_start_x = 0
        self.drag_start_y = 0
        
        self._setup_ui()
        self._bind_events()
    
    def _setup_ui(self):
        """Setup the swatch UI."""
        self.configure(relief=tk.RAISED, borderwidth=2, width=50, height=50)
        
        # Color canvas
        self.canvas = tk.Canvas(self, width=46, height=46, highlightthickness=0)
        self.canvas.pack(padx=2, pady=2)
        
        # Draw color
        self._update_color_display()
        
        # Tooltip
        self._create_tooltip()
    
    def _update_color_display(self):
        """Update the color display."""
        self.canvas.delete("all")
        
        # Draw color rectangle
        hex_color = self.color.hex
        self.canvas.create_rectangle(0, 0, 46, 46, fill=hex_color, outline="", tags="color")
        
        # Add selection border if selected
        if self.is_selected:
            self.canvas.create_rectangle(0, 0, 46, 46, outline="#000000", width=3, tags="selection")
        
        # Add transparency pattern if needed
        if self.color.alpha < 1.0:
            self._draw_transparency_pattern()
    
    def _draw_transparency_pattern(self):
        """Draw transparency checkerboard pattern."""
        for x in range(0, 46, 6):
            for y in range(0, 46, 6):
                if (x // 6 + y // 6) % 2 == 0:
                    self.canvas.create_rectangle(x, y, x+6, y+6, fill="#ffffff", outline="", tags="transparency")
                else:
                    self.canvas.create_rectangle(x, y, x+6, y+6, fill="#cccccc", outline="", tags="transparency")
        
        # Overlay color with alpha simulation
        alpha_color = f"#{self.color.r:02x}{self.color.g:02x}{self.color.b:02x}"
        self.canvas.create_rectangle(0, 0, 46, 46, fill=alpha_color, outline="", stipple="gray50", tags="alpha")
    
    def _create_tooltip(self):
        """Create tooltip showing color information."""
        def show_tooltip(event):
            tooltip_text = f"{self.color.hex}\nRGB: {self.color.rgb}\nIndex: {self.index}"
            # Simple tooltip implementation
            self.tooltip_label = tk.Label(self, text=tooltip_text, 
                                        background="lightyellow", relief=tk.SOLID, borderwidth=1,
                                        font=("TkDefaultFont", 8))
            self.tooltip_label.place(x=event.x + 10, y=event.y + 10)
        
        def hide_tooltip(event):
            if hasattr(self, 'tooltip_label'):
                self.tooltip_label.destroy()
        
        self.canvas.bind("<Enter>", show_tooltip)
        self.canvas.bind("<Leave>", hide_tooltip)
    
    def _bind_events(self):
        """Bind mouse events for interaction."""
        self.canvas.bind("<Button-1>", self._on_left_click)
        self.canvas.bind("<Button-3>", self._on_right_click_event)
        self.canvas.bind("<ButtonPress-1>", self._on_drag_start_event)
        self.canvas.bind("<B1-Motion>", self._on_drag_motion)
        self.canvas.bind("<ButtonRelease-1>", self._on_drag_end_event)
    
    def _on_left_click(self, event):
        """Handle left click."""
        if self.on_click:
            self.on_click(self, event)
    
    def _on_right_click_event(self, event):
        """Handle right click."""
        if self.on_right_click:
            self.on_right_click(self, event)
    
    def _on_drag_start_event(self, event):
        """Handle drag start."""
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        
        if self.on_drag_start:
            self.on_drag_start(self, event)
    
    def _on_drag_motion(self, event):
        """Handle drag motion."""
        # Check if we've moved enough to start dragging
        dx = abs(event.x - self.drag_start_x)
        dy = abs(event.y - self.drag_start_y)
        
        if not self.is_dragging and (dx > 5 or dy > 5):
            self.is_dragging = True
            self.configure(relief=tk.SUNKEN)
    
    def _on_drag_end_event(self, event):
        """Handle drag end."""
        if self.is_dragging:
            self.is_dragging = False
            self.configure(relief=tk.RAISED)
            
            if self.on_drag_end:
                self.on_drag_end(self, event)
    
    def set_selected(self, selected: bool):
        """Set selection state."""
        self.is_selected = selected
        self._update_color_display()
    
    def update_color(self, color: ColorData):
        """Update the color."""
        self.color = color
        self._update_color_display()


class PaletteListWidget(tk.Frame):
    """Widget for displaying and managing saved palettes."""
    
    def __init__(self, parent, palette_service: PaletteService, 
                 on_palette_selected: Optional[Callable] = None, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.palette_service = palette_service
        self.on_palette_selected = on_palette_selected
        self.palettes: List[Palette] = []
        
        self._setup_ui()
        self._load_palettes()
    
    def _setup_ui(self):
        """Setup the UI."""
        # Title
        title_label = ttk.Label(self, text="Saved Palettes", font=("TkDefaultFont", 10, "bold"))
        title_label.pack(anchor="w", pady=(0, 5))
        
        # Palette list frame with scrollbar
        list_frame = ttk.Frame(self)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollable listbox
        self.palette_listbox = tk.Listbox(list_frame, height=8)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.palette_listbox.yview)
        self.palette_listbox.configure(yscrollcommand=scrollbar.set)
        
        self.palette_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind selection event
        self.palette_listbox.bind("<<ListboxSelect>>", self._on_palette_select)
        self.palette_listbox.bind("<Double-Button-1>", self._on_palette_double_click)
        
        # Buttons frame
        buttons_frame = ttk.Frame(self)
        buttons_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(buttons_frame, text="Load", command=self._load_selected_palette).pack(side=tk.LEFT, padx=(0, 2))
        ttk.Button(buttons_frame, text="Delete", command=self._delete_selected_palette).pack(side=tk.LEFT, padx=2)
        ttk.Button(buttons_frame, text="Refresh", command=self._load_palettes).pack(side=tk.LEFT, padx=2)
    
    def _load_palettes(self):
        """Load saved palettes from storage."""
        try:
            self.palettes = self.palette_service.get_saved_palettes()
            
            # Update listbox
            self.palette_listbox.delete(0, tk.END)
            for palette in self.palettes:
                display_text = f"{palette.name} ({len(palette.colors)} colors)"
                self.palette_listbox.insert(tk.END, display_text)
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load palettes: {str(e)}")
    
    def _on_palette_select(self, event):
        """Handle palette selection."""
        selection = self.palette_listbox.curselection()
        if selection and self.on_palette_selected:
            palette = self.palettes[selection[0]]
            self.on_palette_selected(palette)
    
    def _on_palette_double_click(self, event):
        """Handle double-click to load palette."""
        self._load_selected_palette()
    
    def _load_selected_palette(self):
        """Load the selected palette."""
        selection = self.palette_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a palette to load.")
            return
        
        palette = self.palettes[selection[0]]
        if self.on_palette_selected:
            self.on_palette_selected(palette)
    
    def _delete_selected_palette(self):
        """Delete the selected palette."""
        selection = self.palette_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a palette to delete.")
            return
        
        palette = self.palettes[selection[0]]
        
        # Confirm deletion
        if messagebox.askyesno("Confirm Delete", f"Delete palette '{palette.name}'?"):
            try:
                self.palette_service.delete_palette(palette.name)
                self._load_palettes()  # Refresh list
                messagebox.showinfo("Success", f"Palette '{palette.name}' deleted successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete palette: {str(e)}")
    
    def refresh(self):
        """Refresh the palette list."""
        self._load_palettes()


class PaletteManagementPanel(ttk.Frame):
    """
    Comprehensive palette management panel with creation, editing,
    drag-and-drop organization, and export functionality.
    """
    
    def __init__(self, parent, event_bus: EventBus, palette_service: Optional[PaletteService] = None, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.event_bus = event_bus
        self.palette_service = palette_service or PaletteService()
        
        self.current_palette: Optional[Palette] = None
        self.color_swatches: List[ColorSwatchWidget] = []
        self.selected_swatch: Optional[ColorSwatchWidget] = None
        self.drag_source: Optional[ColorSwatchWidget] = None
        
        self._setup_ui()
        self._setup_event_subscriptions()
    
    def _setup_ui(self):
        """Setup the user interface."""
        # Create main paned window
        self.paned_window = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel - Current palette
        self.left_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.left_frame, weight=2)
        
        # Right panel - Saved palettes
        self.right_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.right_frame, weight=1)
        
        self._setup_current_palette_panel()
        self._setup_saved_palettes_panel()
    
    def _setup_current_palette_panel(self):
        """Setup the current palette editing panel."""
        # Title and controls
        header_frame = ttk.Frame(self.left_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(header_frame, text="Current Palette", font=("TkDefaultFont", 12, "bold")).pack(side=tk.LEFT)
        
        # Palette name
        name_frame = ttk.Frame(self.left_frame)
        name_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(name_frame, text="Name:").pack(side=tk.LEFT)
        self.palette_name_var = tk.StringVar(value="New Palette")
        self.palette_name_entry = ttk.Entry(name_frame, textvariable=self.palette_name_var, width=20)
        self.palette_name_entry.pack(side=tk.LEFT, padx=(5, 0), fill=tk.X, expand=True)
        
        # Control buttons
        controls_frame = ttk.Frame(self.left_frame)
        controls_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(controls_frame, text="New", command=self._new_palette).pack(side=tk.LEFT, padx=(0, 2))
        ttk.Button(controls_frame, text="Save", command=self._save_palette).pack(side=tk.LEFT, padx=2)
        ttk.Button(controls_frame, text="Load", command=self._load_palette_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(controls_frame, text="Export", command=self._export_palette_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(controls_frame, text="Clear", command=self._clear_palette).pack(side=tk.LEFT, padx=2)
        
        # Color swatches area
        swatches_label = ttk.Label(self.left_frame, text="Colors (drag to reorder):", font=("TkDefaultFont", 10, "bold"))
        swatches_label.pack(anchor="w", pady=(0, 5))
        
        # Scrollable frame for swatches
        self._setup_swatches_area()
        
        # Add color controls
        add_frame = ttk.Frame(self.left_frame)
        add_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(add_frame, text="Add Current Color", command=self._add_current_color).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(add_frame, text="Add Custom Color", command=self._add_custom_color).pack(side=tk.LEFT, padx=5)
        ttk.Button(add_frame, text="Remove Selected", command=self._remove_selected_color).pack(side=tk.LEFT, padx=5)
        
        # Palette info
        self.info_label = ttk.Label(self.left_frame, text="0 colors", font=("TkDefaultFont", 8))
        self.info_label.pack(anchor="w", pady=(5, 0))
    
    def _setup_swatches_area(self):
        """Setup the scrollable swatches area."""
        # Create canvas and scrollbar for swatches
        canvas_frame = ttk.Frame(self.left_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.swatches_canvas = tk.Canvas(canvas_frame, height=200, bg="white")
        v_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.swatches_canvas.yview)
        h_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=self.swatches_canvas.xview)
        
        self.swatches_canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Create scrollable frame
        self.swatches_frame = ttk.Frame(self.swatches_canvas)
        self.swatches_canvas_window = self.swatches_canvas.create_window(0, 0, anchor="nw", window=self.swatches_frame)
        
        # Pack scrollbars and canvas
        self.swatches_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Bind canvas resize
        self.swatches_canvas.bind("<Configure>", self._on_canvas_configure)
        self.swatches_frame.bind("<Configure>", self._on_frame_configure)
        
        # Bind mouse wheel
        self.swatches_canvas.bind("<MouseWheel>", self._on_mousewheel)
    
    def _setup_saved_palettes_panel(self):
        """Setup the saved palettes panel."""
        self.palette_list = PaletteListWidget(self.right_frame, self.palette_service, 
                                            on_palette_selected=self._load_palette)
        self.palette_list.pack(fill=tk.BOTH, expand=True)
    
    def _setup_event_subscriptions(self):
        """Setup event bus subscriptions."""
        self.event_bus.subscribe("color_picked", self._on_color_picked)
        self.event_bus.subscribe("palette_saved", self._on_palette_saved)
    
    def _new_palette(self):
        """Create a new empty palette."""
        self.current_palette = Palette(
            name=self.palette_name_var.get(),
            colors=[],
            created_at=datetime.now(),
            modified_at=datetime.now(),
            tags=[]
        )
        self._update_swatches_display()
        self._update_info()
    
    def _save_palette(self):
        """Save the current palette."""
        if not self.current_palette:
            messagebox.showwarning("No Palette", "No palette to save. Create a new palette first.")
            return
        
        if not self.current_palette.colors:
            messagebox.showwarning("Empty Palette", "Cannot save an empty palette.")
            return
        
        # Update palette name
        self.current_palette.name = self.palette_name_var.get()
        self.current_palette.modified_at = datetime.now()
        
        try:
            self.palette_service.save_palette(self.current_palette)
            messagebox.showinfo("Success", f"Palette '{self.current_palette.name}' saved successfully.")
            
            # Refresh saved palettes list
            self.palette_list.refresh()
            
            # Publish event
            self.event_bus.publish("palette_saved", {
                "palette": self.current_palette
            }, source="palette_panel")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save palette: {str(e)}")
    
    def _load_palette_dialog(self):
        """Open file dialog to load palette."""
        file_path = filedialog.askopenfilename(
            title="Load Palette",
            filetypes=[
                ("JSON files", "*.json"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            try:
                palette = self.palette_service.load_palette(file_path)
                self._load_palette(palette)
                messagebox.showinfo("Success", f"Palette '{palette.name}' loaded successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load palette: {str(e)}")
    
    def _load_palette(self, palette: Palette):
        """Load a palette into the editor."""
        self.current_palette = palette
        self.palette_name_var.set(palette.name)
        self._update_swatches_display()
        self._update_info()
        
        # Publish event
        self.event_bus.publish("palette_loaded", {
            "palette": palette
        }, source="palette_panel")
    
    def _export_palette_dialog(self):
        """Open export dialog."""
        if not self.current_palette or not self.current_palette.colors:
            messagebox.showwarning("No Palette", "No palette to export.")
            return
        
        # Create export dialog
        export_dialog = tk.Toplevel(self)
        export_dialog.title("Export Palette")
        export_dialog.geometry("300x200")
        export_dialog.transient(self)
        export_dialog.grab_set()
        
        # Format selection
        ttk.Label(export_dialog, text="Export Format:").pack(pady=10)
        
        format_var = tk.StringVar(value="JSON")
        formats = ["JSON", "CSS", "SCSS", "ASE", "ACO", "GPL"]
        
        for fmt in formats:
            ttk.Radiobutton(export_dialog, text=fmt, variable=format_var, value=fmt).pack(anchor="w", padx=20)
        
        # Buttons
        button_frame = ttk.Frame(export_dialog)
        button_frame.pack(pady=20)
        
        def do_export():
            try:
                format_enum = ExportFormat(format_var.get().lower())
                
                # Get file extension
                ext_map = {
                    ExportFormat.JSON: ".json",
                    ExportFormat.CSS: ".css",
                    ExportFormat.SCSS: ".scss",
                    ExportFormat.ASE: ".ase",
                    ExportFormat.ACO: ".aco",
                    ExportFormat.GPL: ".gpl"
                }
                
                ext = ext_map.get(format_enum, ".json")
                
                # File dialog
                file_path = filedialog.asksaveasfilename(
                    title="Export Palette",
                    defaultextension=ext,
                    filetypes=[(f"{format_var.get()} files", f"*{ext}"), ("All files", "*.*")]
                )
                
                if file_path:
                    exported_data = self.palette_service.export_palette(self.current_palette, format_enum)
                    
                    with open(file_path, 'w') as f:
                        f.write(exported_data)
                    
                    messagebox.showinfo("Success", f"Palette exported to {file_path}")
                    export_dialog.destroy()
                    
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export palette: {str(e)}")
        
        ttk.Button(button_frame, text="Export", command=do_export).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=export_dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def _clear_palette(self):
        """Clear the current palette."""
        if self.current_palette and self.current_palette.colors:
            if messagebox.askyesno("Confirm Clear", "Clear all colors from the palette?"):
                self.current_palette.colors.clear()
                self._update_swatches_display()
                self._update_info()
    
    def _add_current_color(self):
        """Add the currently selected color to the palette."""
        # This would typically get the color from the color panel
        # For now, we'll publish an event requesting the current color
        self.event_bus.publish("request_current_color", {
            "requester": "palette_panel"
        }, source="palette_panel")
    
    def _add_custom_color(self):
        """Add a custom color via color picker dialog."""
        # Simple color input dialog
        color_hex = simpledialog.askstring("Custom Color", "Enter hex color (e.g., #FF0000):")
        
        if color_hex:
            try:
                color = ColorData.from_hex(color_hex)
                self._add_color_to_palette(color)
            except Exception as e:
                messagebox.showerror("Invalid Color", f"Invalid color format: {str(e)}")
    
    def _add_color_to_palette(self, color: ColorData):
        """Add a color to the current palette."""
        if not self.current_palette:
            self._new_palette()
        
        self.current_palette.colors.append(color)
        self.current_palette.modified_at = datetime.now()
        self._update_swatches_display()
        self._update_info()
    
    def _remove_selected_color(self):
        """Remove the selected color from the palette."""
        if not self.selected_swatch or not self.current_palette:
            messagebox.showwarning("No Selection", "Please select a color to remove.")
            return
        
        # Remove color
        index = self.selected_swatch.index
        if 0 <= index < len(self.current_palette.colors):
            self.current_palette.colors.pop(index)
            self.current_palette.modified_at = datetime.now()
            self.selected_swatch = None
            self._update_swatches_display()
            self._update_info()
    
    def _update_swatches_display(self):
        """Update the color swatches display."""
        # Clear existing swatches
        for swatch in self.color_swatches:
            swatch.destroy()
        self.color_swatches.clear()
        
        if not self.current_palette:
            return
        
        # Create new swatches
        cols = 8  # Number of columns
        for i, color in enumerate(self.current_palette.colors):
            row = i // cols
            col = i % cols
            
            swatch = ColorSwatchWidget(
                self.swatches_frame, color, i,
                on_click=self._on_swatch_click,
                on_right_click=self._on_swatch_right_click,
                on_drag_start=self._on_swatch_drag_start,
                on_drag_end=self._on_swatch_drag_end
            )
            swatch.grid(row=row, column=col, padx=2, pady=2)
            self.color_swatches.append(swatch)
        
        # Update scroll region
        self.swatches_frame.update_idletasks()
        self.swatches_canvas.configure(scrollregion=self.swatches_canvas.bbox("all"))
    
    def _update_info(self):
        """Update the palette information display."""
        if self.current_palette:
            count = len(self.current_palette.colors)
            self.info_label.configure(text=f"{count} colors")
        else:
            self.info_label.configure(text="No palette")
    
    def _on_swatch_click(self, swatch: ColorSwatchWidget, event):
        """Handle swatch click."""
        # Deselect previous
        if self.selected_swatch:
            self.selected_swatch.set_selected(False)
        
        # Select new
        self.selected_swatch = swatch
        swatch.set_selected(True)
        
        # Publish color selected event
        self.event_bus.publish("color_selected", {
            "color": swatch.color,
            "source": "palette"
        }, source="palette_panel")
    
    def _on_swatch_right_click(self, swatch: ColorSwatchWidget, event):
        """Handle swatch right-click."""
        # Create context menu
        context_menu = tk.Menu(self, tearoff=0)
        context_menu.add_command(label="Copy Color", command=lambda: self._copy_color(swatch.color))
        context_menu.add_command(label="Edit Color", command=lambda: self._edit_color(swatch))
        context_menu.add_separator()
        context_menu.add_command(label="Remove Color", command=lambda: self._remove_color(swatch))
        
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
    
    def _on_swatch_drag_start(self, swatch: ColorSwatchWidget, event):
        """Handle drag start."""
        self.drag_source = swatch
    
    def _on_swatch_drag_end(self, swatch: ColorSwatchWidget, event):
        """Handle drag end."""
        if self.drag_source and self.drag_source != swatch:
            # Reorder colors
            self._reorder_colors(self.drag_source.index, swatch.index)
        
        self.drag_source = None
    
    def _copy_color(self, color: ColorData):
        """Copy color to clipboard."""
        try:
            import pyperclip
            pyperclip.copy(color.hex)
            messagebox.showinfo("Copied", f"Color {color.hex} copied to clipboard!")
        except ImportError:
            messagebox.showerror("Error", "pyperclip not available for clipboard operations.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy color: {str(e)}")
    
    def _edit_color(self, swatch: ColorSwatchWidget):
        """Edit color in swatch."""
        current_hex = swatch.color.hex
        new_hex = simpledialog.askstring("Edit Color", f"Edit color (current: {current_hex}):", 
                                        initialvalue=current_hex)
        
        if new_hex and new_hex != current_hex:
            try:
                new_color = ColorData.from_hex(new_hex)
                swatch.update_color(new_color)
                
                # Update palette
                if self.current_palette and 0 <= swatch.index < len(self.current_palette.colors):
                    self.current_palette.colors[swatch.index] = new_color
                    self.current_palette.modified_at = datetime.now()
                    
            except Exception as e:
                messagebox.showerror("Invalid Color", f"Invalid color format: {str(e)}")
    
    def _remove_color(self, swatch: ColorSwatchWidget):
        """Remove color from palette."""
        if self.current_palette and 0 <= swatch.index < len(self.current_palette.colors):
            self.current_palette.colors.pop(swatch.index)
            self.current_palette.modified_at = datetime.now()
            self._update_swatches_display()
            self._update_info()
    
    def _reorder_colors(self, from_index: int, to_index: int):
        """Reorder colors in the palette."""
        if not self.current_palette or from_index == to_index:
            return
        
        colors = self.current_palette.colors
        if 0 <= from_index < len(colors) and 0 <= to_index < len(colors):
            # Move color
            color = colors.pop(from_index)
            colors.insert(to_index, color)
            
            self.current_palette.modified_at = datetime.now()
            self._update_swatches_display()
    
    # Canvas event handlers
    def _on_canvas_configure(self, event):
        """Handle canvas resize."""
        self.swatches_canvas.configure(scrollregion=self.swatches_canvas.bbox("all"))
    
    def _on_frame_configure(self, event):
        """Handle frame resize."""
        self.swatches_canvas.configure(scrollregion=self.swatches_canvas.bbox("all"))
    
    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling."""
        self.swatches_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    # Event bus handlers
    def _on_color_picked(self, event_data: EventData):
        """Handle color picked event."""
        data = event_data.data
        if "color" in data:
            # Auto-add picked colors if enabled
            # For now, we'll just store the last picked color
            self.last_picked_color = data["color"]
    
    def _on_palette_saved(self, event_data: EventData):
        """Handle palette saved event."""
        # Refresh the saved palettes list
        self.palette_list.refresh()
    
    def get_current_palette(self) -> Optional[Palette]:
        """Get the current palette."""
        return self.current_palette
    
    def add_color(self, color: ColorData):
        """Add a color to the current palette (public method)."""
        self._add_color_to_palette(color)