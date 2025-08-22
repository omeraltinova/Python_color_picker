"""
Enhanced Color Picker - Error Notification Component

This module provides user-friendly error notification components for displaying
errors, warnings, and recovery suggestions to users.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, Optional, List
from enum import Enum
import threading
import time

from ...core.exceptions import ErrorSeverity


class NotificationType(Enum):
    """Types of notifications"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    SUCCESS = "success"


class ErrorNotificationManager:
    """
    Manages error notifications and user-friendly error display.
    
    Provides various notification methods including toast notifications,
    modal dialogs, and status bar messages.
    """
    
    def __init__(self, parent_window: tk.Tk, i18n_service=None):
        self.parent_window = parent_window
        self.i18n_service = i18n_service
        self.active_notifications = []
        self.notification_queue = []
        self.max_concurrent_notifications = 3
        
    def show_error_notification(self, notification_data: Dict[str, Any]):
        """
        Show error notification to user based on severity and type.
        
        Args:
            notification_data: Dictionary containing notification information
        """
        severity = notification_data.get("severity", "medium")
        message = notification_data.get("message", "An error occurred")
        recovery_suggestions = notification_data.get("recovery_suggestions", [])
        show_details = notification_data.get("show_details", False)
        
        if severity == ErrorSeverity.CRITICAL.value:
            self._show_critical_error_dialog(message, recovery_suggestions)
        elif severity == ErrorSeverity.HIGH.value:
            self._show_error_dialog(message, recovery_suggestions, show_details)
        elif severity == ErrorSeverity.MEDIUM.value:
            self._show_warning_toast(message, recovery_suggestions)
        else:  # LOW severity
            self._show_info_toast(message)
            
    def _show_critical_error_dialog(self, message: str, suggestions: List[str]):
        """Show critical error dialog with application restart option"""
        dialog = CriticalErrorDialog(
            self.parent_window,
            message,
            suggestions,
            self.i18n_service
        )
        result = dialog.show()
        
        if result == "restart":
            self._restart_application()
        elif result == "exit":
            self.parent_window.quit()
            
    def _show_error_dialog(self, message: str, suggestions: List[str], show_details: bool):
        """Show error dialog with recovery options"""
        dialog = ErrorDialog(
            self.parent_window,
            message,
            suggestions,
            show_details,
            self.i18n_service
        )
        dialog.show()
        
    def _show_warning_toast(self, message: str, suggestions: List[str]):
        """Show warning toast notification"""
        if len(self.active_notifications) >= self.max_concurrent_notifications:
            self.notification_queue.append({
                "type": NotificationType.WARNING,
                "message": message,
                "suggestions": suggestions
            })
            return
            
        toast = ToastNotification(
            self.parent_window,
            message,
            NotificationType.WARNING,
            suggestions,
            self.i18n_service
        )
        self.active_notifications.append(toast)
        toast.show(callback=lambda: self._remove_notification(toast))
        
    def _show_info_toast(self, message: str):
        """Show info toast notification"""
        if len(self.active_notifications) >= self.max_concurrent_notifications:
            self.notification_queue.append({
                "type": NotificationType.INFO,
                "message": message,
                "suggestions": []
            })
            return
            
        toast = ToastNotification(
            self.parent_window,
            message,
            NotificationType.INFO,
            [],
            self.i18n_service
        )
        self.active_notifications.append(toast)
        toast.show(callback=lambda: self._remove_notification(toast))
        
    def _remove_notification(self, notification):
        """Remove notification and process queue"""
        if notification in self.active_notifications:
            self.active_notifications.remove(notification)
            
        # Process queued notifications
        if self.notification_queue and len(self.active_notifications) < self.max_concurrent_notifications:
            queued = self.notification_queue.pop(0)
            if queued["type"] == NotificationType.WARNING:
                self._show_warning_toast(queued["message"], queued["suggestions"])
            elif queued["type"] == NotificationType.INFO:
                self._show_info_toast(queued["message"])
                
    def _restart_application(self):
        """Restart the application"""
        # This would be implemented based on the application's restart mechanism
        import sys
        import os
        
        try:
            # Save any critical data before restart
            self.parent_window.quit()
            
            # Restart the application
            python = sys.executable
            os.execl(python, python, *sys.argv)
        except Exception as e:
            messagebox.showerror(
                "Restart Failed",
                f"Failed to restart application: {e}\nPlease restart manually."
            )
            self.parent_window.quit()
            
    def show_success_notification(self, message: str):
        """Show success notification"""
        toast = ToastNotification(
            self.parent_window,
            message,
            NotificationType.SUCCESS,
            [],
            self.i18n_service
        )
        self.active_notifications.append(toast)
        toast.show(callback=lambda: self._remove_notification(toast))
        
    def clear_all_notifications(self):
        """Clear all active notifications"""
        for notification in self.active_notifications[:]:
            notification.close()
        self.active_notifications.clear()
        self.notification_queue.clear()


class CriticalErrorDialog:
    """Critical error dialog with restart/exit options"""
    
    def __init__(self, parent: tk.Tk, message: str, suggestions: List[str], i18n_service=None):
        self.parent = parent
        self.message = message
        self.suggestions = suggestions
        self.i18n_service = i18n_service
        self.result = None
        self.dialog = None
        
    def show(self) -> str:
        """Show the critical error dialog and return user choice"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Critical Error" if not self.i18n_service else 
                         self.i18n_service.translate("errors.critical_error_title"))
        self.dialog.geometry("500x400")
        self.dialog.resizable(False, False)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.geometry("+%d+%d" % (
            self.parent.winfo_rootx() + 50,
            self.parent.winfo_rooty() + 50
        ))
        
        self._create_widgets()
        
        # Wait for user response
        self.dialog.wait_window()
        return self.result
        
    def _create_widgets(self):
        """Create dialog widgets"""
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Error icon and title
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 20))
        
        title_label = ttk.Label(
            title_frame,
            text="Critical Error Occurred",
            font=("TkDefaultFont", 12, "bold"),
            foreground="red"
        )
        title_label.pack()
        
        # Error message
        message_frame = ttk.LabelFrame(main_frame, text="Error Details", padding="10")
        message_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        message_text = tk.Text(
            message_frame,
            height=6,
            wrap=tk.WORD,
            state=tk.DISABLED,
            background=self.dialog.cget("bg")
        )
        message_text.pack(fill=tk.BOTH, expand=True)
        
        message_text.config(state=tk.NORMAL)
        message_text.insert(tk.END, self.message)
        message_text.config(state=tk.DISABLED)
        
        # Recovery suggestions
        if self.suggestions:
            suggestions_frame = ttk.LabelFrame(main_frame, text="Recovery Suggestions", padding="10")
            suggestions_frame.pack(fill=tk.X, pady=(0, 20))
            
            for i, suggestion in enumerate(self.suggestions, 1):
                suggestion_label = ttk.Label(
                    suggestions_frame,
                    text=f"{i}. {suggestion}",
                    wraplength=450
                )
                suggestion_label.pack(anchor=tk.W, pady=2)
                
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        restart_button = ttk.Button(
            button_frame,
            text="Restart Application",
            command=self._restart_clicked
        )
        restart_button.pack(side=tk.RIGHT, padx=(10, 0))
        
        exit_button = ttk.Button(
            button_frame,
            text="Exit Application",
            command=self._exit_clicked
        )
        exit_button.pack(side=tk.RIGHT)
        
    def _restart_clicked(self):
        """Handle restart button click"""
        self.result = "restart"
        self.dialog.destroy()
        
    def _exit_clicked(self):
        """Handle exit button click"""
        self.result = "exit"
        self.dialog.destroy()


class ErrorDialog:
    """Standard error dialog with recovery suggestions"""
    
    def __init__(self, parent: tk.Tk, message: str, suggestions: List[str], 
                 show_details: bool, i18n_service=None):
        self.parent = parent
        self.message = message
        self.suggestions = suggestions
        self.show_details = show_details
        self.i18n_service = i18n_service
        
    def show(self):
        """Show the error dialog"""
        dialog = tk.Toplevel(self.parent)
        dialog.title("Error" if not self.i18n_service else 
                    self.i18n_service.translate("errors.error_title"))
        dialog.geometry("400x300")
        dialog.resizable(True, True)
        dialog.transient(self.parent)
        
        # Center the dialog
        dialog.geometry("+%d+%d" % (
            self.parent.winfo_rootx() + 100,
            self.parent.winfo_rooty() + 100
        ))
        
        main_frame = ttk.Frame(dialog, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Error message
        message_label = ttk.Label(
            main_frame,
            text=self.message,
            wraplength=350,
            justify=tk.LEFT
        )
        message_label.pack(anchor=tk.W, pady=(0, 15))
        
        # Recovery suggestions
        if self.suggestions:
            suggestions_frame = ttk.LabelFrame(main_frame, text="What you can try:", padding="10")
            suggestions_frame.pack(fill=tk.X, pady=(0, 15))
            
            for suggestion in self.suggestions:
                suggestion_label = ttk.Label(
                    suggestions_frame,
                    text=f"• {suggestion}",
                    wraplength=320,
                    justify=tk.LEFT
                )
                suggestion_label.pack(anchor=tk.W, pady=2)
                
        # OK button
        ok_button = ttk.Button(
            main_frame,
            text="OK",
            command=dialog.destroy
        )
        ok_button.pack(pady=(10, 0))


class ToastNotification:
    """Toast notification for non-critical messages"""
    
    def __init__(self, parent: tk.Tk, message: str, notification_type: NotificationType,
                 suggestions: List[str], i18n_service=None):
        self.parent = parent
        self.message = message
        self.notification_type = notification_type
        self.suggestions = suggestions
        self.i18n_service = i18n_service
        self.toast_window = None
        self.auto_close_timer = None
        
    def show(self, duration: int = 5000, callback=None):
        """Show toast notification"""
        self.toast_window = tk.Toplevel(self.parent)
        self.toast_window.withdraw()  # Hide initially
        
        # Configure window
        self.toast_window.overrideredirect(True)
        self.toast_window.attributes("-topmost", True)
        
        # Create content
        self._create_content()
        
        # Position toast
        self._position_toast()
        
        # Show with animation
        self.toast_window.deiconify()
        self._animate_in()
        
        # Auto close timer
        if duration > 0:
            self.auto_close_timer = self.toast_window.after(
                duration,
                lambda: self.close(callback)
            )
            
    def _create_content(self):
        """Create toast content"""
        # Color scheme based on notification type
        colors = {
            NotificationType.ERROR: {"bg": "#ffebee", "fg": "#c62828", "border": "#f44336"},
            NotificationType.WARNING: {"bg": "#fff3e0", "fg": "#ef6c00", "border": "#ff9800"},
            NotificationType.INFO: {"bg": "#e3f2fd", "fg": "#1565c0", "border": "#2196f3"},
            NotificationType.SUCCESS: {"bg": "#e8f5e8", "fg": "#2e7d32", "border": "#4caf50"}
        }
        
        color_scheme = colors.get(self.notification_type, colors[NotificationType.INFO])
        
        # Main frame
        main_frame = tk.Frame(
            self.toast_window,
            bg=color_scheme["bg"],
            relief=tk.SOLID,
            bd=1,
            highlightbackground=color_scheme["border"],
            highlightthickness=2
        )
        main_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Message
        message_label = tk.Label(
            main_frame,
            text=self.message,
            bg=color_scheme["bg"],
            fg=color_scheme["fg"],
            wraplength=300,
            justify=tk.LEFT,
            font=("TkDefaultFont", 9)
        )
        message_label.pack(anchor=tk.W, padx=10, pady=(10, 5))
        
        # Suggestions (if any)
        if self.suggestions:
            for suggestion in self.suggestions[:2]:  # Show max 2 suggestions in toast
                suggestion_label = tk.Label(
                    main_frame,
                    text=f"• {suggestion}",
                    bg=color_scheme["bg"],
                    fg=color_scheme["fg"],
                    wraplength=280,
                    justify=tk.LEFT,
                    font=("TkDefaultFont", 8)
                )
                suggestion_label.pack(anchor=tk.W, padx=15, pady=1)
                
        # Close button
        close_button = tk.Button(
            main_frame,
            text="×",
            bg=color_scheme["bg"],
            fg=color_scheme["fg"],
            relief=tk.FLAT,
            font=("TkDefaultFont", 12, "bold"),
            command=self.close,
            cursor="hand2"
        )
        close_button.pack(anchor=tk.NE, padx=5, pady=5)
        
    def _position_toast(self):
        """Position toast in bottom-right corner"""
        self.toast_window.update_idletasks()
        
        toast_width = self.toast_window.winfo_reqwidth()
        toast_height = self.toast_window.winfo_reqheight()
        
        screen_width = self.parent.winfo_screenwidth()
        screen_height = self.parent.winfo_screenheight()
        
        x = screen_width - toast_width - 20
        y = screen_height - toast_height - 60
        
        self.toast_window.geometry(f"+{x}+{y}")
        
    def _animate_in(self):
        """Simple fade-in animation"""
        # This is a simplified animation - could be enhanced with more sophisticated effects
        self.toast_window.attributes("-alpha", 0.0)
        self._fade_in(0.0)
        
    def _fade_in(self, alpha):
        """Fade in animation"""
        if alpha < 1.0:
            alpha += 0.1
            self.toast_window.attributes("-alpha", alpha)
            self.toast_window.after(50, lambda: self._fade_in(alpha))
            
    def close(self, callback=None):
        """Close toast notification"""
        if self.auto_close_timer:
            self.toast_window.after_cancel(self.auto_close_timer)
            
        if self.toast_window and self.toast_window.winfo_exists():
            self.toast_window.destroy()
            
        if callback:
            callback()


# Global notification manager instance
_notification_manager: Optional[ErrorNotificationManager] = None


def get_notification_manager() -> Optional[ErrorNotificationManager]:
    """Get the global notification manager instance"""
    return _notification_manager


def initialize_notification_manager(parent_window: tk.Tk, i18n_service=None):
    """Initialize the global notification manager"""
    global _notification_manager
    _notification_manager = ErrorNotificationManager(parent_window, i18n_service)


def show_error_notification(notification_data: Dict[str, Any]):
    """Convenience function to show error notification"""
    if _notification_manager:
        _notification_manager.show_error_notification(notification_data)


def show_success_notification(message: str):
    """Convenience function to show success notification"""
    if _notification_manager:
        _notification_manager.show_success_notification(message)