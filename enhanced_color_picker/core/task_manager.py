"""
Background task management system for heavy operations.

This module provides a centralized task management system that handles
background operations while keeping the UI responsive.
"""

import threading
import time
from concurrent.futures import ThreadPoolExecutor, Future, as_completed
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union
from uuid import uuid4


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class TaskPriority(Enum):
    """Task priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class TaskProgress:
    """Task progress information."""
    current: int = 0
    total: int = 100
    message: str = ""
    
    @property
    def percentage(self) -> float:
        """Get progress as percentage."""
        if self.total == 0:
            return 0.0
        return min(100.0, (self.current / self.total) * 100.0)


@dataclass
class TaskInfo:
    """Information about a background task."""
    task_id: str
    name: str
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.NORMAL
    progress: TaskProgress = field(default_factory=TaskProgress)
    result: Any = None
    error: Optional[Exception] = None
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    future: Optional[Future] = None
    
    @property
    def duration(self) -> Optional[float]:
        """Get task duration in seconds."""
        if self.started_at is None:
            return None
        end_time = self.completed_at or time.time()
        return end_time - self.started_at


class ProgressCallback:
    """Callback interface for task progress updates."""
    
    def __init__(self, task_id: str, task_manager: 'BackgroundTaskManager'):
        self.task_id = task_id
        self.task_manager = task_manager
        self._cancelled = False
    
    def update(self, current: int, total: int = None, message: str = ""):
        """Update task progress."""
        if self._cancelled:
            raise TaskCancelledException(f"Task {self.task_id} was cancelled")
        
        self.task_manager._update_progress(self.task_id, current, total, message)
    
    def is_cancelled(self) -> bool:
        """Check if task was cancelled."""
        return self._cancelled
    
    def _set_cancelled(self):
        """Mark callback as cancelled."""
        self._cancelled = True


class TaskCancelledException(Exception):
    """Exception raised when a task is cancelled."""
    pass


class BackgroundTaskManager:
    """
    Manages background tasks to keep UI responsive.
    
    Features:
    - Thread pool for concurrent execution
    - Progress tracking with callbacks
    - Task cancellation
    - Priority-based scheduling
    - UI responsiveness monitoring
    """
    
    def __init__(self, max_workers: int = 4, ui_check_interval: float = 0.1):
        """
        Initialize task manager.
        
        Args:
            max_workers: Maximum number of worker threads
            ui_check_interval: Interval for UI responsiveness checks (seconds)
        """
        self.max_workers = max_workers
        self.ui_check_interval = ui_check_interval
        
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._tasks: Dict[str, TaskInfo] = {}
        self._task_callbacks: Dict[str, List[Callable]] = {}
        self._progress_callbacks: Dict[str, ProgressCallback] = {}
        self._lock = threading.RLock()
        self._shutdown = False
        
        # UI responsiveness monitoring
        self._ui_monitor_thread = None
        self._last_ui_update = time.time()
        self._ui_freeze_threshold = 0.5  # seconds
        self._ui_callbacks: List[Callable[[float], None]] = []
        
        self._start_ui_monitor()
    
    def submit_task(
        self,
        func: Callable,
        *args,
        name: str = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        progress_callback: Callable[[TaskProgress], None] = None,
        completion_callback: Callable[[TaskInfo], None] = None,
        **kwargs
    ) -> str:
        """
        Submit a task for background execution.
        
        Args:
            func: Function to execute
            *args: Function arguments
            name: Task name for identification
            priority: Task priority
            progress_callback: Callback for progress updates
            completion_callback: Callback when task completes
            **kwargs: Function keyword arguments
        
        Returns:
            Task ID for tracking
        """
        if self._shutdown:
            raise RuntimeError("Task manager is shutting down")
        
        task_id = str(uuid4())
        task_name = name or f"{func.__name__}_{task_id[:8]}"
        
        # Create task info
        task_info = TaskInfo(
            task_id=task_id,
            name=task_name,
            priority=priority
        )
        
        # Create progress callback
        progress_cb = ProgressCallback(task_id, self)
        
        with self._lock:
            self._tasks[task_id] = task_info
            self._task_callbacks[task_id] = []
            self._progress_callbacks[task_id] = progress_cb
            
            if progress_callback:
                self._task_callbacks[task_id].append(
                    lambda info: progress_callback(info.progress)
                )
            
            if completion_callback:
                self._task_callbacks[task_id].append(completion_callback)
        
        # Submit task to executor
        future = self._executor.submit(
            self._execute_task, task_id, func, progress_cb, *args, **kwargs
        )
        
        with self._lock:
            self._tasks[task_id].future = future
        
        return task_id
    
    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a running or pending task.
        
        Args:
            task_id: ID of task to cancel
        
        Returns:
            True if task was cancelled, False otherwise
        """
        with self._lock:
            if task_id not in self._tasks:
                return False
            
            task_info = self._tasks[task_id]
            
            if task_info.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
                return False
            
            # Cancel the future
            if task_info.future and task_info.future.cancel():
                task_info.status = TaskStatus.CANCELLED
                task_info.completed_at = time.time()
                
                # Mark progress callback as cancelled
                if task_id in self._progress_callbacks:
                    self._progress_callbacks[task_id]._set_cancelled()
                
                self._notify_callbacks(task_id)
                return True
            
            # If future couldn't be cancelled, mark progress callback as cancelled
            # so the task can check and exit gracefully
            if task_id in self._progress_callbacks:
                self._progress_callbacks[task_id]._set_cancelled()
                task_info.status = TaskStatus.CANCELLED
                return True
            
            return False
    
    def get_task_info(self, task_id: str) -> Optional[TaskInfo]:
        """Get information about a task."""
        with self._lock:
            return self._tasks.get(task_id)
    
    def get_all_tasks(self) -> List[TaskInfo]:
        """Get information about all tasks."""
        with self._lock:
            return list(self._tasks.values())
    
    def get_running_tasks(self) -> List[TaskInfo]:
        """Get information about currently running tasks."""
        with self._lock:
            return [task for task in self._tasks.values() 
                   if task.status == TaskStatus.RUNNING]
    
    def wait_for_task(self, task_id: str, timeout: float = None) -> Optional[Any]:
        """
        Wait for a task to complete and return its result.
        
        Args:
            task_id: ID of task to wait for
            timeout: Maximum time to wait (seconds)
        
        Returns:
            Task result or None if task failed/cancelled
        """
        task_info = self.get_task_info(task_id)
        if not task_info or not task_info.future:
            return None
        
        try:
            return task_info.future.result(timeout=timeout)
        except Exception:
            return None
    
    def clear_completed_tasks(self):
        """Remove completed, cancelled, and failed tasks from memory."""
        with self._lock:
            completed_ids = [
                task_id for task_id, task_info in self._tasks.items()
                if task_info.status in (TaskStatus.COMPLETED, TaskStatus.CANCELLED, TaskStatus.FAILED)
            ]
            
            for task_id in completed_ids:
                del self._tasks[task_id]
                self._task_callbacks.pop(task_id, None)
                self._progress_callbacks.pop(task_id, None)
    
    def add_ui_responsiveness_callback(self, callback: Callable[[float], None]):
        """
        Add callback for UI responsiveness monitoring.
        
        Args:
            callback: Function called with freeze duration when UI becomes unresponsive
        """
        self._ui_callbacks.append(callback)
    
    def update_ui_timestamp(self):
        """Update timestamp for UI responsiveness monitoring."""
        self._last_ui_update = time.time()
    
    def shutdown(self, wait: bool = True):
        """
        Shutdown the task manager.
        
        Args:
            wait: Whether to wait for running tasks to complete
        """
        self._shutdown = True
        
        # Stop UI monitor
        if self._ui_monitor_thread and self._ui_monitor_thread.is_alive():
            self._ui_monitor_thread.join(timeout=1.0)
        
        # Cancel all pending tasks
        with self._lock:
            for task_id in list(self._tasks.keys()):
                self.cancel_task(task_id)
        
        # Shutdown executor
        self._executor.shutdown(wait=wait)
    
    def _execute_task(
        self, 
        task_id: str, 
        func: Callable, 
        progress_callback: ProgressCallback,
        *args, 
        **kwargs
    ) -> Any:
        """Execute a task with proper error handling and progress tracking."""
        with self._lock:
            if task_id not in self._tasks:
                return None
            
            task_info = self._tasks[task_id]
            task_info.status = TaskStatus.RUNNING
            task_info.started_at = time.time()
        
        try:
            # Execute the function with progress callback
            result = func(progress_callback, *args, **kwargs)
            
            with self._lock:
                task_info.status = TaskStatus.COMPLETED
                task_info.result = result
                task_info.completed_at = time.time()
                task_info.progress.current = task_info.progress.total
                task_info.progress.message = "Completed"
            
            self._notify_callbacks(task_id)
            return result
            
        except TaskCancelledException:
            with self._lock:
                task_info.status = TaskStatus.CANCELLED
                task_info.completed_at = time.time()
                task_info.progress.message = "Cancelled"
            
            self._notify_callbacks(task_id)
            return None
            
        except Exception as e:
            with self._lock:
                task_info.status = TaskStatus.FAILED
                task_info.error = e
                task_info.completed_at = time.time()
                task_info.progress.message = f"Failed: {str(e)}"
            
            self._notify_callbacks(task_id)
            raise
    
    def _update_progress(self, task_id: str, current: int, total: int = None, message: str = ""):
        """Update task progress and notify callbacks."""
        with self._lock:
            if task_id not in self._tasks:
                return
            
            task_info = self._tasks[task_id]
            task_info.progress.current = current
            
            if total is not None:
                task_info.progress.total = total
            
            if message:
                task_info.progress.message = message
        
        self._notify_callbacks(task_id)
    
    def _notify_callbacks(self, task_id: str):
        """Notify all callbacks for a task."""
        with self._lock:
            if task_id not in self._tasks or task_id not in self._task_callbacks:
                return
            
            task_info = self._tasks[task_id]
            callbacks = self._task_callbacks[task_id][:]
        
        # Call callbacks outside of lock to prevent deadlocks
        for callback in callbacks:
            try:
                callback(task_info)
            except Exception:
                # Ignore callback errors to prevent task failure
                pass
    
    def _start_ui_monitor(self):
        """Start UI responsiveness monitoring thread."""
        def monitor_ui():
            while not self._shutdown:
                time.sleep(self.ui_check_interval)
                
                current_time = time.time()
                freeze_duration = current_time - self._last_ui_update
                
                if freeze_duration > self._ui_freeze_threshold:
                    # UI appears frozen, notify callbacks
                    for callback in self._ui_callbacks:
                        try:
                            callback(freeze_duration)
                        except Exception:
                            pass
        
        self._ui_monitor_thread = threading.Thread(target=monitor_ui, daemon=True)
        self._ui_monitor_thread.start()


# Global task manager instance
_task_manager: Optional[BackgroundTaskManager] = None


def get_task_manager() -> BackgroundTaskManager:
    """Get the global task manager instance."""
    global _task_manager
    if _task_manager is None:
        _task_manager = BackgroundTaskManager()
    return _task_manager


def shutdown_task_manager():
    """Shutdown the global task manager."""
    global _task_manager
    if _task_manager is not None:
        _task_manager.shutdown()
        _task_manager = None