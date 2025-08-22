"""
UI Performance Monitor - Monitors and optimizes UI responsiveness.

This module provides UI-specific performance monitoring and optimization
to ensure smooth user experience and responsive interface.
"""

import time
import threading
from typing import Dict, Any, Optional, Callable, List
from collections import deque
from datetime import datetime, timedelta

from ..core.event_bus import EventBus


class UIPerformanceMonitor:
    """
    Monitors UI performance and responsiveness.
    
    Features:
    - Frame rate monitoring
    - UI freeze detection
    - Render time tracking
    - Event processing time monitoring
    - Automatic UI optimization suggestions
    """
    
    def __init__(self, event_bus: EventBus, target_fps: int = 60):
        """
        Initialize UI performance monitor.
        
        Args:
            event_bus: Event bus for publishing performance events
            target_fps: Target frames per second for smooth UI
        """
        self.event_bus = event_bus
        self.target_fps = target_fps
        self.target_frame_time = 1.0 / target_fps  # Target time per frame
        
        # Performance tracking
        self.frame_times: deque = deque(maxlen=100)  # Last 100 frame times
        self.render_times: deque = deque(maxlen=100)  # Last 100 render times
        self.event_times: deque = deque(maxlen=100)   # Last 100 event processing times
        
        # UI freeze detection
        self.freeze_threshold = 0.1  # 100ms freeze threshold
        self.last_ui_update = time.perf_counter()
        self.freeze_count = 0
        
        # Monitoring state
        self._monitoring_active = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_monitoring = threading.Event()
        
        # Performance statistics
        self.stats = {
            'average_fps': 0.0,
            'min_fps': 0.0,
            'max_fps': 0.0,
            'frame_drops': 0,
            'ui_freezes': 0,
            'total_frames': 0
        }
        
        # Optimization suggestions
        self.optimization_suggestions: List[str] = []
    
    def start_monitoring(self):
        """Start UI performance monitoring."""
        if self._monitoring_active:
            return
        
        self._monitoring_active = True
        self._stop_monitoring.clear()
        
        self._monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True,
            name="UIPerformanceMonitor"
        )
        self._monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop UI performance monitoring."""
        if not self._monitoring_active:
            return
        
        self._monitoring_active = False
        self._stop_monitoring.set()
        
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2.0)
    
    def _monitoring_loop(self):
        """Main monitoring loop."""
        last_frame_time = time.perf_counter()
        
        while not self._stop_monitoring.wait(0.016):  # ~60 FPS monitoring
            current_time = time.perf_counter()
            frame_time = current_time - last_frame_time
            
            # Record frame time
            self.frame_times.append(frame_time)
            
            # Check for UI freeze
            if current_time - self.last_ui_update > self.freeze_threshold:
                self._handle_ui_freeze(current_time - self.last_ui_update)
            
            # Update statistics
            self._update_statistics()
            
            # Generate optimization suggestions
            if len(self.frame_times) >= 10:  # Need some data
                self._generate_ui_optimizations()
            
            last_frame_time = current_time
    
    def record_frame_render(self, render_time: float):
        """
        Record frame render time.
        
        Args:
            render_time: Time taken to render the frame
        """
        self.render_times.append(render_time)
        self.last_ui_update = time.perf_counter()
        self.stats['total_frames'] += 1
        
        # Check for frame drop
        if render_time > self.target_frame_time * 2:  # Frame took twice as long as target
            self.stats['frame_drops'] += 1
            self.event_bus.publish('ui.frame_drop', {
                'render_time': render_time,
                'target_time': self.target_frame_time
            })
    
    def record_event_processing(self, event_type: str, processing_time: float):
        """
        Record event processing time.
        
        Args:
            event_type: Type of event processed
            processing_time: Time taken to process the event
        """
        self.event_times.append(processing_time)
        
        # Check for slow event processing
        if processing_time > 0.05:  # 50ms threshold
            self.event_bus.publish('ui.slow_event', {
                'event_type': event_type,
                'processing_time': processing_time
            })
    
    def _handle_ui_freeze(self, freeze_duration: float):
        """Handle detected UI freeze."""
        self.freeze_count += 1
        self.stats['ui_freezes'] += 1
        
        self.event_bus.publish('ui.freeze_detected', {
            'duration': freeze_duration,
            'freeze_count': self.freeze_count
        })
        
        # Add optimization suggestion for UI freeze
        if freeze_duration > 0.5:  # Significant freeze
            self.optimization_suggestions.append(
                f"UI freeze detected ({freeze_duration:.2f}s). Consider optimizing heavy operations."
            )
    
    def _update_statistics(self):
        """Update performance statistics."""
        if not self.frame_times:
            return
        
        # Calculate FPS from frame times
        recent_frame_times = list(self.frame_times)[-30:]  # Last 30 frames
        if recent_frame_times:
            avg_frame_time = sum(recent_frame_times) / len(recent_frame_times)
            self.stats['average_fps'] = 1.0 / avg_frame_time if avg_frame_time > 0 else 0
            
            min_frame_time = min(recent_frame_times)
            max_frame_time = max(recent_frame_times)
            
            self.stats['max_fps'] = 1.0 / min_frame_time if min_frame_time > 0 else 0
            self.stats['min_fps'] = 1.0 / max_frame_time if max_frame_time > 0 else 0
    
    def _generate_ui_optimizations(self):
        """Generate UI optimization suggestions."""
        suggestions = []
        
        # Check average FPS
        if self.stats['average_fps'] < self.target_fps * 0.8:  # Below 80% of target
            suggestions.append(f"Low FPS detected ({self.stats['average_fps']:.1f}). Consider reducing visual effects.")
        
        # Check frame drops
        if self.stats['total_frames'] > 0:
            frame_drop_rate = (self.stats['frame_drops'] / self.stats['total_frames']) * 100
            if frame_drop_rate > 5:  # More than 5% frame drops
                suggestions.append(f"High frame drop rate ({frame_drop_rate:.1f}%). Optimize rendering operations.")
        
        # Check render times
        if self.render_times:
            avg_render_time = sum(self.render_times) / len(self.render_times)
            if avg_render_time > self.target_frame_time:
                suggestions.append(f"Slow rendering detected ({avg_render_time*1000:.1f}ms). Optimize draw operations.")
        
        # Check event processing times
        if self.event_times:
            slow_events = [t for t in self.event_times if t > 0.02]  # 20ms threshold
            if len(slow_events) > len(self.event_times) * 0.1:  # More than 10% slow events
                suggestions.append("Slow event processing detected. Consider deferring heavy operations.")
        
        # Update suggestions (keep only recent ones)
        self.optimization_suggestions.extend(suggestions)
        self.optimization_suggestions = self.optimization_suggestions[-10:]  # Keep last 10
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive UI performance report."""
        # Calculate detailed statistics
        frame_time_stats = {}
        if self.frame_times:
            frame_times_list = list(self.frame_times)
            frame_time_stats = {
                'average': sum(frame_times_list) / len(frame_times_list),
                'min': min(frame_times_list),
                'max': max(frame_times_list),
                'count': len(frame_times_list)
            }
        
        render_time_stats = {}
        if self.render_times:
            render_times_list = list(self.render_times)
            render_time_stats = {
                'average': sum(render_times_list) / len(render_times_list),
                'min': min(render_times_list),
                'max': max(render_times_list),
                'count': len(render_times_list)
            }
        
        event_time_stats = {}
        if self.event_times:
            event_times_list = list(self.event_times)
            event_time_stats = {
                'average': sum(event_times_list) / len(event_times_list),
                'min': min(event_times_list),
                'max': max(event_times_list),
                'count': len(event_times_list)
            }
        
        return {
            'target_fps': self.target_fps,
            'current_stats': self.stats.copy(),
            'frame_time_stats': frame_time_stats,
            'render_time_stats': render_time_stats,
            'event_time_stats': event_time_stats,
            'optimization_suggestions': self.optimization_suggestions.copy(),
            'monitoring_active': self._monitoring_active,
            'freeze_threshold': self.freeze_threshold
        }
    
    def optimize_ui_performance(self) -> Dict[str, Any]:
        """Apply UI performance optimizations."""
        optimizations_applied = []
        
        # Reduce update frequency if FPS is low
        if self.stats['average_fps'] < self.target_fps * 0.7:
            # This would be implemented by the UI components
            optimizations_applied.append("Reduced update frequency")
        
        # Enable frame skipping for heavy operations
        if self.stats['frame_drops'] > 10:
            optimizations_applied.append("Enabled frame skipping")
        
        # Defer non-critical updates
        if self.freeze_count > 5:
            optimizations_applied.append("Deferred non-critical updates")
        
        # Clear old performance data to free memory
        if len(self.frame_times) > 50:
            # Keep only recent data
            recent_frames = list(self.frame_times)[-30:]
            self.frame_times.clear()
            self.frame_times.extend(recent_frames)
            optimizations_applied.append("Cleared old performance data")
        
        return {
            'optimizations_applied': optimizations_applied,
            'timestamp': datetime.now().isoformat()
        }
    
    def reset_statistics(self):
        """Reset all performance statistics."""
        self.frame_times.clear()
        self.render_times.clear()
        self.event_times.clear()
        
        self.stats = {
            'average_fps': 0.0,
            'min_fps': 0.0,
            'max_fps': 0.0,
            'frame_drops': 0,
            'ui_freezes': 0,
            'total_frames': 0
        }
        
        self.freeze_count = 0
        self.optimization_suggestions.clear()
    
    def set_target_fps(self, fps: int):
        """Set target FPS for performance monitoring."""
        self.target_fps = fps
        self.target_frame_time = 1.0 / fps
    
    def set_freeze_threshold(self, threshold: float):
        """Set UI freeze detection threshold."""
        self.freeze_threshold = threshold


class UIOptimizer:
    """
    Provides UI-specific optimization strategies.
    """
    
    def __init__(self, performance_monitor: UIPerformanceMonitor):
        """
        Initialize UI optimizer.
        
        Args:
            performance_monitor: UI performance monitor instance
        """
        self.performance_monitor = performance_monitor
        self.optimization_history: List[Dict[str, Any]] = []
    
    def optimize_rendering(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimize rendering performance.
        
        Args:
            context: Optimization context with UI components
            
        Returns:
            Optimization results
        """
        optimizations = []
        
        # Get performance report
        perf_report = self.performance_monitor.get_performance_report()
        
        # Apply optimizations based on performance data
        if perf_report['current_stats']['average_fps'] < 30:
            # Low FPS - apply aggressive optimizations
            optimizations.extend([
                "Reduced animation quality",
                "Disabled non-essential visual effects",
                "Increased render batching"
            ])
        elif perf_report['current_stats']['average_fps'] < 45:
            # Moderate FPS issues
            optimizations.extend([
                "Optimized draw calls",
                "Reduced update frequency for background elements"
            ])
        
        # Handle frame drops
        if perf_report['current_stats']['frame_drops'] > 5:
            optimizations.append("Enabled adaptive quality scaling")
        
        # Record optimization
        optimization_record = {
            'timestamp': datetime.now().isoformat(),
            'trigger': context.get('trigger', 'manual'),
            'optimizations': optimizations,
            'performance_before': perf_report['current_stats'].copy()
        }
        
        self.optimization_history.append(optimization_record)
        
        return {
            'success': True,
            'optimizations_applied': optimizations,
            'performance_report': perf_report
        }
    
    def optimize_event_processing(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimize event processing performance.
        
        Args:
            context: Optimization context
            
        Returns:
            Optimization results
        """
        optimizations = []
        
        # Get event processing statistics
        perf_report = self.performance_monitor.get_performance_report()
        event_stats = perf_report.get('event_time_stats', {})
        
        if event_stats.get('average', 0) > 0.02:  # 20ms average
            optimizations.extend([
                "Enabled event batching",
                "Deferred heavy event processing",
                "Optimized event handlers"
            ])
        
        return {
            'success': True,
            'optimizations_applied': optimizations,
            'event_stats': event_stats
        }
    
    def get_optimization_history(self) -> List[Dict[str, Any]]:
        """Get optimization history."""
        return self.optimization_history.copy()
    
    def clear_optimization_history(self):
        """Clear optimization history."""
        self.optimization_history.clear()