"""
Batch Operations Panel for bulk color and palette operations.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import List, Dict, Any, Optional, Callable
import threading
from pathlib import Path

from ...models.color_data import ColorData
from ...models.palette import Palette
from ...models.enums import ColorFormat, ExportFormat
from ...services.batch_service import BatchService, BatchOperation
from ...services.export_service import ExportService


class BatchOperationsPanel(ttk.Frame):
    """
    Panel for performing batch operations on colors and palettes.
    
    Provides UI for bulk copying, format conversion, export operations,
    and palette management tasks.
    """
    
    def __init__(self, parent, event_bus=None, **kwargs):
        """Initialize the batch operations panel."""
        super().__init__(parent, **kwargs)
        
        self.event_bus = event_bus
        self.batch_service = BatchService(ExportService())
        self.current_colors: List[ColorData] = []
        self.current_palettes: List[Palette] = []
        self.active_operations: Dict[str, BatchOperation] = {}
        
        self._setup_ui()
        self._setup_event_handlers()
    
    def _setup_ui(self):
        """Setup the user interface."""
        # Main notebook for different batch operation types
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Color operations tab
        self.color_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.color_frame, text="Color Operations")
        self._setup_color_operations()
        
        # Palette operations tab
        self.palette_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.palette_frame, text="Palette Operations")
        self._setup_palette_operations()
        
        # Export operations tab
        self.export_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.export_frame, text="Export Operations")
        self._setup_export_operations()
        
        # Progress tracking frame
        self.progress_frame = ttk.LabelFrame(self, text="Operation Progress")
        self.progress_frame.pack(fill=tk.X, padx=5, pady=5)
        self._setup_progress_tracking()
    
    def _setup_color_operations(self):
        """Setup color operations UI."""
        # Bulk copy section
        copy_frame = ttk.LabelFrame(self.color_frame, text="Bulk Copy Colors")
        copy_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Format selection for copying
        ttk.Label(copy_frame, text="Copy Formats:").pack(anchor=tk.W, padx=5, pady=2)
        
        self.copy_formats_frame = ttk.Frame(copy_frame)
        self.copy_formats_frame.pack(fill=tk.X, padx=5, pady=2)
        
        self.copy_format_vars = {}
        for format_type in ColorFormat:
            var = tk.BooleanVar(value=True if format_type == ColorFormat.HEX else False)
            self.copy_format_vars[format_type] = var
            ttk.Checkbutton(
                self.copy_formats_frame,
                text=format_type.value.upper(),
                variable=var
            ).pack(side=tk.LEFT, padx=5)
        
        # Copy button
        self.copy_button = ttk.Button(
            copy_frame,
            text="Copy Selected Colors",
            command=self._bulk_copy_colors
        )
        self.copy_button.pack(pady=5)
        
        # Format conversion section
        convert_frame = ttk.LabelFrame(self.color_frame, text="Bulk Format Conversion")
        convert_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(convert_frame, text="Target Format:").pack(anchor=tk.W, padx=5, pady=2)
        
        self.target_format_var = tk.StringVar(value=ColorFormat.HEX.value)
        format_combo = ttk.Combobox(
            convert_frame,
            textvariable=self.target_format_var,
            values=[f.value for f in ColorFormat],
            state="readonly"
        )
        format_combo.pack(fill=tk.X, padx=5, pady=2)
        
        self.convert_button = ttk.Button(
            convert_frame,
            text="Convert and Copy",
            command=self._bulk_convert_colors
        )
        self.convert_button.pack(pady=5)
    
    def _setup_palette_operations(self):
        """Setup palette operations UI."""
        # Palette management section
        mgmt_frame = ttk.LabelFrame(self.palette_frame, text="Palette Management")
        mgmt_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Operation selection
        ttk.Label(mgmt_frame, text="Operations:").pack(anchor=tk.W, padx=5, pady=2)
        
        self.palette_ops_frame = ttk.Frame(mgmt_frame)
        self.palette_ops_frame.pack(fill=tk.X, padx=5, pady=2)
        
        self.palette_op_vars = {}
        operations = ["deduplicate", "sort", "reverse", "shuffle", "limit"]
        for op in operations:
            var = tk.BooleanVar()
            self.palette_op_vars[op] = var
            ttk.Checkbutton(
                self.palette_ops_frame,
                text=op.title(),
                variable=var
            ).pack(anchor=tk.W, padx=5)
        
        # Sort options
        sort_frame = ttk.Frame(mgmt_frame)
        sort_frame.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Label(sort_frame, text="Sort by:").pack(side=tk.LEFT, padx=5)
        self.sort_by_var = tk.StringVar(value="hue")
        sort_combo = ttk.Combobox(
            sort_frame,
            textvariable=self.sort_by_var,
            values=["hue", "saturation", "lightness", "brightness", "red", "green", "blue", "luminance"],
            state="readonly",
            width=12
        )
        sort_combo.pack(side=tk.LEFT, padx=5)
        
        self.sort_reverse_var = tk.BooleanVar()
        ttk.Checkbutton(
            sort_frame,
            text="Reverse",
            variable=self.sort_reverse_var
        ).pack(side=tk.LEFT, padx=5)
        
        # Limit options
        limit_frame = ttk.Frame(mgmt_frame)
        limit_frame.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Label(limit_frame, text="Limit to:").pack(side=tk.LEFT, padx=5)
        self.limit_var = tk.StringVar(value="10")
        limit_spin = ttk.Spinbox(
            limit_frame,
            from_=1,
            to=100,
            textvariable=self.limit_var,
            width=10
        )
        limit_spin.pack(side=tk.LEFT, padx=5)
        ttk.Label(limit_frame, text="colors").pack(side=tk.LEFT, padx=2)
        
        # Apply operations button
        self.apply_ops_button = ttk.Button(
            mgmt_frame,
            text="Apply Operations",
            command=self._apply_palette_operations
        )
        self.apply_ops_button.pack(pady=5)
    
    def _setup_export_operations(self):
        """Setup export operations UI."""
        # Bulk palette export
        palette_export_frame = ttk.LabelFrame(self.export_frame, text="Bulk Palette Export")
        palette_export_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Export format selection
        ttk.Label(palette_export_frame, text="Export Format:").pack(anchor=tk.W, padx=5, pady=2)
        
        self.export_format_var = tk.StringVar(value=ExportFormat.JSON.value)
        export_combo = ttk.Combobox(
            palette_export_frame,
            textvariable=self.export_format_var,
            values=[f.value for f in ExportFormat],
            state="readonly"
        )
        export_combo.pack(fill=tk.X, padx=5, pady=2)
        
        # Output directory selection
        dir_frame = ttk.Frame(palette_export_frame)
        dir_frame.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Label(dir_frame, text="Output Directory:").pack(anchor=tk.W)
        
        dir_select_frame = ttk.Frame(dir_frame)
        dir_select_frame.pack(fill=tk.X, pady=2)
        
        self.output_dir_var = tk.StringVar(value=str(Path.home() / "Downloads"))\n        self.output_dir_entry = ttk.Entry(
            dir_select_frame,
            textvariable=self.output_dir_var
        )
        self.output_dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        ttk.Button(
            dir_select_frame,
            text="Browse",
            command=self._browse_output_directory
        ).pack(side=tk.RIGHT)
        
        # Export button
        self.export_palettes_button = ttk.Button(
            palette_export_frame,
            text="Export Palettes",
            command=self._bulk_export_palettes
        )
        self.export_palettes_button.pack(pady=5)
        
        # Color export section
        color_export_frame = ttk.LabelFrame(self.export_frame, text="Bulk Color Export")
        color_export_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Multiple format selection
        ttk.Label(color_export_frame, text="Export Formats:").pack(anchor=tk.W, padx=5, pady=2)
        
        self.export_formats_frame = ttk.Frame(color_export_frame)
        self.export_formats_frame.pack(fill=tk.X, padx=5, pady=2)
        
        self.export_format_vars = {}
        common_formats = [ExportFormat.JSON, ExportFormat.CSS, ExportFormat.SCSS, 
                         ExportFormat.PYTHON, ExportFormat.JAVASCRIPT]
        for format_type in common_formats:
            var = tk.BooleanVar()
            self.export_format_vars[format_type] = var
            ttk.Checkbutton(
                self.export_formats_frame,
                text=format_type.value.upper(),
                variable=var
            ).pack(anchor=tk.W, padx=5)
        
        # Base name for color exports
        name_frame = ttk.Frame(color_export_frame)
        name_frame.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Label(name_frame, text="Base Name:").pack(side=tk.LEFT, padx=5)
        self.color_export_name_var = tk.StringVar(value="colors")
        ttk.Entry(
            name_frame,
            textvariable=self.color_export_name_var,
            width=20
        ).pack(side=tk.LEFT, padx=5)
        
        # Export colors button
        self.export_colors_button = ttk.Button(
            color_export_frame,
            text="Export Colors",
            command=self._bulk_export_colors
        )
        self.export_colors_button.pack(pady=5)
    
    def _setup_progress_tracking(self):
        """Setup progress tracking UI."""
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            self.progress_frame,
            variable=self.progress_var,
            maximum=100
        )
        self.progress_bar.pack(fill=tk.X, padx=5, pady=2)
        
        # Status label
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(
            self.progress_frame,
            textvariable=self.status_var
        )
        self.status_label.pack(anchor=tk.W, padx=5, pady=2)
        
        # Operation list
        list_frame = ttk.Frame(self.progress_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=2)
        
        # Operations listbox with scrollbar
        list_scroll_frame = ttk.Frame(list_frame)
        list_scroll_frame.pack(fill=tk.BOTH, expand=True)
        
        self.operations_listbox = tk.Listbox(list_scroll_frame, height=4)
        scrollbar = ttk.Scrollbar(list_scroll_frame, orient=tk.VERTICAL, command=self.operations_listbox.yview)
        self.operations_listbox.configure(yscrollcommand=scrollbar.set)
        
        self.operations_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Control buttons
        button_frame = ttk.Frame(list_frame)
        button_frame.pack(fill=tk.X, pady=2)
        
        ttk.Button(
            button_frame,
            text="Cancel Selected",
            command=self._cancel_selected_operation
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            button_frame,
            text="Clear Completed",
            command=self._clear_completed_operations
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            button_frame,
            text="Refresh",
            command=self._refresh_operations_list
        ).pack(side=tk.RIGHT, padx=2)
    
    def _setup_event_handlers(self):
        """Setup event handlers."""
        if self.event_bus:
            self.event_bus.subscribe("colors_selected", self._on_colors_selected)
            self.event_bus.subscribe("palettes_selected", self._on_palettes_selected)
        
        # Start progress update timer
        self._update_progress()
    
    def _on_colors_selected(self, colors: List[ColorData]):
        """Handle colors selection event."""
        self.current_colors = colors
        self._update_ui_state()
    
    def _on_palettes_selected(self, palettes: List[Palette]):
        """Handle palettes selection event."""
        self.current_palettes = palettes
        self._update_ui_state()
    
    def _update_ui_state(self):
        """Update UI state based on current selections."""
        has_colors = len(self.current_colors) > 0
        has_palettes = len(self.current_palettes) > 0
        
        # Enable/disable color operation buttons
        self.copy_button.configure(state=tk.NORMAL if has_colors else tk.DISABLED)
        self.convert_button.configure(state=tk.NORMAL if has_colors else tk.DISABLED)
        self.export_colors_button.configure(state=tk.NORMAL if has_colors else tk.DISABLED)
        
        # Enable/disable palette operation buttons
        self.apply_ops_button.configure(state=tk.NORMAL if has_palettes else tk.DISABLED)
        self.export_palettes_button.configure(state=tk.NORMAL if has_palettes else tk.DISABLED)
        
        # Update status
        if has_colors and has_palettes:
            self.status_var.set(f"Ready - {len(self.current_colors)} colors, {len(self.current_palettes)} palettes selected")
        elif has_colors:
            self.status_var.set(f"Ready - {len(self.current_colors)} colors selected")
        elif has_palettes:
            self.status_var.set(f"Ready - {len(self.current_palettes)} palettes selected")
        else:
            self.status_var.set("Ready - No items selected")
    
    def _bulk_copy_colors(self):
        """Perform bulk color copying."""
        if not self.current_colors:
            messagebox.showwarning("No Colors", "Please select colors to copy.")
            return
        
        # Get selected formats
        selected_formats = [
            format_type for format_type, var in self.copy_format_vars.items()
            if var.get()
        ]
        
        if not selected_formats:
            messagebox.showwarning("No Formats", "Please select at least one format to copy.")
            return
        
        # Start bulk copy operation
        operation_id = self.batch_service.bulk_copy_colors(
            self.current_colors,
            selected_formats,
            progress_callback=self._on_progress_update
        )
        
        self.status_var.set(f"Copying {len(self.current_colors)} colors in {len(selected_formats)} formats...")
    
    def _bulk_convert_colors(self):
        """Perform bulk color format conversion."""
        if not self.current_colors:
            messagebox.showwarning("No Colors", "Please select colors to convert.")
            return
        
        target_format = ColorFormat(self.target_format_var.get())
        
        # Start bulk conversion operation
        operation_id = self.batch_service.bulk_convert_colors(
            self.current_colors,
            target_format,
            progress_callback=self._on_progress_update
        )
        
        self.status_var.set(f"Converting {len(self.current_colors)} colors to {target_format.value}...")
    
    def _apply_palette_operations(self):
        """Apply selected operations to palettes."""
        if not self.current_palettes:
            messagebox.showwarning("No Palettes", "Please select palettes to modify.")
            return
        
        # Get selected operations
        selected_ops = [
            op for op, var in self.palette_op_vars.items()
            if var.get()
        ]
        
        if not selected_ops:
            messagebox.showwarning("No Operations", "Please select at least one operation to perform.")
            return
        
        # Prepare operation kwargs
        kwargs = {
            'sort_by': self.sort_by_var.get(),
            'reverse': self.sort_reverse_var.get(),
            'max_colors': int(self.limit_var.get())
        }
        
        # Start batch palette operations
        operation_id = self.batch_service.batch_palette_operations(
            self.current_palettes,
            selected_ops,
            progress_callback=self._on_progress_update,
            **kwargs
        )
        
        self.status_var.set(f"Applying {len(selected_ops)} operations to {len(self.current_palettes)} palettes...")
    
    def _bulk_export_palettes(self):
        """Perform bulk palette export."""
        if not self.current_palettes:
            messagebox.showwarning("No Palettes", "Please select palettes to export.")
            return
        
        export_format = ExportFormat(self.export_format_var.get())
        output_dir = self.output_dir_var.get()
        
        if not output_dir or not Path(output_dir).exists():
            messagebox.showerror("Invalid Directory", "Please select a valid output directory.")
            return
        
        # Start bulk export operation
        operation_id = self.batch_service.bulk_export_palettes(
            self.current_palettes,
            export_format,
            output_dir,
            progress_callback=self._on_progress_update
        )
        
        self.status_var.set(f"Exporting {len(self.current_palettes)} palettes as {export_format.value}...")
    
    def _bulk_export_colors(self):
        """Perform bulk color export."""
        if not self.current_colors:
            messagebox.showwarning("No Colors", "Please select colors to export.")
            return
        
        # Get selected export formats
        selected_formats = [
            format_type for format_type, var in self.export_format_vars.items()
            if var.get()
        ]
        
        if not selected_formats:
            messagebox.showwarning("No Formats", "Please select at least one export format.")
            return
        
        output_dir = self.output_dir_var.get()
        base_name = self.color_export_name_var.get() or "colors"
        
        if not output_dir or not Path(output_dir).exists():
            messagebox.showerror("Invalid Directory", "Please select a valid output directory.")
            return
        
        # Start bulk color export operation
        operation_id = self.batch_service.bulk_export_colors(
            self.current_colors,
            selected_formats,
            output_dir,
            base_name,
            progress_callback=self._on_progress_update
        )
        
        self.status_var.set(f"Exporting {len(self.current_colors)} colors in {len(selected_formats)} formats...")
    
    def _browse_output_directory(self):
        """Browse for output directory."""
        directory = filedialog.askdirectory(
            title="Select Output Directory",
            initialdir=self.output_dir_var.get()
        )
        if directory:
            self.output_dir_var.set(directory)
    
    def _on_progress_update(self, operation: BatchOperation):
        """Handle progress update from batch operations."""
        self.active_operations[operation.operation_id] = operation
        
        # Update progress bar with the most recent operation
        self.progress_var.set(operation.progress_percentage)
        
        # Update operations list
        self._refresh_operations_list()
    
    def _update_progress(self):
        """Update progress display periodically."""
        # Get all operations from batch service
        all_operations = self.batch_service.get_all_operations()
        self.active_operations.update(all_operations)
        
        # Update UI
        self._refresh_operations_list()
        
        # Schedule next update
        self.after(1000, self._update_progress)
    
    def _refresh_operations_list(self):
        """Refresh the operations list display."""
        self.operations_listbox.delete(0, tk.END)
        
        for op_id, operation in self.active_operations.items():
            status_text = f"{op_id}: {operation.status} ({operation.progress_percentage:.1f}%)"
            if operation.failed_items > 0:
                status_text += f" - {operation.failed_items} failed"
            
            self.operations_listbox.insert(tk.END, status_text)
    
    def _cancel_selected_operation(self):
        """Cancel the selected operation."""
        selection = self.operations_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an operation to cancel.")
            return
        
        # Get operation ID from selection
        selected_text = self.operations_listbox.get(selection[0])
        op_id = selected_text.split(":")[0]
        
        if self.batch_service.cancel_operation(op_id):
            messagebox.showinfo("Operation Cancelled", f"Operation '{op_id}' has been cancelled.")
        else:
            messagebox.showwarning("Cannot Cancel", f"Operation '{op_id}' cannot be cancelled.")
    
    def _clear_completed_operations(self):
        """Clear completed operations from the list."""
        self.batch_service.clear_completed_operations()
        self.active_operations = {
            op_id: op for op_id, op in self.active_operations.items()
            if not op.is_complete
        }
        self._refresh_operations_list()
    
    def set_colors(self, colors: List[ColorData]):
        """Set the current colors for batch operations."""
        self.current_colors = colors
        self._update_ui_state()
    
    def set_palettes(self, palettes: List[Palette]):
        """Set the current palettes for batch operations."""
        self.current_palettes = palettes
        self._update_ui_state()
    
    def cleanup(self):
        """Cleanup resources when panel is destroyed."""
        if self.batch_service:
            self.batch_service.shutdown()