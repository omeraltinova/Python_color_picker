"""
Intelligent caching system with memory management and performance optimization.
"""

import hashlib
import pickle
import time
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Callable, Generic, TypeVar, List
from collections import OrderedDict
from pathlib import Path

from ..core.memory_manager import (
    get_memory_manager, MemoryPriority, ResourceType, MemoryManager
)

T = TypeVar('T')


@dataclass
class CacheEntry(Generic[T]):
    """Cache entry with metadata."""
    key: str
    value: T
    size_bytes: int
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)
    access_count: int = 0
    priority: MemoryPriority = MemoryPriority.NORMAL
    
    def update_access(self):
        """Update access statistics."""
        self.last_accessed = time.time()
        self.access_count += 1
    
    @property
    def age(self) -> float:
        """Get entry age in seconds."""
        return time.time() - self.created_at
    
    @property
    def idle_time(self) -> float:
        """Get time since last access in seconds."""
        return time.time() - self.last_accessed


class CacheEvictionPolicy(ABC):
    """Abstract base class for cache eviction policies."""
    
    @abstractmethod
    def select_victims(
        self, 
        entries: Dict[str, CacheEntry], 
        target_size: int
    ) -> List[str]:
        """
        Select cache entries to evict.
        
        Args:
            entries: Dictionary of cache entries
            target_size: Target number of bytes to free
        
        Returns:
            List of keys to evict
        """
        pass


class LRUEvictionPolicy(CacheEvictionPolicy):
    """Least Recently Used eviction policy."""
    
    def select_victims(
        self, 
        entries: Dict[str, CacheEntry], 
        target_size: int
    ) -> List[str]:
        # Sort by last accessed time (oldest first)
        sorted_entries = sorted(
            entries.items(),
            key=lambda x: x[1].last_accessed
        )
        
        victims = []
        freed_size = 0
        
        for key, entry in sorted_entries:
            if freed_size >= target_size:
                break
            
            # Don't evict critical priority items unless absolutely necessary
            if entry.priority == MemoryPriority.CRITICAL and freed_size > 0:
                continue
            
            victims.append(key)
            freed_size += entry.size_bytes
        
        return victims


class LFUEvictionPolicy(CacheEvictionPolicy):
    """Least Frequently Used eviction policy."""
    
    def select_victims(
        self, 
        entries: Dict[str, CacheEntry], 
        target_size: int
    ) -> List[str]:
        # Sort by access count (least accessed first)
        sorted_entries = sorted(
            entries.items(),
            key=lambda x: (x[1].access_count, x[1].last_accessed)
        )
        
        victims = []
        freed_size = 0
        
        for key, entry in sorted_entries:
            if freed_size >= target_size:
                break
            
            if entry.priority == MemoryPriority.CRITICAL and freed_size > 0:
                continue
            
            victims.append(key)
            freed_size += entry.size_bytes
        
        return victims


class AdaptiveEvictionPolicy(CacheEvictionPolicy):
    """Adaptive eviction policy combining LRU and LFU with priority."""
    
    def select_victims(
        self, 
        entries: Dict[str, CacheEntry], 
        target_size: int
    ) -> List[str]:
        # Calculate composite score for each entry
        scored_entries = []
        
        for key, entry in entries.items():
            # Combine age, access frequency, and priority
            age_score = entry.idle_time / max(1, entry.age)  # Normalized idle time
            frequency_score = 1.0 / max(1, entry.access_count)  # Inverse frequency
            priority_score = entry.priority.value  # Higher value = lower priority
            
            # Composite score (higher = more likely to evict)
            composite_score = (age_score * 0.4 + frequency_score * 0.4 + priority_score * 0.2)
            scored_entries.append((composite_score, key, entry))
        
        # Sort by composite score (highest first)
        scored_entries.sort(reverse=True)
        
        victims = []
        freed_size = 0
        
        for score, key, entry in scored_entries:
            if freed_size >= target_size:
                break
            
            if entry.priority == MemoryPriority.CRITICAL and freed_size > 0:
                continue
            
            victims.append(key)
            freed_size += entry.size_bytes
        
        return victims


class IntelligentCache(Generic[T]):
    """
    Intelligent cache with memory management and adaptive eviction.
    
    Features:
    - Multiple eviction policies
    - Memory pressure awareness
    - Priority-based caching
    - Automatic size estimation
    - Thread-safe operations
    - Integration with global memory manager
    """
    
    def __init__(
        self,
        name: str,
        max_size_mb: int = 64,
        max_entries: int = 1000,
        resource_type: ResourceType = ResourceType.IMAGE_CACHE,
        eviction_policy: CacheEvictionPolicy = None,
        enable_persistence: bool = False,
        persistence_path: Optional[Path] = None
    ):
        """
        Initialize intelligent cache.
        
        Args:
            name: Cache name for identification
            max_size_mb: Maximum cache size in MB
            max_entries: Maximum number of entries
            resource_type: Type of resource being cached
            eviction_policy: Eviction policy to use
            enable_persistence: Whether to persist cache to disk
            persistence_path: Path for cache persistence
        """
        self.name = name
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.max_entries = max_entries
        self.resource_type = resource_type
        self.eviction_policy = eviction_policy or AdaptiveEvictionPolicy()
        self.enable_persistence = enable_persistence
        self.persistence_path = persistence_path
        
        # Cache storage
        self._entries: Dict[str, CacheEntry[T]] = {}
        self._current_size = 0
        self._lock = threading.RLock()
        
        # Statistics
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        
        # Memory manager integration
        self._memory_manager = get_memory_manager()
        self._memory_manager.add_memory_warning_callback(self._on_memory_warning)
        
        # Load persisted cache if enabled
        if self.enable_persistence:
            self._load_from_disk()
    
    def get(self, key: str, default: T = None) -> Optional[T]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            default: Default value if key not found
        
        Returns:
            Cached value or default
        """
        with self._lock:
            if key in self._entries:
                entry = self._entries[key]
                entry.update_access()
                
                # Update memory manager
                self._memory_manager.access_resource(f"{self.name}:{key}")
                
                self._hits += 1
                return entry.value
            else:
                self._misses += 1
                return default
    
    def put(
        self, 
        key: str, 
        value: T, 
        priority: MemoryPriority = MemoryPriority.NORMAL,
        size_hint: Optional[int] = None
    ):
        """
        Put value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            priority: Cache priority
            size_hint: Hint about value size in bytes
        """
        with self._lock:
            # Estimate size if not provided
            if size_hint is None:
                size_bytes = self._estimate_size(value)
            else:
                size_bytes = size_hint
            
            # Check if we need to make room
            if key not in self._entries:
                self._ensure_capacity(size_bytes)
            else:
                # Update existing entry
                old_entry = self._entries[key]
                self._current_size -= old_entry.size_bytes
                
                # Unregister from memory manager
                self._memory_manager.unregister_resource(f"{self.name}:{key}")
            
            # Create new entry
            entry = CacheEntry(
                key=key,
                value=value,
                size_bytes=size_bytes,
                priority=priority
            )
            
            self._entries[key] = entry
            self._current_size += size_bytes
            
            # Register with memory manager
            self._memory_manager.register_resource(
                resource_id=f"{self.name}:{key}",
                resource_type=self.resource_type,
                size_bytes=size_bytes,
                priority=priority,
                cleanup_callback=lambda: self.remove(key),
                resource_ref=value
            )
            
            # Persist if enabled
            if self.enable_persistence:
                self._persist_entry(key, entry)
    
    def remove(self, key: str) -> bool:
        """
        Remove entry from cache.
        
        Args:
            key: Cache key to remove
        
        Returns:
            True if key was removed, False if not found
        """
        with self._lock:
            if key in self._entries:
                entry = self._entries[key]
                del self._entries[key]
                self._current_size -= entry.size_bytes
                
                # Unregister from memory manager
                self._memory_manager.unregister_resource(f"{self.name}:{key}")
                
                # Remove from persistence
                if self.enable_persistence:
                    self._remove_persisted_entry(key)
                
                return True
            return False
    
    def clear(self):
        """Clear all cache entries."""
        with self._lock:
            # Unregister all resources
            for key in list(self._entries.keys()):
                self._memory_manager.unregister_resource(f"{self.name}:{key}")
            
            self._entries.clear()
            self._current_size = 0
            
            # Clear persistence
            if self.enable_persistence:
                self._clear_persistence()
    
    def contains(self, key: str) -> bool:
        """Check if key exists in cache."""
        with self._lock:
            return key in self._entries
    
    def size(self) -> int:
        """Get number of entries in cache."""
        with self._lock:
            return len(self._entries)
    
    def size_bytes(self) -> int:
        """Get total size of cache in bytes."""
        with self._lock:
            return self._current_size
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = self._hits / total_requests if total_requests > 0 else 0.0
            
            return {
                'name': self.name,
                'entries': len(self._entries),
                'size_bytes': self._current_size,
                'size_mb': self._current_size / (1024 * 1024),
                'max_size_mb': self.max_size_bytes / (1024 * 1024),
                'utilization': self._current_size / self.max_size_bytes,
                'hits': self._hits,
                'misses': self._misses,
                'hit_rate': hit_rate,
                'evictions': self._evictions
            }
    
    def cleanup(self, target_size: Optional[int] = None):
        """
        Manually trigger cache cleanup.
        
        Args:
            target_size: Target size to free (bytes)
        """
        with self._lock:
            if target_size is None:
                target_size = self._current_size // 4  # Free 25%
            
            self._evict_entries(target_size)
    
    def _ensure_capacity(self, required_bytes: int):
        """Ensure cache has capacity for new entry."""
        # Check entry count limit
        if len(self._entries) >= self.max_entries:
            self._evict_entries(0, min_entries=1)
        
        # Check size limit
        if self._current_size + required_bytes > self.max_size_bytes:
            target_size = (self._current_size + required_bytes) - self.max_size_bytes
            self._evict_entries(target_size)
    
    def _evict_entries(self, target_size: int, min_entries: int = 0):
        """Evict entries using the configured policy."""
        if not self._entries:
            return
        
        # Get victims from eviction policy
        victims = self.eviction_policy.select_victims(self._entries, target_size)
        
        # Ensure minimum entries are evicted
        if len(victims) < min_entries:
            # Add more victims if needed
            remaining_keys = [k for k in self._entries.keys() if k not in victims]
            additional_victims = remaining_keys[:min_entries - len(victims)]
            victims.extend(additional_victims)
        
        # Remove victims
        for key in victims:
            if key in self._entries:
                self.remove(key)
                self._evictions += 1
    
    def _estimate_size(self, value: T) -> int:
        """Estimate size of value in bytes."""
        try:
            # Try to get size from object if it has a size method/property
            if hasattr(value, 'size'):
                return value.size
            elif hasattr(value, '__sizeof__'):
                return value.__sizeof__()
            else:
                # Fallback to pickle size estimation
                return len(pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL))
        except Exception:
            # Conservative estimate
            return 1024  # 1KB default
    
    def _on_memory_warning(self, memory_stats):
        """Handle memory warning from memory manager."""
        # Aggressive cleanup during memory pressure
        pressure = memory_stats.memory_pressure
        
        if pressure > 0.8:
            # High pressure - free 50% of cache
            target_size = self._current_size // 2
        elif pressure > 0.6:
            # Medium pressure - free 25% of cache
            target_size = self._current_size // 4
        else:
            # Low pressure - free 10% of cache
            target_size = self._current_size // 10
        
        if target_size > 0:
            self.cleanup(target_size)
    
    def _load_from_disk(self):
        """Load cache from disk if persistence is enabled."""
        if not self.persistence_path or not self.persistence_path.exists():
            return
        
        try:
            with open(self.persistence_path, 'rb') as f:
                persisted_data = pickle.load(f)
            
            for key, entry_data in persisted_data.items():
                # Recreate cache entry
                entry = CacheEntry(**entry_data)
                self._entries[key] = entry
                self._current_size += entry.size_bytes
                
                # Register with memory manager
                self._memory_manager.register_resource(
                    resource_id=f"{self.name}:{key}",
                    resource_type=self.resource_type,
                    size_bytes=entry.size_bytes,
                    priority=entry.priority,
                    cleanup_callback=lambda k=key: self.remove(k)
                )
        
        except Exception:
            # Ignore persistence errors
            pass
    
    def _persist_entry(self, key: str, entry: CacheEntry[T]):
        """Persist single entry to disk."""
        # Implementation would depend on specific persistence requirements
        pass
    
    def _remove_persisted_entry(self, key: str):
        """Remove persisted entry from disk."""
        # Implementation would depend on specific persistence requirements
        pass
    
    def _clear_persistence(self):
        """Clear all persisted data."""
        if self.persistence_path and self.persistence_path.exists():
            try:
                self.persistence_path.unlink()
            except Exception:
                pass


class CacheManager:
    """Manager for multiple intelligent caches."""
    
    def __init__(self):
        self._caches: Dict[str, IntelligentCache] = {}
        self._lock = threading.RLock()
    
    def create_cache(
        self,
        name: str,
        max_size_mb: int = 64,
        max_entries: int = 1000,
        resource_type: ResourceType = ResourceType.IMAGE_CACHE,
        eviction_policy: CacheEvictionPolicy = None
    ) -> IntelligentCache:
        """Create a new intelligent cache."""
        with self._lock:
            if name in self._caches:
                return self._caches[name]
            
            cache = IntelligentCache(
                name=name,
                max_size_mb=max_size_mb,
                max_entries=max_entries,
                resource_type=resource_type,
                eviction_policy=eviction_policy
            )
            
            self._caches[name] = cache
            return cache
    
    def get_cache(self, name: str) -> Optional[IntelligentCache]:
        """Get existing cache by name."""
        with self._lock:
            return self._caches.get(name)
    
    def remove_cache(self, name: str) -> bool:
        """Remove and cleanup cache."""
        with self._lock:
            if name in self._caches:
                cache = self._caches[name]
                cache.clear()
                del self._caches[name]
                return True
            return False
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all caches."""
        with self._lock:
            return {name: cache.get_stats() for name, cache in self._caches.items()}
    
    def cleanup_all(self):
        """Cleanup all caches."""
        with self._lock:
            for cache in self._caches.values():
                cache.cleanup()
    
    def clear_all(self):
        """Clear all caches."""
        with self._lock:
            for cache in self._caches.values():
                cache.clear()


# Global cache manager instance
_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """Get the global cache manager instance."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


def shutdown_cache_system():
    """Shutdown the cache system."""
    global _cache_manager
    if _cache_manager is not None:
        _cache_manager.clear_all()
        _cache_manager = None