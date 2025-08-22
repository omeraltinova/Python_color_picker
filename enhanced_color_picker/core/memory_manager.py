"""
Memory and resource management system for optimal performance.

This module provides intelligent memory management, garbage collection,
and resource cleanup to ensure optimal application performance.
"""

import gc
import os
import psutil
import threading
import time
import weakref
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any, Set
from collections import defaultdict
from enum import Enum


class MemoryPriority(Enum):
    """Memory priority levels for resource management."""
    CRITICAL = 1    # Essential for app functionality
    HIGH = 2        # Important for user experience
    NORMAL = 3      # Standard cached data
    LOW = 4         # Nice to have, first to be cleaned


class ResourceType(Enum):
    """Types of resources being managed."""
    IMAGE_CACHE = "image_cache"
    COLOR_CACHE = "color_cache"
    PALETTE_CACHE = "palette_cache"
    UI_CACHE = "ui_cache"
    TEMP_FILES = "temp_files"
    ANALYSIS_CACHE = "analysis_cache"


@dataclass
class MemoryStats:
    """Memory usage statistics."""
    total_memory: int = 0           # Total system memory (bytes)
    available_memory: int = 0       # Available system memory (bytes)
    process_memory: int = 0         # Current process memory usage (bytes)
    memory_percent: float = 0.0     # Process memory as % of total
    cached_memory: int = 0          # Memory used by caches (bytes)
    
    @property
    def memory_pressure(self) -> float:
        """Calculate memory pressure (0.0 = no pressure, 1.0 = critical)."""
        if self.total_memory == 0:
            return 0.0
        return min(1.0, self.process_memory / (self.available_memory + self.process_memory))
            return 0.0
        
        # Consider both system and process memory usage
        system_pressure = 1.0 - (self.available_memory / self.total_memory)
        process_pressure = self.memory_percent / 100.0
        
        # Return the higher pressure
        return max(system_pressure, process_pressure)


@dataclass
class ResourceInfo:
    """Information about a managed resource."""
    resource_id: str
    resource_type: ResourceType
    priority: MemoryPriority
    size_bytes: int
    last_accessed: float = field(default_factory=time.time)
    access_count: int = 0
    cleanup_callback: Optional[Callable] = None
    
    def update_access(self):
        """Update access statistics."""
        self.last_accessed = time.time()
        self.access_count += 1


class MemoryManager:
    """
    Intelligent memory and resource management system.
    
    Features:
    - Memory usage monitoring and alerts
    - Intelligent garbage collection
    - Resource cleanup with priority-based eviction
    - Lazy loading support
    - Memory pressure detection
    """
    
    def __init__(
        self,
        memory_limit_mb: int = 512,
        cache_limit_mb: int = 256,
        cleanup_threshold: float = 0.8,
        monitor_interval: float = 5.0
    ):
        """
        Initialize memory manager.
        
        Args:
            memory_limit_mb: Maximum memory usage for the process (MB)
            cache_limit_mb: Maximum memory for caches (MB)
            cleanup_threshold: Memory usage threshold to trigger cleanup (0.0-1.0)
            monitor_interval: Monitoring interval in seconds
        """
        self.memory_limit_bytes = memory_limit_mb * 1024 * 1024
        self.cache_limit_bytes = cache_limit_mb * 1024 * 1024
        self.cleanup_threshold = cleanup_threshold
        self.monitor_interval = monitor_interval
        
        # Resource tracking
        self._resources: Dict[str, ResourceInfo] = {}
        self._resource_refs: Dict[str, weakref.ref] = {}
        self._resource_locks: Dict[ResourceType, threading.RLock] = defaultdict(threading.RLock)
        self._total_cache_size = 0
        
        # Monitoring
        self._monitor_thread: Optional[threading.Thread] = None
        self._shutdown = False
        self._stats = MemoryStats()
        
        # Callbacks
        self._memory_warning_callbacks: List[Callable[[MemoryStats], None]] = []
        self._cleanup_callbacks: List[Callable[[ResourceType, int], None]] = []
        
        # Lazy loading registry
        self._lazy_loaders: Dict[str, Callable] = {}
        self._loaded_resources: Set[str] = set()
        
        self._start_monitoring()
    
    def register_resource(
        self,
        resource_id: str,
        resource_type: ResourceType,
        size_bytes: int,
        priority: MemoryPriority = MemoryPriority.NORMAL,
        cleanup_callback: Callable = None,
        resource_ref: Any = None
    ):
        """
        Register a resource for memory management.
        
        Args:
            resource_id: Unique identifier for the resource
            resource_type: Type of resource
            size_bytes: Size of resource in bytes
            priority: Memory priority level
            cleanup_callback: Function to call when resource is cleaned up
            resource_ref: Weak reference to the actual resource object
        """
        with self._resource_locks[resource_type]:
            resource_info = ResourceInfo(
                resource_id=resource_id,
                resource_type=resource_type,
                priority=priority,
                size_bytes=size_bytes,
                cleanup_callback=cleanup_callback
            )
            
            self._resources[resource_id] = resource_info
            self._total_cache_size += size_bytes
            
            # Store weak reference if provided
            if resource_ref is not None:
                self._resource_refs[resource_id] = weakref.ref(
                    resource_ref,
                    lambda ref: self._on_resource_deleted(resource_id)
                )
    
    def unregister_resource(self, resource_id: str):
        """Unregister a resource from memory management."""
        if resource_id in self._resources:
            resource_info = self._resources[resource_id]
            
            with self._resource_locks[resource_info.resource_type]:
                self._total_cache_size -= resource_info.size_bytes
                del self._resources[resource_id]
                
                if resource_id in self._resource_refs:
                    del self._resource_refs[resource_id]
    
    def access_resource(self, resource_id: str):
        """Mark a resource as accessed (for LRU tracking)."""
        if resource_id in self._resources:
            self._resources[resource_id].update_access()
    
    def get_memory_stats(self) -> MemoryStats:
        """Get current memory usage statistics."""
        try:
            # Get system memory info
            memory = psutil.virtual_memory()
            process = psutil.Process()
            process_memory = process.memory_info()
            
            self._stats = MemoryStats(
                total_memory=memory.total,
                available_memory=memory.available,
                process_memory=process_memory.rss,
                memory_percent=process.memory_percent(),
                cached_memory=self._total_cache_size
            )
            
        except Exception:
            # Fallback if psutil fails
            pass
        
        return self._stats
    
    def check_memory_pressure(self) -> float:
        """Check current memory pressure level."""
        stats = self.get_memory_stats()
        return stats.memory_pressure
    
    def cleanup_resources(
        self,
        target_bytes: int = None,
        resource_types: List[ResourceType] = None,
        force: bool = False
    ) -> int:
        """
        Clean up resources to free memory.
        
        Args:
            target_bytes: Target amount of memory to free
            resource_types: Specific resource types to clean up
            force: Force cleanup regardless of priority
        
        Returns:
            Amount of memory freed in bytes
        """
        if target_bytes is None:
            # Default to freeing 25% of cache
            target_bytes = self._total_cache_size // 4
        
        if resource_types is None:
            resource_types = list(ResourceType)
        
        freed_bytes = 0
        resources_to_remove = []
        
        # Sort resources by cleanup priority (LRU + priority)
        cleanup_candidates = []
        
        for resource_id, resource_info in self._resources.items():
            if resource_info.resource_type in resource_types:
                # Calculate cleanup score (higher = clean up first)
                age_score = time.time() - resource_info.last_accessed
                priority_score = resource_info.priority.value * 1000
                access_score = max(1, resource_info.access_count)
                
                cleanup_score = (age_score + priority_score) / access_score
                
                cleanup_candidates.append((cleanup_score, resource_id, resource_info))
        
        # Sort by cleanup score (highest first)
        cleanup_candidates.sort(reverse=True)
        
        # Clean up resources until target is reached
        for cleanup_score, resource_id, resource_info in cleanup_candidates:
            if freed_bytes >= target_bytes and not force:
                break
            
            # Skip critical resources unless forced
            if resource_info.priority == MemoryPriority.CRITICAL and not force:
                continue
            
            # Call cleanup callback if provided
            if resource_info.cleanup_callback:
                try:
                    resource_info.cleanup_callback()
                except Exception:
                    pass  # Ignore cleanup errors
            
            # Mark for removal
            resources_to_remove.append(resource_id)
            freed_bytes += resource_info.size_bytes
            
            # Notify cleanup callbacks
            for callback in self._cleanup_callbacks:
                try:
                    callback(resource_info.resource_type, resource_info.size_bytes)
                except Exception:
                    pass
        
        # Remove cleaned up resources
        for resource_id in resources_to_remove:
            self.unregister_resource(resource_id)
        
        return freed_bytes
    
    def force_garbage_collection(self):
        """Force garbage collection and return collected objects count."""
        # Clear weak references to deleted objects
        dead_refs = []
        for resource_id, ref in self._resource_refs.items():
            if ref() is None:
                dead_refs.append(resource_id)
        
        for resource_id in dead_refs:
            self.unregister_resource(resource_id)
        
        # Force garbage collection
        collected = gc.collect()
        
        return collected
    
    def register_lazy_loader(self, resource_id: str, loader_func: Callable):
        """
        Register a lazy loader for a resource.
        
        Args:
            resource_id: Unique identifier for the resource
            loader_func: Function to call when resource is needed
        """
        self._lazy_loaders[resource_id] = loader_func
    
    def load_resource_lazy(self, resource_id: str) -> Any:
        """
        Load a resource using its lazy loader.
        
        Args:
            resource_id: ID of resource to load
        
        Returns:
            Loaded resource or None if not found
        """
        if resource_id in self._loaded_resources:
            # Already loaded, just mark as accessed
            self.access_resource(resource_id)
            return None
        
        if resource_id in self._lazy_loaders:
            try:
                # Load the resource
                resource = self._lazy_loaders[resource_id]()
                self._loaded_resources.add(resource_id)
                self.access_resource(resource_id)
                return resource
            except Exception:
                return None
        
        return None
    
    def add_memory_warning_callback(self, callback: Callable[[MemoryStats], None]):
        """Add callback for memory warning notifications."""
        self._memory_warning_callbacks.append(callback)
    
    def add_cleanup_callback(self, callback: Callable[[ResourceType, int], None]):
        """Add callback for resource cleanup notifications."""
        self._cleanup_callbacks.append(callback)
    
    def get_resource_summary(self) -> Dict[ResourceType, Dict[str, Any]]:
        """Get summary of managed resources by type."""
        summary = defaultdict(lambda: {
            'count': 0,
            'total_size': 0,
            'avg_size': 0,
            'oldest_access': time.time(),
            'newest_access': 0
        })
        
        for resource_info in self._resources.values():
            res_type = resource_info.resource_type
            summary[res_type]['count'] += 1
            summary[res_type]['total_size'] += resource_info.size_bytes
            summary[res_type]['oldest_access'] = min(
                summary[res_type]['oldest_access'],
                resource_info.last_accessed
            )
            summary[res_type]['newest_access'] = max(
                summary[res_type]['newest_access'],
                resource_info.last_accessed
            )
        
        # Calculate averages
        for res_type in summary:
            if summary[res_type]['count'] > 0:
                summary[res_type]['avg_size'] = (
                    summary[res_type]['total_size'] / summary[res_type]['count']
                )
        
        return dict(summary)
    
    def optimize_memory_usage(self) -> Dict[str, Any]:
        """
        Perform comprehensive memory optimization.
        
        Returns:
            Optimization results and statistics
        """
        optimization_start = time.time()
        initial_stats = self.get_memory_stats()
        
        optimization_results = {
            'initial_memory': initial_stats.process_memory,
            'initial_cached': initial_stats.cached_memory,
            'optimizations_applied': [],
            'memory_freed': 0,
            'optimization_time': 0
        }
        
        # 1. Force garbage collection
        collected_objects = gc.collect()
        if collected_objects > 0:
            optimization_results['optimizations_applied'].append(f"Garbage collection: {collected_objects} objects")
        
        # 2. Clean up expired resources
        expired_cleaned = self._cleanup_expired_resources()
        if expired_cleaned > 0:
            optimization_results['optimizations_applied'].append(f"Expired resources: {expired_cleaned} items")
        
        # 3. Apply memory pressure-based cleanup
        memory_pressure = self.check_memory_pressure()
        if memory_pressure > 0.7:  # High memory pressure
            freed_bytes = self.cleanup_resources(force=True)
            optimization_results['optimizations_applied'].append(f"Pressure cleanup: {freed_bytes} bytes")
        elif memory_pressure > 0.5:  # Moderate memory pressure
            freed_bytes = self.cleanup_resources(target_bytes=self._total_cache_size // 4)
            optimization_results['optimizations_applied'].append(f"Moderate cleanup: {freed_bytes} bytes")
        
        # 4. Optimize cache sizes
        cache_optimized = self._optimize_cache_sizes()
        if cache_optimized:
            optimization_results['optimizations_applied'].append("Cache size optimization")
        
        # 5. Defragment memory (Python-specific optimizations)
        self._defragment_memory()
        optimization_results['optimizations_applied'].append("Memory defragmentation")
        
        # Calculate results
        final_stats = self.get_memory_stats()
        optimization_results.update({
            'final_memory': final_stats.process_memory,
            'final_cached': final_stats.cached_memory,
            'memory_freed': initial_stats.process_memory - final_stats.process_memory,
            'optimization_time': time.time() - optimization_start
        })
        
        return optimization_results
    
    def _cleanup_expired_resources(self) -> int:
        """Clean up expired resources."""
        current_time = time.time()
        expired_resources = []
        
        for resource_id, resource_info in self._resources.items():
            if (resource_info.ttl > 0 and 
                current_time - resource_info.created_at > resource_info.ttl):
                expired_resources.append(resource_id)
        
        for resource_id in expired_resources:
            self.unregister_resource(resource_id)
        
        return len(expired_resources)
    
    def _optimize_cache_sizes(self) -> bool:
        """Optimize cache sizes based on usage patterns."""
        optimized = False
        
        # Analyze resource usage patterns
        resource_usage = defaultdict(list)
        for resource_info in self._resources.values():
            resource_usage[resource_info.resource_type].append(resource_info)
        
        # Optimize each resource type
        for resource_type, resources in resource_usage.items():
            if len(resources) > 10:  # Only optimize if we have enough data
                # Sort by access frequency
                resources.sort(key=lambda r: r.access_count, reverse=True)
                
                # Keep top 80% most accessed, remove bottom 20%
                keep_count = int(len(resources) * 0.8)
                resources_to_remove = resources[keep_count:]
                
                for resource in resources_to_remove:
                    self.unregister_resource(resource.resource_id)
                    optimized = True
        
        return optimized
    
    def _defragment_memory(self):
        """Perform memory defragmentation optimizations."""
        # Force multiple garbage collection cycles
        for _ in range(3):
            gc.collect()
        
        # Optimize garbage collection thresholds
        current_thresholds = gc.get_threshold()
        # Temporarily lower thresholds for more aggressive collection
        gc.set_threshold(current_thresholds[0] // 2, current_thresholds[1] // 2, current_thresholds[2] // 2)
        
        # Collect again with new thresholds
        gc.collect()
        
        # Restore original thresholds
        gc.set_threshold(*current_thresholds)
    
    def get_optimization_recommendations(self) -> List[str]:
        """Get memory optimization recommendations."""
        recommendations = []
        stats = self.get_memory_stats()
        memory_pressure = stats.memory_pressure
        
        if memory_pressure > 0.8:
            recommendations.append("Critical: Memory usage is very high. Consider closing unused features.")
        elif memory_pressure > 0.6:
            recommendations.append("Warning: Memory usage is high. Clear caches or reduce image sizes.")
        
        # Check cache efficiency
        if self._total_cache_size > 100 * 1024 * 1024:  # 100MB
            recommendations.append("Large cache detected. Consider reducing cache sizes.")
        
        # Check resource count
        if len(self._resources) > 1000:
            recommendations.append("Many resources tracked. Consider cleanup of unused resources.")
        
        # Check for memory leaks
        if hasattr(self, '_previous_memory') and stats.process_memory > self._previous_memory * 1.5:
            recommendations.append("Potential memory leak detected. Monitor memory usage closely.")
        
        self._previous_memory = stats.process_memory
        
        return recommendations
    
    def force_cleanup(self) -> Dict[str, Any]:
        """Force aggressive memory cleanup."""
        cleanup_results = {
            'resources_cleaned': 0,
            'memory_freed': 0,
            'caches_cleared': 0
        }
        
        initial_memory = self.get_memory_stats().process_memory
        
        # Clear all low and normal priority resources
        resources_to_remove = []
        for resource_id, resource_info in self._resources.items():
            if resource_info.priority in [MemoryPriority.LOW, MemoryPriority.NORMAL]:
                resources_to_remove.append(resource_id)
        
        for resource_id in resources_to_remove:
            self.unregister_resource(resource_id)
        
        cleanup_results['resources_cleaned'] = len(resources_to_remove)
        
        # Force aggressive garbage collection
        for _ in range(5):
            gc.collect()
        
        # Calculate memory freed
        final_memory = self.get_memory_stats().process_memory
        cleanup_results['memory_freed'] = initial_memory - final_memory
        
        return cleanup_results
    
    def shutdown(self):
        """Shutdown the memory manager."""
        self._shutdown = True
        
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=2.0)
        
        # Clean up all resources
        self.cleanup_resources(force=True)
        
        # Clear callbacks
        self._memory_warning_callbacks.clear()
        self._cleanup_callbacks.clear()
    
    def _start_monitoring(self):
        """Start memory monitoring thread."""
        def monitor_memory():
            while not self._shutdown:
                try:
                    stats = self.get_memory_stats()
                    pressure = stats.memory_pressure
                    
                    # Check if cleanup is needed
                    if pressure > self.cleanup_threshold:
                        # Calculate how much memory to free
                        target_bytes = int(self._total_cache_size * 0.3)  # Free 30% of cache
                        self.cleanup_resources(target_bytes)
                        
                        # Force garbage collection
                        self.force_garbage_collection()
                        
                        # Notify warning callbacks
                        for callback in self._memory_warning_callbacks:
                            try:
                                callback(stats)
                            except Exception:
                                pass
                    
                    # Check for very high memory usage
                    if stats.process_memory > self.memory_limit_bytes:
                        # Emergency cleanup
                        emergency_target = int(self._total_cache_size * 0.5)
                        self.cleanup_resources(emergency_target, force=True)
                        self.force_garbage_collection()
                    
                except Exception:
                    pass  # Continue monitoring even if errors occur
                
                time.sleep(self.monitor_interval)
        
        self._monitor_thread = threading.Thread(target=monitor_memory, daemon=True)
        self._monitor_thread.start()
    
    def _on_resource_deleted(self, resource_id: str):
        """Handle resource deletion via weak reference callback."""
        if resource_id in self._resources:
            self.unregister_resource(resource_id)


class ResourceCleanupManager:
    """Manages cleanup of various application resources."""
    
    def __init__(self):
        self._cleanup_handlers: Dict[str, Callable] = {}
        self._temp_files: Set[str] = set()
        self._temp_dirs: Set[str] = set()
    
    def register_cleanup_handler(self, name: str, handler: Callable):
        """Register a cleanup handler."""
        self._cleanup_handlers[name] = handler
    
    def add_temp_file(self, file_path: str):
        """Add a temporary file for cleanup."""
        self._temp_files.add(file_path)
    
    def add_temp_dir(self, dir_path: str):
        """Add a temporary directory for cleanup."""
        self._temp_dirs.add(dir_path)
    
    def cleanup_temp_files(self):
        """Clean up temporary files."""
        for file_path in list(self._temp_files):
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                self._temp_files.discard(file_path)
            except Exception:
                pass  # Ignore cleanup errors
    
    def cleanup_temp_dirs(self):
        """Clean up temporary directories."""
        import shutil
        
        for dir_path in list(self._temp_dirs):
            try:
                if os.path.exists(dir_path):
                    shutil.rmtree(dir_path)
                self._temp_dirs.discard(dir_path)
            except Exception:
                pass  # Ignore cleanup errors
    
    def cleanup_all(self):
        """Run all cleanup handlers."""
        # Clean up temporary files and directories
        self.cleanup_temp_files()
        self.cleanup_temp_dirs()
        
        # Run registered cleanup handlers
        for name, handler in self._cleanup_handlers.items():
            try:
                handler()
            except Exception:
                pass  # Ignore cleanup errors


# Global instances
_memory_manager: Optional[MemoryManager] = None
_cleanup_manager: Optional[ResourceCleanupManager] = None


def get_memory_manager() -> MemoryManager:
    """Get the global memory manager instance."""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager()
    return _memory_manager


def get_cleanup_manager() -> ResourceCleanupManager:
    """Get the global cleanup manager instance."""
    global _cleanup_manager
    if _cleanup_manager is None:
        _cleanup_manager = ResourceCleanupManager()
    return _cleanup_manager


def shutdown_memory_management():
    """Shutdown memory management systems."""
    global _memory_manager, _cleanup_manager
    
    if _memory_manager is not None:
        _memory_manager.shutdown()
        _memory_manager = None
    
    if _cleanup_manager is not None:
        _cleanup_manager.cleanup_all()
        _cleanup_manager = None