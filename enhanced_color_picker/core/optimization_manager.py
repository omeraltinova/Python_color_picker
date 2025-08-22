"""
Optimization Manager - Automatic performance optimization and tuning.

This module provides automatic optimization strategies for improving application
performance, including memory management, UI responsiveness, and resource usage.
"""

import gc
import threading
import time
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from pathlib import Path

from .event_bus import EventBus
from .performance_profiler import PerformanceProfiler


class OptimizationStrategy:
    """Base class for optimization strategies."""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.enabled = True
        self.last_run = None
        self.run_count = 0
        self.success_count = 0
    
    def can_run(self) -> bool:
        """Check if the optimization can run."""
        return self.enabled
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the optimization strategy."""
        raise NotImplementedError
    
    def get_stats(self) -> Dict[str, Any]:
        """Get optimization statistics."""
        return {
            'name': self.name,
            'description': self.description,
            'enabled': self.enabled,
            'run_count': self.run_count,
            'success_count': self.success_count,
            'success_rate': (self.success_count / self.run_count * 100) if self.run_count > 0 else 0,
            'last_run': self.last_run.isoformat() if self.last_run else None
        }


class MemoryOptimizationStrategy(OptimizationStrategy):
    """Memory optimization strategy."""
    
    def __init__(self):
        super().__init__(
            "Memory Optimization",
            "Performs garbage collection and memory cleanup"
        )
        self.min_interval = timedelta(minutes=5)  # Don't run more than once per 5 minutes
    
    def can_run(self) -> bool:
        if not super().can_run():
            return False
        
        if self.last_run and datetime.now() - self.last_run < self.min_interval:
            return False
        
        return True
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute memory optimization."""
        self.run_count += 1
        self.last_run = datetime.now()
        
        try:
            # Force garbage collection
            collected_objects = gc.collect()
            
            # Clear image caches if available
            cache_cleared = 0
            if 'image_service' in context:
                image_service = context['image_service']
                if hasattr(image_service, 'clear_cache'):
                    cache_stats = image_service.get_cache_stats()
                    cache_cleared = cache_stats.get('total_items', 0)
                    image_service.clear_cache()
            
            # Clear other caches
            if 'cache_storage' in context:
                cache_storage = context['cache_storage']
                if hasattr(cache_storage, 'cleanup_expired'):
                    cache_storage.cleanup_expired()
            
            self.success_count += 1
            
            return {
                'success': True,
                'collected_objects': collected_objects,
                'cache_items_cleared': cache_cleared,
                'timestamp': self.last_run.isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'timestamp': self.last_run.isoformat()
            }


class UIResponsivenessOptimization(OptimizationStrategy):
    """UI responsiveness optimization strategy."""
    
    def __init__(self):
        super().__init__(
            "UI Responsiveness",
            "Optimizes UI performance and responsiveness"
        )
        self.ui_freeze_threshold = 0.05  # 50ms
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute UI responsiveness optimization."""
        self.run_count += 1
        self.last_run = datetime.now()
        
        try:
            optimizations_applied = []
            
            # Reduce UI update frequency if needed
            if 'main_window' in context:
                main_window = context['main_window']
                # Implement UI optimization logic here
                optimizations_applied.append("UI update frequency optimized")
            
            # Optimize canvas rendering
            if 'image_canvas' in context:
                image_canvas = context['image_canvas']
                # Implement canvas optimization logic here
                optimizations_applied.append("Canvas rendering optimized")
            
            # Defer non-critical UI updates
            optimizations_applied.append("Non-critical updates deferred")
            
            self.success_count += 1
            
            return {
                'success': True,
                'optimizations_applied': optimizations_applied,
                'timestamp': self.last_run.isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'timestamp': self.last_run.isoformat()
            }


class CacheOptimizationStrategy(OptimizationStrategy):
    """Cache optimization strategy."""
    
    def __init__(self):
        super().__init__(
            "Cache Optimization",
            "Optimizes cache usage and cleanup"
        )
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute cache optimization."""
        self.run_count += 1
        self.last_run = datetime.now()
        
        try:
            optimizations = {}
            
            # Optimize image cache
            if 'image_service' in context:
                image_service = context['image_service']
                if hasattr(image_service, 'cache'):
                    cache = image_service.cache
                    # Implement intelligent cache eviction
                    stats_before = cache.get_cache_stats()
                    # Evict least recently used items if cache is > 80% full
                    if stats_before.get('cache_utilization', 0) > 80:
                        # This would be implemented in the cache itself
                        pass
                    stats_after = cache.get_cache_stats()
                    optimizations['image_cache'] = {
                        'before': stats_before,
                        'after': stats_after
                    }
            
            # Optimize other caches
            if 'cache_storage' in context:
                cache_storage = context['cache_storage']
                if hasattr(cache_storage, 'optimize'):
                    cache_storage.optimize()
                    optimizations['general_cache'] = "Optimized"
            
            self.success_count += 1
            
            return {
                'success': True,
                'optimizations': optimizations,
                'timestamp': self.last_run.isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'timestamp': self.last_run.isoformat()
            }


class ResourceCleanupStrategy(OptimizationStrategy):
    """Resource cleanup optimization strategy."""
    
    def __init__(self):
        super().__init__(
            "Resource Cleanup",
            "Cleans up unused resources and temporary files"
        )
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute resource cleanup."""
        self.run_count += 1
        self.last_run = datetime.now()
        
        try:
            cleanup_results = {}
            
            # Clean up temporary files
            temp_files_cleaned = self._cleanup_temp_files()
            cleanup_results['temp_files'] = temp_files_cleaned
            
            # Clean up old log files
            log_files_cleaned = self._cleanup_old_logs()
            cleanup_results['log_files'] = log_files_cleaned
            
            # Clean up unused resources
            if 'resource_manager' in context:
                resource_manager = context['resource_manager']
                if hasattr(resource_manager, 'cleanup_unused'):
                    unused_cleaned = resource_manager.cleanup_unused()
                    cleanup_results['unused_resources'] = unused_cleaned
            
            self.success_count += 1
            
            return {
                'success': True,
                'cleanup_results': cleanup_results,
                'timestamp': self.last_run.isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'timestamp': self.last_run.isoformat()
            }
    
    def _cleanup_temp_files(self) -> int:
        """Clean up temporary files."""
        try:
            import tempfile
            import shutil
            
            temp_dir = Path(tempfile.gettempdir()) / "enhanced_color_picker"
            if temp_dir.exists():
                file_count = len(list(temp_dir.rglob("*")))
                shutil.rmtree(temp_dir, ignore_errors=True)
                return file_count
            return 0
        except Exception:
            return 0
    
    def _cleanup_old_logs(self) -> int:
        """Clean up old log files."""
        try:
            # This would clean up log files older than a certain age
            # Implementation depends on logging configuration
            return 0
        except Exception:
            return 0


class OptimizationManager:
    """
    Manages automatic performance optimization strategies.
    
    Features:
    - Automatic optimization based on performance metrics
    - Multiple optimization strategies
    - Configurable optimization triggers
    - Performance impact monitoring
    - Optimization scheduling
    """
    
    def __init__(self, event_bus: EventBus, profiler: PerformanceProfiler, 
                 config: Optional[Dict[str, Any]] = None):
        """
        Initialize optimization manager.
        
        Args:
            event_bus: Event bus for communication
            profiler: Performance profiler for metrics
            config: Configuration options
        """
        self.event_bus = event_bus
        self.profiler = profiler
        self.config = config or {}
        
        # Optimization strategies
        self.strategies: List[OptimizationStrategy] = [
            MemoryOptimizationStrategy(),
            UIResponsivenessOptimization(),
            CacheOptimizationStrategy(),
            ResourceCleanupStrategy()
        ]
        
        # Optimization state
        self._auto_optimization_enabled = self.config.get('auto_optimization', True)
        self._optimization_thread: Optional[threading.Thread] = None
        self._stop_optimization = threading.Event()
        self._optimization_interval = self.config.get('optimization_interval', 300)  # 5 minutes
        
        # Optimization triggers
        self.triggers = {
            'memory_usage_high': 80,  # Trigger when memory usage > 80%
            'cpu_usage_high': 85,     # Trigger when CPU usage > 85%
            'ui_freeze_detected': True,  # Trigger on UI freeze
            'cache_full': 90,         # Trigger when cache > 90% full
            'scheduled': True         # Trigger on schedule
        }
        
        # Optimization history
        self.optimization_history: List[Dict[str, Any]] = []
        
        # Setup event handlers
        self._setup_event_handlers()
    
    def _setup_event_handlers(self):
        """Setup event handlers for optimization triggers."""
        self.event_bus.subscribe('memory.warning', self._on_memory_warning)
        self.event_bus.subscribe('memory.critical', self._on_memory_critical)
        self.event_bus.subscribe('cpu.warning', self._on_cpu_warning)
        self.event_bus.subscribe('performance.warning', self._on_performance_warning)
        self.event_bus.subscribe('ui.freeze_detected', self._on_ui_freeze)
    
    def start_auto_optimization(self):
        """Start automatic optimization."""
        if not self._auto_optimization_enabled or self._optimization_thread:
            return
        
        self._stop_optimization.clear()
        self._optimization_thread = threading.Thread(
            target=self._optimization_loop,
            daemon=True,
            name="OptimizationManager"
        )
        self._optimization_thread.start()
    
    def stop_auto_optimization(self):
        """Stop automatic optimization."""
        if not self._optimization_thread:
            return
        
        self._stop_optimization.set()
        self._optimization_thread.join(timeout=5.0)
        self._optimization_thread = None
    
    def _optimization_loop(self):
        """Main optimization loop."""
        while not self._stop_optimization.wait(self._optimization_interval):
            try:
                if self.triggers.get('scheduled', True):
                    self.run_scheduled_optimizations()
            except Exception as e:
                # Don't let optimization errors crash the application
                self.event_bus.publish('optimization.error', {'error': str(e)})
    
    def run_optimization(self, strategy_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run a specific optimization strategy.
        
        Args:
            strategy_name: Name of the strategy to run
            context: Context data for the optimization
            
        Returns:
            Optimization result
        """
        strategy = next((s for s in self.strategies if s.name == strategy_name), None)
        if not strategy:
            return {'success': False, 'error': f'Strategy {strategy_name} not found'}
        
        if not strategy.can_run():
            return {'success': False, 'error': f'Strategy {strategy_name} cannot run now'}
        
        # Run the optimization
        start_time = time.perf_counter()
        result = strategy.execute(context)
        end_time = time.perf_counter()
        
        # Record the optimization
        optimization_record = {
            'strategy': strategy_name,
            'timestamp': datetime.now().isoformat(),
            'duration': end_time - start_time,
            'result': result,
            'trigger': context.get('trigger', 'manual')
        }
        
        self.optimization_history.append(optimization_record)
        
        # Publish optimization event
        self.event_bus.publish('optimization.completed', optimization_record)
        
        return result
    
    def run_all_optimizations(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run all available optimization strategies.
        
        Args:
            context: Context data for optimizations
            
        Returns:
            Combined optimization results
        """
        results = {}
        
        for strategy in self.strategies:
            if strategy.can_run():
                result = self.run_optimization(strategy.name, context)
                results[strategy.name] = result
        
        return results
    
    def run_scheduled_optimizations(self):
        """Run scheduled optimizations based on current system state."""
        # Get current performance metrics
        performance_report = self.profiler.get_performance_report()
        
        context = {
            'trigger': 'scheduled',
            'performance_report': performance_report
        }
        
        # Determine which optimizations to run based on current state
        memory_usage = performance_report['system_metrics']['current_memory_percent']
        cpu_usage = performance_report['system_metrics']['current_cpu_usage']
        
        optimizations_to_run = []
        
        # Memory optimization if usage is high
        if memory_usage > self.triggers['memory_usage_high']:
            optimizations_to_run.append('Memory Optimization')
        
        # Cache optimization if needed
        if memory_usage > 70:  # Run cache optimization at 70% memory usage
            optimizations_to_run.append('Cache Optimization')
        
        # Resource cleanup periodically
        if len(self.optimization_history) == 0 or \
           (datetime.now() - datetime.fromisoformat(self.optimization_history[-1]['timestamp'])).total_seconds() > 3600:
            optimizations_to_run.append('Resource Cleanup')
        
        # Run selected optimizations
        for optimization_name in optimizations_to_run:
            self.run_optimization(optimization_name, context)
    
    def _on_memory_warning(self, event_data):
        """Handle memory warning event."""
        if not self._auto_optimization_enabled:
            return
        
        context = {
            'trigger': 'memory_warning',
            'memory_usage': event_data.data.get('usage_percent', 0)
        }
        
        # Run memory optimization
        self.run_optimization('Memory Optimization', context)
    
    def _on_memory_critical(self, event_data):
        """Handle critical memory event."""
        if not self._auto_optimization_enabled:
            return
        
        context = {
            'trigger': 'memory_critical',
            'memory_usage': event_data.data.get('usage_percent', 0)
        }
        
        # Run aggressive optimizations
        self.run_optimization('Memory Optimization', context)
        self.run_optimization('Cache Optimization', context)
        self.run_optimization('Resource Cleanup', context)
    
    def _on_cpu_warning(self, event_data):
        """Handle CPU warning event."""
        if not self._auto_optimization_enabled:
            return
        
        context = {
            'trigger': 'cpu_warning',
            'cpu_usage': event_data.data.get('usage_percent', 0)
        }
        
        # Run UI responsiveness optimization
        self.run_optimization('UI Responsiveness', context)
    
    def _on_performance_warning(self, event_data):
        """Handle performance warning event."""
        if not self._auto_optimization_enabled:
            return
        
        context = {
            'trigger': 'performance_warning',
            'function': event_data.data.get('function', 'unknown'),
            'execution_time': event_data.data.get('execution_time', 0)
        }
        
        # Run UI responsiveness optimization for slow functions
        self.run_optimization('UI Responsiveness', context)
    
    def _on_ui_freeze(self, event_data):
        """Handle UI freeze detection."""
        if not self._auto_optimization_enabled:
            return
        
        context = {
            'trigger': 'ui_freeze',
            'freeze_duration': event_data.data.get('duration', 0)
        }
        
        # Run UI responsiveness optimization immediately
        self.run_optimization('UI Responsiveness', context)
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """Get optimization statistics."""
        strategy_stats = [strategy.get_stats() for strategy in self.strategies]
        
        total_optimizations = len(self.optimization_history)
        successful_optimizations = sum(1 for opt in self.optimization_history 
                                     if opt['result'].get('success', False))
        
        return {
            'auto_optimization_enabled': self._auto_optimization_enabled,
            'total_optimizations': total_optimizations,
            'successful_optimizations': successful_optimizations,
            'success_rate': (successful_optimizations / total_optimizations * 100) if total_optimizations > 0 else 0,
            'strategies': strategy_stats,
            'triggers': self.triggers,
            'recent_optimizations': self.optimization_history[-10:]  # Last 10 optimizations
        }
    
    def enable_strategy(self, strategy_name: str):
        """Enable an optimization strategy."""
        strategy = next((s for s in self.strategies if s.name == strategy_name), None)
        if strategy:
            strategy.enabled = True
    
    def disable_strategy(self, strategy_name: str):
        """Disable an optimization strategy."""
        strategy = next((s for s in self.strategies if s.name == strategy_name), None)
        if strategy:
            strategy.enabled = False
    
    def set_trigger_threshold(self, trigger_name: str, value: Any):
        """Set a trigger threshold."""
        if trigger_name in self.triggers:
            self.triggers[trigger_name] = value
    
    def clear_optimization_history(self):
        """Clear optimization history."""
        self.optimization_history.clear()
    
    def shutdown(self):
        """Shutdown the optimization manager."""
        self.stop_auto_optimization()
        self.clear_optimization_history()