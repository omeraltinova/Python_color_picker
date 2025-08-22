"""
Enhanced Color Picker - Error Handler

This module provides centralized error handling, logging, and user notification
functionality for the Enhanced Color Picker application.
"""

import logging
import traceback
from typing import Optional, Callable, Dict, Any
from pathlib import Path
import json
from datetime import datetime

from .exceptions import (
    ColorPickerError, ErrorSeverity, ErrorCategory,
    ImageLoadError, UnsupportedFormatError, ColorConversionError,
    PaletteError, ValidationError, MemoryError, FileOperationError,
    NetworkError, UIError
)


class ErrorHandler:
    """
    Centralized error handler for the Enhanced Color Picker application.
    
    Provides error logging, user notification, and graceful degradation
    functionality.
    """
    
    def __init__(self, i18n_service=None, notification_callback: Callable = None):
        self.i18n_service = i18n_service
        self.notification_callback = notification_callback
        self.logger = self._setup_logger()
        self.error_stats = {
            "total_errors": 0,
            "errors_by_category": {},
            "errors_by_severity": {}
        }
        
    def _setup_logger(self) -> logging.Logger:
        """Setup application logger with appropriate handlers"""
        logger = logging.getLogger("enhanced_color_picker")
        logger.setLevel(logging.DEBUG)
        
        # Create logs directory if it doesn't exist
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # File handler for all logs
        file_handler = logging.FileHandler(
            log_dir / f"color_picker_{datetime.now().strftime('%Y%m%d')}.log"
        )
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler for errors and warnings
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
        
    def handle_error(
        self,
        error: Exception,
        context: Dict[str, Any] = None,
        show_to_user: bool = True,
        allow_graceful_degradation: bool = True
    ) -> bool:
        """
        Handle an error with appropriate logging and user notification.
        
        Args:
            error: The exception that occurred
            context: Additional context information
            show_to_user: Whether to show error to user
            allow_graceful_degradation: Whether to attempt graceful degradation
            
        Returns:
            bool: True if error was handled gracefully, False if critical
        """
        context = context or {}
        
        # Convert to ColorPickerError if needed
        if not isinstance(error, ColorPickerError):
            error = self._wrap_generic_error(error, context)
            
        # Log the error
        self._log_error(error, context)
        
        # Update error statistics
        self._update_error_stats(error)
        
        # Show to user if requested
        if show_to_user:
            self._notify_user(error)
            
        # Attempt graceful degradation for non-critical errors
        if allow_graceful_degradation and error.severity != ErrorSeverity.CRITICAL:
            return self._attempt_graceful_degradation(error, context)
            
        return error.severity != ErrorSeverity.CRITICAL
        
    def _wrap_generic_error(self, error: Exception, context: Dict[str, Any]) -> ColorPickerError:
        """Wrap a generic exception in a ColorPickerError"""
        error_type = type(error).__name__
        
        # Map common exceptions to specific ColorPickerError types
        if isinstance(error, (IOError, OSError)):
            file_path = context.get("file_path", "unknown")
            return FileOperationError("file_access", file_path, str(error))
        elif isinstance(error, MemoryError):
            operation = context.get("operation", "unknown")
            return MemoryError(operation)
        elif isinstance(error, ValueError):
            field_name = context.get("field_name", "unknown")
            return ValidationError(field_name, context.get("value", ""), str(error))
        else:
            return ColorPickerError(
                message=f"Unexpected error: {error_type}: {str(error)}",
                user_message_key="errors.unexpected_error",
                severity=ErrorSeverity.MEDIUM,
                category=ErrorCategory.SYSTEM,
                technical_details={"error_type": error_type, "context": context},
                original_exception=error
            )
            
    def _log_error(self, error: ColorPickerError, context: Dict[str, Any]):
        """Log error with appropriate detail level"""
        error_dict = error.to_dict()
        error_dict["context"] = context
        
        # Log based on severity
        if error.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(
                f"CRITICAL ERROR: {error.message}",
                extra={"error_data": error_dict, "stack_trace": traceback.format_exc()}
            )
        elif error.severity == ErrorSeverity.HIGH:
            self.logger.error(
                f"HIGH SEVERITY: {error.message}",
                extra={"error_data": error_dict}
            )
        elif error.severity == ErrorSeverity.MEDIUM:
            self.logger.warning(
                f"MEDIUM SEVERITY: {error.message}",
                extra={"error_data": error_dict}
            )
        else:  # LOW severity
            self.logger.info(
                f"LOW SEVERITY: {error.message}",
                extra={"error_data": error_dict}
            )
            
    def _update_error_stats(self, error: ColorPickerError):
        """Update error statistics"""
        self.error_stats["total_errors"] += 1
        
        # Update category stats
        category = error.category.value
        if category not in self.error_stats["errors_by_category"]:
            self.error_stats["errors_by_category"][category] = 0
        self.error_stats["errors_by_category"][category] += 1
        
        # Update severity stats
        severity = error.severity.value
        if severity not in self.error_stats["errors_by_severity"]:
            self.error_stats["errors_by_severity"][severity] = 0
        self.error_stats["errors_by_severity"][severity] += 1
        
    def _notify_user(self, error: ColorPickerError):
        """Notify user about the error"""
        if not self.notification_callback:
            return
            
        # Get localized message
        user_message = self._get_localized_message(error)
        
        # Prepare notification data
        notification_data = {
            "message": user_message,
            "severity": error.severity.value,
            "recovery_suggestions": self._get_localized_suggestions(error.recovery_suggestions),
            "show_details": error.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]
        }
        
        # Call notification callback
        try:
            self.notification_callback(notification_data)
        except Exception as e:
            self.logger.error(f"Failed to notify user: {e}")
            
    def _get_localized_message(self, error: ColorPickerError) -> str:
        """Get localized error message"""
        if not self.i18n_service:
            return error.message
            
        try:
            # Try to get localized message
            return self.i18n_service.translate(
                error.user_message_key,
                **error.technical_details
            )
        except Exception:
            # Fallback to English or generic message
            return error.message
            
    def _get_localized_suggestions(self, suggestions: list) -> list:
        """Get localized recovery suggestions"""
        if not self.i18n_service or not suggestions:
            return suggestions
            
        localized_suggestions = []
        for suggestion in suggestions:
            try:
                # Try to translate suggestion
                localized = self.i18n_service.translate(f"suggestions.{suggestion}")
                localized_suggestions.append(localized)
            except Exception:
                # Use original suggestion if translation fails
                localized_suggestions.append(suggestion)
                
        return localized_suggestions
        
    def _attempt_graceful_degradation(
        self,
        error: ColorPickerError,
        context: Dict[str, Any]
    ) -> bool:
        """
        Attempt graceful degradation based on error type and context.
        
        Returns:
            bool: True if degradation was successful, False otherwise
        """
        try:
            if isinstance(error, ImageLoadError):
                return self._degrade_image_loading(error, context)
            elif isinstance(error, ColorConversionError):
                return self._degrade_color_conversion(error, context)
            elif isinstance(error, PaletteError):
                return self._degrade_palette_operation(error, context)
            elif isinstance(error, UIError):
                return self._degrade_ui_operation(error, context)
            else:
                return self._generic_degradation(error, context)
        except Exception as degradation_error:
            self.logger.error(f"Graceful degradation failed: {degradation_error}")
            return False
            
    def _degrade_image_loading(self, error: ImageLoadError, context: Dict[str, Any]) -> bool:
        """Handle image loading failures gracefully"""
        # Try to load a default placeholder image
        try:
            placeholder_path = context.get("placeholder_image")
            if placeholder_path and Path(placeholder_path).exists():
                self.logger.info("Using placeholder image due to loading failure")
                return True
        except Exception:
            pass
            
        # Continue without image
        self.logger.info("Continuing without image due to loading failure")
        return True
        
    def _degrade_color_conversion(self, error: ColorConversionError, context: Dict[str, Any]) -> bool:
        """Handle color conversion failures gracefully"""
        # Try alternative conversion method or use default color
        default_color = context.get("default_color", "#000000")
        self.logger.info(f"Using default color {default_color} due to conversion failure")
        return True
        
    def _degrade_palette_operation(self, error: PaletteError, context: Dict[str, Any]) -> bool:
        """Handle palette operation failures gracefully"""
        # Continue with empty palette or default palette
        self.logger.info("Continuing with empty palette due to operation failure")
        return True
        
    def _degrade_ui_operation(self, error: UIError, context: Dict[str, Any]) -> bool:
        """Handle UI operation failures gracefully"""
        # Hide problematic UI component or use simplified version
        component = error.technical_details.get("component", "unknown")
        self.logger.info(f"Hiding component {component} due to UI error")
        return True
        
    def _generic_degradation(self, error: ColorPickerError, context: Dict[str, Any]) -> bool:
        """Generic graceful degradation"""
        # Log and continue
        self.logger.info(f"Continuing despite error: {error.message}")
        return True
        
    def get_error_stats(self) -> Dict[str, Any]:
        """Get current error statistics"""
        return self.error_stats.copy()
        
    def reset_error_stats(self):
        """Reset error statistics"""
        self.error_stats = {
            "total_errors": 0,
            "errors_by_category": {},
            "errors_by_severity": {}
        }
        
    def export_error_log(self, file_path: str) -> bool:
        """Export error statistics and recent logs to file"""
        try:
            export_data = {
                "timestamp": datetime.now().isoformat(),
                "error_stats": self.error_stats,
                "log_file": str(Path("logs") / f"color_picker_{datetime.now().strftime('%Y%m%d')}.log")
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
                
            return True
        except Exception as e:
            self.logger.error(f"Failed to export error log: {e}")
            return False


# Global error handler instance
_error_handler: Optional[ErrorHandler] = None


def get_error_handler() -> ErrorHandler:
    """Get the global error handler instance"""
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler


def initialize_error_handler(i18n_service=None, notification_callback: Callable = None):
    """Initialize the global error handler with services"""
    global _error_handler
    _error_handler = ErrorHandler(i18n_service, notification_callback)


def handle_error(
    error: Exception,
    context: Dict[str, Any] = None,
    show_to_user: bool = True,
    allow_graceful_degradation: bool = True
) -> bool:
    """Convenience function to handle errors using the global handler"""
    return get_error_handler().handle_error(
        error, context, show_to_user, allow_graceful_degradation
    )