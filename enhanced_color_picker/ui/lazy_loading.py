"""
Lazy loading system for UI components to optimize memory usage and startup time.
"""

import threading
import time
import weakref
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Callable, List, Set, Type
from enum import Enum

from ..core.memory_manager import get_memory_manager, MemoryPriority, ResourceType


class LoadingState(Enum):
    """States of lazy-loaded components."""
    NOT_LOADED = "not_loaded"
    LOADING = "loading"
    LOADED = "loaded"
    FAILED = "failed"
    UNLOADED = "unloaded"


@dataclass
class LazyComponentInfo:
    """Information about a lazy-loaded component."""
    component_id: str
    component_type: str
    state: LoadingState = LoadingState.NOT_LOADED
    priority: MemoryPriority = MemoryPriority.NORMAL
    loader_func: Optional[Callable] = None
    unloader_func: Optional[Callable] = None
    dependencies: List[str] = field(default_factory=list)
    last_accessed: float = field(default_factory=time.time)
    load_time: Optional[float] = None
    error: Optional[Exception] = None
    
    def update_access(self):
        """Update last accessed time."""
        self.last_accessed = time.time()


class LazyLoadable(ABC):
    """Abstract base class for lazy-loadable components."""
    
    def __init__(self, component_id: str):
        self.component_id = component_id
        self._loaded = False
        self._loading = False
        self._load_callbacks: List[Callable] = []
        self._unload_callbacks: List[Callable] = []
    
    @abstractmethod
    def _do_load(self) -> bool:
        """
        Perform the actual loading operation.
        
        Returns:
            True if loading was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def _do_unload(self) -> bool:
        """
        Perform the actual unloading operation.
        
        Returns:
            True if unloading was successful, False otherwise
        """
        pass
    
    def is_loaded(self) -> bool:
        """Check if component is loaded."""
        return self._loaded
    
    def is_loading(self) -> bool:
        """Check if component is currently loading."""
        return self._loading
    
    def load(self) -> bool:
        """Load the component if not already loaded."""
        if self._loaded or self._loading:
            return self._loaded
        
        self._loading = True
        try:
            success = self._do_load()
            if success:
                self._loaded = True
                self._notify_load_callbacks()
            return success
        except Exception as e:
            self._loading = False
            raise e
        finally:
            self._loading = False
    
    def unload(self) -> bool:
        """Unload the component if loaded."""
        if not self._loaded:
            return True
        
        try:
            success = self._do_unload()
            if success:
                self._loaded = False
                self._notify_unload_callbacks()
            return success
        except Exception:
            return False
    
    def add_load_callback(self, callback: Callable):
        """Add callback to be called when component is loaded."""
        self._load_callbacks.append(callback)
    
    def add_unload_callback(self, callback: Callable):
        """Add callback to be called when component is unloaded."""
        self._unload_callbacks.append(callback)
    
    def _notify_load_callbacks(self):
        """Notify all load callbacks."""
        for callback in self._load_callbacks:
            try:
                callback(self)
            except Exception:
                pass  # Ignore callback errors
    
    def _notify_unload_callbacks(self):
        """Notify all unload callbacks."""
        for callback in self._unload_callbacks:
            try:
                callback(self)
            except Exception:
                pass  # Ignore callback errors


class LazyUIComponent(LazyLoadable):
    """Base class for lazy-loaded UI components."""
    
    def __init__(
        self,
        component_id: str,
        parent_widget: Any,
        component_class: Type,
        init_args: tuple = (),
        init_kwargs: dict = None
    ):
        super().__init__(component_id)
        self.parent_widget = parent_widget
        self.component_class = component_class
        self.init_args = init_args
        self.init_kwargs = init_kwargs or {}
        self.widget: Optional[Any] = None
    
    def _do_load(self) -> bool:
        """Load the UI component."""
        try:
            # Create the widget instance
            self.widget = self.component_class(
                self.parent_widget,
                *self.init_args,
                **self.init_kwargs
            )
            
            # Register with memory manager
            memory_manager = get_memory_manager()
            memory_manager.register_resource(
                resource_id=f"ui_component:{self.component_id}",
                resource_type=ResourceType.UI_CACHE,
                size_bytes=self._estimate_widget_size(),
                priority=MemoryPriority.HIGH,
                cleanup_callback=self.unload,
                resource_ref=self.widget
            )
            
            return True
        except Exception:
            return False
    
    def _do_unload(self) -> bool:
        """Unload the UI component."""
        try:
            if self.widget:
                # Destroy the widget
                if hasattr(self.widget, 'destroy'):
                    self.widget.destroy()
                elif hasattr(self.widget, 'deleteLater'):
                    self.widget.deleteLater()
                
                # Unregister from memory manager
                memory_manager = get_memory_manager()
                memory_manager.unregister_resource(f"ui_component:{self.component_id}")
                
                self.widget = None
            
            return True
        except Exception:
            return False
    
    def get_widget(self) -> Optional[Any]:
        """Get the widget, loading it if necessary."""
        if not self.is_loaded():
            self.load()
        return self.widget
    
    def _estimate_widget_size(self) -> int:
        """Estimate memory usage of the widget."""
        # Basic estimation - could be improved with actual measurements
        base_size = 1024  # 1KB base
        
        if hasattr(self.widget, 'children'):
            # Add size for child widgets
            child_count = len(getattr(self.widget, 'children', []))
            base_size += child_count * 512
        
        return base_size


class LazyImageComponent(LazyLoadable):
    """Lazy-loaded image component."""
    
    def __init__(
        self,
        component_id: str,
        image_path: str,
        max_size: Optional[tuple] = None
    ):
        super().__init__(component_id)
        self.image_path = image_path
        self.max_size = max_size
        self.image_data: Optional[Any] = None
    
    def _do_load(self) -> bool:
        """Load the image."""
        try:
            from PIL import Image
            from ..utils.image_utils import resize_image_with_quality
            
            # Load image
            image = Image.open(self.image_path)
            
            # Resize if needed
            if self.max_size and (image.width > self.max_size[0] or image.height > self.max_size[1]):
                image = resize_image_with_quality(image, self.max_size)
            
            self.image_data = image
            
            # Register with memory manager
            memory_manager = get_memory_manager()
            image_size = image.width * image.height * len(image.getbands())
            
            memory_manager.register_resource(
                resource_id=f"lazy_image:{self.component_id}",
                resource_type=ResourceType.IMAGE_CACHE,
                size_bytes=image_size,
                priority=MemoryPriority.NORMAL,
                cleanup_callback=self.unload,
                resource_ref=image
            )
            
            return True
        except Exception:
            return False
    
    def _do_unload(self) -> bool:
        """Unload the image."""
        try:
            if self.image_data:
                # Close the image
                if hasattr(self.image_data, 'close'):
                    self.image_data.close()
                
                # Unregister from memory manager
                memory_manager = get_memory_manager()
                memory_manager.unregister_resource(f"lazy_image:{self.component_id}")
                
                self.image_data = None
            
            return True
        except Exception:
            return False
    
    def get_image(self) -> Optional[Any]:
        """Get the image, loading it if necessary."""
        if not self.is_loaded():
            self.load()
        return self.image_data


class LazyLoadingManager:
    """
    Manager for lazy-loaded components with dependency resolution and memory optimization.
    """
    
    def __init__(self):
        self._components: Dict[str, LazyComponentInfo] = {}
        self._loadable_objects: Dict[str, weakref.ref] = {}
        self._lock = threading.RLock()
        
        # Loading queue and worker
        self._loading_queue: List[str] = []
        self._loading_worker: Optional[threading.Thread] = None
        self._shutdown = False
        
        # Statistics
        self._load_count = 0
        self._unload_count = 0
        self._failed_loads = 0
        
        # Memory manager integration
        self._memory_manager = get_memory_manager()
        self._memory_manager.add_memory_warning_callback(self._on_memory_warning)
        
        self._start_loading_worker()
    
    def register_component(
        self,
        component_id: str,
        component_type: str,
        loader_func: Callable,
        unloader_func: Callable = None,
        dependencies: List[str] = None,
        priority: MemoryPriority = MemoryPriority.NORMAL
    ):
        """
        Register a lazy-loadable component.
        
        Args:
            component_id: Unique identifier for the component
            component_type: Type/category of the component
            loader_func: Function to load the component
            unloader_func: Function to unload the component
            dependencies: List of component IDs this component depends on
            priority: Memory priority of the component
        """
        with self._lock:
            info = LazyComponentInfo(
                component_id=component_id,
                component_type=component_type,
                loader_func=loader_func,
                unloader_func=unloader_func,
                dependencies=dependencies or [],
                priority=priority
            )
            
            self._components[component_id] = info
    
    def register_loadable_object(self, obj: LazyLoadable):
        """Register a LazyLoadable object."""
        with self._lock:
            self._loadable_objects[obj.component_id] = weakref.ref(
                obj,
                lambda ref: self._on_object_deleted(obj.component_id)
            )
            
            # Register component info if not already registered
            if obj.component_id not in self._components:
                self.register_component(
                    component_id=obj.component_id,
                    component_type=type(obj).__name__,
                    loader_func=obj.load,
                    unloader_func=obj.unload
                )
    
    def load_component(self, component_id: str, async_load: bool = False) -> bool:
        """
        Load a component and its dependencies.
        
        Args:
            component_id: ID of component to load
            async_load: Whether to load asynchronously
        
        Returns:
            True if loading was successful (or queued for async)
        """
        with self._lock:
            if component_id not in self._components:
                return False
            
            info = self._components[component_id]
            
            if info.state == LoadingState.LOADED:
                info.update_access()
                return True
            
            if info.state == LoadingState.LOADING:
                return True  # Already loading
            
            if async_load:
                # Queue for background loading
                if component_id not in self._loading_queue:
                    self._loading_queue.append(component_id)
                return True
            else:
                # Load synchronously
                return self._load_component_sync(component_id)
    
    def unload_component(self, component_id: str) -> bool:
        """Unload a component."""
        with self._lock:
            if component_id not in self._components:
                return False
            
            info = self._components[component_id]
            
            if info.state != LoadingState.LOADED:
                return True  # Already unloaded
            
            # Check if other components depend on this one
            dependents = self._find_dependents(component_id)
            if dependents:
                # Unload dependents first
                for dependent_id in dependents:
                    self.unload_component(dependent_id)
            
            # Unload the component
            success = self._unload_component_sync(component_id)
            if success:
                self._unload_count += 1
            
            return success
    
    def is_loaded(self, component_id: str) -> bool:
        """Check if a component is loaded."""
        with self._lock:
            if component_id in self._components:
                return self._components[component_id].state == LoadingState.LOADED
            return False
    
    def get_component_info(self, component_id: str) -> Optional[LazyComponentInfo]:
        """Get information about a component."""
        with self._lock:
            return self._components.get(component_id)
    
    def get_all_components(self) -> Dict[str, LazyComponentInfo]:
        """Get information about all components."""
        with self._lock:
            return self._components.copy()
    
    def cleanup_unused_components(self, max_idle_time: float = 300.0):
        """
        Clean up components that haven't been accessed recently.
        
        Args:
            max_idle_time: Maximum idle time in seconds before cleanup
        """
        with self._lock:
            current_time = time.time()
            to_unload = []
            
            for component_id, info in self._components.items():
                if (info.state == LoadingState.LOADED and 
                    info.priority != MemoryPriority.CRITICAL and
                    current_time - info.last_accessed > max_idle_time):
                    to_unload.append(component_id)
            
            for component_id in to_unload:
                self.unload_component(component_id)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get loading statistics."""
        with self._lock:
            loaded_count = sum(1 for info in self._components.values() 
                             if info.state == LoadingState.LOADED)
            loading_count = sum(1 for info in self._components.values() 
                              if info.state == LoadingState.LOADING)
            
            return {
                'total_components': len(self._components),
                'loaded_components': loaded_count,
                'loading_components': loading_count,
                'queued_components': len(self._loading_queue),
                'total_loads': self._load_count,
                'total_unloads': self._unload_count,
                'failed_loads': self._failed_loads
            }
    
    def shutdown(self):
        """Shutdown the lazy loading manager."""
        self._shutdown = True
        
        if self._loading_worker and self._loading_worker.is_alive():
            self._loading_worker.join(timeout=2.0)
        
        # Unload all components
        with self._lock:
            for component_id in list(self._components.keys()):
                self.unload_component(component_id)
    
    def _load_component_sync(self, component_id: str) -> bool:
        """Load component synchronously."""
        info = self._components[component_id]
        info.state = LoadingState.LOADING
        
        try:
            # Load dependencies first
            for dep_id in info.dependencies:
                if not self.load_component(dep_id, async_load=False):
                    info.state = LoadingState.FAILED
                    info.error = Exception(f"Failed to load dependency: {dep_id}")
                    return False
            
            # Load the component
            start_time = time.time()
            
            if info.loader_func:
                success = info.loader_func()
            elif component_id in self._loadable_objects:
                obj_ref = self._loadable_objects[component_id]
                obj = obj_ref()
                if obj:
                    success = obj.load()
                else:
                    success = False
            else:
                success = False
            
            info.load_time = time.time() - start_time
            
            if success:
                info.state = LoadingState.LOADED
                info.update_access()
                self._load_count += 1
            else:
                info.state = LoadingState.FAILED
                self._failed_loads += 1
            
            return success
            
        except Exception as e:
            info.state = LoadingState.FAILED
            info.error = e
            self._failed_loads += 1
            return False
    
    def _unload_component_sync(self, component_id: str) -> bool:
        """Unload component synchronously."""
        info = self._components[component_id]
        
        try:
            if info.unloader_func:
                success = info.unloader_func()
            elif component_id in self._loadable_objects:
                obj_ref = self._loadable_objects[component_id]
                obj = obj_ref()
                if obj:
                    success = obj.unload()
                else:
                    success = True  # Object already gone
            else:
                success = True
            
            if success:
                info.state = LoadingState.UNLOADED
            
            return success
            
        except Exception:
            return False
    
    def _find_dependents(self, component_id: str) -> List[str]:
        """Find components that depend on the given component."""
        dependents = []
        
        for other_id, other_info in self._components.items():
            if component_id in other_info.dependencies:
                dependents.append(other_id)
        
        return dependents
    
    def _start_loading_worker(self):
        """Start background loading worker thread."""
        def loading_worker():
            while not self._shutdown:
                try:
                    with self._lock:
                        if self._loading_queue:
                            component_id = self._loading_queue.pop(0)
                        else:
                            component_id = None
                    
                    if component_id:
                        self._load_component_sync(component_id)
                    else:
                        time.sleep(0.1)  # Wait for work
                        
                except Exception:
                    pass  # Continue working even if errors occur
        
        self._loading_worker = threading.Thread(target=loading_worker, daemon=True)
        self._loading_worker.start()
    
    def _on_memory_warning(self, memory_stats):
        """Handle memory warning by unloading low-priority components."""
        pressure = memory_stats.memory_pressure
        
        if pressure > 0.8:
            # High pressure - unload normal and low priority components
            self._unload_by_priority([MemoryPriority.LOW, MemoryPriority.NORMAL])
        elif pressure > 0.6:
            # Medium pressure - unload low priority components
            self._unload_by_priority([MemoryPriority.LOW])
    
    def _unload_by_priority(self, priorities: List[MemoryPriority]):
        """Unload components with specified priorities."""
        with self._lock:
            to_unload = []
            
            for component_id, info in self._components.items():
                if (info.state == LoadingState.LOADED and 
                    info.priority in priorities):
                    to_unload.append(component_id)
            
            # Sort by last accessed time (oldest first)
            to_unload.sort(key=lambda cid: self._components[cid].last_accessed)
            
            for component_id in to_unload:
                self.unload_component(component_id)
    
    def _on_object_deleted(self, component_id: str):
        """Handle deletion of a loadable object."""
        with self._lock:
            if component_id in self._loadable_objects:
                del self._loadable_objects[component_id]


# Global lazy loading manager instance
_lazy_loading_manager: Optional[LazyLoadingManager] = None


def get_lazy_loading_manager() -> LazyLoadingManager:
    """Get the global lazy loading manager instance."""
    global _lazy_loading_manager
    if _lazy_loading_manager is None:
        _lazy_loading_manager = LazyLoadingManager()
    return _lazy_loading_manager


def shutdown_lazy_loading():
    """Shutdown the lazy loading system."""
    global _lazy_loading_manager
    if _lazy_loading_manager is not None:
        _lazy_loading_manager.shutdown()
        _lazy_loading_manager = None