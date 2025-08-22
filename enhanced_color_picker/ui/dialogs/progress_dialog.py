"""
Progress dialog for displaying background task progress.
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable

from ...core.task_manager import TaskInfo, TaskStatus, BackgroundTaskManager


class ProgressDialog:
    """Dialog for displaying task progress with cancellation support."""
    
    def __init__(
        self, 
        parent: tk.Widget,
        task_manager: BackgroundTaskManager,
        title: str = "Processing...",
        show_details: bool = True,
        allow_cancel: bool = True
    ):
        """
        Initialize progress dialog.
        
        Args:
            parent: Parent widget
            task_manager: Background task manager
            title: Dialog title
            show_details: Whether to show detailed progress info
            allow_cancel: Whether to allow task cancellation
        """
        self.parent = parent
        self.task_manager = task_manager
        self.title = title
        self.show_details = show_details
        self.allow_cancel = allow_cancel
        
        self.dialog: Optional[tk.Toplevel] = None
        self.progress_var = tk.DoubleVar()
        self.status_var = tk.StringVar()
        self.details_var = tk.StringVar()
        
        self.current_task_id: Optional[str] = None
        self.on_cancel: Optional[Callable] = None
        self.on_complete: Optional[Callable] = None
        
        self._cancelled = False
        self._update_job = None
    
    def show_for_task(
        self, 
        task_id: str,
        on_cancel: Callable = None,
        on_complete: Callable = None
    ):
        """
        Show dialog for a specific task.
        
        Args:
            task_id: ID of task to monitor
            on_cancel: Callback when user cancels
            on_complete: Callback when task completes
        """
        self.current_task_id = task_id
        self.on_cancel = on_cancel
        self.on_complete = on_complete
        self._cancelled = False
        
        self._create_dialog()
        self._start_monitoring()
    
    def hide(self):
        """Hide the progress dialog."""
        if self._update_job:
            self.parent.after_cancel(self._update_job)
            self._update_job = None
        
        if self.dialog:
            self.dialog.destroy()
            self.dialog = None
    
    def _create_dialog(self):
        """Create the progress dialog UI."""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title(self.title)
        self.dialog.resizable(False, False)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Center dialog on parent
        self.dialog.geometry("400x150")
        self._center_dialog()
        
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Status label
        status_label = ttk.Label(main_frame, textvariable=self.status_var)
        status_label.pack(pady=(0, 10))
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(
            main_frame,
            variable=self.progress_var,
            maximum=100,
            length=360
        )
        self.progress_bar.pack(pady=(0, 10))
        
        # Details label (if enabled)
        if self.show_details:
            details_label = ttk.Label(
                main_frame, 
                textvariable=self.details_var,
                font=("TkDefaultFont", 8)
            )
            details_label.pack(pady=(0, 10))
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        if self.allow_cancel:
            cancel_button = ttk.Button(
                button_frame,
                text="Cancel",
                command=self._on_cancel_clicked
            )
            cancel_button.pack(side=tk.RIGHT)
        
        # Handle dialog close
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_cancel_clicked)
    
    def _center_dialog(self):
        """Center dialog on parent window."""
        self.dialog.update_idletasks()
        
        # Get parent geometry
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        # Get dialog size
        dialog_width = self.dialog.winfo_reqwidth()
        dialog_height = self.dialog.winfo_reqheight()
        
        # Calculate center position
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        
        self.dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
    
    def _start_monitoring(self):
        """Start monitoring task progress."""
        self._update_progress()
    
    def _update_progress(self):
        """Update progress display."""
        if not self.current_task_id or not self.dialog:
            return
        
        task_info = self.task_manager.get_task_info(self.current_task_id)
        if not task_info:
            self.hide()
            return
        
        # Update progress bar
        self.progress_var.set(task_info.progress.percentage)
        
        # Update status
        status_text = f"{task_info.name}"
        if task_info.status == TaskStatus.RUNNING:
            status_text += f" ({task_info.progress.percentage:.1f}%)"
        elif task_info.status == TaskStatus.COMPLETED:
            status_text += " - Completed"
        elif task_info.status == TaskStatus.CANCELLED:
            status_text += " - Cancelled"
        elif task_info.status == TaskStatus.FAILED:
            status_text += " - Failed"
        
        self.status_var.set(status_text)
        
        # Update details
        if self.show_details:
            details = task_info.progress.message
            if task_info.duration:
                details += f" (Duration: {task_info.duration:.1f}s)"
            self.details_var.set(details)
        
        # Check if task is complete
        if task_info.status in (TaskStatus.COMPLETED, TaskStatus.CANCELLED, TaskStatus.FAILED):
            self.parent.after(1000, self._on_task_complete)  # Show result for 1 second
        else:
            # Schedule next update
            self._update_job = self.parent.after(100, self._update_progress)
    
    def _on_cancel_clicked(self):
        """Handle cancel button click."""
        if self.current_task_id and not self._cancelled:
            self._cancelled = True
            self.task_manager.cancel_task(self.current_task_id)
            
            if self.on_cancel:
                self.on_cancel()
        
        self.hide()
    
    def _on_task_complete(self):
        """Handle task completion."""
        if self.on_complete:
            task_info = self.task_manager.get_task_info(self.current_task_id)
            self.on_complete(task_info)
        
        self.hide()


class MultiTaskProgressDialog:
    """Dialog for monitoring multiple tasks simultaneously."""
    
    def __init__(
        self,
        parent: tk.Widget,
        task_manager: BackgroundTaskManager,
        title: str = "Processing Tasks..."
    ):
        """
        Initialize multi-task progress dialog.
        
        Args:
            parent: Parent widget
            task_manager: Background task manager
            title: Dialog title
        """
        self.parent = parent
        self.task_manager = task_manager
        self.title = title
        
        self.dialog: Optional[tk.Toplevel] = None
        self.task_frames = {}
        self.monitored_tasks = set()
        
        self._update_job = None
    
    def show_for_tasks(self, task_ids: list):
        """
        Show dialog for multiple tasks.
        
        Args:
            task_ids: List of task IDs to monitor
        """
        self.monitored_tasks = set(task_ids)
        self._create_dialog()
        self._start_monitoring()
    
    def add_task(self, task_id: str):
        """Add a task to monitor."""
        self.monitored_tasks.add(task_id)
        if self.dialog:
            self._create_task_frame(task_id)
    
    def remove_task(self, task_id: str):
        """Remove a task from monitoring."""
        self.monitored_tasks.discard(task_id)
        if task_id in self.task_frames:
            self.task_frames[task_id].destroy()
            del self.task_frames[task_id]
    
    def hide(self):
        """Hide the progress dialog."""
        if self._update_job:
            self.parent.after_cancel(self._update_job)
            self._update_job = None
        
        if self.dialog:
            self.dialog.destroy()
            self.dialog = None
        
        self.task_frames.clear()
        self.monitored_tasks.clear()
    
    def _create_dialog(self):
        """Create the multi-task progress dialog UI."""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title(self.title)
        self.dialog.resizable(True, True)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Set minimum size
        self.dialog.minsize(500, 200)
        self.dialog.geometry("500x300")
        self._center_dialog()
        
        # Main frame with scrollbar
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Scrollable frame
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create frames for each task
        for task_id in self.monitored_tasks:
            self._create_task_frame(task_id)
        
        # Close button
        close_button = ttk.Button(self.dialog, text="Close", command=self.hide)
        close_button.pack(pady=(0, 10))
        
        # Handle dialog close
        self.dialog.protocol("WM_DELETE_WINDOW", self.hide)
    
    def _create_task_frame(self, task_id: str):
        """Create UI frame for a single task."""
        task_info = self.task_manager.get_task_info(task_id)
        if not task_info:
            return
        
        # Task frame
        task_frame = ttk.LabelFrame(self.scrollable_frame, text=task_info.name, padding="10")
        task_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Progress bar
        progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(task_frame, variable=progress_var, maximum=100)
        progress_bar.pack(fill=tk.X, pady=(0, 5))
        
        # Status label
        status_var = tk.StringVar()
        status_label = ttk.Label(task_frame, textvariable=status_var)
        status_label.pack(anchor=tk.W)
        
        # Cancel button
        cancel_button = ttk.Button(
            task_frame,
            text="Cancel",
            command=lambda tid=task_id: self._cancel_task(tid)
        )
        cancel_button.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Store references
        self.task_frames[task_id] = {
            'frame': task_frame,
            'progress_var': progress_var,
            'status_var': status_var,
            'cancel_button': cancel_button
        }
    
    def _center_dialog(self):
        """Center dialog on parent window."""
        self.dialog.update_idletasks()
        
        # Get parent geometry
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        # Get dialog size
        dialog_width = self.dialog.winfo_reqwidth()
        dialog_height = self.dialog.winfo_reqheight()
        
        # Calculate center position
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        
        self.dialog.geometry(f"+{x}+{y}")
    
    def _start_monitoring(self):
        """Start monitoring all tasks."""
        self._update_all_progress()
    
    def _update_all_progress(self):
        """Update progress for all monitored tasks."""
        if not self.dialog:
            return
        
        completed_tasks = set()
        
        for task_id in self.monitored_tasks:
            task_info = self.task_manager.get_task_info(task_id)
            if not task_info:
                completed_tasks.add(task_id)
                continue
            
            if task_id in self.task_frames:
                frame_data = self.task_frames[task_id]
                
                # Update progress
                frame_data['progress_var'].set(task_info.progress.percentage)
                
                # Update status
                status = f"{task_info.status.value.title()}"
                if task_info.progress.message:
                    status += f": {task_info.progress.message}"
                frame_data['status_var'].set(status)
                
                # Update cancel button
                if task_info.status in (TaskStatus.COMPLETED, TaskStatus.CANCELLED, TaskStatus.FAILED):
                    frame_data['cancel_button'].configure(state=tk.DISABLED)
                    completed_tasks.add(task_id)
        
        # Remove completed tasks after a delay
        for task_id in completed_tasks:
            self.monitored_tasks.discard(task_id)
        
        # Continue monitoring if there are active tasks
        if self.monitored_tasks:
            self._update_job = self.parent.after(100, self._update_all_progress)
        else:
            # All tasks completed, close dialog after delay
            self.parent.after(2000, self.hide)
    
    def _cancel_task(self, task_id: str):
        """Cancel a specific task."""
        self.task_manager.cancel_task(task_id)
        if task_id in self.task_frames:
            self.task_frames[task_id]['cancel_button'].configure(state=tk.DISABLED)