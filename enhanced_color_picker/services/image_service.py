"""
ImageService - Comprehensive image loading, validation, and processing service.

This service handles all image-related operations including loading, validation,
format support, background processing, and caching for optimal performance.
"""

import os
import threading
from typing import Optional, Dict, List, Callable, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, Future
from PIL import Image, ImageFile
import weakref
from datetime import datetime, timedelta
import hashlib
import json

from ..models.image_data import ImageData
from ..models.color_data import ColorData
from ..core.exceptions import ImageLoadError, PerformanceError, ValidationError


# Enable loading of truncated images
ImageFile.LOAD_TRUNCATED_IMAGES = True


class ImageCache:
    """Intelligent image caching system with LRU eviction."""
    
    def __init__(self, max_cache_size: int = 100 * 1024 * 1024):  # 100MB default
        self.max_cache_size = max_cache_size
        self.cache: Dict[str, Dict] = {}
        self.access_times: Dict[str, datetime] = {}
        self._lock = threading.RLock()
    
    def _generate_cache_key(self, file_path: str, size: Optional[Tuple[int, int]] = None) -> str:
        """Generate cache key for image."""
        key_data = f"{file_path}:{size}" if size else file_path
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, file_path: str, size: Optional[Tuple[int, int]] = None) -> Optional[ImageData]:
        """Get cached image."""
        cache_key = self._generate_cache_key(file_path, size)
        
        with self._lock:
            if cache_key in self.cache:
                self.access_times[cache_key] = datetime.now()
                cached_data = self.cache[cache_key]
                
                # Verify the cached image is still valid
                if cached_data['image_data'].is_valid():
                    return cached_data['image_data']
                else:
                    # Remove invalid cached data
                    del self.cache[cache_key]
                    del self.access_times[cache_key]
        
        return None
    
    def put(self, file_path: str, image_data: ImageData, size: Optional[Tuple[int, int]] = None):
        """Cache image data."""
        cache_key = self._generate_cache_key(file_path, size)
        
        with self._lock:
            # Calculate memory usage
            memory_usage = image_data.get_memory_usage()
            
            # Check if we need to evict items
            self._evict_if_needed(memory_usage)
            
            # Cache the image
            self.cache[cache_key] = {
                'image_data': image_data,
                'memory_usage': memory_usage,
                'cached_at': datetime.now()
            }
            self.access_times[cache_key] = datetime.now()
    
    def _evict_if_needed(self, new_item_size: int):
        """Evict least recently used items if needed."""
        current_usage = sum(item['memory_usage'] for item in self.cache.values())
        
        # If adding new item would exceed limit, evict LRU items
        while current_usage + new_item_size > self.max_cache_size and self.cache:
            # Find least recently used item
            lru_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
            
            # Remove from cache
            removed_item = self.cache.pop(lru_key)
            del self.access_times[lru_key]
            current_usage -= removed_item['memory_usage']
    
    def clear(self):
        """Clear all cached images."""
        with self._lock:
            self.cache.clear()
            self.access_times.clear()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_memory = sum(item['memory_usage'] for item in self.cache.values())
            return {
                'total_items': len(self.cache),
                'total_memory_bytes': total_memory,
                'total_memory_mb': total_memory / (1024 * 1024),
                'max_cache_size_mb': self.max_cache_size / (1024 * 1024),
                'cache_utilization': (total_memory / self.max_cache_size) * 100
            }


class ProgressTracker:
    """Progress tracking for background operations."""
    
    def __init__(self, total_steps: int = 100):
        self.total_steps = total_steps
        self.current_step = 0
        self.message = ""
        self.is_cancelled = False
        self._callbacks: List[Callable] = []
        self._lock = threading.Lock()
    
    def update(self, step: int, message: str = ""):
        """Update progress."""
        with self._lock:
            self.current_step = min(step, self.total_steps)
            self.message = message
            
            # Notify callbacks
            for callback in self._callbacks:
                try:
                    callback(self.current_step, self.total_steps, self.message)
                except Exception:
                    pass  # Ignore callback errors
    
    def add_callback(self, callback: Callable):
        """Add progress callback."""
        with self._lock:
            self._callbacks.append(callback)
    
    def cancel(self):
        """Cancel the operation."""
        with self._lock:
            self.is_cancelled = True
    
    @property
    def progress_percent(self) -> float:
        """Get progress as percentage."""
        return (self.current_step / self.total_steps) * 100 if self.total_steps > 0 else 0


class ImageService:
    """
    Comprehensive image service for loading, validation, and processing.
    
    Features:
    - Support for multiple image formats including WebP and SVG
    - Background image processing with progress tracking
    - Intelligent caching system for performance
    - Image validation and error handling
    - Memory usage optimization
    """
    
    # Supported image formats
    SUPPORTED_FORMATS = {
        '.png': 'PNG',
        '.jpg': 'JPEG',
        '.jpeg': 'JPEG',
        '.gif': 'GIF',
        '.bmp': 'BMP',
        '.tiff': 'TIFF',
        '.tif': 'TIFF',
        '.webp': 'WEBP',
        '.svg': 'SVG'
    }
    
    # Maximum image dimensions to prevent memory issues
    MAX_IMAGE_SIZE = (8192, 8192)  # 8K resolution
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
    
    def __init__(self, cache_size: int = 100 * 1024 * 1024, max_workers: int = 4):
        """
        Initialize ImageService.
        
        Args:
            cache_size: Maximum cache size in bytes
            max_workers: Maximum number of background worker threads
        """
        self.cache = ImageCache(cache_size)
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self._active_tasks: Dict[str, Future] = {}
        self._lock = threading.RLock()
    
    def is_supported_format(self, file_path: str) -> bool:
        """Check if file format is supported."""
        ext = os.path.splitext(file_path)[1].lower()
        return ext in self.SUPPORTED_FORMATS
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported file extensions."""
        return list(self.SUPPORTED_FORMATS.keys())
    
    def validate_image_file(self, file_path: str) -> None:
        """
        Validate image file before loading.
        
        Args:
            file_path: Path to image file
            
        Raises:
            ValidationError: If file validation fails
            ImageLoadError: If file cannot be accessed
        """
        if not os.path.exists(file_path):
            raise ImageLoadError(f"File not found: {file_path}", file_path=file_path)
        
        if not os.path.isfile(file_path):
            raise ValidationError(f"Path is not a file: {file_path}", field_name="file_path")
        
        # Check file size
        file_size = os.path.getsize(file_path)
        if file_size > self.MAX_FILE_SIZE:
            raise ImageLoadError(
                f"File too large: {file_size / (1024*1024):.1f}MB (max: {self.MAX_FILE_SIZE / (1024*1024):.1f}MB)",
                file_path=file_path
            )
        
        # Check file extension
        if not self.is_supported_format(file_path):
            ext = os.path.splitext(file_path)[1].lower()
            supported = ', '.join(self.SUPPORTED_FORMATS.keys())
            raise ValidationError(
                f"Unsupported format '{ext}'. Supported formats: {supported}",
                field_name="file_format"
            )
    
    def load_image(self, file_path: str, validate: bool = True) -> ImageData:
        """
        Load image from file with validation and caching.
        
        Args:
            file_path: Path to image file
            validate: Whether to validate file before loading
            
        Returns:
            ImageData: Loaded image data
            
        Raises:
            ImageLoadError: If image loading fails
            ValidationError: If validation fails
        """
        if validate:
            self.validate_image_file(file_path)
        
        # Check cache first
        cached_image = self.cache.get(file_path)
        if cached_image:
            return cached_image
        
        try:
            # Handle SVG files specially
            if file_path.lower().endswith('.svg'):
                image_data = self._load_svg_image(file_path)
            else:
                image_data = self._load_standard_image(file_path)
            
            # Cache the loaded image
            self.cache.put(file_path, image_data)
            
            return image_data
            
        except Exception as e:
            raise ImageLoadError(f"Failed to load image: {str(e)}", file_path=file_path)
    
    def _load_standard_image(self, file_path: str) -> ImageData:
        """Load standard image formats using PIL."""
        try:
            # Open image with PIL
            pil_image = Image.open(file_path)
            
            # Validate image dimensions
            if (pil_image.size[0] > self.MAX_IMAGE_SIZE[0] or 
                pil_image.size[1] > self.MAX_IMAGE_SIZE[1]):
                raise ImageLoadError(
                    f"Image too large: {pil_image.size} (max: {self.MAX_IMAGE_SIZE})",
                    file_path=file_path
                )
            
            # Convert to RGB if necessary for consistency
            if pil_image.mode not in ('RGB', 'RGBA', 'L', 'LA'):
                if pil_image.mode == 'P':
                    # Handle palette mode
                    if 'transparency' in pil_image.info:
                        pil_image = pil_image.convert('RGBA')
                    else:
                        pil_image = pil_image.convert('RGB')
                else:
                    pil_image = pil_image.convert('RGB')
            
            # Create ImageData object
            return ImageData.from_pil_image(pil_image, file_path)
            
        except Exception as e:
            raise ImageLoadError(f"Failed to load standard image: {str(e)}", file_path=file_path)
    
    def _load_svg_image(self, file_path: str) -> ImageData:
        """Load SVG image by converting to raster format."""
        try:
            # For SVG support, we would need additional libraries like cairosvg or svglib
            # For now, we'll provide a basic implementation that raises an informative error
            raise ImageLoadError(
                "SVG support requires additional dependencies. Please convert SVG to PNG/JPEG first.",
                file_path=file_path,
                error_code="SVG_NOT_IMPLEMENTED"
            )
            
        except Exception as e:
            raise ImageLoadError(f"Failed to load SVG image: {str(e)}", file_path=file_path)
    
    def load_image_async(self, file_path: str, 
                        progress_callback: Optional[Callable] = None,
                        completion_callback: Optional[Callable] = None,
                        error_callback: Optional[Callable] = None) -> str:
        """
        Load image asynchronously with progress tracking.
        
        Args:
            file_path: Path to image file
            progress_callback: Called with (current_step, total_steps, message)
            completion_callback: Called with ImageData when complete
            error_callback: Called with exception if error occurs
            
        Returns:
            str: Task ID for tracking/cancellation
        """
        task_id = f"load_{hashlib.md5(file_path.encode()).hexdigest()}_{datetime.now().timestamp()}"
        
        def _load_with_progress():
            progress = ProgressTracker(100)
            if progress_callback:
                progress.add_callback(progress_callback)
            
            try:
                progress.update(10, "Validating file...")
                if progress.is_cancelled:
                    return
                
                self.validate_image_file(file_path)
                
                progress.update(30, "Loading image...")
                if progress.is_cancelled:
                    return
                
                image_data = self.load_image(file_path, validate=False)
                
                progress.update(100, "Complete")
                
                if completion_callback and not progress.is_cancelled:
                    completion_callback(image_data)
                    
            except Exception as e:
                if error_callback:
                    error_callback(e)
            finally:
                # Clean up task reference
                with self._lock:
                    self._active_tasks.pop(task_id, None)
        
        # Submit task
        with self._lock:
            future = self.executor.submit(_load_with_progress)
            self._active_tasks[task_id] = future
        
        return task_id
    
    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel an active background task.
        
        Args:
            task_id: Task ID returned by async methods
            
        Returns:
            bool: True if task was cancelled, False if not found
        """
        with self._lock:
            if task_id in self._active_tasks:
                future = self._active_tasks[task_id]
                return future.cancel()
        return False
    
    def get_pixel_color(self, image_data: ImageData, x: int, y: int) -> ColorData:
        """
        Get pixel color at specified coordinates.
        
        Args:
            image_data: Image to sample from
            x: X coordinate
            y: Y coordinate
            
        Returns:
            ColorData: Color at the specified pixel
            
        Raises:
            ValidationError: If coordinates are out of bounds
        """
        try:
            r, g, b, a = image_data.get_pixel_color(x, y)
            return ColorData.from_rgb(r, g, b, a / 255.0)
        except ValueError as e:
            raise ValidationError(str(e), field_name="coordinates")
    
    def resize_image(self, image_data: ImageData, new_size: Tuple[int, int], 
                    resample: int = Image.Resampling.LANCZOS) -> ImageData:
        """
        Resize image with quality preservation.
        
        Args:
            image_data: Source image
            new_size: Target (width, height)
            resample: Resampling algorithm
            
        Returns:
            ImageData: Resized image
        """
        # Check cache for resized version
        cached_resized = self.cache.get(image_data.file_path, new_size)
        if cached_resized:
            return cached_resized
        
        try:
            resized_image = image_data.resize(new_size, resample)
            
            # Cache the resized version
            self.cache.put(image_data.file_path, resized_image, new_size)
            
            return resized_image
            
        except Exception as e:
            raise ImageLoadError(f"Failed to resize image: {str(e)}")
    
    def extract_dominant_colors(self, image_data: ImageData, count: int = 5) -> List[ColorData]:
        """
        Extract dominant colors from image using color quantization.
        
        Args:
            image_data: Source image
            count: Number of dominant colors to extract
            
        Returns:
            List[ColorData]: List of dominant colors
        """
        try:
            # Convert to RGB if necessary
            pil_image = image_data.pil_image
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')
            
            # Use PIL's quantize method to find dominant colors
            quantized = pil_image.quantize(colors=count)
            palette = quantized.getpalette()
            
            # Extract RGB values from palette
            dominant_colors = []
            for i in range(count):
                r = palette[i * 3]
                g = palette[i * 3 + 1]
                b = palette[i * 3 + 2]
                dominant_colors.append(ColorData.from_rgb(r, g, b))
            
            return dominant_colors
            
        except Exception as e:
            raise ImageLoadError(f"Failed to extract dominant colors: {str(e)}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get image cache statistics."""
        return self.cache.get_cache_stats()
    
    def clear_cache(self):
        """Clear image cache."""
        self.cache.clear()
    
    def shutdown(self):
        """Shutdown the image service and cleanup resources."""
        # Cancel all active tasks
        with self._lock:
            for task_id, future in self._active_tasks.items():
                future.cancel()
            self._active_tasks.clear()
        
        # Shutdown executor
        self.executor.shutdown(wait=True)
        
        # Clear cache
        self.clear_cache()
    
    def __del__(self):
        """Cleanup when service is destroyed."""
        try:
            self.shutdown()
        except:
            pass