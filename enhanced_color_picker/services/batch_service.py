"""
Batch operations service for bulk color and palette operations.
Handles bulk copying, format conversion, and export operations.
"""

import json
from typing import List, Dict, Any, Optional, Union, Callable
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from dataclasses import dataclass

from ..models.color_data import ColorData
from ..models.palette import Palette
from ..models.enums import ColorFormat, ExportFormat
from .export_service import ExportService


@dataclass
class BatchOperation:
    """Represents a batch operation with progress tracking."""
    operation_id: str
    total_items: int
    completed_items: int = 0
    failed_items: int = 0
    status: str = "pending"  # pending, running, completed, failed, cancelled
    error_messages: List[str] = None
    
    def __post_init__(self):
        if self.error_messages is None:
            self.error_messages = []
    
    @property
    def progress_percentage(self) -> float:
        """Get progress as percentage."""
        if self.total_items == 0:
            return 100.0
        return (self.completed_items / self.total_items) * 100.0
    
    @property
    def is_complete(self) -> bool:
        """Check if operation is complete."""
        return self.status in ["completed", "failed", "cancelled"]


class BatchService:
    """
    Service for performing batch operations on colors and palettes.
    
    Supports bulk copying, format conversion, export operations, and palette management.
    """
    
    def __init__(self, export_service: Optional[ExportService] = None):
        """Initialize the batch service."""
        self.export_service = export_service or ExportService()
        self._operations: Dict[str, BatchOperation] = {}
        self._operation_lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=4)
        self._cancelled_operations = set()
    
    def bulk_copy_colors(self, colors: List[ColorData], formats: List[ColorFormat],
                        operation_id: str = None, progress_callback: Callable = None) -> str:
        """
        Copy multiple colors in multiple formats to clipboard.
        
        Args:
            colors: List of colors to copy
            formats: List of formats to copy each color in
            operation_id: Optional operation ID for tracking
            progress_callback: Optional callback for progress updates
            
        Returns:
            Operation ID for tracking progress
        """
        if not operation_id:
            operation_id = f"bulk_copy_{len(colors)}_{len(formats)}"
        
        total_operations = len(colors) * len(formats)
        operation = BatchOperation(operation_id, total_operations)
        
        with self._operation_lock:
            self._operations[operation_id] = operation
        
        def _copy_task():
            try:
                operation.status = "running"
                clipboard_content = []
                
                for color in colors:
                    if operation_id in self._cancelled_operations:
                        operation.status = "cancelled"
                        return
                    
                    color_formats = []
                    for format_type in formats:
                        try:
                            formatted_color = self._format_color_for_clipboard(color, format_type)
                            color_formats.append(formatted_color)
                            operation.completed_items += 1
                            
                            if progress_callback:
                                progress_callback(operation)
                                
                        except Exception as e:
                            operation.failed_items += 1
                            operation.error_messages.append(f"Failed to format color {color.hex} as {format_type}: {str(e)}")
                    
                    if color_formats:
                        clipboard_content.append(" | ".join(color_formats))
                
                # Copy to clipboard (this would need platform-specific implementation)
                final_content = "\n".join(clipboard_content)
                self._copy_to_clipboard(final_content)
                
                operation.status = "completed"
                
            except Exception as e:
                operation.status = "failed"
                operation.error_messages.append(f"Bulk copy operation failed: {str(e)}")
        
        self._executor.submit(_copy_task)
        return operation_id
    
    def bulk_convert_colors(self, colors: List[ColorData], target_format: ColorFormat,
                           operation_id: str = None, progress_callback: Callable = None) -> str:
        """
        Convert multiple colors to a target format.
        
        Args:
            colors: List of colors to convert
            target_format: Target format for conversion
            operation_id: Optional operation ID for tracking
            progress_callback: Optional callback for progress updates
            
        Returns:
            Operation ID for tracking progress
        """
        if not operation_id:
            operation_id = f"bulk_convert_{len(colors)}_{target_format.value}"
        
        operation = BatchOperation(operation_id, len(colors))
        
        with self._operation_lock:
            self._operations[operation_id] = operation
        
        def _convert_task():
            try:
                operation.status = "running"
                converted_colors = []
                
                for color in colors:
                    if operation_id in self._cancelled_operations:
                        operation.status = "cancelled"
                        return
                    
                    try:
                        formatted_color = self._format_color_for_clipboard(color, target_format)
                        converted_colors.append(formatted_color)
                        operation.completed_items += 1
                        
                        if progress_callback:
                            progress_callback(operation)
                            
                    except Exception as e:
                        operation.failed_items += 1
                        operation.error_messages.append(f"Failed to convert color {color.hex}: {str(e)}")
                
                # Copy converted colors to clipboard
                final_content = "\n".join(converted_colors)
                self._copy_to_clipboard(final_content)
                
                operation.status = "completed"
                
            except Exception as e:
                operation.status = "failed"
                operation.error_messages.append(f"Bulk conversion operation failed: {str(e)}")
        
        self._executor.submit(_convert_task)
        return operation_id
    
    def bulk_export_palettes(self, palettes: List[Palette], export_format: ExportFormat,
                           output_directory: str, operation_id: str = None,
                           progress_callback: Callable = None, **export_kwargs) -> str:
        """
        Export multiple palettes to files.
        
        Args:
            palettes: List of palettes to export
            export_format: Export format
            output_directory: Directory to save exported files
            operation_id: Optional operation ID for tracking
            progress_callback: Optional callback for progress updates
            **export_kwargs: Additional export options
            
        Returns:
            Operation ID for tracking progress
        """
        if not operation_id:
            operation_id = f"bulk_export_{len(palettes)}_{export_format.value}"
        
        operation = BatchOperation(operation_id, len(palettes))
        
        with self._operation_lock:
            self._operations[operation_id] = operation
        
        def _export_task():
            try:
                operation.status = "running"
                output_path = Path(output_directory)
                output_path.mkdir(parents=True, exist_ok=True)
                
                for palette in palettes:
                    if operation_id in self._cancelled_operations:
                        operation.status = "cancelled"
                        return
                    
                    try:
                        # Generate filename
                        safe_name = self._sanitize_filename(palette.name)
                        extension = self.export_service.get_format_extension(export_format)
                        file_path = output_path / f"{safe_name}{extension}"
                        
                        # Export palette
                        self.export_service.export_palette(
                            palette, export_format, str(file_path), **export_kwargs
                        )
                        
                        operation.completed_items += 1
                        
                        if progress_callback:
                            progress_callback(operation)
                            
                    except Exception as e:
                        operation.failed_items += 1
                        operation.error_messages.append(f"Failed to export palette '{palette.name}': {str(e)}")
                
                operation.status = "completed"
                
            except Exception as e:
                operation.status = "failed"
                operation.error_messages.append(f"Bulk export operation failed: {str(e)}")
        
        self._executor.submit(_export_task)
        return operation_id
    
    def bulk_export_colors(self, colors: List[ColorData], export_formats: List[ExportFormat],
                          output_directory: str, base_name: str = "colors",
                          operation_id: str = None, progress_callback: Callable = None,
                          **export_kwargs) -> str:
        """
        Export colors in multiple formats.
        
        Args:
            colors: List of colors to export
            export_formats: List of export formats
            output_directory: Directory to save exported files
            base_name: Base name for exported files
            operation_id: Optional operation ID for tracking
            progress_callback: Optional callback for progress updates
            **export_kwargs: Additional export options
            
        Returns:
            Operation ID for tracking progress
        """
        if not operation_id:
            operation_id = f"bulk_export_colors_{len(colors)}_{len(export_formats)}"
        
        total_operations = len(export_formats)
        operation = BatchOperation(operation_id, total_operations)
        
        with self._operation_lock:
            self._operations[operation_id] = operation
        
        def _export_task():
            try:
                operation.status = "running"
                output_path = Path(output_directory)
                output_path.mkdir(parents=True, exist_ok=True)
                
                for export_format in export_formats:
                    if operation_id in self._cancelled_operations:
                        operation.status = "cancelled"
                        return
                    
                    try:
                        # Generate filename
                        extension = self.export_service.get_format_extension(export_format)
                        file_path = output_path / f"{base_name}{extension}"
                        
                        # Export colors
                        self.export_service.export_colors(
                            colors, export_format, base_name, **export_kwargs
                        )
                        
                        operation.completed_items += 1
                        
                        if progress_callback:
                            progress_callback(operation)
                            
                    except Exception as e:
                        operation.failed_items += 1
                        operation.error_messages.append(f"Failed to export colors as {export_format.value}: {str(e)}")
                
                operation.status = "completed"
                
            except Exception as e:
                operation.status = "failed"
                operation.error_messages.append(f"Bulk color export operation failed: {str(e)}")
        
        self._executor.submit(_export_task)
        return operation_id
    
    def batch_palette_operations(self, palettes: List[Palette], operations: List[str],
                                operation_id: str = None, progress_callback: Callable = None,
                                **operation_kwargs) -> str:
        """
        Perform batch operations on multiple palettes.
        
        Args:
            palettes: List of palettes to operate on
            operations: List of operations to perform ('deduplicate', 'sort', 'reverse', etc.)
            operation_id: Optional operation ID for tracking
            progress_callback: Optional callback for progress updates
            **operation_kwargs: Additional operation options
            
        Returns:
            Operation ID for tracking progress
        """
        if not operation_id:
            operation_id = f"batch_palette_ops_{len(palettes)}_{len(operations)}"
        
        total_operations = len(palettes) * len(operations)
        operation = BatchOperation(operation_id, total_operations)
        
        with self._operation_lock:
            self._operations[operation_id] = operation
        
        def _batch_task():
            try:
                operation.status = "running"
                
                for palette in palettes:
                    if operation_id in self._cancelled_operations:
                        operation.status = "cancelled"
                        return
                    
                    for op in operations:
                        try:
                            self._perform_palette_operation(palette, op, **operation_kwargs)
                            operation.completed_items += 1
                            
                            if progress_callback:
                                progress_callback(operation)
                                
                        except Exception as e:
                            operation.failed_items += 1
                            operation.error_messages.append(f"Failed to perform '{op}' on palette '{palette.name}': {str(e)}")
                
                operation.status = "completed"
                
            except Exception as e:
                operation.status = "failed"
                operation.error_messages.append(f"Batch palette operations failed: {str(e)}")
        
        self._executor.submit(_batch_task)
        return operation_id
    
    def get_operation_status(self, operation_id: str) -> Optional[BatchOperation]:
        """Get the status of a batch operation."""
        with self._operation_lock:
            return self._operations.get(operation_id)
    
    def cancel_operation(self, operation_id: str) -> bool:
        """Cancel a running batch operation."""
        with self._operation_lock:
            if operation_id in self._operations:
                self._cancelled_operations.add(operation_id)
                operation = self._operations[operation_id]
                if operation.status == "running":
                    operation.status = "cancelled"
                return True
        return False
    
    def clear_completed_operations(self):
        """Clear completed operations from memory."""
        with self._operation_lock:
            completed_ops = [
                op_id for op_id, op in self._operations.items()
                if op.is_complete
            ]
            for op_id in completed_ops:
                del self._operations[op_id]
                self._cancelled_operations.discard(op_id)
    
    def get_all_operations(self) -> Dict[str, BatchOperation]:
        """Get all batch operations."""
        with self._operation_lock:
            return self._operations.copy()
    
    def shutdown(self):
        """Shutdown the batch service and cleanup resources."""
        # Cancel all running operations
        with self._operation_lock:
            for op_id in list(self._operations.keys()):
                self.cancel_operation(op_id)
        
        # Shutdown executor
        self._executor.shutdown(wait=True)
    
    # Helper methods
    
    def _format_color_for_clipboard(self, color: ColorData, format_type: ColorFormat) -> str:
        """Format a color for clipboard copying."""
        if format_type == ColorFormat.RGB:
            if color.alpha < 1.0:
                return f"rgba({color.r}, {color.g}, {color.b}, {color.alpha})"
            else:
                return f"rgb({color.r}, {color.g}, {color.b})"
        elif format_type == ColorFormat.HEX:
            if color.alpha < 1.0:
                return color.hex_with_alpha
            else:
                return color.hex
        elif format_type == ColorFormat.HSL:
            h, s, l = color.hsl
            if color.alpha < 1.0:
                return f"hsla({h}, {s}%, {l}%, {color.alpha})"
            else:
                return f"hsl({h}, {s}%, {l}%)"
        elif format_type == ColorFormat.HSV:
            h, s, v = color.hsv
            return f"hsv({h}, {s}%, {v}%)"
        elif format_type == ColorFormat.CMYK:
            c, m, y, k = color.cmyk
            return f"cmyk({c}%, {m}%, {y}%, {k}%)"
        else:
            return color.hex
    
    def _copy_to_clipboard(self, content: str):
        """Copy content to clipboard. Platform-specific implementation needed."""
        try:
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()  # Hide the window
            root.clipboard_clear()
            root.clipboard_append(content)
            root.update()  # Required to make the clipboard content available
            root.destroy()
        except ImportError:
            # Fallback: print to console or use other clipboard library
            print(f"Clipboard content:\n{content}")
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe file system usage."""
        import re
        # Remove or replace invalid characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Remove leading/trailing spaces and dots
        sanitized = sanitized.strip(' .')
        # Limit length
        if len(sanitized) > 200:
            sanitized = sanitized[:200]
        return sanitized or "unnamed"
    
    def _perform_palette_operation(self, palette: Palette, operation: str, **kwargs):
        """Perform a specific operation on a palette."""
        if operation == "deduplicate":
            palette.remove_duplicates()
        elif operation == "sort":
            sort_by = kwargs.get('sort_by', 'hue')
            reverse = kwargs.get('reverse', False)
            self._sort_palette_colors(palette, sort_by, reverse)
        elif operation == "reverse":
            palette.colors.reverse()
            palette.modified_at = palette.modified_at.__class__.now()
        elif operation == "shuffle":
            import random
            random.shuffle(palette.colors)
            palette.modified_at = palette.modified_at.__class__.now()
        elif operation == "limit":
            max_colors = kwargs.get('max_colors', 10)
            if len(palette.colors) > max_colors:
                palette.colors = palette.colors[:max_colors]
                palette.modified_at = palette.modified_at.__class__.now()
        else:
            raise ValueError(f"Unknown palette operation: {operation}")
    
    def _sort_palette_colors(self, palette: Palette, sort_by: str, reverse: bool = False):
        """Sort palette colors by specified criteria."""
        if sort_by == "hue":
            palette.colors.sort(key=lambda c: c.hsl[0], reverse=reverse)
        elif sort_by == "saturation":
            palette.colors.sort(key=lambda c: c.hsl[1], reverse=reverse)
        elif sort_by == "lightness":
            palette.colors.sort(key=lambda c: c.hsl[2], reverse=reverse)
        elif sort_by == "brightness":
            palette.colors.sort(key=lambda c: c.hsv[2], reverse=reverse)
        elif sort_by == "red":
            palette.colors.sort(key=lambda c: c.r, reverse=reverse)
        elif sort_by == "green":
            palette.colors.sort(key=lambda c: c.g, reverse=reverse)
        elif sort_by == "blue":
            palette.colors.sort(key=lambda c: c.b, reverse=reverse)
        elif sort_by == "luminance":
            palette.colors.sort(key=lambda c: c.get_luminance(), reverse=reverse)
        else:
            raise ValueError(f"Unknown sort criteria: {sort_by}")
        
        palette.modified_at = palette.modified_at.__class__.now()