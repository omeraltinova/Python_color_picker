"""
Export service for color palettes and individual colors.
Supports multiple export formats including CSS, programming languages, and Adobe formats.
"""

import json
import struct
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from pathlib import Path

from ..models.color_data import ColorData
from ..models.palette import Palette
from ..models.enums import ExportFormat


class ExportService:
    """
    Service for exporting colors and palettes to various formats.
    
    Supports CSS, SCSS, programming languages, Adobe formats, and GIMP palettes.
    """
    
    def __init__(self):
        """Initialize the export service."""
        self._format_handlers = {
            ExportFormat.JSON: self._export_json,
            ExportFormat.CSS: self._export_css,
            ExportFormat.SCSS: self._export_scss,
            ExportFormat.SASS: self._export_sass,
            ExportFormat.LESS: self._export_less,
            ExportFormat.PYTHON: self._export_python,
            ExportFormat.JAVASCRIPT: self._export_javascript,
            ExportFormat.JAVA: self._export_java,
            ExportFormat.CSHARP: self._export_csharp,
            ExportFormat.SWIFT: self._export_swift,
            ExportFormat.KOTLIN: self._export_kotlin,
            ExportFormat.GPL: self._export_gpl,
            ExportFormat.ASE: self._export_ase,
            ExportFormat.ACO: self._export_aco,
        }
    
    def export_palette(self, palette: Palette, format: ExportFormat, 
                      file_path: Optional[str] = None, **kwargs) -> str:
        """
        Export a palette to the specified format.
        
        Args:
            palette: The palette to export
            format: The export format
            file_path: Optional file path to save to
            **kwargs: Additional format-specific options
            
        Returns:
            The exported content as string (or file path for binary formats)
        """
        if format not in self._format_handlers:
            raise ValueError(f"Unsupported export format: {format}")
        
        handler = self._format_handlers[format]
        content = handler(palette, **kwargs)
        
        if file_path and format not in [ExportFormat.ASE, ExportFormat.ACO]:
            # Save text-based formats
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        elif file_path and format in [ExportFormat.ASE, ExportFormat.ACO]:
            # Binary formats are handled differently
            pass
            
        return content
    
    def export_colors(self, colors: List[ColorData], format: ExportFormat,
                     name: str = "colors", **kwargs) -> str:
        """
        Export a list of colors to the specified format.
        
        Args:
            colors: List of colors to export
            format: The export format
            name: Name for the color collection
            **kwargs: Additional format-specific options
            
        Returns:
            The exported content as string
        """
        # Create a temporary palette for export
        temp_palette = Palette(name=name, colors=colors)
        return self.export_palette(temp_palette, format, **kwargs)
    
    def export_single_color(self, color: ColorData, format: ExportFormat,
                           name: str = "color", **kwargs) -> str:
        """
        Export a single color to the specified format.
        
        Args:
            color: The color to export
            format: The export format
            name: Name for the color
            **kwargs: Additional format-specific options
            
        Returns:
            The exported content as string
        """
        return self.export_colors([color], format, name, **kwargs)
    
    def get_supported_formats(self) -> List[ExportFormat]:
        """Get list of supported export formats."""
        return list(self._format_handlers.keys())
    
    def get_format_extension(self, format: ExportFormat) -> str:
        """Get the file extension for a format."""
        extensions = {
            ExportFormat.JSON: ".json",
            ExportFormat.CSS: ".css",
            ExportFormat.SCSS: ".scss",
            ExportFormat.SASS: ".sass",
            ExportFormat.LESS: ".less",
            ExportFormat.PYTHON: ".py",
            ExportFormat.JAVASCRIPT: ".js",
            ExportFormat.JAVA: ".java",
            ExportFormat.CSHARP: ".cs",
            ExportFormat.SWIFT: ".swift",
            ExportFormat.KOTLIN: ".kt",
            ExportFormat.GPL: ".gpl",
            ExportFormat.ASE: ".ase",
            ExportFormat.ACO: ".aco",
        }
        return extensions.get(format, ".txt")
    
    # Format-specific export methods
    
    def _export_json(self, palette: Palette, **kwargs) -> str:
        """Export palette as JSON."""
        data = {
            "name": palette.name,
            "description": palette.description,
            "created_at": palette.created_at.isoformat(),
            "colors": []
        }
        
        for i, color in enumerate(palette.colors):
            color_data = {
                "name": f"color_{i+1}",
                "hex": color.hex,
                "rgb": {"r": color.r, "g": color.g, "b": color.b},
                "hsl": {"h": color.hsl[0], "s": color.hsl[1], "l": color.hsl[2]},
                "hsv": {"h": color.hsv[0], "s": color.hsv[1], "v": color.hsv[2]},
                "cmyk": {"c": color.cmyk[0], "m": color.cmyk[1], "y": color.cmyk[2], "k": color.cmyk[3]}
            }
            if color.alpha < 1.0:
                color_data["alpha"] = color.alpha
            data["colors"].append(color_data)
        
        return json.dumps(data, indent=2, ensure_ascii=False)
    
    def _export_css(self, palette: Palette, **kwargs) -> str:
        """Export palette as CSS custom properties."""
        css_format = kwargs.get('css_format', 'custom_properties')  # 'custom_properties' or 'classes'
        
        lines = [
            f"/* {palette.name} */",
            f"/* Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} */",
            ""
        ]
        
        if css_format == 'custom_properties':
            lines.append(":root {")
            for i, color in enumerate(palette.colors):
                var_name = f"--color-{i+1}"
                if color.alpha < 1.0:
                    lines.append(f"  {var_name}: rgba({color.r}, {color.g}, {color.b}, {color.alpha});")
                else:
                    lines.append(f"  {var_name}: {color.hex};")
            lines.append("}")
        else:  # classes
            for i, color in enumerate(palette.colors):
                class_name = f".color-{i+1}"
                if color.alpha < 1.0:
                    lines.extend([
                        f"{class_name} {{",
                        f"  color: rgba({color.r}, {color.g}, {color.b}, {color.alpha});",
                        "}"
                    ])
                else:
                    lines.extend([
                        f"{class_name} {{",
                        f"  color: {color.hex};",
                        "}"
                    ])
                lines.append("")
        
        return "\n".join(lines)
    
    def _export_scss(self, palette: Palette, **kwargs) -> str:
        """Export palette as SCSS variables."""
        lines = [
            f"// {palette.name}",
            f"// Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            ""
        ]
        
        for i, color in enumerate(palette.colors):
            var_name = f"$color-{i+1}"
            if color.alpha < 1.0:
                lines.append(f"{var_name}: rgba({color.r}, {color.g}, {color.b}, {color.alpha});")
            else:
                lines.append(f"{var_name}: {color.hex};")
        
        return "\n".join(lines)
    
    def _export_sass(self, palette: Palette, **kwargs) -> str:
        """Export palette as Sass variables (indented syntax)."""
        lines = [
            f"// {palette.name}",
            f"// Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            ""
        ]
        
        for i, color in enumerate(palette.colors):
            var_name = f"$color-{i+1}"
            if color.alpha < 1.0:
                lines.append(f"{var_name}: rgba({color.r}, {color.g}, {color.b}, {color.alpha})")
            else:
                lines.append(f"{var_name}: {color.hex}")
        
        return "\n".join(lines)
    
    def _export_less(self, palette: Palette, **kwargs) -> str:
        """Export palette as LESS variables."""
        lines = [
            f"// {palette.name}",
            f"// Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            ""
        ]
        
        for i, color in enumerate(palette.colors):
            var_name = f"@color-{i+1}"
            if color.alpha < 1.0:
                lines.append(f"{var_name}: rgba({color.r}, {color.g}, {color.b}, {color.alpha});")
            else:
                lines.append(f"{var_name}: {color.hex};")
        
        return "\n".join(lines)
    
    def _export_python(self, palette: Palette, **kwargs) -> str:
        """Export palette as Python constants."""
        format_type = kwargs.get('format', 'dict')  # 'dict', 'tuple', 'list'
        
        lines = [
            f'"""',
            f'{palette.name}',
            f'Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
            f'"""',
            ""
        ]
        
        if format_type == 'dict':
            lines.append("COLORS = {")
            for i, color in enumerate(palette.colors):
                if color.alpha < 1.0:
                    lines.append(f'    "color_{i+1}": ({color.r}, {color.g}, {color.b}, {color.alpha}),')
                else:
                    lines.append(f'    "color_{i+1}": ({color.r}, {color.g}, {color.b}),')
            lines.append("}")
        elif format_type == 'tuple':
            lines.append("COLORS = (")
            for color in palette.colors:
                if color.alpha < 1.0:
                    lines.append(f'    ({color.r}, {color.g}, {color.b}, {color.alpha}),')
                else:
                    lines.append(f'    ({color.r}, {color.g}, {color.b}),')
            lines.append(")")
        else:  # list
            lines.append("COLORS = [")
            for color in palette.colors:
                if color.alpha < 1.0:
                    lines.append(f'    [{color.r}, {color.g}, {color.b}, {color.alpha}],')
                else:
                    lines.append(f'    [{color.r}, {color.g}, {color.b}],')
            lines.append("]")
        
        return "\n".join(lines)
    
    def _export_javascript(self, palette: Palette, **kwargs) -> str:
        """Export palette as JavaScript constants."""
        format_type = kwargs.get('format', 'object')  # 'object', 'array'
        
        lines = [
            f'/**',
            f' * {palette.name}',
            f' * Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
            f' */',
            ""
        ]
        
        if format_type == 'object':
            lines.append("const COLORS = {")
            for i, color in enumerate(palette.colors):
                if color.alpha < 1.0:
                    lines.append(f'  color{i+1}: {{ r: {color.r}, g: {color.g}, b: {color.b}, a: {color.alpha} }},')
                else:
                    lines.append(f'  color{i+1}: {{ r: {color.r}, g: {color.g}, b: {color.b} }},')
            lines.append("};")
        else:  # array
            lines.append("const COLORS = [")
            for color in palette.colors:
                if color.alpha < 1.0:
                    lines.append(f'  {{ r: {color.r}, g: {color.g}, b: {color.b}, a: {color.alpha} }},')
                else:
                    lines.append(f'  {{ r: {color.r}, g: {color.g}, b: {color.b} }},')
            lines.append("];")
        
        return "\n".join(lines)
    
    def _export_java(self, palette: Palette, **kwargs) -> str:
        """Export palette as Java constants."""
        class_name = kwargs.get('class_name', 'Colors')
        
        lines = [
            f'/**',
            f' * {palette.name}',
            f' * Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
            f' */',
            "",
            "import java.awt.Color;",
            "",
            f"public class {class_name} {{",
            ""
        ]
        
        for i, color in enumerate(palette.colors):
            if color.alpha < 1.0:
                alpha_int = int(color.alpha * 255)
                lines.append(f'    public static final Color COLOR_{i+1} = new Color({color.r}, {color.g}, {color.b}, {alpha_int});')
            else:
                lines.append(f'    public static final Color COLOR_{i+1} = new Color({color.r}, {color.g}, {color.b});')
        
        lines.extend(["", "}"])
        
        return "\n".join(lines)
    
    def _export_csharp(self, palette: Palette, **kwargs) -> str:
        """Export palette as C# constants."""
        class_name = kwargs.get('class_name', 'Colors')
        namespace = kwargs.get('namespace', 'ColorPalette')
        
        lines = [
            f'/**',
            f' * {palette.name}',
            f' * Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
            f' */',
            "",
            "using System.Drawing;",
            "",
            f"namespace {namespace}",
            "{",
            f"    public static class {class_name}",
            "    {",
        ]
        
        for i, color in enumerate(palette.colors):
            if color.alpha < 1.0:
                alpha_int = int(color.alpha * 255)
                lines.append(f'        public static readonly Color Color{i+1} = Color.FromArgb({alpha_int}, {color.r}, {color.g}, {color.b});')
            else:
                lines.append(f'        public static readonly Color Color{i+1} = Color.FromArgb({color.r}, {color.g}, {color.b});')
        
        lines.extend(["    }", "}"])
        
        return "\n".join(lines)
    
    def _export_swift(self, palette: Palette, **kwargs) -> str:
        """Export palette as Swift constants."""
        lines = [
            f'/**',
            f' * {palette.name}',
            f' * Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
            f' */',
            "",
            "import UIKit",
            "",
            "struct Colors {",
        ]
        
        for i, color in enumerate(palette.colors):
            r_norm = color.r / 255.0
            g_norm = color.g / 255.0
            b_norm = color.b / 255.0
            
            lines.append(f'    static let color{i+1} = UIColor(red: {r_norm:.3f}, green: {g_norm:.3f}, blue: {b_norm:.3f}, alpha: {color.alpha})')
        
        lines.append("}")
        
        return "\n".join(lines)
    
    def _export_kotlin(self, palette: Palette, **kwargs) -> str:
        """Export palette as Kotlin constants."""
        lines = [
            f'/**',
            f' * {palette.name}',
            f' * Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
            f' */',
            "",
            "import android.graphics.Color",
            "",
            "object Colors {",
        ]
        
        for i, color in enumerate(palette.colors):
            if color.alpha < 1.0:
                alpha_int = int(color.alpha * 255)
                lines.append(f'    val COLOR_{i+1} = Color.argb({alpha_int}, {color.r}, {color.g}, {color.b})')
            else:
                lines.append(f'    val COLOR_{i+1} = Color.rgb({color.r}, {color.g}, {color.b})')
        
        lines.append("}")
        
        return "\n".join(lines)
    
    def _export_gpl(self, palette: Palette, **kwargs) -> str:
        """Export palette as GIMP Palette (.gpl) format."""
        lines = [
            "GIMP Palette",
            f"Name: {palette.name}",
            f"# Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "#"
        ]
        
        for i, color in enumerate(palette.colors):
            # GIMP palette format: R G B Name
            lines.append(f"{color.r:3d} {color.g:3d} {color.b:3d} Color {i+1}")
        
        return "\n".join(lines)
    
    def _export_ase(self, palette: Palette, file_path: str = None, **kwargs) -> str:
        """Export palette as Adobe Swatch Exchange (.ase) format."""
        if not file_path:
            raise ValueError("ASE export requires a file path")
        
        # ASE is a binary format
        with open(file_path, 'wb') as f:
            # ASE Header
            f.write(b'ASEF')  # Signature
            f.write(struct.pack('>HH', 1, 0))  # Version (1.0)
            f.write(struct.pack('>I', len(palette.colors)))  # Number of blocks
            
            for i, color in enumerate(palette.colors):
                # Block header
                f.write(struct.pack('>H', 0x0001))  # Block type (Color Entry)
                
                # Color name
                color_name = f"Color {i+1}"
                name_length = len(color_name) + 1  # +1 for null terminator
                f.write(struct.pack('>I', 22 + name_length * 2))  # Block length
                f.write(struct.pack('>H', name_length))  # Name length
                
                # Write name as UTF-16BE
                for char in color_name:
                    f.write(char.encode('utf-16be'))
                f.write(b'\x00\x00')  # Null terminator
                
                # Color model (RGB)
                f.write(b'RGB ')
                
                # RGB values (32-bit floats)
                r_float = color.r / 255.0
                g_float = color.g / 255.0
                b_float = color.b / 255.0
                
                f.write(struct.pack('>fff', r_float, g_float, b_float))
                
                # Color type (0 = Global, 1 = Spot, 2 = Normal)
                f.write(struct.pack('>H', 2))
        
        return file_path
    
    def _export_aco(self, palette: Palette, file_path: str = None, **kwargs) -> str:
        """Export palette as Adobe Color (.aco) format."""
        if not file_path:
            raise ValueError("ACO export requires a file path")
        
        # ACO is a binary format
        with open(file_path, 'wb') as f:
            # ACO Header
            f.write(struct.pack('>H', 1))  # Version
            f.write(struct.pack('>H', len(palette.colors)))  # Number of colors
            
            # Write colors
            for color in palette.colors:
                f.write(struct.pack('>H', 0))  # Color space (RGB)
                f.write(struct.pack('>H', color.r * 257))  # Red (0-65535)
                f.write(struct.pack('>H', color.g * 257))  # Green (0-65535)
                f.write(struct.pack('>H', color.b * 257))  # Blue (0-65535)
                f.write(struct.pack('>H', 0))  # Padding
        
        return file_path