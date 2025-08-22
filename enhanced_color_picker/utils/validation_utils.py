"""
Enhanced Color Picker - Validation Utilities

This module provides comprehensive input validation and security utilities
for the Enhanced Color Picker application.
"""

import os
import re
import mimetypes
from pathlib import Path
from typing import Union, List, Dict, Any, Optional, Tuple
import magic
from PIL import Image
import json

from ..core.exceptions import ValidationError, FileOperationError
from ..models.enums import ColorFormat


class SecurityConfig:
    """Security configuration constants"""
    
    # File size limits (in bytes)
    MAX_IMAGE_SIZE = 100 * 1024 * 1024  # 100MB
    MAX_PALETTE_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_CONFIG_SIZE = 1 * 1024 * 1024    # 1MB
    
    # Memory limits
    MAX_IMAGE_PIXELS = 100 * 1024 * 1024  # 100 megapixels
    MAX_PALETTE_COLORS = 10000
    
    # Allowed file extensions
    ALLOWED_IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.tif', '.webp', '.svg'}
    ALLOWED_PALETTE_EXTENSIONS = {'.json', '.ase', '.aco', '.gpl'}
    ALLOWED_CONFIG_EXTENSIONS = {'.json', '.ini', '.cfg'}
    
    # MIME types
    ALLOWED_IMAGE_MIMES = {
        'image/png', 'image/jpeg', 'image/gif', 'image/bmp',
        'image/tiff', 'image/webp', 'image/svg+xml'
    }
    
    # Path traversal protection
    FORBIDDEN_PATH_PATTERNS = [
        r'\.\./',  # Parent directory traversal
        r'\.\.\\',  # Windows parent directory traversal
        r'/etc/',   # System directories
        r'/proc/',
        r'/sys/',
        r'C:\\Windows\\',
        r'C:\\System32\\',
    ]
    
    # Dangerous file patterns
    DANGEROUS_EXTENSIONS = {'.exe', '.bat', '.cmd', '.com', '.scr', '.pif', '.vbs', '.js', '.jar'}


class FileValidator:
    """File validation and security utilities"""
    
    def __init__(self):
        self.config = SecurityConfig()
        
    def validate_image_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Validate image file for security and format compliance.
        
        Args:
            file_path: Path to the image file
            
        Returns:
            Dict containing validation results and file metadata
            
        Raises:
            ValidationError: If validation fails
            FileOperationError: If file access fails
        """
        file_path = Path(file_path)
        
        # Basic file existence and access checks
        self._check_file_exists(file_path)
        self._check_file_readable(file_path)
        
        # Security checks
        self._check_path_traversal(file_path)
        self._check_file_extension(file_path, self.config.ALLOWED_IMAGE_EXTENSIONS)
        self._check_file_size(file_path, self.config.MAX_IMAGE_SIZE)
        
        # MIME type validation
        mime_type = self._get_mime_type(file_path)
        self._check_mime_type(mime_type, self.config.ALLOWED_IMAGE_MIMES)
        
        # Image-specific validation
        image_info = self._validate_image_content(file_path)
        
        return {
            "valid": True,
            "file_path": str(file_path),
            "file_size": file_path.stat().st_size,
            "mime_type": mime_type,
            "image_info": image_info
        }
        
    def validate_palette_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Validate palette file for security and format compliance.
        
        Args:
            file_path: Path to the palette file
            
        Returns:
            Dict containing validation results and file metadata
            
        Raises:
            ValidationError: If validation fails
            FileOperationError: If file access fails
        """
        file_path = Path(file_path)
        
        # Basic checks
        self._check_file_exists(file_path)
        self._check_file_readable(file_path)
        
        # Security checks
        self._check_path_traversal(file_path)
        self._check_file_extension(file_path, self.config.ALLOWED_PALETTE_EXTENSIONS)
        self._check_file_size(file_path, self.config.MAX_PALETTE_SIZE)
        
        # Content validation based on extension
        if file_path.suffix.lower() == '.json':
            palette_data = self._validate_json_palette(file_path)
        else:
            # For other formats, basic validation
            palette_data = {"colors": [], "format": file_path.suffix.lower()}
            
        return {
            "valid": True,
            "file_path": str(file_path),
            "file_size": file_path.stat().st_size,
            "palette_data": palette_data
        }
        
    def validate_config_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Validate configuration file for security and format compliance.
        
        Args:
            file_path: Path to the config file
            
        Returns:
            Dict containing validation results and file metadata
            
        Raises:
            ValidationError: If validation fails
            FileOperationError: If file access fails
        """
        file_path = Path(file_path)
        
        # Basic checks
        self._check_file_exists(file_path)
        self._check_file_readable(file_path)
        
        # Security checks
        self._check_path_traversal(file_path)
        self._check_file_extension(file_path, self.config.ALLOWED_CONFIG_EXTENSIONS)
        self._check_file_size(file_path, self.config.MAX_CONFIG_SIZE)
        
        # Content validation
        if file_path.suffix.lower() == '.json':
            config_data = self._validate_json_config(file_path)
        else:
            config_data = {}
            
        return {
            "valid": True,
            "file_path": str(file_path),
            "file_size": file_path.stat().st_size,
            "config_data": config_data
        }
        
    def _check_file_exists(self, file_path: Path):
        """Check if file exists"""
        if not file_path.exists():
            raise FileOperationError(
                "file_check",
                str(file_path),
                "File does not exist"
            )
            
    def _check_file_readable(self, file_path: Path):
        """Check if file is readable"""
        if not os.access(file_path, os.R_OK):
            raise FileOperationError(
                "file_access",
                str(file_path),
                "File is not readable"
            )
            
    def _check_path_traversal(self, file_path: Path):
        """Check for path traversal attacks"""
        path_str = str(file_path.resolve())
        
        for pattern in self.config.FORBIDDEN_PATH_PATTERNS:
            if re.search(pattern, path_str, re.IGNORECASE):
                raise ValidationError(
                    "file_path",
                    str(file_path),
                    "Path contains forbidden patterns"
                )
                
    def _check_file_extension(self, file_path: Path, allowed_extensions: set):
        """Check if file extension is allowed"""
        extension = file_path.suffix.lower()
        
        if extension in self.config.DANGEROUS_EXTENSIONS:
            raise ValidationError(
                "file_extension",
                extension,
                "Dangerous file extension detected"
            )
            
        if extension not in allowed_extensions:
            raise ValidationError(
                "file_extension",
                extension,
                f"Extension not in allowed list: {allowed_extensions}"
            )
            
    def _check_file_size(self, file_path: Path, max_size: int):
        """Check if file size is within limits"""
        file_size = file_path.stat().st_size
        
        if file_size > max_size:
            raise ValidationError(
                "file_size",
                f"{file_size} bytes",
                f"File size exceeds maximum allowed size of {max_size} bytes"
            )
            
    def _get_mime_type(self, file_path: Path) -> str:
        """Get MIME type of file"""
        try:
            # Try using python-magic for accurate detection
            mime_type = magic.from_file(str(file_path), mime=True)
        except:
            # Fallback to mimetypes module
            mime_type, _ = mimetypes.guess_type(str(file_path))
            
        return mime_type or "application/octet-stream"
        
    def _check_mime_type(self, mime_type: str, allowed_mimes: set):
        """Check if MIME type is allowed"""
        if mime_type not in allowed_mimes:
            raise ValidationError(
                "mime_type",
                mime_type,
                f"MIME type not in allowed list: {allowed_mimes}"
            )
            
    def _validate_image_content(self, file_path: Path) -> Dict[str, Any]:
        """Validate image content and extract metadata"""
        try:
            with Image.open(file_path) as img:
                # Check image dimensions and pixel count
                width, height = img.size
                pixel_count = width * height
                
                if pixel_count > self.config.MAX_IMAGE_PIXELS:
                    raise ValidationError(
                        "image_pixels",
                        f"{pixel_count} pixels",
                        f"Image has too many pixels (max: {self.config.MAX_IMAGE_PIXELS})"
                    )
                    
                # Extract image metadata
                image_info = {
                    "width": width,
                    "height": height,
                    "mode": img.mode,
                    "format": img.format,
                    "has_transparency": img.mode in ('RGBA', 'LA') or 'transparency' in img.info
                }
                
                # Additional security checks
                if hasattr(img, 'verify'):
                    img.verify()  # Verify image integrity
                    
                return image_info
                
        except Exception as e:
            raise ValidationError(
                "image_content",
                str(file_path),
                f"Invalid image content: {str(e)}"
            )
            
    def _validate_json_palette(self, file_path: Path) -> Dict[str, Any]:
        """Validate JSON palette file content"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Check if it's a valid palette structure
            if not isinstance(data, dict):
                raise ValidationError(
                    "palette_format",
                    "root",
                    "Palette file must contain a JSON object"
                )
                
            colors = data.get('colors', [])
            if not isinstance(colors, list):
                raise ValidationError(
                    "palette_format",
                    "colors",
                    "Colors must be a list"
                )
                
            if len(colors) > self.config.MAX_PALETTE_COLORS:
                raise ValidationError(
                    "palette_size",
                    f"{len(colors)} colors",
                    f"Too many colors (max: {self.config.MAX_PALETTE_COLORS})"
                )
                
            # Validate each color
            for i, color in enumerate(colors):
                self._validate_color_data(color, f"colors[{i}]")
                
            return data
            
        except json.JSONDecodeError as e:
            raise ValidationError(
                "json_format",
                str(file_path),
                f"Invalid JSON format: {str(e)}"
            )
        except Exception as e:
            raise ValidationError(
                "palette_content",
                str(file_path),
                f"Invalid palette content: {str(e)}"
            )
            
    def _validate_json_config(self, file_path: Path) -> Dict[str, Any]:
        """Validate JSON configuration file content"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            if not isinstance(data, dict):
                raise ValidationError(
                    "config_format",
                    "root",
                    "Configuration file must contain a JSON object"
                )
                
            return data
            
        except json.JSONDecodeError as e:
            raise ValidationError(
                "json_format",
                str(file_path),
                f"Invalid JSON format: {str(e)}"
            )
        except Exception as e:
            raise ValidationError(
                "config_content",
                str(file_path),
                f"Invalid configuration content: {str(e)}"
            )
            
    def _validate_color_data(self, color_data: Any, field_name: str):
        """Validate individual color data"""
        if not isinstance(color_data, dict):
            raise ValidationError(
                field_name,
                str(color_data),
                "Color data must be an object"
            )
            
        # Check for required fields (at least one color format)
        color_formats = ['rgb', 'hex', 'hsl', 'hsv', 'cmyk']
        if not any(fmt in color_data for fmt in color_formats):
            raise ValidationError(
                field_name,
                str(color_data),
                f"Color must have at least one format: {color_formats}"
            )


class InputValidator:
    """Input validation utilities for user inputs"""
    
    def validate_color_value(self, value: Any, color_format: ColorFormat) -> bool:
        """
        Validate color value based on format.
        
        Args:
            value: Color value to validate
            color_format: Expected color format
            
        Returns:
            bool: True if valid
            
        Raises:
            ValidationError: If validation fails
        """
        if color_format == ColorFormat.RGB:
            return self._validate_rgb(value)
        elif color_format == ColorFormat.HEX:
            return self._validate_hex(value)
        elif color_format == ColorFormat.HSL:
            return self._validate_hsl(value)
        elif color_format == ColorFormat.HSV:
            return self._validate_hsv(value)
        elif color_format == ColorFormat.CMYK:
            return self._validate_cmyk(value)
        else:
            raise ValidationError(
                "color_format",
                str(color_format),
                "Unknown color format"
            )
            
    def _validate_rgb(self, value: Any) -> bool:
        """Validate RGB color value"""
        if not isinstance(value, (list, tuple)) or len(value) != 3:
            raise ValidationError(
                "rgb_format",
                str(value),
                "RGB value must be a list/tuple of 3 numbers"
            )
            
        for i, component in enumerate(value):
            if not isinstance(component, (int, float)):
                raise ValidationError(
                    f"rgb_component_{i}",
                    str(component),
                    "RGB component must be a number"
                )
                
            if not (0 <= component <= 255):
                raise ValidationError(
                    f"rgb_component_{i}",
                    str(component),
                    "RGB component must be between 0 and 255"
                )
                
        return True
        
    def _validate_hex(self, value: Any) -> bool:
        """Validate HEX color value"""
        if not isinstance(value, str):
            raise ValidationError(
                "hex_format",
                str(value),
                "HEX value must be a string"
            )
            
        # Remove # if present
        hex_value = value.lstrip('#')
        
        if len(hex_value) not in (3, 6):
            raise ValidationError(
                "hex_length",
                value,
                "HEX value must be 3 or 6 characters long"
            )
            
        if not re.match(r'^[0-9A-Fa-f]+$', hex_value):
            raise ValidationError(
                "hex_characters",
                value,
                "HEX value must contain only hexadecimal characters"
            )
            
        return True
        
    def _validate_hsl(self, value: Any) -> bool:
        """Validate HSL color value"""
        if not isinstance(value, (list, tuple)) or len(value) != 3:
            raise ValidationError(
                "hsl_format",
                str(value),
                "HSL value must be a list/tuple of 3 numbers"
            )
            
        h, s, l = value
        
        if not isinstance(h, (int, float)) or not (0 <= h <= 360):
            raise ValidationError(
                "hsl_hue",
                str(h),
                "HSL hue must be between 0 and 360"
            )
            
        if not isinstance(s, (int, float)) or not (0 <= s <= 100):
            raise ValidationError(
                "hsl_saturation",
                str(s),
                "HSL saturation must be between 0 and 100"
            )
            
        if not isinstance(l, (int, float)) or not (0 <= l <= 100):
            raise ValidationError(
                "hsl_lightness",
                str(l),
                "HSL lightness must be between 0 and 100"
            )
            
        return True
        
    def _validate_hsv(self, value: Any) -> bool:
        """Validate HSV color value"""
        if not isinstance(value, (list, tuple)) or len(value) != 3:
            raise ValidationError(
                "hsv_format",
                str(value),
                "HSV value must be a list/tuple of 3 numbers"
            )
            
        h, s, v = value
        
        if not isinstance(h, (int, float)) or not (0 <= h <= 360):
            raise ValidationError(
                "hsv_hue",
                str(h),
                "HSV hue must be between 0 and 360"
            )
            
        if not isinstance(s, (int, float)) or not (0 <= s <= 100):
            raise ValidationError(
                "hsv_saturation",
                str(s),
                "HSV saturation must be between 0 and 100"
            )
            
        if not isinstance(v, (int, float)) or not (0 <= v <= 100):
            raise ValidationError(
                "hsv_value",
                str(v),
                "HSV value must be between 0 and 100"
            )
            
        return True
        
    def _validate_cmyk(self, value: Any) -> bool:
        """Validate CMYK color value"""
        if not isinstance(value, (list, tuple)) or len(value) != 4:
            raise ValidationError(
                "cmyk_format",
                str(value),
                "CMYK value must be a list/tuple of 4 numbers"
            )
            
        for i, component in enumerate(value):
            component_names = ['cyan', 'magenta', 'yellow', 'key']
            
            if not isinstance(component, (int, float)):
                raise ValidationError(
                    f"cmyk_{component_names[i]}",
                    str(component),
                    f"CMYK {component_names[i]} must be a number"
                )
                
            if not (0 <= component <= 100):
                raise ValidationError(
                    f"cmyk_{component_names[i]}",
                    str(component),
                    f"CMYK {component_names[i]} must be between 0 and 100"
                )
                
        return True
        
    def validate_coordinates(self, x: Any, y: Any, max_x: int = None, max_y: int = None) -> bool:
        """
        Validate coordinate values.
        
        Args:
            x: X coordinate
            y: Y coordinate
            max_x: Maximum allowed X value
            max_y: Maximum allowed Y value
            
        Returns:
            bool: True if valid
            
        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(x, (int, float)):
            raise ValidationError(
                "x_coordinate",
                str(x),
                "X coordinate must be a number"
            )
            
        if not isinstance(y, (int, float)):
            raise ValidationError(
                "y_coordinate",
                str(y),
                "Y coordinate must be a number"
            )
            
        if x < 0:
            raise ValidationError(
                "x_coordinate",
                str(x),
                "X coordinate must be non-negative"
            )
            
        if y < 0:
            raise ValidationError(
                "y_coordinate",
                str(y),
                "Y coordinate must be non-negative"
            )
            
        if max_x is not None and x > max_x:
            raise ValidationError(
                "x_coordinate",
                str(x),
                f"X coordinate must not exceed {max_x}"
            )
            
        if max_y is not None and y > max_y:
            raise ValidationError(
                "y_coordinate",
                str(y),
                f"Y coordinate must not exceed {max_y}"
            )
            
        return True
        
    def validate_palette_name(self, name: str) -> bool:
        """
        Validate palette name.
        
        Args:
            name: Palette name to validate
            
        Returns:
            bool: True if valid
            
        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(name, str):
            raise ValidationError(
                "palette_name",
                str(name),
                "Palette name must be a string"
            )
            
        if not name.strip():
            raise ValidationError(
                "palette_name",
                name,
                "Palette name cannot be empty"
            )
            
        if len(name) > 100:
            raise ValidationError(
                "palette_name",
                name,
                "Palette name must be 100 characters or less"
            )
            
        # Check for invalid characters
        invalid_chars = r'[<>:"/\\|?*]'
        if re.search(invalid_chars, name):
            raise ValidationError(
                "palette_name",
                name,
                "Palette name contains invalid characters"
            )
            
        return True


class MemoryLimitEnforcer:
    """Memory usage monitoring and enforcement"""
    
    def __init__(self, max_memory_mb: int = 1024):
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        
    def check_memory_usage(self) -> Dict[str, Any]:
        """
        Check current memory usage.
        
        Returns:
            Dict containing memory usage information
        """
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            
            return {
                "rss": memory_info.rss,  # Resident Set Size
                "vms": memory_info.vms,  # Virtual Memory Size
                "percent": process.memory_percent(),
                "available": psutil.virtual_memory().available,
                "limit_exceeded": memory_info.rss > self.max_memory_bytes
            }
        except ImportError:
            # Fallback if psutil is not available
            import resource
            usage = resource.getrusage(resource.RUSAGE_SELF)
            memory_kb = usage.ru_maxrss
            
            # Convert to bytes (Linux reports in KB, macOS in bytes)
            import platform
            if platform.system() == 'Linux':
                memory_bytes = memory_kb * 1024
            else:
                memory_bytes = memory_kb
                
            return {
                "rss": memory_bytes,
                "vms": 0,
                "percent": 0,
                "available": 0,
                "limit_exceeded": memory_bytes > self.max_memory_bytes
            }
            
    def enforce_memory_limit(self):
        """
        Enforce memory limit and raise error if exceeded.
        
        Raises:
            MemoryError: If memory limit is exceeded
        """
        memory_info = self.check_memory_usage()
        
        if memory_info["limit_exceeded"]:
            from ..core.exceptions import MemoryError
            raise MemoryError(
                "memory_limit_check",
                memory_info["rss"],
                self.max_memory_bytes
            )


# Global instances
_file_validator: Optional[FileValidator] = None
_input_validator: Optional[InputValidator] = None
_memory_enforcer: Optional[MemoryLimitEnforcer] = None


def get_file_validator() -> FileValidator:
    """Get global file validator instance"""
    global _file_validator
    if _file_validator is None:
        _file_validator = FileValidator()
    return _file_validator


def get_input_validator() -> InputValidator:
    """Get global input validator instance"""
    global _input_validator
    if _input_validator is None:
        _input_validator = InputValidator()
    return _input_validator


def get_memory_enforcer() -> MemoryLimitEnforcer:
    """Get global memory enforcer instance"""
    global _memory_enforcer
    if _memory_enforcer is None:
        _memory_enforcer = MemoryLimitEnforcer()
    return _memory_enforcer


def initialize_validators(max_memory_mb: int = 1024):
    """Initialize global validator instances"""
    global _file_validator, _input_validator, _memory_enforcer
    _file_validator = FileValidator()
    _input_validator = InputValidator()
    _memory_enforcer = MemoryLimitEnforcer(max_memory_mb)