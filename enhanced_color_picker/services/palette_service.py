"""
PaletteService - Comprehensive palette creation, management, and export service.

This service handles all palette-related operations including creation, persistence,
import/export functionality, and validation with error handling.
"""

import os
import json
import struct
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
from datetime import datetime

from ..models.palette import Palette
from ..models.color_data import ColorData
from ..models.enums import ExportFormat
from ..core.exceptions import PaletteError, ValidationError, ColorPickerError


class PaletteExporter:
    """Handles exporting palettes to various formats."""
    
    @staticmethod
    def export_to_json(palette: Palette) -> str:
        """Export palette to JSON format."""
        return json.dumps(palette.to_dict(), indent=2, ensure_ascii=False)
    
    @staticmethod
    def export_to_css(palette: Palette) -> str:
        """Export palette to CSS format."""
        css_content = f"/* Palette: {palette.name} */\n"
        css_content += f"/* Created: {palette.created_at.strftime('%Y-%m-%d %H:%M:%S')} */\n"
        css_content += f"/* Colors: {len(palette.colors)} */\n\n"
        
        css_content += ":root {\n"
        for i, color in enumerate(palette.colors):
            var_name = f"--color-{i+1}"
            css_content += f"  {var_name}: {color.hex};\n"
        css_content += "}\n\n"
        
        # Add individual color classes
        for i, color in enumerate(palette.colors):
            class_name = f"color-{i+1}"
            css_content += f".{class_name} {{\n"
            css_content += f"  color: {color.hex};\n"
            css_content += "}\n\n"
            css_content += f".bg-{class_name} {{\n"
            css_content += f"  background-color: {color.hex};\n"
            css_content += "}\n\n"
        
        return css_content
    
    @staticmethod
    def export_to_scss(palette: Palette) -> str:
        """Export palette to SCSS format."""
        scss_content = f"// Palette: {palette.name}\n"
        scss_content += f"// Created: {palette.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
        scss_content += f"// Colors: {len(palette.colors)}\n\n"
        
        # SCSS variables
        for i, color in enumerate(palette.colors):
            var_name = f"$color-{i+1}"
            scss_content += f"{var_name}: {color.hex};\n"
        
        scss_content += "\n// Color map\n"
        scss_content += f"$palette-{palette.name.lower().replace(' ', '-')}: (\n"
        for i, color in enumerate(palette.colors):
            scss_content += f"  'color-{i+1}': {color.hex},\n"
        scss_content += ");\n"
        
        return scss_content
    
    @staticmethod
    def export_to_ase(palette: Palette) -> bytes:
        """Export palette to Adobe Swatch Exchange (ASE) format."""
        # ASE file format implementation
        # This is a simplified version - full ASE support would require more complex handling
        
        # ASE Header
        signature = b'ASEF'  # ASE signature
        version = struct.pack('>HH', 1, 0)  # Version 1.0
        num_blocks = struct.pack('>I', len(palette.colors))
        
        header = signature + version + num_blocks
        
        # Color blocks
        blocks = b''
        for color in palette.colors:
            # Block type (color entry)
            block_type = struct.pack('>H', 0x0001)
            
            # Color name (UTF-16)
            color_name = f"Color {color.hex}".encode('utf-16be')
            name_length = struct.pack('>H', len(color_name) // 2)
            
            # Color data (RGB)
            color_space = b'RGB '
            r = struct.pack('>f', color.r / 255.0)
            g = struct.pack('>f', color.g / 255.0)
            b = struct.pack('>f', color.b / 255.0)
            color_data = color_space + r + g + b
            
            # Color type (global)
            color_type = struct.pack('>H', 0x0002)
            
            # Block length
            block_content = name_length + color_name + color_data + color_type
            block_length = struct.pack('>I', len(block_content))
            
            blocks += block_type + block_length + block_content
        
        return header + blocks
    
    @staticmethod
    def export_to_aco(palette: Palette) -> bytes:
        """Export palette to Adobe Color (ACO) format."""
        # ACO file format implementation
        # Version 1 format (simplified)
        
        # Header
        version = struct.pack('>H', 1)  # Version 1
        num_colors = struct.pack('>H', len(palette.colors))
        
        header = version + num_colors
        
        # Color entries
        colors_data = b''
        for color in palette.colors:
            # Color space (RGB = 0)
            color_space = struct.pack('>H', 0)
            
            # RGB values (16-bit)
            r = struct.pack('>H', int(color.r * 257))  # Convert 8-bit to 16-bit
            g = struct.pack('>H', int(color.g * 257))
            b = struct.pack('>H', int(color.b * 257))
            
            # Padding
            padding = struct.pack('>H', 0)
            
            colors_data += color_space + r + g + b + padding
        
        return header + colors_data
    
    @staticmethod
    def export_to_gpl(palette: Palette) -> str:
        """Export palette to GIMP Palette (GPL) format."""
        gpl_content = "GIMP Palette\n"
        gpl_content += f"Name: {palette.name}\n"
        gpl_content += f"Columns: {min(16, len(palette.colors))}\n"
        gpl_content += f"# Created: {palette.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
        gpl_content += f"# Colors: {len(palette.colors)}\n"
        
        if palette.description:
            gpl_content += f"# Description: {palette.description}\n"
        
        gpl_content += "#\n"
        
        for i, color in enumerate(palette.colors):
            color_name = f"Color {i+1}"
            gpl_content += f"{color.r:3d} {color.g:3d} {color.b:3d}\t{color_name}\n"
        
        return gpl_content


class PaletteImporter:
    """Handles importing palettes from various formats."""
    
    @staticmethod
    def import_from_json(json_data: str) -> Palette:
        """Import palette from JSON format."""
        try:
            data = json.loads(json_data)
            return Palette.from_dict(data)
        except json.JSONDecodeError as e:
            raise PaletteError(f"Invalid JSON format: {str(e)}", operation="import")
        except Exception as e:
            raise PaletteError(f"Failed to import JSON palette: {str(e)}", operation="import")
    
    @staticmethod
    def import_from_gpl(gpl_data: str) -> Palette:
        """Import palette from GIMP Palette (GPL) format."""
        lines = gpl_data.strip().split('\n')
        
        if not lines or not lines[0].startswith('GIMP Palette'):
            raise PaletteError("Invalid GPL format: missing GIMP Palette header", operation="import")
        
        palette_name = "Imported Palette"
        colors = []
        
        for line in lines[1:]:
            line = line.strip()
            
            if line.startswith('Name:'):
                palette_name = line[5:].strip()
            elif line.startswith('#') or line.startswith('Columns:') or not line:
                continue
            else:
                # Parse color line: "R G B    ColorName"
                parts = line.split()
                if len(parts) >= 3:
                    try:
                        r = int(parts[0])
                        g = int(parts[1])
                        b = int(parts[2])
                        colors.append(ColorData(r, g, b))
                    except ValueError:
                        continue  # Skip invalid color lines
        
        if not colors:
            raise PaletteError("No valid colors found in GPL file", operation="import")
        
        return Palette(name=palette_name, colors=colors)
    
    @staticmethod
    def import_from_hex_list(hex_list: List[str], name: str = "Imported Palette") -> Palette:
        """Import palette from list of hex color codes."""
        colors = []
        
        for hex_code in hex_list:
            try:
                color = ColorData.from_hex(hex_code)
                colors.append(color)
            except Exception:
                continue  # Skip invalid hex codes
        
        if not colors:
            raise PaletteError("No valid hex colors found", operation="import")
        
        return Palette(name=name, colors=colors)


class PaletteService:
    """
    Comprehensive palette service for creation, management, and export.
    
    Features:
    - Palette creation and management
    - JSON persistence with validation
    - Import/export in multiple formats (JSON, CSS, SCSS, ASE, ACO, GPL)
    - Palette validation and error handling
    - Search and filtering capabilities
    """
    
    def __init__(self, palettes_directory: Optional[str] = None):
        """
        Initialize PaletteService.
        
        Args:
            palettes_directory: Directory to store palette files
        """
        self.palettes_directory = Path(palettes_directory or "palettes")
        self.palettes_directory.mkdir(exist_ok=True)
        
        self.exporter = PaletteExporter()
        self.importer = PaletteImporter()
        
        # Cache for loaded palettes
        self._palette_cache: Dict[str, Palette] = {}
    
    def create_palette(self, name: str, colors: Optional[List[ColorData]] = None,
                      description: str = "", tags: Optional[List[str]] = None) -> Palette:
        """
        Create a new color palette.
        
        Args:
            name: Palette name
            colors: List of colors (optional)
            description: Palette description
            tags: List of tags
            
        Returns:
            Created palette
            
        Raises:
            ValidationError: If palette data is invalid
        """
        if not name or not name.strip():
            raise ValidationError("Palette name cannot be empty", field_name="name")
        
        name = name.strip()
        
        # Check for duplicate names
        if self.palette_exists(name):
            raise ValidationError(f"Palette with name '{name}' already exists", field_name="name")
        
        palette = Palette(
            name=name,
            colors=colors or [],
            description=description,
            tags=tags or []
        )
        
        return palette
    
    def save_palette(self, palette: Palette, file_path: Optional[str] = None) -> str:
        """
        Save palette to JSON file.
        
        Args:
            palette: Palette to save
            file_path: Custom file path (optional)
            
        Returns:
            Path where palette was saved
            
        Raises:
            PaletteError: If saving fails
        """
        try:
            if file_path is None:
                # Generate filename from palette name
                safe_name = "".join(c for c in palette.name if c.isalnum() or c in (' ', '-', '_')).strip()
                safe_name = safe_name.replace(' ', '_')
                file_path = self.palettes_directory / f"{safe_name}.json"
            else:
                file_path = Path(file_path)
            
            # Ensure directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Export to JSON
            json_data = self.exporter.export_to_json(palette)
            
            # Write to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(json_data)
            
            # Update cache
            self._palette_cache[palette.name] = palette
            
            return str(file_path)
            
        except Exception as e:
            raise PaletteError(
                f"Failed to save palette '{palette.name}': {str(e)}",
                palette_name=palette.name,
                operation="save"
            )
    
    def load_palette(self, file_path: str) -> Palette:
        """
        Load palette from JSON file.
        
        Args:
            file_path: Path to palette file
            
        Returns:
            Loaded palette
            
        Raises:
            PaletteError: If loading fails
        """
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                raise PaletteError(f"Palette file not found: {file_path}", operation="load")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                json_data = f.read()
            
            palette = self.importer.import_from_json(json_data)
            
            # Update cache
            self._palette_cache[palette.name] = palette
            
            return palette
            
        except PaletteError:
            raise
        except Exception as e:
            raise PaletteError(
                f"Failed to load palette from {file_path}: {str(e)}",
                operation="load"
            )
    
    def list_saved_palettes(self) -> List[Dict[str, Any]]:
        """
        List all saved palette files.
        
        Returns:
            List of palette information dictionaries
        """
        palettes = []
        
        try:
            for file_path in self.palettes_directory.glob("*.json"):
                try:
                    # Try to load basic info without full parsing
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    palettes.append({
                        'name': data.get('name', file_path.stem),
                        'file_path': str(file_path),
                        'color_count': len(data.get('colors', [])),
                        'created_at': data.get('created_at'),
                        'modified_at': data.get('modified_at'),
                        'tags': data.get('tags', []),
                        'description': data.get('description', '')
                    })
                except Exception:
                    # Skip invalid files
                    continue
        except Exception:
            # Return empty list if directory access fails
            pass
        
        return palettes
    
    def delete_palette(self, palette_name: str) -> bool:
        """
        Delete a saved palette.
        
        Args:
            palette_name: Name of palette to delete
            
        Returns:
            True if deleted successfully
            
        Raises:
            PaletteError: If deletion fails
        """
        try:
            # Find palette file
            palette_file = None
            for file_path in self.palettes_directory.glob("*.json"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    if data.get('name') == palette_name:
                        palette_file = file_path
                        break
                except Exception:
                    continue
            
            if palette_file is None:
                raise PaletteError(f"Palette '{palette_name}' not found", palette_name=palette_name)
            
            # Delete file
            palette_file.unlink()
            
            # Remove from cache
            self._palette_cache.pop(palette_name, None)
            
            return True
            
        except PaletteError:
            raise
        except Exception as e:
            raise PaletteError(
                f"Failed to delete palette '{palette_name}': {str(e)}",
                palette_name=palette_name,
                operation="delete"
            )
    
    def export_palette(self, palette: Palette, format: ExportFormat, file_path: str) -> str:
        """
        Export palette to specified format.
        
        Args:
            palette: Palette to export
            format: Export format
            file_path: Output file path
            
        Returns:
            Path where palette was exported
            
        Raises:
            PaletteError: If export fails
        """
        try:
            file_path = Path(file_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            if format == ExportFormat.JSON:
                content = self.exporter.export_to_json(palette)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                    
            elif format == ExportFormat.CSS:
                content = self.exporter.export_to_css(palette)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                    
            elif format == ExportFormat.SCSS:
                content = self.exporter.export_to_scss(palette)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                    
            elif format == ExportFormat.ASE:
                content = self.exporter.export_to_ase(palette)
                with open(file_path, 'wb') as f:
                    f.write(content)
                    
            elif format == ExportFormat.ACO:
                content = self.exporter.export_to_aco(palette)
                with open(file_path, 'wb') as f:
                    f.write(content)
                    
            elif format == ExportFormat.GPL:
                content = self.exporter.export_to_gpl(palette)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                    
            else:
                raise ValidationError(f"Unsupported export format: {format}")
            
            return str(file_path)
            
        except Exception as e:
            raise PaletteError(
                f"Failed to export palette '{palette.name}' to {format.value}: {str(e)}",
                palette_name=palette.name,
                operation="export"
            )
    
    def import_palette(self, file_path: str, format: Optional[ExportFormat] = None) -> Palette:
        """
        Import palette from file.
        
        Args:
            file_path: Path to palette file
            format: Format hint (auto-detected if None)
            
        Returns:
            Imported palette
            
        Raises:
            PaletteError: If import fails
        """
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                raise PaletteError(f"File not found: {file_path}", operation="import")
            
            # Auto-detect format if not specified
            if format is None:
                ext = file_path.suffix.lower()
                format_map = {
                    '.json': ExportFormat.JSON,
                    '.gpl': ExportFormat.GPL,
                    '.css': ExportFormat.CSS,
                    '.scss': ExportFormat.SCSS
                }
                format = format_map.get(ext)
                
                if format is None:
                    raise ValidationError(f"Cannot auto-detect format for file: {file_path}")
            
            # Import based on format
            if format == ExportFormat.JSON:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return self.importer.import_from_json(content)
                
            elif format == ExportFormat.GPL:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return self.importer.import_from_gpl(content)
                
            else:
                raise ValidationError(f"Import not supported for format: {format.value}")
                
        except PaletteError:
            raise
        except Exception as e:
            raise PaletteError(
                f"Failed to import palette from {file_path}: {str(e)}",
                operation="import"
            )
    
    def validate_palette(self, palette: Palette) -> Dict[str, Any]:
        """
        Validate palette data and return validation results.
        
        Args:
            palette: Palette to validate
            
        Returns:
            Validation results dictionary
        """
        validation = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'info': {
                'name': palette.name,
                'color_count': len(palette.colors),
                'has_description': bool(palette.description),
                'tag_count': len(palette.tags),
                'created_at': palette.created_at,
                'modified_at': palette.modified_at
            }
        }
        
        # Check name
        if not palette.name or not palette.name.strip():
            validation['errors'].append("Palette name is required")
            validation['is_valid'] = False
        
        # Check colors
        if not palette.colors:
            validation['warnings'].append("Palette has no colors")
        elif len(palette.colors) > 1000:
            validation['warnings'].append("Palette has many colors (>1000), may impact performance")
        
        # Check for duplicate colors
        unique_colors = palette.get_unique_colors()
        if len(unique_colors) < len(palette.colors):
            duplicate_count = len(palette.colors) - len(unique_colors)
            validation['warnings'].append(f"Palette contains {duplicate_count} duplicate colors")
        
        # Check color validity
        invalid_colors = []
        for i, color in enumerate(palette.colors):
            if not (0 <= color.r <= 255 and 0 <= color.g <= 255 and 0 <= color.b <= 255):
                invalid_colors.append(i)
            if not (0.0 <= color.alpha <= 1.0):
                invalid_colors.append(i)
        
        if invalid_colors:
            validation['errors'].append(f"Invalid color values at indices: {invalid_colors}")
            validation['is_valid'] = False
        
        return validation
    
    def search_palettes(self, query: str, search_in_tags: bool = True, 
                       search_in_description: bool = True) -> List[Dict[str, Any]]:
        """
        Search for palettes by name, tags, or description.
        
        Args:
            query: Search query
            search_in_tags: Whether to search in tags
            search_in_description: Whether to search in description
            
        Returns:
            List of matching palette information
        """
        query = query.lower().strip()
        if not query:
            return self.list_saved_palettes()
        
        matching_palettes = []
        all_palettes = self.list_saved_palettes()
        
        for palette_info in all_palettes:
            match = False
            
            # Search in name
            if query in palette_info['name'].lower():
                match = True
            
            # Search in tags
            if search_in_tags and palette_info.get('tags'):
                for tag in palette_info['tags']:
                    if query in tag.lower():
                        match = True
                        break
            
            # Search in description
            if search_in_description and palette_info.get('description'):
                if query in palette_info['description'].lower():
                    match = True
            
            if match:
                matching_palettes.append(palette_info)
        
        return matching_palettes
    
    def palette_exists(self, name: str) -> bool:
        """Check if a palette with the given name exists."""
        palettes = self.list_saved_palettes()
        return any(p['name'] == name for p in palettes)
    
    def get_palette_stats(self) -> Dict[str, Any]:
        """Get statistics about saved palettes."""
        palettes = self.list_saved_palettes()
        
        total_colors = sum(p['color_count'] for p in palettes)
        all_tags = []
        for p in palettes:
            all_tags.extend(p.get('tags', []))
        
        unique_tags = list(set(all_tags))
        
        return {
            'total_palettes': len(palettes),
            'total_colors': total_colors,
            'average_colors_per_palette': total_colors / len(palettes) if palettes else 0,
            'total_tags': len(unique_tags),
            'most_common_tags': self._get_most_common_tags(all_tags, 10)
        }
    
    def _get_most_common_tags(self, tags: List[str], limit: int = 10) -> List[Dict[str, Any]]:
        """Get most common tags with counts."""
        tag_counts = {}
        for tag in tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
        
        return [{'tag': tag, 'count': count} for tag, count in sorted_tags[:limit]]
    
    def clear_cache(self):
        """Clear the palette cache."""
        self._palette_cache.clear()
    
    def get_cached_palette(self, name: str) -> Optional[Palette]:
        """Get palette from cache."""
        return self._palette_cache.get(name)