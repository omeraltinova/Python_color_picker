"""
Resource cleanup system for proper application shutdown and resource management.
"""

import atexit
import gc
import os
import shutil
import signal
import sys
import tempfile
import threading
import time
import weakref
from pathlib import Path
from typing import Dict, List, Callable, Any, Optional, Set
from dataclasses import dataclass, field
from enum import Enum


class CleanupPriority(Enum):
    """Priority levels for cleanup operations."""
    CRITICAL = 1    # Must be cleaned up (file handles, network connections)
    HIGH = 2        # Important for data integrity (unsaved data, caches)
    NORMAL = 3      # Standard cleanup (temporary files, UI resources)
    LOW = 4         # Nice to have (logs, statistics)


@dataclass
class CleanupTask:
    """A cleanup task to be executed during shutdown."""
    name: str
    cleanup_func: Callable
    priority: CleanupPriority = CleanupPriority.NORMAL
    timeout: float = 5.0
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    
    def execute(self) -> bool:
        """Execute the cleanup task."""
        try:
            self.cleanup_func(*self.args, **self.kwargs)
            return True
        except Exception:
            return False


class ResourceTracker:
    """Tracks resources that need cleanup."""
    
    def __init__(self):
        self._resources: Dict[str, Any] = {}
        self._resource_types: Dict[str, str] = {}
        self._cleanup_callbacks: Dict[str, Callable] = {}
        self._lock = threading.RLock()
    
    def register_resource(
        self,
        resource_id: str,
        resource: Any,
        resource_type: str,
        cleanup_callback: Callable = None
    ):
        """Register a resource for tracking."""
        with self._lock:
            self._resources[resource_id] = weakref.ref(
                resource,
                lambda ref: self._on_resource_deleted(resource_id)
            )
            self._resource_types[resource_id] = resource_type
            
            if cleanup_callback:
                self._cleanup_callbacks[resource_id] = cleanup_callback
    
    def unregister_resource(self, resource_id: str):
        """Unregister a resource."""
        with self._lock:
            self._resources.pop(resource_id, None)
            self._resource_types.pop(resource_id, None)
            self._cleanup_callbacks.pop(resource_id, None)
    
    def get_resources_by_type(self, resource_type: str) -> List[str]:
        """Get all resource IDs of a specific type."""
        with self._lock:
            return [
                resource_id for resource_id, rtype in self._resource_types.items()
                if rtype == resource_type
            ]
    
    def cleanup_resources_by_type(self, resource_type: str) -> int:
        """Clean up all resources of a specific type."""
        resource_ids = self.get_resources_by_type(resource_type)
        cleaned_count = 0
        
        for resource_id in resource_ids:
            if self._cleanup_resource(resource_id):
                cleaned_count += 1
        
        return cleaned_count
    
    def cleanup_all_resources(self) -> int:
        """Clean up all tracked resources."""
        with self._lock:
            resource_ids = list(self._resources.keys())
        
        cleaned_count = 0
        for resource_id in resource_ids:
            if self._cleanup_resource(resource_id):
                cleaned_count += 1
        
        return cleaned_count
    
    def _cleanup_resource(self, resource_id: str) -> bool:
        """Clean up a specific resource."""
        with self._lock:
            if resource_id in self._cleanup_callbacks:
                try:
                    self._cleanup_callbacks[resource_id]()
                    self.unregister_resource(resource_id)
                    return True
                except Exception:
                    return False
            else:
                # No specific cleanup callback, just unregister
                self.unregister_resource(resource_id)
                return True
    
    def _on_resource_deleted(self, resource_id: str):
        """Handle resource deletion via weak reference."""
        self.unregister_resource(resource_id)


class ResourceCleanupManager:
    """
    Comprehensive resource cleanup manager for application shutdown.
    
    Features:
    - Priority-based cleanup ordering
    - Timeout handling for cleanup tasks
    - Signal handling for graceful shutdown
    - Temporary file and directory cleanup
    - Resource tracking and automatic cleanup
    - Thread-safe operations
    """
    
    def __init__(self):
        self._cleanup_tasks: List[CleanupTask] = []
        self._temp_files: Set[str] = set()
        self._temp_dirs: Set[str] = set()
        self._lock = threading.RLock()
        self._shutdown_started = False
        self._resource_tracker = ResourceTracker()
        
        # Statistics
        self._cleanup_stats = {
            'tasks_executed': 0,
            'tasks_failed': 0,
            'resources_cleaned': 0,
            'temp_files_cleaned': 0,
            'temp_dirs_cleaned': 0
        }
        
        # Register signal handlers
        self._register_signal_handlers()
        
        # Register atexit handler
        atexit.register(self.cleanup_all)
    
    def register_cleanup_task(
        self,
        name: str,
        cleanup_func: Callable,
        priority: CleanupPriority = CleanupPriority.NORMAL,
        timeout: float = 5.0,
        *args,
        **kwargs
    ):
        """
        Register a cleanup task.
        
        Args:
            name: Descriptive name for the task
            cleanup_func: Function to call for cleanup
            priority: Priority level for execution order
            timeout: Maximum time to wait for task completion
            *args: Arguments to pass to cleanup function
            **kwargs: Keyword arguments to pass to cleanup function
        """
        with self._lock:
            task = CleanupTask(
                name=name,
                cleanup_func=cleanup_func,
                priority=priority,
                timeout=timeout,
                args=args,
                kwargs=kwargs
            )
            self._cleanup_tasks.append(task)
    
    def register_resource(
        self,
        resource_id: str,
        resource: Any,
        resource_type: str,
        cleanup_callback: Callable = None
    ):
        """Register a resource for automatic cleanup."""
        self._resource_tracker.register_resource(
            resource_id, resource, resource_type, cleanup_callback
        )
    
    def unregister_resource(self, resource_id: str):
        """Unregister a resource."""
        self._resource_tracker.unregister_resource(resource_id)
    
    def add_temp_file(self, file_path: str):
        """Add a temporary file for cleanup."""
        with self._lock:
            self._temp_files.add(str(file_path))
    
    def add_temp_dir(self, dir_path: str):
        """Add a temporary directory for cleanup."""
        with self._lock:
            self._temp_dirs.add(str(dir_path))
    
    def remove_temp_file(self, file_path: str):
        """Remove a temporary file from cleanup list."""
        with self._lock:
            self._temp_files.discard(str(file_path))
    
    def remove_temp_dir(self, dir_path: str):
        """Remove a temporary directory from cleanup list."""
        with self._lock:
            self._temp_dirs.discard(str(dir_path))
    
    def cleanup_temp_files(self) -> int:
        """Clean up all temporary files."""
        with self._lock:
            temp_files = list(self._temp_files)
        
        cleaned_count = 0
        for file_path in temp_files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    cleaned_count += 1
                self._temp_files.discard(file_path)
            except Exception:
                pass  # Ignore cleanup errors
        
        self._cleanup_stats['temp_files_cleaned'] += cleaned_count
        return cleaned_count
    
    def cleanup_temp_dirs(self) -> int:
        """Clean up all temporary directories."""
        with self._lock:
            temp_dirs = list(self._temp_dirs)
        
        cleaned_count = 0
        for dir_path in temp_dirs:
            try:
                if os.path.exists(dir_path):
                    shutil.rmtree(dir_path)
                    cleaned_count += 1
                self._temp_dirs.discard(dir_path)
            except Exception:
                pass  # Ignore cleanup errors
        
        self._cleanup_stats['temp_dirs_cleaned'] += cleaned_count
        return cleaned_count
    
    def cleanup_resources(self) -> int:
        """Clean up all tracked resources."""
        cleaned_count = self._resource_tracker.cleanup_all_resources()
        self._cleanup_stats['resources_cleaned'] += cleaned_count
        return cleaned_count
    
    def cleanup_tasks(self) -> Dict[str, Any]:
        """Execute all cleanup tasks."""
        with self._lock:
            # Sort tasks by priority (critical first)
            sorted_tasks = sorted(self._cleanup_tasks, key=lambda t: t.priority.value)
        
        results = {
            'executed': 0,
            'failed': 0,
            'skipped': 0,
            'details': []
        }
        
        for task in sorted_tasks:
            start_time = time.time()
            
            try:
                # Execute task with timeout
                success = self._execute_task_with_timeout(task)
                execution_time = time.time() - start_time
                
                if success:
                    results['executed'] += 1
                    self._cleanup_stats['tasks_executed'] += 1
                else:
                    results['failed'] += 1
                    self._cleanup_stats['tasks_failed'] += 1
                
                results['details'].append({
                    'name': task.name,
                    'success': success,
                    'execution_time': execution_time,
                    'priority': task.priority.name
                })
                
            except Exception as e:
                results['failed'] += 1
                self._cleanup_stats['tasks_failed'] += 1
                results['details'].append({
                    'name': task.name,
                    'success': False,
                    'error': str(e),
                    'priority': task.priority.name
                })
        
        return results
    
    def cleanup_all(self):
        """Perform complete cleanup of all resources."""
        if self._shutdown_started:
            return  # Avoid multiple cleanup attempts
        
        self._shutdown_started = True
        
        try:
            # 1. Execute cleanup tasks
            task_results = self.cleanup_tasks()
            
            # 2. Clean up tracked resources
            self.cleanup_resources()
            
            # 3. Clean up temporary files and directories
            self.cleanup_temp_files()
            self.cleanup_temp_dirs()
            
            # 4. Force garbage collection
            gc.collect()
            
        except Exception:
            pass  # Ignore errors during shutdown
    
    def force_cleanup(self):
        """Force immediate cleanup (for emergency shutdown)."""
        self._shutdown_started = True
        
        # Quick cleanup without timeouts
        try:
            # Clean up critical resources first
            critical_tasks = [
                task for task in self._cleanup_tasks
                if task.priority == CleanupPriority.CRITICAL
            ]
            
            for task in critical_tasks:
                try:
                    task.execute()
                except Exception:
                    pass
            
            # Clean up resources
            self.cleanup_resources()
            
            # Clean up temp files
            self.cleanup_temp_files()
            self.cleanup_temp_dirs()
            
        except Exception:
            pass
    
    def get_cleanup_stats(self) -> Dict[str, Any]:
        """Get cleanup statistics."""
        with self._lock:
            stats = self._cleanup_stats.copy()
            stats.update({
                'registered_tasks': len(self._cleanup_tasks),
                'temp_files_pending': len(self._temp_files),
                'temp_dirs_pending': len(self._temp_dirs),
                'shutdown_started': self._shutdown_started
            })
            return stats
    
    def _execute_task_with_timeout(self, task: CleanupTask) -> bool:
        """Execute a cleanup task with timeout."""
        if task.timeout <= 0:
            # No timeout, execute directly
            return task.execute()
        
        # Use threading for timeout
        result = [False]  # Mutable container for result
        
        def execute_task():
            result[0] = task.execute()
        
        thread = threading.Thread(target=execute_task)
        thread.daemon = True
        thread.start()
        thread.join(timeout=task.timeout)
        
        if thread.is_alive():
            # Task timed out
            return False
        
        return result[0]
    
    def _register_signal_handlers(self):
        """Register signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            self.cleanup_all()
            sys.exit(0)
        
        # Register handlers for common termination signals
        try:
            signal.signal(signal.SIGTERM, signal_handler)
            signal.signal(signal.SIGINT, signal_handler)
            
            # Windows-specific signals
            if hasattr(signal, 'SIGBREAK'):
                signal.signal(signal.SIGBREAK, signal_handler)
                
        except (OSError, ValueError):
            # Some signals might not be available on all platforms
            pass


class TempFileManager:
    """Manager for temporary files and directories with automatic cleanup."""
    
    def __init__(self, cleanup_manager: ResourceCleanupManager):
        self.cleanup_manager = cleanup_manager
        self._temp_dir = None
    
    def get_temp_dir(self) -> Path:
        """Get or create application temporary directory."""
        if self._temp_dir is None:
            self._temp_dir = Path(tempfile.mkdtemp(prefix="enhanced_color_picker_"))
            self.cleanup_manager.add_temp_dir(str(self._temp_dir))
        
        return self._temp_dir
    
    def create_temp_file(
        self,
        suffix: str = "",
        prefix: str = "temp_",
        dir: Optional[Path] = None
    ) -> Path:
        """Create a temporary file."""
        if dir is None:
            dir = self.get_temp_dir()
        
        # Create temporary file
        fd, temp_path = tempfile.mkstemp(
            suffix=suffix,
            prefix=prefix,
            dir=str(dir)
        )
        os.close(fd)  # Close file descriptor
        
        temp_file = Path(temp_path)
        self.cleanup_manager.add_temp_file(str(temp_file))
        
        return temp_file
    
    def create_temp_dir(
        self,
        suffix: str = "",
        prefix: str = "temp_",
        dir: Optional[Path] = None
    ) -> Path:
        """Create a temporary directory."""
        if dir is None:
            dir = self.get_temp_dir()
        
        temp_dir = Path(tempfile.mkdtemp(
            suffix=suffix,
            prefix=prefix,
            dir=str(dir)
        ))
        
        self.cleanup_manager.add_temp_dir(str(temp_dir))
        return temp_dir


# Global cleanup manager instance
_cleanup_manager: Optional[ResourceCleanupManager] = None
_temp_file_manager: Optional[TempFileManager] = None


def get_cleanup_manager() -> ResourceCleanupManager:
    """Get the global cleanup manager instance."""
    global _cleanup_manager
    if _cleanup_manager is None:
        _cleanup_manager = ResourceCleanupManager()
    return _cleanup_manager


def get_temp_file_manager() -> TempFileManager:
    """Get the global temporary file manager instance."""
    global _temp_file_manager
    if _temp_file_manager is None:
        _temp_file_manager = TempFileManager(get_cleanup_manager())
    return _temp_file_manager


def register_cleanup_task(
    name: str,
    cleanup_func: Callable,
    priority: CleanupPriority = CleanupPriority.NORMAL,
    timeout: float = 5.0,
    *args,
    **kwargs
):
    """Register a cleanup task with the global cleanup manager."""
    cleanup_manager = get_cleanup_manager()
    cleanup_manager.register_cleanup_task(
        name, cleanup_func, priority, timeout, *args, **kwargs
    )


def register_resource(
    resource_id: str,
    resource: Any,
    resource_type: str,
    cleanup_callback: Callable = None
):
    """Register a resource with the global cleanup manager."""
    cleanup_manager = get_cleanup_manager()
    cleanup_manager.register_resource(
        resource_id, resource, resource_type, cleanup_callback
    )


def cleanup_on_exit():
    """Perform cleanup on application exit."""
    cleanup_manager = get_cleanup_manager()
    cleanup_manager.cleanup_all()