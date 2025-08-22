"""
Performance Profiler - Application performance monitoring and optimization.

This module provides comprehensive performance monitoring, profiling, and optimization
capabilities for the Enhanced Color Picker application.
"""

import time
import threading
import psutil
import gc
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import weakref

from .event_bus import EventBus


@dataclass
class PerformanceMetric:
    """Performance metric data structure."""
    name: str
    value: float
    unit: str
    timestamp: datetime = field(default_factory=datetime.now)
    category: str = "general"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProfileResult:
    """Profiling result data structure."""
    function_name: str
    execution_time: float
    memory_usage: float
    cpu_usage: float
    call_count: int = 1
    average_time: float = 0.0
    max_time: float = 0.0
    min_time: float = float('inf')


class PerformanceProfiler:
    """
    Comprehensive performance profiler for monitoring application performance.
    
    Features:
    - Function execution time profiling
    - Memory usage monitoring
    - CPU usage tracking
    - UI responsiveness monitoring
    - Automatic optimization suggestions
    - Performance bottleneck detection
    """
    
    def __init__(self, event_bus: EventBus, enable_profiling: bool = True):
        """
        Initialize performance profiler.
        
        Args:
            event_bus: Event bus for publishing performance events
            enable_profiling: Whether to enable profiling (can be disabled for production)
        """
        self.event_bus = event_bus
        self.enable_profiling = enable_profiling
        
        # Profiling data
        self.function_profiles: Dict[str, ProfileResult] = {}
        self.metrics_history: deque = deque(maxlen=1000)  # Keep last 1000 metrics
        self.performance_warnings: List[str] = []
        
        # Monitoring state
        self._monitoring_active = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_monitoring = threading.Event()
        
        # Performance thresholds
        self.thresholds = {
            'function_time_warning': 0.1,  # 100ms
            'function_time_critical': 0.5,  # 500ms
            'memory_usage_warning': 80,     # 80% of available memory
            'memory_usage_critical': 90,    # 90% of available memory
            'cpu_usage_warning': 80,        # 80% CPU usage
            'cpu_usage_critical': 95,       # 95% CPU usage
            'ui_freeze_threshold': 0.05     # 50ms UI freeze threshold
        }
        
        # Optimization suggestions
        self.optimization_suggestions: List[str] = []
        
        # Weak references to monitored objects
        self._monitored_objects: List[weakref.ref] = []
    
    def profile_function(self, func_name: str = None):
        """
        Decorator for profiling function execution.
        
        Args:
            func_name: Custom function name for profiling
        """
        def decorator(func):
            if not self.enable_profiling:
                return func
            
            name = func_name or f"{func.__module__}.{func.__name__}"
            
            def wrapper(*args, **kwargs):
                start_time = time.perf_counter()
                start_memory = self._get_memory_usage()
                start_cpu = self._get_cpu_usage()
                
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    end_time = time.perf_counter()
                    end_memory = self._get_memory_usage()
                    end_cpu = self._get_cpu_usage()
                    
                    execution_time = end_time - start_time
                    memory_delta = end_memory - start_memory
                    cpu_delta = end_cpu - start_cpu
                    
                    self._record_function_profile(name, execution_time, memory_delta, cpu_delta)
            
            return wrapper
        return decorator
    
    def _record_function_profile(self, func_name: str, execution_time: float, 
                                memory_delta: float, cpu_delta: float):
        """Record function profiling data."""
        if func_name in self.function_profiles:
            profile = self.function_profiles[func_name]
            profile.call_count += 1
            profile.execution_time += execution_time
            profile.memory_usage += memory_delta
            profile.cpu_usage += cpu_delta
            profile.average_time = profile.execution_time / profile.call_count
            profile.max_time = max(profile.max_time, execution_time)
            profile.min_time = min(profile.min_time, execution_time)
        else:
            self.function_profiles[func_name] = ProfileResult(
                function_name=func_name,
                execution_time=execution_time,
                memory_usage=memory_delta,
                cpu_usage=cpu_delta,
                average_time=execution_time,
                max_time=execution_time,
                min_time=execution_time
            )
        
        # Check for performance warnings
        self._check_performance_thresholds(func_name, execution_time)
    
    def _check_performance_thresholds(self, func_name: str, execution_time: float):
        """Check if function execution exceeds performance thresholds."""
        if execution_time > self.thresholds['function_time_critical']:
            warning = f"CRITICAL: Function '{func_name}' took {execution_time:.3f}s to execute"
            self.performance_warnings.append(warning)
            self.event_bus.publish('performance.critical', {
                'function': func_name,
                'execution_time': execution_time,
                'threshold': self.thresholds['function_time_critical']
            })
        elif execution_time > self.thresholds['function_time_warning']:
            warning = f"WARNING: Function '{func_name}' took {execution_time:.3f}s to execute"
            self.performance_warnings.append(warning)
            self.event_bus.publish('performance.warning', {
                'function': func_name,
                'execution_time': execution_time,
                'threshold': self.thresholds['function_time_warning']
            })
    
    def start_monitoring(self, interval: float = 1.0):
        """
        Start continuous performance monitoring.
        
        Args:
            interval: Monitoring interval in seconds
        """
        if self._monitoring_active:
            return
        
        self._monitoring_active = True
        self._stop_monitoring.clear()
        
        self._monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(interval,),
            daemon=True,
            name="PerformanceMonitor"
        )
        self._monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop continuous performance monitoring."""
        if not self._monitoring_active:
            return
        
        self._monitoring_active = False
        self._stop_monitoring.set()
        
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2.0)
    
    def _monitoring_loop(self, interval: float):
        """Main monitoring loop."""
        while not self._stop_monitoring.wait(interval):
            try:
                # Collect system metrics
                memory_usage = self._get_memory_usage_percent()
                cpu_usage = self._get_cpu_usage()
                
                # Record metrics
                self._record_metric("memory_usage", memory_usage, "percent")
                self._record_metric("cpu_usage", cpu_usage, "percent")
                
                # Check thresholds
                self._check_system_thresholds(memory_usage, cpu_usage)
                
                # Clean up weak references
                self._cleanup_weak_references()
                
                # Generate optimization suggestions
                self._generate_optimization_suggestions()
                
            except Exception as e:
                # Don't let monitoring errors crash the application
                pass
    
    def _record_metric(self, name: str, value: float, unit: str, category: str = "system"):
        """Record a performance metric."""
        metric = PerformanceMetric(
            name=name,
            value=value,
            unit=unit,
            category=category
        )
        self.metrics_history.append(metric)
    
    def _check_system_thresholds(self, memory_usage: float, cpu_usage: float):
        """Check system resource thresholds."""
        # Memory usage checks
        if memory_usage > self.thresholds['memory_usage_critical']:
            self.event_bus.publish('memory.critical', {
                'usage_percent': memory_usage,
                'threshold': self.thresholds['memory_usage_critical']
            })
        elif memory_usage > self.thresholds['memory_usage_warning']:
            self.event_bus.publish('memory.warning', {
                'usage_percent': memory_usage,
                'threshold': self.thresholds['memory_usage_warning']
            })
        
        # CPU usage checks
        if cpu_usage > self.thresholds['cpu_usage_critical']:
            self.event_bus.publish('cpu.critical', {
                'usage_percent': cpu_usage,
                'threshold': self.thresholds['cpu_usage_critical']
            })
        elif cpu_usage > self.thresholds['cpu_usage_warning']:
            self.event_bus.publish('cpu.warning', {
                'usage_percent': cpu_usage,
                'threshold': self.thresholds['cpu_usage_warning']
            })
    
    def _generate_optimization_suggestions(self):
        """Generate optimization suggestions based on profiling data."""
        suggestions = []
        
        # Analyze function profiles for optimization opportunities
        for func_name, profile in self.function_profiles.items():
            if profile.average_time > self.thresholds['function_time_warning']:
                if profile.call_count > 10:  # Frequently called slow function
                    suggestions.append(f"Consider optimizing '{func_name}' - called {profile.call_count} times with average time {profile.average_time:.3f}s")
            
            if profile.memory_usage > 10 * 1024 * 1024:  # 10MB memory usage
                suggestions.append(f"Function '{func_name}' uses significant memory ({profile.memory_usage / 1024 / 1024:.1f}MB)")
        
        # Check for memory leaks
        current_memory = self._get_memory_usage()
        if len(self.metrics_history) > 100:
            old_memory = next((m.value for m in list(self.metrics_history)[-100:] if m.name == "memory_usage"), current_memory)
            if current_memory > old_memory * 1.5:  # 50% increase
                suggestions.append("Potential memory leak detected - memory usage has increased significantly")
        
        # Update suggestions
        self.optimization_suggestions = suggestions[-10:]  # Keep last 10 suggestions
    
    def _cleanup_weak_references(self):
        """Clean up dead weak references."""
        self._monitored_objects = [ref for ref in self._monitored_objects if ref() is not None]
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in bytes."""
        try:
            process = psutil.Process()
            return process.memory_info().rss
        except:
            return 0.0
    
    def _get_memory_usage_percent(self) -> float:
        """Get current memory usage as percentage."""
        try:
            return psutil.virtual_memory().percent
        except:
            return 0.0
    
    def _get_cpu_usage(self) -> float:
        """Get current CPU usage percentage."""
        try:
            return psutil.cpu_percent(interval=None)
        except:
            return 0.0
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        # Calculate statistics
        total_functions = len(self.function_profiles)
        slow_functions = sum(1 for p in self.function_profiles.values() 
                           if p.average_time > self.thresholds['function_time_warning'])
        
        # Get recent metrics
        recent_metrics = list(self.metrics_history)[-100:] if self.metrics_history else []
        
        # Memory statistics
        memory_metrics = [m for m in recent_metrics if m.name == "memory_usage"]
        avg_memory = sum(m.value for m in memory_metrics) / len(memory_metrics) if memory_metrics else 0
        
        # CPU statistics
        cpu_metrics = [m for m in recent_metrics if m.name == "cpu_usage"]
        avg_cpu = sum(m.value for m in cpu_metrics) / len(cpu_metrics) if cpu_metrics else 0
        
        return {
            'summary': {
                'total_functions_profiled': total_functions,
                'slow_functions': slow_functions,
                'performance_warnings': len(self.performance_warnings),
                'optimization_suggestions': len(self.optimization_suggestions)
            },
            'system_metrics': {
                'current_memory_usage': self._get_memory_usage(),
                'current_memory_percent': self._get_memory_usage_percent(),
                'average_memory_percent': avg_memory,
                'current_cpu_usage': self._get_cpu_usage(),
                'average_cpu_usage': avg_cpu
            },
            'function_profiles': {
                name: {
                    'call_count': profile.call_count,
                    'average_time': profile.average_time,
                    'max_time': profile.max_time,
                    'min_time': profile.min_time,
                    'total_time': profile.execution_time,
                    'memory_usage': profile.memory_usage
                }
                for name, profile in sorted(
                    self.function_profiles.items(),
                    key=lambda x: x[1].average_time,
                    reverse=True
                )[:20]  # Top 20 slowest functions
            },
            'warnings': self.performance_warnings[-20:],  # Last 20 warnings
            'optimization_suggestions': self.optimization_suggestions,
            'thresholds': self.thresholds
        }
    
    def optimize_memory(self):
        """Perform memory optimization."""
        # Force garbage collection
        collected = gc.collect()
        
        # Clear function profiles for functions not called recently
        cutoff_time = datetime.now() - timedelta(minutes=10)
        profiles_to_remove = []
        
        for func_name, profile in self.function_profiles.items():
            # Remove profiles for functions not called in the last 10 minutes
            # (This is a simplified check - in reality, we'd need to track last call time)
            if profile.call_count == 1 and profile.execution_time < 0.001:
                profiles_to_remove.append(func_name)
        
        for func_name in profiles_to_remove:
            del self.function_profiles[func_name]
        
        # Trim metrics history if it's getting too large
        if len(self.metrics_history) > 500:
            # Keep only the most recent 300 metrics
            recent_metrics = list(self.metrics_history)[-300:]
            self.metrics_history.clear()
            self.metrics_history.extend(recent_metrics)
        
        # Clear old warnings
        if len(self.performance_warnings) > 50:
            self.performance_warnings = self.performance_warnings[-25:]
        
        return {
            'garbage_collected': collected,
            'profiles_removed': len(profiles_to_remove),
            'metrics_trimmed': len(self.metrics_history),
            'warnings_cleared': len(self.performance_warnings)
        }
    
    def reset_profiling_data(self):
        """Reset all profiling data."""
        self.function_profiles.clear()
        self.metrics_history.clear()
        self.performance_warnings.clear()
        self.optimization_suggestions.clear()
    
    def set_threshold(self, threshold_name: str, value: float):
        """Set a performance threshold."""
        if threshold_name in self.thresholds:
            self.thresholds[threshold_name] = value
    
    def get_top_slow_functions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get the top slowest functions."""
        sorted_profiles = sorted(
            self.function_profiles.items(),
            key=lambda x: x[1].average_time,
            reverse=True
        )
        
        return [
            {
                'name': name,
                'average_time': profile.average_time,
                'call_count': profile.call_count,
                'total_time': profile.execution_time,
                'max_time': profile.max_time
            }
            for name, profile in sorted_profiles[:limit]
        ]
    
    def monitor_object(self, obj: Any, name: str = None):
        """Monitor an object for memory usage."""
        ref = weakref.ref(obj)
        self._monitored_objects.append(ref)
        
        # Record initial memory usage
        if name:
            try:
                import sys
                size = sys.getsizeof(obj)
                self._record_metric(f"object_size_{name}", size, "bytes", "objects")
            except:
                pass
    
    def shutdown(self):
        """Shutdown the performance profiler."""
        self.stop_monitoring()
        self.reset_profiling_data()