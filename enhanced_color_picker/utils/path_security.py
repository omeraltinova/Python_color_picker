"""
Enhanced Color Picker - Path Security Utilities

This module provides path sanitization and security utilities to prevent
directory traversal attacks and ensure safe file operations.
"""

import os
import re
from pathlib import Path, PurePath
from typing import Union, Optional, List, Set
import tempfile
import urllib.parse

from ..core.exceptions import ValidationError, FileOperationError


class PathSecurity:
    """
    Path security utilities for preventing directory traversal and other
    path-based security vulnerabilities.
    """
    
    # Dangerous path patterns
    DANGEROUS_PATTERNS = [
        r'\.\./',           # Unix parent directory
        r'\.\.\\',          # Windows parent directory  
        r'\.\.%2F',         # URL encoded parent directory
        r'\.\.%5C',         # URL encoded Windows parent directory
        r'%2E%2E%2F',       # Double URL encoded parent directory
        r'%2E%2E%5C',       # Double URL encoded Windows parent directory
        r'\.\.%252F',       # Triple URL encoded parent directory
        r'\.\.%255C',       # Triple URL encoded Windows parent directory
    ]
    
    # System directories to protect (Unix-like)
    PROTECTED_UNIX_DIRS = {
        '/etc', '/proc', '/sys', '/dev', '/boot', '/root',
        '/usr/bin', '/usr/sbin', '/sbin', '/bin'
    }
    
    # System directories to protect (Windows)
    PROTECTED_WINDOWS_DIRS = {
        'C:\\Windows', 'C:\\System32', 'C:\\Program Files',
        'C:\\Program Files (x86)', 'C:\\ProgramData'
    }
    
    # Dangerous file extensions
    DANGEROUS_EXTENSIONS = {
        '.exe', '.bat', '.cmd', '.com', '.scr', '.pif', '.vbs', '.js',
        '.jar', '.msi', '.dll', '.sys', '.drv', '.ocx', '.cpl', '.inf'
    }
    
    # Reserved Windows filenames
    WINDOWS_RESERVED_NAMES = {
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    }
    
    def __init__(self, allowed_base_paths: Optional[List[Union[str, Path]]] = None):
        """
        Initialize path security with allowed base paths.
        
        Args:
            allowed_base_paths: List of allowed base paths for file operations
        """
        self.allowed_base_paths = self._normalize_base_paths(allowed_base_paths or [])
        
    def _normalize_base_paths(self, paths: List[Union[str, Path]]) -> List[Path]:
        """Normalize and validate base paths"""
        normalized = []
        
        for path in paths:
            try:
                normalized_path = Path(path).resolve()
                if normalized_path.exists() and normalized_path.is_dir():
                    normalized.append(normalized_path)
            except (OSError, ValueError):
                continue
                
        # Add default safe paths if none provided
        if not normalized:
            normalized = [
                Path.home(),
                Path.cwd(),
                Path(tempfile.gettempdir())
            ]
            
        return normalized
        
    def sanitize_path(self, path: Union[str, Path], 
                     base_path: Optional[Union[str, Path]] = None) -> Path:
        """
        Sanitize and validate a file path.
        
        Args:
            path: Path to sanitize
            base_path: Optional base path to resolve relative paths against
            
        Returns:
            Sanitized Path object
            
        Raises:
            ValidationError: If path is invalid or dangerous
        """
        # Convert to string for initial processing
        path_str = str(path)
        
        # URL decode the path
        path_str = self._url_decode_path(path_str)
        
        # Check for dangerous patterns
        self._check_dangerous_patterns(path_str)
        
        # Convert to Path object
        try:
            path_obj = Path(path_str)
        except (ValueError, OSError) as e:
            raise ValidationError(
                "path_format",
                path_str,
                f"Invalid path format: {e}"
            )
            
        # Handle relative paths
        if not path_obj.is_absolute() and base_path:
            base_path_obj = Path(base_path).resolve()
            path_obj = base_path_obj / path_obj
            
        # Resolve the path
        try:
            resolved_path = path_obj.resolve()
        except (OSError, ValueError) as e:
            raise ValidationError(
                "path_resolution",
                str(path_obj),
                f"Cannot resolve path: {e}"
            )
            
        # Additional security checks
        self._check_system_directories(resolved_path)
        self._check_file_extension(resolved_path)
        self._check_filename(resolved_path)
        
        # Check against allowed base paths
        if self.allowed_base_paths:
            self._check_allowed_paths(resolved_path)
            
        return resolved_path
        
    def _url_decode_path(self, path: str) -> str:
        """URL decode path to handle encoded traversal attempts"""
        # Multiple rounds of decoding to handle double/triple encoding
        decoded = path
        for _ in range(3):  # Maximum 3 rounds of decoding
            try:
                new_decoded = urllib.parse.unquote(decoded)
                if new_decoded == decoded:
                    break  # No more decoding needed
                decoded = new_decoded
            except Exception:
                break
                
        return decoded
        
    def _check_dangerous_patterns(self, path: str):
        """Check for dangerous path patterns"""
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, path, re.IGNORECASE):
                raise ValidationError(
                    "path_traversal",
                    path,
                    f"Path contains dangerous pattern: {pattern}"
                )
                
    def _check_system_directories(self, path: Path):
        """Check if path points to protected system directories"""
        path_str = str(path).lower()
        
        # Check Unix system directories
        for protected_dir in self.PROTECTED_UNIX_DIRS:
            if path_str.startswith(protected_dir.lower()):
                raise ValidationError(
                    "system_directory",
                    str(path),
                    f"Access to system directory not allowed: {protected_dir}"
                )
                
        # Check Windows system directories
        for protected_dir in self.PROTECTED_WINDOWS_DIRS:
            if path_str.startswith(protected_dir.lower()):
                raise ValidationError(
                    "system_directory",
                    str(path),
                    f"Access to system directory not allowed: {protected_dir}"
                )
                
    def _check_file_extension(self, path: Path):
        """Check for dangerous file extensions"""
        extension = path.suffix.lower()
        
        if extension in self.DANGEROUS_EXTENSIONS:
            raise ValidationError(
                "dangerous_extension",
                extension,
                f"File extension not allowed: {extension}"
            )
            
    def _check_filename(self, path: Path):
        """Check for reserved or dangerous filenames"""
        filename = path.stem.upper()
        
        # Check Windows reserved names
        if filename in self.WINDOWS_RESERVED_NAMES:
            raise ValidationError(
                "reserved_filename",
                filename,
                f"Reserved filename not allowed: {filename}"
            )
            
        # Check for null bytes and other dangerous characters
        if '\x00' in str(path):
            raise ValidationError(
                "null_byte",
                str(path),
                "Path contains null byte"
            )
            
        # Check for excessively long filenames
        if len(path.name) > 255:
            raise ValidationError(
                "filename_length",
                path.name,
                "Filename too long (max 255 characters)"
            )
            
    def _check_allowed_paths(self, path: Path):
        """Check if path is within allowed base paths"""
        for allowed_base in self.allowed_base_paths:
            try:
                # Check if path is relative to allowed base
                path.relative_to(allowed_base)
                return  # Path is allowed
            except ValueError:
                continue
                
        # Path is not within any allowed base path
        raise ValidationError(
            "path_not_allowed",
            str(path),
            f"Path not within allowed directories: {[str(p) for p in self.allowed_base_paths]}"
        )
        
    def create_safe_filename(self, filename: str, max_length: int = 200) -> str:
        """
        Create a safe filename by removing dangerous characters.
        
        Args:
            filename: Original filename
            max_length: Maximum filename length
            
        Returns:
            Safe filename string
        """
        # Remove or replace dangerous characters
        safe_chars = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', filename)
        
        # Remove leading/trailing dots and spaces
        safe_chars = safe_chars.strip('. ')
        
        # Ensure it's not empty
        if not safe_chars:
            safe_chars = "file"
            
        # Check for reserved names
        name_part = safe_chars.split('.')[0].upper()
        if name_part in self.WINDOWS_RESERVED_NAMES:
            safe_chars = f"safe_{safe_chars}"
            
        # Truncate if too long
        if len(safe_chars) > max_length:
            name, ext = os.path.splitext(safe_chars)
            max_name_length = max_length - len(ext)
            safe_chars = name[:max_name_length] + ext
            
        return safe_chars
        
    def get_safe_temp_path(self, filename: str = None) -> Path:
        """
        Get a safe temporary file path.
        
        Args:
            filename: Optional filename for the temp file
            
        Returns:
            Safe temporary file path
        """
        temp_dir = Path(tempfile.gettempdir())
        
        if filename:
            safe_filename = self.create_safe_filename(filename)
            return temp_dir / safe_filename
        else:
            # Create a unique temporary file
            fd, temp_path = tempfile.mkstemp()
            os.close(fd)  # Close the file descriptor
            return Path(temp_path)
            
    def validate_directory_creation(self, directory: Union[str, Path]) -> Path:
        """
        Validate directory creation request.
        
        Args:
            directory: Directory path to validate
            
        Returns:
            Validated directory path
            
        Raises:
            ValidationError: If directory creation is not safe
        """
        dir_path = self.sanitize_path(directory)
        
        # Check if parent directory exists and is writable
        parent = dir_path.parent
        if not parent.exists():
            raise ValidationError(
                "parent_directory",
                str(parent),
                "Parent directory does not exist"
            )
            
        if not os.access(parent, os.W_OK):
            raise ValidationError(
                "parent_writable",
                str(parent),
                "Parent directory is not writable"
            )
            
        # Check if directory already exists
        if dir_path.exists() and not dir_path.is_dir():
            raise ValidationError(
                "path_exists",
                str(dir_path),
                "Path exists but is not a directory"
            )
            
        return dir_path
        
    def secure_file_copy(self, source: Union[str, Path], 
                        destination: Union[str, Path]) -> Path:
        """
        Perform secure file copy with validation.
        
        Args:
            source: Source file path
            destination: Destination file path
            
        Returns:
            Destination path
            
        Raises:
            ValidationError: If copy operation is not safe
            FileOperationError: If copy fails
        """
        # Validate both paths
        source_path = self.sanitize_path(source)
        dest_path = self.sanitize_path(destination)
        
        # Check source file exists and is readable
        if not source_path.exists():
            raise FileOperationError(
                "file_copy",
                str(source_path),
                "Source file does not exist"
            )
            
        if not source_path.is_file():
            raise ValidationError(
                "source_type",
                str(source_path),
                "Source is not a regular file"
            )
            
        if not os.access(source_path, os.R_OK):
            raise FileOperationError(
                "file_copy",
                str(source_path),
                "Source file is not readable"
            )
            
        # Check destination directory is writable
        dest_dir = dest_path.parent
        if not dest_dir.exists():
            raise FileOperationError(
                "file_copy",
                str(dest_dir),
                "Destination directory does not exist"
            )
            
        if not os.access(dest_dir, os.W_OK):
            raise FileOperationError(
                "file_copy",
                str(dest_dir),
                "Destination directory is not writable"
            )
            
        # Perform the copy
        try:
            import shutil
            shutil.copy2(source_path, dest_path)
            return dest_path
        except Exception as e:
            raise FileOperationError(
                "file_copy",
                f"{source_path} -> {dest_path}",
                f"Copy failed: {e}"
            )


class SecurePathManager:
    """
    Manager for secure path operations with configurable security policies.
    """
    
    def __init__(self, config_manager=None):
        """
        Initialize secure path manager.
        
        Args:
            config_manager: Configuration manager for security settings
        """
        self.config_manager = config_manager
        self.path_security = None
        self._initialize_path_security()
        
    def _initialize_path_security(self):
        """Initialize path security with configuration"""
        allowed_paths = []
        
        if self.config_manager:
            config = self.config_manager.get_config()
            allowed_paths = config.security.allowed_directories
            
        self.path_security = PathSecurity(allowed_paths)
        
    def sanitize_user_path(self, path: Union[str, Path], 
                          operation: str = "read") -> Path:
        """
        Sanitize user-provided path based on operation type.
        
        Args:
            path: User-provided path
            operation: Type of operation (read, write, create)
            
        Returns:
            Sanitized path
            
        Raises:
            ValidationError: If path is not safe for operation
        """
        sanitized = self.path_security.sanitize_path(path)
        
        # Additional checks based on operation
        if operation == "write" or operation == "create":
            # Check if parent directory is writable
            parent = sanitized.parent
            if parent.exists() and not os.access(parent, os.W_OK):
                raise ValidationError(
                    "write_permission",
                    str(parent),
                    "Directory is not writable"
                )
                
        elif operation == "read":
            # Check if file exists and is readable
            if sanitized.exists() and not os.access(sanitized, os.R_OK):
                raise ValidationError(
                    "read_permission",
                    str(sanitized),
                    "File is not readable"
                )
                
        return sanitized
        
    def get_secure_workspace(self) -> Path:
        """
        Get a secure workspace directory for temporary operations.
        
        Returns:
            Secure workspace directory path
        """
        if self.config_manager:
            return self.config_manager.get_safe_temp_dir()
        else:
            return Path(tempfile.gettempdir()) / "enhanced_color_picker"
            
    def cleanup_temp_files(self, workspace: Path, max_age_hours: int = 24):
        """
        Clean up old temporary files in workspace.
        
        Args:
            workspace: Workspace directory to clean
            max_age_hours: Maximum age of files to keep in hours
        """
        if not workspace.exists() or not workspace.is_dir():
            return
            
        import time
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        try:
            for file_path in workspace.iterdir():
                if file_path.is_file():
                    file_age = current_time - file_path.stat().st_mtime
                    if file_age > max_age_seconds:
                        try:
                            file_path.unlink()
                        except OSError:
                            pass  # Ignore errors when cleaning up
        except OSError:
            pass  # Ignore errors when accessing workspace


# Global path security instances
_path_security: Optional[PathSecurity] = None
_secure_path_manager: Optional[SecurePathManager] = None


def get_path_security() -> PathSecurity:
    """Get global path security instance"""
    global _path_security
    if _path_security is None:
        _path_security = PathSecurity()
    return _path_security


def get_secure_path_manager() -> SecurePathManager:
    """Get global secure path manager instance"""
    global _secure_path_manager
    if _secure_path_manager is None:
        _secure_path_manager = SecurePathManager()
    return _secure_path_manager


def initialize_path_security(config_manager=None, allowed_paths: List[Union[str, Path]] = None):
    """Initialize global path security instances"""
    global _path_security, _secure_path_manager
    
    if allowed_paths:
        _path_security = PathSecurity(allowed_paths)
    else:
        _path_security = PathSecurity()
        
    _secure_path_manager = SecurePathManager(config_manager)