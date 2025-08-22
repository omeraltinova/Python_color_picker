"""
Enhanced Color Picker - Core Exception Classes

This module defines the exception hierarchy and error handling infrastructure
for the Enhanced Color Picker application.
"""

from enum import Enum
from typing import Optional, Dict, Any
import logging
from datetime import datetime


class ErrorSeverity(Enum):
    """Error severity levels for categorizing errors"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for better error organization"""
    IMAGE_PROCESSING = "image_processing"
    COLOR_CONVERSION = "color_conversion"
    FILE_OPERATION = "file_operation"
    VALIDATION = "validation"
    MEMORY = "memory"
    NETWORK = "network"
    UI = "ui"
    SYSTEM = "system"


class ColorPickerError(Exception):
    """
    Base exception class for all Enhanced Color Picker errors.
    
    Provides structured error information including severity, category,
    user-friendly messages, and recovery suggestions.
    """
    
    def __init__(
        self,
        message: str,
        user_message_key: str = None,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        category: ErrorCategory = ErrorCategory.SYSTEM,
        recovery_suggestions: list = None,
        technical_details: Dict[str, Any] = None,
        original_exception: Exception = None
    ):
        super().__init__(message)
        self.message = message
        self.user_message_key = user_message_key or "errors.generic_error"
        self.severity = severity
        self.category = category
        self.recovery_suggestions = recovery_suggestions or []
        self.technical_details = technical_details or {}
        self.original_exception = original_exception
        self.timestamp = datetime.now()
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for logging and serialization"""
        return {
            "message": self.message,
            "user_message_key": self.user_message_key,
            "severity": self.severity.value,
            "category": self.category.value,
            "recovery_suggestions": self.recovery_suggestions,
            "technical_details": self.technical_details,
            "timestamp": self.timestamp.isoformat(),
            "original_exception": str(self.original_exception) if self.original_exception else None
        }


class ImageLoadError(ColorPickerError):
    """Raised when image loading operations fail"""
    
    def __init__(self, file_path: str, reason: str, original_exception: Exception = None):
        super().__init__(
            message=f"Failed to load image from {file_path}: {reason}",
            user_message_key="errors.image_load_failed",
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.IMAGE_PROCESSING,
            recovery_suggestions=[
                "Check if the file exists and is accessible",
                "Verify the file format is supported",
                "Try with a different image file",
                "Check file permissions"
            ],
            technical_details={"file_path": file_path, "reason": reason},
            original_exception=original_exception
        )


class UnsupportedFormatError(ColorPickerError):
    """Raised when an unsupported file format is encountered"""
    
    def __init__(self, file_path: str, detected_format: str = None):
        super().__init__(
            message=f"Unsupported file format: {file_path}",
            user_message_key="errors.unsupported_format",
            severity=ErrorSeverity.LOW,
            category=ErrorCategory.VALIDATION,
            recovery_suggestions=[
                "Use a supported image format (PNG, JPEG, GIF, BMP, TIFF, WebP, SVG)",
                "Convert the image to a supported format",
                "Check if the file extension matches the actual format"
            ],
            technical_details={
                "file_path": file_path,
                "detected_format": detected_format,
                "supported_formats": ["PNG", "JPEG", "GIF", "BMP", "TIFF", "WebP", "SVG"]
            }
        )


class ColorConversionError(ColorPickerError):
    """Raised when color conversion operations fail"""
    
    def __init__(self, source_format: str, target_format: str, color_value: Any, reason: str = None):
        super().__init__(
            message=f"Failed to convert color from {source_format} to {target_format}",
            user_message_key="errors.color_conversion_failed",
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.COLOR_CONVERSION,
            recovery_suggestions=[
                "Check if the color values are within valid ranges",
                "Try with a different color format",
                "Verify the input color data is correct"
            ],
            technical_details={
                "source_format": source_format,
                "target_format": target_format,
                "color_value": str(color_value),
                "reason": reason
            }
        )


class PaletteError(ColorPickerError):
    """Raised when palette operations fail"""
    
    def __init__(self, operation: str, palette_name: str = None, reason: str = None):
        super().__init__(
            message=f"Palette operation failed: {operation}",
            user_message_key="errors.palette_operation_failed",
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.FILE_OPERATION,
            recovery_suggestions=[
                "Check if the palette file exists and is accessible",
                "Verify the palette format is correct",
                "Try creating a new palette",
                "Check file permissions"
            ],
            technical_details={
                "operation": operation,
                "palette_name": palette_name,
                "reason": reason
            }
        )


class ValidationError(ColorPickerError):
    """Raised when input validation fails"""
    
    def __init__(self, field_name: str, value: Any, validation_rule: str):
        super().__init__(
            message=f"Validation failed for {field_name}: {validation_rule}",
            user_message_key="errors.validation_failed",
            severity=ErrorSeverity.LOW,
            category=ErrorCategory.VALIDATION,
            recovery_suggestions=[
                f"Check the {field_name} value",
                "Ensure the input meets the required format",
                "Try with a different value"
            ],
            technical_details={
                "field_name": field_name,
                "value": str(value),
                "validation_rule": validation_rule
            }
        )


class MemoryError(ColorPickerError):
    """Raised when memory-related issues occur"""
    
    def __init__(self, operation: str, memory_usage: int = None, limit: int = None):
        super().__init__(
            message=f"Memory error during {operation}",
            user_message_key="errors.memory_error",
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.MEMORY,
            recovery_suggestions=[
                "Close other applications to free memory",
                "Try with a smaller image",
                "Restart the application",
                "Check available system memory"
            ],
            technical_details={
                "operation": operation,
                "memory_usage": memory_usage,
                "memory_limit": limit
            }
        )


class FileOperationError(ColorPickerError):
    """Raised when file operations fail"""
    
    def __init__(self, operation: str, file_path: str, reason: str = None):
        super().__init__(
            message=f"File operation failed: {operation} on {file_path}",
            user_message_key="errors.file_operation_failed",
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.FILE_OPERATION,
            recovery_suggestions=[
                "Check if the file path is correct",
                "Verify file permissions",
                "Ensure the directory exists",
                "Try with a different location"
            ],
            technical_details={
                "operation": operation,
                "file_path": file_path,
                "reason": reason
            }
        )


class NetworkError(ColorPickerError):
    """Raised when network operations fail"""
    
    def __init__(self, operation: str, url: str = None, reason: str = None):
        super().__init__(
            message=f"Network operation failed: {operation}",
            user_message_key="errors.network_error",
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.NETWORK,
            recovery_suggestions=[
                "Check your internet connection",
                "Try again later",
                "Verify the URL is correct",
                "Check firewall settings"
            ],
            technical_details={
                "operation": operation,
                "url": url,
                "reason": reason
            }
        )


class UIError(ColorPickerError):
    """Raised when UI operations fail"""
    
    def __init__(self, component: str, operation: str, reason: str = None):
        super().__init__(
            message=f"UI error in {component}: {operation}",
            user_message_key="errors.ui_error",
            severity=ErrorSeverity.LOW,
            category=ErrorCategory.UI,
            recovery_suggestions=[
                "Try refreshing the interface",
                "Restart the application",
                "Check if the component is properly initialized"
            ],
            technical_details={
                "component": component,
                "operation": operation,
                "reason": reason
            }
        )


class ConfigurationError(ColorPickerError):
    """Raised when configuration-related issues occur"""
    
    def __init__(self, config_key: str = None, reason: str = None):
        super().__init__(
            message=f"Configuration error: {reason or 'Invalid configuration'}",
            user_message_key="errors.configuration_error",
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.SYSTEM,
            recovery_suggestions=[
                "Check the configuration file",
                "Reset to default configuration",
                "Verify configuration syntax",
                "Check file permissions"
            ],
            technical_details={
                "config_key": config_key,
                "reason": reason
            }
        )


# Error handling utility functions
def handle_error(error: Exception, logger: logging.Logger = None) -> ColorPickerError:
    """
    Handle and convert exceptions to ColorPickerError instances.
    
    Args:
        error: The original exception
        logger: Optional logger for error reporting
        
    Returns:
        ColorPickerError instance
    """
    if isinstance(error, ColorPickerError):
        if logger:
            logger.error(f"ColorPicker error: {error.message}", extra=error.to_dict())
        return error
    
    # Convert common exceptions to ColorPickerError
    if isinstance(error, FileNotFoundError):
        converted_error = FileOperationError(
            operation="file_access",
            file_path=str(error.filename) if error.filename else "unknown",
            reason="File not found"
        )
    elif isinstance(error, PermissionError):
        converted_error = FileOperationError(
            operation="file_access",
            file_path=str(error.filename) if error.filename else "unknown",
            reason="Permission denied"
        )
    elif isinstance(error, MemoryError):
        converted_error = MemoryError(
            operation="memory_allocation",
            reason="Out of memory"
        )
    elif isinstance(error, ValueError):
        converted_error = ValidationError(
            field_name="input_value",
            value=str(error),
            validation_rule="Value validation failed"
        )
    else:
        # Generic error conversion
        converted_error = ColorPickerError(
            message=str(error),
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.SYSTEM,
            original_exception=error
        )
    
    if logger:
        logger.error(f"Converted error: {converted_error.message}", extra=converted_error.to_dict())
    
    return converted_error


def format_error_for_user(error: ColorPickerError, i18n_service=None) -> str:
    """
    Format error message for user display.
    
    Args:
        error: ColorPickerError instance
        i18n_service: Optional internationalization service
        
    Returns:
        User-friendly error message
    """
    if i18n_service:
        try:
            # Try to get localized message
            user_message = i18n_service.translate(
                error.user_message_key,
                **error.technical_details
            )
            if user_message != error.user_message_key:  # Translation found
                return user_message
        except Exception:
            pass  # Fall back to default message
    
    # Default user-friendly messages
    user_messages = {
        "errors.image_load_failed": "Could not load the image file. Please check if the file exists and is a valid image format.",
        "errors.unsupported_format": "This file format is not supported. Please use PNG, JPEG, GIF, BMP, TIFF, WebP, or SVG files.",
        "errors.color_conversion_failed": "Could not convert the color to the requested format. Please try with different color values.",
        "errors.palette_operation_failed": "Could not complete the palette operation. Please check if the file is accessible.",
        "errors.validation_failed": "The input value is not valid. Please check your input and try again.",
        "errors.memory_error": "The operation requires too much memory. Please try with a smaller image or close other applications.",
        "errors.file_operation_failed": "Could not access the file. Please check the file path and permissions.",
        "errors.network_error": "Network operation failed. Please check your internet connection and try again.",
        "errors.ui_error": "A user interface error occurred. Please try refreshing or restarting the application.",
        "errors.configuration_error": "Configuration error occurred. Please check your settings.",
        "errors.generic_error": "An unexpected error occurred. Please try again or contact support."
    }
    
    return user_messages.get(error.user_message_key, error.message)