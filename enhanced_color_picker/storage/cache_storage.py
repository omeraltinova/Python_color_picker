"""
Cache management system for Enhanced Color Picker.

This module provides intelligent image caching with LRU eviction,
zoom-level specific cache management, memory usage monitoring,
and cache persistence across sessions.
"""

import os
import pickle
import threading
import time
import weakref
from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, List, Union
from datetime import datetime, timedelta
import logging
import hashlib
import psutil

from ..models.image_data import ImageData
from ..core.event_bus import EventBus, get_global_event_bus
from ..core.exceptions import ColorPickerError


class CacheError(ColorPickerError):
    """Raised when cache operations fail."""
    pass


class CacheEntry:
    """Represents a single cache entry with metadata."""
    
    def __init__(self, key: str, data: Any, size_bytes: int = 0):
        """
        Initialize cache entry.
        
        Args:
            key: Unique identifier for the cached item
            data: The cached data
            size_bytes: Size of the data in bytes
        """
        self.key = key
        self.data = data
        self.size_bytes = size_bytes
        self.created_at = datetime.now()
        self.last_accessed = datetime.now()
        self.access_count = 0
        self.hit_count = 0
    
    def access(self) -> Any:
        """Mark entry as accessed and return data."""
        self.last_accessed = datetime.now()
        self.access_count += 1
        self.hit_count += 1
        return self.data
    
    def age_seconds(self) -> float:
        """Get age of entry in seconds."""
        return (datetime.now() - self.created_at).total_seconds()
    
    def idle_seconds(self) -> float:
        """Get idle time since last access in seconds."""
        return (datetime.now() - self.last_accessed).total_seconds()
    
    def __repr__(self) -> str:
        return f"CacheEntry(key='{self.key}', size={self.size_bytes}, age={self.age_seconds():.1f}s)"


class LRUCache:
    """
    Least Recently Used (LRU) cache implementation with size limits.
    
    Features:
    - Size-based eviction (memory limit)
    - Count-based eviction (item limit)
    - Thread-safe operations
    - Access statistics
    - TTL (Time To Live) support
    """
    
    def __init__(self, max_size_bytes: int = 100 * 1024 * 1024,  # 100MB
                 max_items: int = 1000,
                 default_ttl: Optional[float] = None):
        """
        Initialize LRU cache.
        
        Args:
            max_size_bytes: Maximum cache size in bytes
            max_items: Maximum number of items in cache
            default_ttl: Default time-to-live in seconds (None = no expiration)
        """
        self.max_size_bytes = max_size_bytes
        self.max_items = max_items
        self.default_ttl = default_ttl
        
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        self._current_size = 0
        
        # Statistics
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'size_evictions': 0,
            'ttl_evictions': 0,
            'items_added': 0,
            'total_size_added': 0
        }
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get item from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached data or None if not found/expired
        """
        with self._lock:
            if key not in self._cache:
                self._stats['misses'] += 1
                return None
            
            entry = self._cache[key]
            
            # Check TTL
            if self.default_ttl and entry.age_seconds() > self.default_ttl:
                self._remove_entry(key)
                self._stats['ttl_evictions'] += 1
                self._stats['misses'] += 1
                return None
            
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            
            self._stats['hits'] += 1
            return entry.access()
    
    def put(self, key: str, data: Any, size_bytes: Optional[int] = None) -> bool:
        """
        Put item in cache.
        
        Args:
            key: Cache key
            data: Data to cache
            size_bytes: Size of data in bytes (estimated if None)
            
        Returns:
            True if item was cached, False if too large
        """
        if size_bytes is None:
            size_bytes = self._estimate_size(data)
        
        # Check if item is too large for cache
        if size_bytes > self.max_size_bytes:
            return False
        
        with self._lock:
            # Remove existing entry if present
            if key in self._cache:
                self._remove_entry(key)
            
            # Make space if needed
            self._make_space(size_bytes)
            
            # Add new entry
            entry = CacheEntry(key, data, size_bytes)
            self._cache[key] = entry
            self._current_size += size_bytes
            
            self._stats['items_added'] += 1
            self._stats['total_size_added'] += size_bytes
            
            return True
    
    def remove(self, key: str) -> bool:
        """
        Remove item from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if item was removed, False if not found
        """
        with self._lock:
            if key in self._cache:
                self._remove_entry(key)
                return True
            return False
    
    def clear(self) -> None:
        """Clear all items from cache."""
        with self._lock:
            self._cache.clear()
            self._current_size = 0
    
    def _remove_entry(self, key: str) -> None:
        """Remove entry and update size (assumes lock is held)."""
        if key in self._cache:
            entry = self._cache.pop(key)
            self._current_size -= entry.size_bytes
    
    def _make_space(self, needed_bytes: int) -> None:
        """Make space for new entry by evicting old ones (assumes lock is held)."""
        # Evict by count limit
        while len(self._cache) >= self.max_items:
            oldest_key = next(iter(self._cache))
            self._remove_entry(oldest_key)
            self._stats['evictions'] += 1
        
        # Evict by size limit
        while self._current_size + needed_bytes > self.max_size_bytes and self._cache:
            oldest_key = next(iter(self._cache))
            self._remove_entry(oldest_key)
            self._stats['evictions'] += 1
            self._stats['size_evictions'] += 1
    
    def _estimate_size(self, data: Any) -> int:
        """Estimate size of data in bytes."""
        try:
            if hasattr(data, '__sizeof__'):
                return data.__sizeof__()
            elif isinstance(data, (str, bytes)):
                return len(data)
            elif isinstance(data, (list, tuple, dict)):
                return sum(self._estimate_size(item) for item in data)
            else:
                # Fallback: use pickle size
                return len(pickle.dumps(data, protocol=pickle.HIGHEST_PROTOCOL))
        except Exception:
            # Conservative estimate
            return 1024
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_requests = self._stats['hits'] + self._stats['misses']
            hit_rate = self._stats['hits'] / total_requests if total_requests > 0 else 0
            
            return {
                **self._stats,
                'current_items': len(self._cache),
                'current_size_bytes': self._current_size,
                'current_size_mb': self._current_size / (1024 * 1024),
                'max_size_bytes': self.max_size_bytes,
                'max_size_mb': self.max_size_bytes / (1024 * 1024),
                'max_items': self.max_items,
                'hit_rate': hit_rate,
                'utilization': self._current_size / self.max_size_bytes if self.max_size_bytes > 0 else 0
            }
    
    def get_entries_info(self) -> List[Dict[str, Any]]:
        """Get information about cache entries."""
        with self._lock:
            return [
                {
                    'key': entry.key,
                    'size_bytes': entry.size_bytes,
                    'age_seconds': entry.age_seconds(),
                    'idle_seconds': entry.idle_seconds(),
                    'access_count': entry.access_count,
                    'hit_count': entry.hit_count
                }
                for entry in self._cache.values()
            ]


class ImageCache:
    """
    Specialized cache for image data with zoom-level support.
    
    Features:
    - Zoom-level specific caching
    - Image format optimization
    - Memory usage monitoring
    - Automatic cleanup based on memory pressure
    """
    
    def __init__(self, max_size_mb: int = 200, max_items: int = 500):
        """
        Initialize image cache.
        
        Args:
            max_size_mb: Maximum cache size in megabytes
            max_items: Maximum number of cached images
        """
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.max_items = max_items
        
        self._cache = LRUCache(self.max_size_bytes, max_items)
        self._lock = threading.RLock()
        self._logger = logging.getLogger(__name__)
    
    def _generate_key(self, image_path: str, zoom_level: float, 
                     width: Optional[int] = None, height: Optional[int] = None) -> str:
        """Generate cache key for image with zoom level."""
        key_parts = [image_path, f"zoom_{zoom_level:.2f}"]
        
        if width is not None and height is not None:
            key_parts.append(f"size_{width}x{height}")
        
        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get_cached_image(self, image_path: str, zoom_level: float,
                        width: Optional[int] = None, height: Optional[int] = None) -> Optional[ImageData]:
        """
        Get cached image at specific zoom level.
        
        Args:
            image_path: Path to the original image
            zoom_level: Zoom level for the cached version
            width: Target width (optional)
            height: Target height (optional)
            
        Returns:
            Cached ImageData or None if not found
        """
        key = self._generate_key(image_path, zoom_level, width, height)
        return self._cache.get(key)
    
    def cache_image(self, image_path: str, zoom_level: float, image_data: ImageData,
                   width: Optional[int] = None, height: Optional[int] = None) -> bool:
        """
        Cache image at specific zoom level.
        
        Args:
            image_path: Path to the original image
            zoom_level: Zoom level for this cached version
            image_data: Image data to cache
            width: Target width (optional)
            height: Target height (optional)
            
        Returns:
            True if cached successfully
        """
        key = self._generate_key(image_path, zoom_level, width, height)
        
        # Estimate size based on image dimensions and format
        size_bytes = self._estimate_image_size(image_data)
        
        success = self._cache.put(key, image_data, size_bytes)
        
        if success:
            self._logger.debug(f"Cached image: {image_path} at zoom {zoom_level:.2f}")
        else:
            self._logger.warning(f"Failed to cache image (too large): {image_path}")
        
        return success
    
    def remove_image_cache(self, image_path: str) -> int:
        """
        Remove all cached versions of an image.
        
        Args:
            image_path: Path to the image
            
        Returns:
            Number of cache entries removed
        """
        with self._lock:
            # Find all keys that start with the image path hash
            path_hash = hashlib.md5(image_path.encode()).hexdigest()[:8]
            keys_to_remove = []
            
            for entry in self._cache._cache.values():
                if entry.key.startswith(path_hash):
                    keys_to_remove.append(entry.key)
            
            # Remove found entries
            for key in keys_to_remove:
                self._cache.remove(key)
            
            return len(keys_to_remove)
    
    def _estimate_image_size(self, image_data: ImageData) -> int:
        """Estimate memory size of image data."""
        if hasattr(image_data, 'pil_image') and image_data.pil_image:
            # Estimate based on image dimensions and mode
            width, height = image_data.pil_image.size
            mode = image_data.pil_image.mode
            
            # Bytes per pixel based on mode
            bytes_per_pixel = {
                'L': 1,      # Grayscale
                'RGB': 3,    # RGB
                'RGBA': 4,   # RGB with Alpha
                'CMYK': 4,   # CMYK
                'P': 1,      # Palette
            }.get(mode, 4)  # Default to 4 bytes per pixel
            
            return width * height * bytes_per_pixel
        
        # Fallback estimation
        return 1024 * 1024  # 1MB default


class CacheManager:
    """
    Main cache management system for Enhanced Color Picker.
    
    Features:
    - Multiple cache types (image, data, etc.)
    - Memory usage monitoring
    - Automatic cleanup based on system memory
    - Cache persistence across sessions
    - Performance metrics and statistics
    """
    
    def __init__(self, cache_dir: Optional[Path] = None,
                 event_bus: Optional[EventBus] = None,
                 max_memory_mb: int = 300,
                 memory_check_interval: float = 30.0):
        """
        Initialize cache manager.
        
        Args:
            cache_dir: Directory for persistent cache files
            event_bus: Event bus for notifications
            max_memory_mb: Maximum total memory usage in MB
            memory_check_interval: Interval for memory checks in seconds
        """
        self.cache_dir = cache_dir or self._get_default_cache_dir()
        self.event_bus = event_bus or get_global_event_bus()
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.memory_check_interval = memory_check_interval
        
        self._lock = threading.RLock()
        self._logger = logging.getLogger(__name__)
        
        # Initialize caches
        self.image_cache = ImageCache(max_size_mb=200, max_items=500)
        self.data_cache = LRUCache(max_size_bytes=50 * 1024 * 1024, max_items=1000)  # 50MB
        
        # Memory monitoring
        self._memory_monitor_thread = None
        self._monitoring_active = False
        self._last_cleanup = datetime.now()
        
        # Ensure cache directory exists
        self._ensure_cache_dir()
        
        # Load persistent cache if available
        self._load_persistent_cache()
        
        # Start memory monitoring
        self.start_memory_monitoring()
    
    def _get_default_cache_dir(self) -> Path:
        """Get default cache directory."""
        if os.name == 'nt':  # Windows
            base_dir = Path(os.environ.get('LOCALAPPDATA', Path.home() / 'AppData' / 'Local'))
        elif os.name == 'posix':  # Linux/macOS
            if 'XDG_CACHE_HOME' in os.environ:
                base_dir = Path(os.environ['XDG_CACHE_HOME'])
            else:
                base_dir = Path.home() / '.cache'
        else:
            base_dir = Path.home() / '.enhanced_color_picker_cache'
        
        return base_dir / 'enhanced_color_picker'
    
    def _ensure_cache_dir(self) -> None:
        """Ensure cache directory exists."""
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            self._logger.error(f"Failed to create cache directory: {e}")
    
    def _load_persistent_cache(self) -> None:
        """Load persistent cache data from disk."""
        try:
            cache_file = self.cache_dir / 'cache_index.pkl'
            if cache_file.exists():
                with open(cache_file, 'rb') as f:
                    cache_data = pickle.load(f)
                
                # Restore cache entries (validate they still exist)
                restored_count = 0
                for key, entry_data in cache_data.get('data_cache', {}).items():
                    try:
                        self.data_cache.put(key, entry_data['data'], entry_data['size'])
                        restored_count += 1
                    except Exception as e:
                        self._logger.debug(f"Failed to restore cache entry {key}: {e}")
                
                self._logger.info(f"Restored {restored_count} cache entries from disk")
                
        except Exception as e:
            self._logger.warning(f"Failed to load persistent cache: {e}")
    
    def _save_persistent_cache(self) -> None:
        """Save cache data to disk for persistence."""
        try:
            cache_file = self.cache_dir / 'cache_index.pkl'
            
            # Prepare data for serialization
            cache_data = {
                'data_cache': {},
                'saved_at': datetime.now().isoformat(),
                'version': '1.0'
            }
            
            # Save data cache entries (only small, serializable ones)
            with self.data_cache._lock:
                for key, entry in self.data_cache._cache.items():
                    if entry.size_bytes < 1024 * 1024:  # Only save entries < 1MB
                        try:
                            # Test if data is serializable
                            pickle.dumps(entry.data)
                            cache_data['data_cache'][key] = {
                                'data': entry.data,
                                'size': entry.size_bytes
                            }
                        except Exception:
                            # Skip non-serializable data
                            pass
            
            # Write to temporary file first
            temp_file = cache_file.with_suffix('.tmp')
            with open(temp_file, 'wb') as f:
                pickle.dump(cache_data, f, protocol=pickle.HIGHEST_PROTOCOL)
            
            # Atomic rename
            temp_file.replace(cache_file)
            
            self._logger.debug("Persistent cache saved")
            
        except Exception as e:
            self._logger.warning(f"Failed to save persistent cache: {e}")
    
    def start_memory_monitoring(self) -> None:
        """Start memory usage monitoring thread."""
        if self._monitoring_active:
            return
        
        self._monitoring_active = True
        self._memory_monitor_thread = threading.Thread(
            target=self._memory_monitor_loop,
            daemon=True,
            name="CacheMemoryMonitor"
        )
        self._memory_monitor_thread.start()
        
        self._logger.debug("Started memory monitoring")
    
    def stop_memory_monitoring(self) -> None:
        """Stop memory usage monitoring."""
        self._monitoring_active = False
        if self._memory_monitor_thread:
            self._memory_monitor_thread.join(timeout=1.0)
        
        self._logger.debug("Stopped memory monitoring")
    
    def _memory_monitor_loop(self) -> None:
        """Memory monitoring loop."""
        while self._monitoring_active:
            try:
                self._check_memory_usage()
                time.sleep(self.memory_check_interval)
            except Exception as e:
                self._logger.error(f"Error in memory monitoring: {e}")
                time.sleep(self.memory_check_interval)
    
    def _check_memory_usage(self) -> None:
        """Check memory usage and cleanup if necessary."""
        try:
            # Get current memory usage
            process = psutil.Process()
            memory_info = process.memory_info()
            current_memory = memory_info.rss  # Resident Set Size
            
            # Check if we're using too much memory
            if current_memory > self.max_memory_bytes:
                self._logger.info(f"Memory usage high ({current_memory / 1024 / 1024:.1f}MB), cleaning up cache")
                self._cleanup_memory_pressure()
            
            # Periodic cleanup regardless of memory pressure
            if (datetime.now() - self._last_cleanup).total_seconds() > 300:  # 5 minutes
                self._periodic_cleanup()
                self._last_cleanup = datetime.now()
            
        except Exception as e:
            self._logger.debug(f"Memory check failed: {e}")
    
    def _cleanup_memory_pressure(self) -> None:
        """Cleanup cache due to memory pressure."""
        with self._lock:
            # Clear oldest entries from caches
            initial_image_items = len(self.image_cache._cache._cache)
            initial_data_items = len(self.data_cache._cache)
            
            # Reduce image cache by 30%
            target_image_items = int(initial_image_items * 0.7)
            while len(self.image_cache._cache._cache) > target_image_items:
                oldest_key = next(iter(self.image_cache._cache._cache))
                self.image_cache._cache.remove(oldest_key)
            
            # Reduce data cache by 30%
            target_data_items = int(initial_data_items * 0.7)
            while len(self.data_cache._cache) > target_data_items:
                oldest_key = next(iter(self.data_cache._cache))
                self.data_cache.remove(oldest_key)
            
            removed_image = initial_image_items - len(self.image_cache._cache._cache)
            removed_data = initial_data_items - len(self.data_cache._cache)
            
            self._logger.info(f"Memory cleanup: removed {removed_image} image entries, {removed_data} data entries")
            
            # Publish cleanup event
            self.event_bus.publish(
                'cache_cleanup',
                {
                    'reason': 'memory_pressure',
                    'removed_image_entries': removed_image,
                    'removed_data_entries': removed_data,
                    'timestamp': datetime.now().isoformat()
                },
                source='cache_manager'
            )
    
    def _periodic_cleanup(self) -> None:
        """Periodic cache cleanup."""
        with self._lock:
            # Remove expired entries, cleanup invalid references, etc.
            initial_stats = self.get_cache_statistics()
            
            # Force garbage collection of weak references
            import gc
            gc.collect()
            
            final_stats = self.get_cache_statistics()
            
            self._logger.debug(f"Periodic cleanup completed")
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive cache statistics.
        
        Returns:
            Dict containing cache statistics
        """
        with self._lock:
            image_stats = self.image_cache._cache.get_stats()
            data_stats = self.data_cache.get_stats()
            
            # System memory info
            try:
                process = psutil.Process()
                memory_info = process.memory_info()
                system_memory = psutil.virtual_memory()
            except Exception:
                memory_info = None
                system_memory = None
            
            stats = {
                'image_cache': image_stats,
                'data_cache': data_stats,
                'total_memory_mb': (image_stats['current_size_bytes'] + data_stats['current_size_bytes']) / (1024 * 1024),
                'max_memory_mb': self.max_memory_bytes / (1024 * 1024),
                'cache_dir': str(self.cache_dir),
                'monitoring_active': self._monitoring_active,
                'last_cleanup': self._last_cleanup.isoformat()
            }
            
            if memory_info:
                stats['process_memory'] = {
                    'rss_mb': memory_info.rss / (1024 * 1024),
                    'vms_mb': memory_info.vms / (1024 * 1024)
                }
            
            if system_memory:
                stats['system_memory'] = {
                    'total_mb': system_memory.total / (1024 * 1024),
                    'available_mb': system_memory.available / (1024 * 1024),
                    'percent_used': system_memory.percent
                }
            
            return stats
    
    def clear_all_caches(self) -> None:
        """Clear all caches."""
        with self._lock:
            self.image_cache._cache.clear()
            self.data_cache.clear()
            
            self._logger.info("All caches cleared")
            
            self.event_bus.publish(
                'cache_cleared',
                {'timestamp': datetime.now().isoformat()},
                source='cache_manager'
            )
    
    def cleanup(self) -> None:
        """Cleanup cache manager resources."""
        self.stop_memory_monitoring()
        self._save_persistent_cache()
        
        with self._lock:
            self._logger.debug("Cache manager cleanup completed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()


# Global cache manager instance
_global_cache_manager: Optional[CacheManager] = None


def get_global_cache_manager() -> CacheManager:
    """
    Get the global cache manager instance.
    
    Returns:
        CacheManager: Global cache manager instance
    """
    global _global_cache_manager
    if _global_cache_manager is None:
        _global_cache_manager = CacheManager()
    return _global_cache_manager


def set_global_cache_manager(manager: CacheManager) -> None:
    """
    Set the global cache manager instance.
    
    Args:
        manager: CacheManager instance to use as global
    """
    global _global_cache_manager
    if _global_cache_manager:
        _global_cache_manager.cleanup()
    _global_cache_manager = manager