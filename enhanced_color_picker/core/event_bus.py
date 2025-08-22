"""
Event bus system for Enhanced Color Picker.

This module provides a centralized event system that enables loose coupling
between components through publish-subscribe pattern. Components can subscribe
to events and publish events without direct dependencies.
"""

import threading
import weakref
from typing import Any, Callable, Dict, List, Optional, Set
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import logging

from .exceptions import ColorPickerError


class EventPriority(Enum):
    """Event priority levels for ordering event handling."""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class EventData:
    """Container for event data and metadata."""
    event_type: str
    data: Any
    timestamp: datetime
    source: Optional[str] = None
    priority: EventPriority = EventPriority.NORMAL
    
    def __post_init__(self):
        """Set timestamp if not provided."""
        if not hasattr(self, 'timestamp') or self.timestamp is None:
            self.timestamp = datetime.now()


class EventSubscription:
    """Represents a subscription to an event type."""
    
    def __init__(self, callback: Callable, priority: EventPriority = EventPriority.NORMAL,
                 once: bool = False, weak_ref: bool = True):
        """
        Initialize event subscription.
        
        Args:
            callback: Function to call when event is published
            priority: Priority level for event handling order
            once: If True, subscription is removed after first event
            weak_ref: If True, use weak reference to callback (prevents memory leaks)
        """
        self.priority = priority
        self.once = once
        self.created_at = datetime.now()
        self.call_count = 0
        
        if weak_ref and hasattr(callback, '__self__'):
            # Use weak reference for bound methods to prevent memory leaks
            self._callback_ref = weakref.WeakMethod(callback)
        elif weak_ref:
            # Use weak reference for functions
            self._callback_ref = weakref.ref(callback)
        else:
            # Store direct reference
            self._callback_ref = callback
        
        self._weak_ref = weak_ref
    
    @property
    def callback(self) -> Optional[Callable]:
        """Get the callback function, handling weak references."""
        if self._weak_ref:
            if isinstance(self._callback_ref, (weakref.ref, weakref.WeakMethod)):
                return self._callback_ref()
            return self._callback_ref
        else:
            return self._callback_ref
    
    @property
    def is_valid(self) -> bool:
        """Check if subscription is still valid (callback exists)."""
        return self.callback is not None
    
    def __call__(self, event_data: EventData) -> Any:
        """Call the subscription callback."""
        callback = self.callback
        if callback is None:
            return None
        
        self.call_count += 1
        return callback(event_data)


class EventBus:
    """
    Centralized event bus for component communication.
    
    The EventBus enables loose coupling between components by providing
    a publish-subscribe mechanism. Components can subscribe to events
    and publish events without knowing about each other directly.
    """
    
    def __init__(self, enable_logging: bool = False):
        """
        Initialize event bus.
        
        Args:
            enable_logging: Enable event logging for debugging
        """
        self._subscriptions: Dict[str, List[EventSubscription]] = {}
        self._event_history: List[EventData] = []
        self._max_history = 1000
        self._lock = threading.RLock()
        self._enable_logging = enable_logging
        self._logger = logging.getLogger(__name__) if enable_logging else None
        
        # Statistics
        self._stats = {
            'events_published': 0,
            'events_handled': 0,
            'subscriptions_created': 0,
            'subscriptions_removed': 0
        }
    
    def subscribe(self, event_type: str, callback: Callable, 
                  priority: EventPriority = EventPriority.NORMAL,
                  once: bool = False, weak_ref: bool = True) -> EventSubscription:
        """
        Subscribe to an event type.
        
        Args:
            event_type: Type of event to subscribe to
            callback: Function to call when event is published
            priority: Priority level for event handling order
            once: If True, subscription is removed after first event
            weak_ref: If True, use weak reference to callback
            
        Returns:
            EventSubscription: The created subscription
            
        Example:
            def on_color_changed(event_data):
                print(f"Color changed to: {event_data.data}")
            
            subscription = event_bus.subscribe('color_changed', on_color_changed)
        """
        with self._lock:
            if event_type not in self._subscriptions:
                self._subscriptions[event_type] = []
            
            subscription = EventSubscription(callback, priority, once, weak_ref)
            self._subscriptions[event_type].append(subscription)
            
            # Sort by priority (highest first)
            self._subscriptions[event_type].sort(
                key=lambda s: s.priority.value, reverse=True
            )
            
            self._stats['subscriptions_created'] += 1
            
            if self._enable_logging:
                self._logger.debug(f"Subscribed to '{event_type}' with priority {priority.name}")
            
            return subscription
    
    def unsubscribe(self, event_type: str, subscription: EventSubscription) -> bool:
        """
        Unsubscribe from an event type.
        
        Args:
            event_type: Type of event to unsubscribe from
            subscription: The subscription to remove
            
        Returns:
            bool: True if subscription was found and removed
        """
        with self._lock:
            if event_type in self._subscriptions:
                try:
                    self._subscriptions[event_type].remove(subscription)
                    self._stats['subscriptions_removed'] += 1
                    
                    if self._enable_logging:
                        self._logger.debug(f"Unsubscribed from '{event_type}'")
                    
                    return True
                except ValueError:
                    pass
            
            return False
    
    def unsubscribe_all(self, event_type: str) -> int:
        """
        Remove all subscriptions for an event type.
        
        Args:
            event_type: Type of event to clear subscriptions for
            
        Returns:
            int: Number of subscriptions removed
        """
        with self._lock:
            if event_type in self._subscriptions:
                count = len(self._subscriptions[event_type])
                self._subscriptions[event_type].clear()
                self._stats['subscriptions_removed'] += count
                
                if self._enable_logging:
                    self._logger.debug(f"Removed all {count} subscriptions for '{event_type}'")
                
                return count
            
            return 0
    
    def publish(self, event_type: str, data: Any = None, source: Optional[str] = None,
                priority: EventPriority = EventPriority.NORMAL) -> int:
        """
        Publish an event to all subscribers.
        
        Args:
            event_type: Type of event to publish
            data: Event data to send to subscribers
            source: Optional source identifier
            priority: Event priority level
            
        Returns:
            int: Number of subscribers that handled the event
            
        Example:
            event_bus.publish('color_changed', {'rgb': (255, 0, 0)}, source='color_picker')
        """
        event_data = EventData(
            event_type=event_type,
            data=data,
            timestamp=datetime.now(),
            source=source,
            priority=priority
        )
        
        return self._publish_event(event_data)
    
    def _publish_event(self, event_data: EventData) -> int:
        """Internal method to publish event data."""
        with self._lock:
            # Add to history
            self._event_history.append(event_data)
            if len(self._event_history) > self._max_history:
                self._event_history.pop(0)
            
            self._stats['events_published'] += 1
            
            if self._enable_logging:
                self._logger.debug(f"Publishing event '{event_data.event_type}' from {event_data.source}")
            
            # Get subscribers
            subscribers = self._subscriptions.get(event_data.event_type, [])
            handled_count = 0
            
            # Remove invalid subscriptions and handle events
            valid_subscribers = []
            
            for subscription in subscribers:
                if not subscription.is_valid:
                    self._stats['subscriptions_removed'] += 1
                    continue
                
                valid_subscribers.append(subscription)
                
                try:
                    subscription(event_data)
                    handled_count += 1
                    self._stats['events_handled'] += 1
                    
                    # Remove one-time subscriptions
                    if subscription.once:
                        self._stats['subscriptions_removed'] += 1
                        continue
                    
                except Exception as e:
                    if self._enable_logging:
                        self._logger.error(f"Error handling event '{event_data.event_type}': {e}")
                    # Continue with other subscribers even if one fails
            
            # Update subscribers list (remove invalid and one-time subscriptions)
            self._subscriptions[event_data.event_type] = [
                s for s in valid_subscribers if s.is_valid and not s.once
            ]
            
            return handled_count
    
    def publish_async(self, event_type: str, data: Any = None, source: Optional[str] = None,
                      priority: EventPriority = EventPriority.NORMAL) -> None:
        """
        Publish an event asynchronously (non-blocking).
        
        Args:
            event_type: Type of event to publish
            data: Event data to send to subscribers
            source: Optional source identifier
            priority: Event priority level
        """
        def _async_publish():
            self.publish(event_type, data, source, priority)
        
        thread = threading.Thread(target=_async_publish, daemon=True)
        thread.start()
    
    def has_subscribers(self, event_type: str) -> bool:
        """
        Check if there are any subscribers for an event type.
        
        Args:
            event_type: Type of event to check
            
        Returns:
            bool: True if there are active subscribers
        """
        with self._lock:
            subscribers = self._subscriptions.get(event_type, [])
            return any(s.is_valid for s in subscribers)
    
    def get_subscriber_count(self, event_type: str) -> int:
        """
        Get the number of active subscribers for an event type.
        
        Args:
            event_type: Type of event to check
            
        Returns:
            int: Number of active subscribers
        """
        with self._lock:
            subscribers = self._subscriptions.get(event_type, [])
            return sum(1 for s in subscribers if s.is_valid)
    
    def get_event_types(self) -> Set[str]:
        """
        Get all event types that have subscribers.
        
        Returns:
            Set[str]: Set of event types
        """
        with self._lock:
            return set(self._subscriptions.keys())
    
    def get_recent_events(self, count: int = 10, event_type: Optional[str] = None) -> List[EventData]:
        """
        Get recent events from history.
        
        Args:
            count: Maximum number of events to return
            event_type: Optional filter by event type
            
        Returns:
            List[EventData]: Recent events
        """
        with self._lock:
            events = self._event_history
            
            if event_type:
                events = [e for e in events if e.event_type == event_type]
            
            return events[-count:] if count > 0 else events
    
    def clear_history(self) -> None:
        """Clear event history."""
        with self._lock:
            self._event_history.clear()
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get event bus statistics.
        
        Returns:
            Dict[str, Any]: Statistics including event counts and subscription info
        """
        with self._lock:
            stats = dict(self._stats)
            stats.update({
                'active_event_types': len(self._subscriptions),
                'total_active_subscriptions': sum(
                    sum(1 for s in subs if s.is_valid)
                    for subs in self._subscriptions.values()
                ),
                'history_size': len(self._event_history),
                'max_history_size': self._max_history
            })
            return stats
    
    def cleanup(self) -> int:
        """
        Clean up invalid subscriptions and old history.
        
        Returns:
            int: Number of invalid subscriptions removed
        """
        with self._lock:
            removed_count = 0
            
            for event_type in list(self._subscriptions.keys()):
                valid_subscriptions = [
                    s for s in self._subscriptions[event_type] if s.is_valid
                ]
                
                removed = len(self._subscriptions[event_type]) - len(valid_subscriptions)
                removed_count += removed
                
                if valid_subscriptions:
                    self._subscriptions[event_type] = valid_subscriptions
                else:
                    del self._subscriptions[event_type]
            
            self._stats['subscriptions_removed'] += removed_count
            
            if self._enable_logging:
                self._logger.debug(f"Cleaned up {removed_count} invalid subscriptions")
            
            return removed_count
    
    def shutdown(self) -> None:
        """Shutdown the event bus and clean up resources."""
        with self._lock:
            self._subscriptions.clear()
            self._event_history.clear()
            
            if self._enable_logging:
                self._logger.info("Event bus shutdown complete")


# Global event bus instance for convenience
_global_event_bus: Optional[EventBus] = None


def get_global_event_bus() -> EventBus:
    """
    Get the global event bus instance.
    
    Returns:
        EventBus: Global event bus instance
    """
    global _global_event_bus
    if _global_event_bus is None:
        _global_event_bus = EventBus()
    return _global_event_bus


def set_global_event_bus(event_bus: EventBus) -> None:
    """
    Set the global event bus instance.
    
    Args:
        event_bus: EventBus instance to use as global
    """
    global _global_event_bus
    _global_event_bus = event_bus


# Convenience functions for global event bus
def subscribe(event_type: str, callback: Callable, **kwargs) -> EventSubscription:
    """Subscribe to event using global event bus."""
    return get_global_event_bus().subscribe(event_type, callback, **kwargs)


def unsubscribe(event_type: str, subscription: EventSubscription) -> bool:
    """Unsubscribe from event using global event bus."""
    return get_global_event_bus().unsubscribe(event_type, subscription)


def publish(event_type: str, data: Any = None, **kwargs) -> int:
    """Publish event using global event bus."""
    return get_global_event_bus().publish(event_type, data, **kwargs)