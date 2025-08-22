"""
ImageData class with metadata support.
"""

from dataclasses import dataclass
from typing import Tuple, Optional, Dict, Any
from PIL import Image
import os
from datetime import datetime


@dataclass
class ImageData:
    """
    Image data structure with comprehensive metadata support.
    
    Stores PIL Image object along with file information and metadata
    for efficient image processing and display.
    """
    
    pil_image: Image.Image
    file_path: str
    format: str
    size: Tuple[int, int]
    mode: str
    has_transparency: bool
    file_size: int = 0
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Initialize additional metadata after creation."""
        if self.created_at is None:
            self.created_at = datetime.now()
        
        if self.modified_at is None:
            self.modified_at = self.created_at
        
        if self.metadata is None:
            self.metadata = {}
        
        # Get file size if file exists
        if os.path.exists(self.file_path):
            self.file_size = os.path.getsize(self.file_path)
        
        # Extract additional metadata from PIL image
        self._extract_pil_metadata()
    
    def _extract_pil_metadata(self):
        """Extract metadata from PIL Image object."""
        if hasattr(self.pil_image, 'info') and self.pil_image.info:
            self.metadata.update(self.pil_image.info)
        
        # Add basic image properties
        self.metadata.update({
            'width': self.size[0],
            'height': self.size[1],
            'aspect_ratio': self.size[0] / self.size[1] if self.size[1] > 0 else 1.0,
            'total_pixels': self.size[0] * self.size[1],
            'color_mode': self.mode,
            'has_alpha': self.has_transparency
        })
    
    @classmethod
    def from_file(cls, file_path: str) -> 'ImageData':
        """Create ImageData from image file."""
        try:
            pil_image = Image.open(file_path)
            
            # Get basic image information
            format_name = pil_image.format or 'Unknown'
            size = pil_image.size
            mode = pil_image.mode
            
            # Check for transparency
            has_transparency = (
                mode in ('RGBA', 'LA') or 
                'transparency' in pil_image.info or
                (mode == 'P' and 'transparency' in pil_image.info)
            )
            
            return cls(
                pil_image=pil_image,
                file_path=file_path,
                format=format_name,
                size=size,
                mode=mode,
                has_transparency=has_transparency
            )
            
        except Exception as e:
            raise ValueError(f"Failed to load image from {file_path}: {str(e)}")
    
    @classmethod
    def from_pil_image(cls, pil_image: Image.Image, file_path: str = "") -> 'ImageData':
        """Create ImageData from existing PIL Image."""
        format_name = pil_image.format or 'Unknown'
        size = pil_image.size
        mode = pil_image.mode
        
        # Check for transparency
        has_transparency = (
            mode in ('RGBA', 'LA') or 
            'transparency' in pil_image.info or
            (mode == 'P' and 'transparency' in pil_image.info)
        )
        
        return cls(
            pil_image=pil_image,
            file_path=file_path,
            format=format_name,
            size=size,
            mode=mode,
            has_transparency=has_transparency
        )
    
    @property
    def width(self) -> int:
        """Get image width."""
        return self.size[0]
    
    @property
    def height(self) -> int:
        """Get image height."""
        return self.size[1]
    
    @property
    def aspect_ratio(self) -> float:
        """Get image aspect ratio (width/height)."""
        return self.width / self.height if self.height > 0 else 1.0
    
    @property
    def total_pixels(self) -> int:
        """Get total number of pixels."""
        return self.width * self.height
    
    @property
    def file_name(self) -> str:
        """Get file name without path."""
        return os.path.basename(self.file_path)
    
    @property
    def file_extension(self) -> str:
        """Get file extension."""
        return os.path.splitext(self.file_path)[1].lower()
    
    def get_pixel_color(self, x: int, y: int) -> Tuple[int, int, int, int]:
        """
        Get pixel color at specified coordinates.
        
        Args:
            x: X coordinate (0 to width-1)
            y: Y coordinate (0 to height-1)
            
        Returns:
            RGBA tuple (r, g, b, a) where a=255 if no alpha channel
        """
        if not (0 <= x < self.width and 0 <= y < self.height):
            raise ValueError(f"Coordinates ({x}, {y}) out of bounds for image {self.size}")
        
        pixel = self.pil_image.getpixel((x, y))
        
        # Handle different color modes
        if self.mode == 'RGB':
            return (*pixel, 255)  # Add full alpha
        elif self.mode == 'RGBA':
            return pixel
        elif self.mode == 'L':  # Grayscale
            return (pixel, pixel, pixel, 255)
        elif self.mode == 'LA':  # Grayscale with alpha
            return (pixel[0], pixel[0], pixel[0], pixel[1])
        elif self.mode == 'P':  # Palette mode
            # Convert to RGB first
            rgb_image = self.pil_image.convert('RGB')
            rgb_pixel = rgb_image.getpixel((x, y))
            return (*rgb_pixel, 255)
        else:
            # Convert to RGB for other modes
            rgb_image = self.pil_image.convert('RGB')
            rgb_pixel = rgb_image.getpixel((x, y))
            return (*rgb_pixel, 255)
    
    def resize(self, new_size: Tuple[int, int], resample: int = Image.Resampling.LANCZOS) -> 'ImageData':
        """
        Create a resized copy of the image.
        
        Args:
            new_size: New (width, height) tuple
            resample: Resampling algorithm
            
        Returns:
            New ImageData with resized image
        """
        resized_image = self.pil_image.resize(new_size, resample)
        
        return ImageData.from_pil_image(
            pil_image=resized_image,
            file_path=self.file_path
        )
    
    def copy(self) -> 'ImageData':
        """Create a copy of the ImageData."""
        return ImageData(
            pil_image=self.pil_image.copy(),
            file_path=self.file_path,
            format=self.format,
            size=self.size,
            mode=self.mode,
            has_transparency=self.has_transparency,
            file_size=self.file_size,
            created_at=self.created_at,
            modified_at=datetime.now(),
            metadata=self.metadata.copy() if self.metadata else {}
        )
    
    def get_memory_usage(self) -> int:
        """Estimate memory usage in bytes."""
        # Basic calculation: width * height * bytes_per_pixel
        bytes_per_pixel = {
            'L': 1,      # Grayscale
            'LA': 2,     # Grayscale + Alpha
            'RGB': 3,    # RGB
            'RGBA': 4,   # RGB + Alpha
            'P': 1,      # Palette (8-bit)
        }.get(self.mode, 4)  # Default to 4 bytes for unknown modes
        
        return self.total_pixels * bytes_per_pixel
    
    def is_valid(self) -> bool:
        """Check if the image data is valid."""
        try:
            return (
                self.pil_image is not None and
                self.size[0] > 0 and
                self.size[1] > 0 and
                hasattr(self.pil_image, 'getpixel')
            )
        except:
            return False
    
    def __str__(self) -> str:
        """String representation of the image data."""
        return (f"ImageData(file='{self.file_name}', "
                f"size={self.size}, format={self.format}, "
                f"mode={self.mode}, size={self.file_size} bytes)")
    
    def __del__(self):
        """Cleanup PIL image when object is destroyed."""
        if hasattr(self, 'pil_image') and self.pil_image:
            try:
                self.pil_image.close()
            except:
                pass