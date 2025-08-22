"""
Image processing utilities for loading, resizing, and color analysis.
"""

import os
from typing import List, Tuple, Optional, Dict, Any
from PIL import Image, ImageFilter, ImageEnhance
import numpy as np
from collections import Counter
from ..models.image_data import ImageData
from ..models.color_data import ColorData


# Supported image formats
SUPPORTED_FORMATS = {
    '.png': 'PNG',
    '.jpg': 'JPEG',
    '.jpeg': 'JPEG',
    '.gif': 'GIF',
    '.bmp': 'BMP',
    '.tiff': 'TIFF',
    '.tif': 'TIFF',
    '.webp': 'WebP',
    '.svg': 'SVG'
}


def validate_image_format(file_path: str) -> bool:
    """
    Validate if file format is supported.
    
    Args:
        file_path: Path to image file
        
    Returns:
        True if format is supported
    """
    if not os.path.exists(file_path):
        return False
    
    _, ext = os.path.splitext(file_path.lower())
    return ext in SUPPORTED_FORMATS


def load_image_with_validation(file_path: str) -> ImageData:
    """
    Load image with comprehensive validation.
    
    Args:
        file_path: Path to image file
        
    Returns:
        ImageData object
        
    Raises:
        ValueError: If file is invalid or unsupported
        FileNotFoundError: If file doesn't exist
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Image file not found: {file_path}")
    
    if not validate_image_format(file_path):
        _, ext = os.path.splitext(file_path.lower())
        raise ValueError(f"Unsupported image format: {ext}")
    
    try:
        # Special handling for SVG files
        if file_path.lower().endswith('.svg'):
            return _load_svg_image(file_path)
        
        # Load regular image formats
        return ImageData.from_file(file_path)
        
    except Exception as e:
        raise ValueError(f"Failed to load image: {str(e)}")


def _load_svg_image(file_path: str) -> ImageData:
    """Load SVG image with conversion to raster format."""
    try:
        # Try to use cairosvg if available for better SVG support
        try:
            import cairosvg
            from io import BytesIO
            
            # Convert SVG to PNG in memory
            png_data = cairosvg.svg2png(url=file_path)
            pil_image = Image.open(BytesIO(png_data))
            
        except ImportError:
            # Fallback: use PIL's basic SVG support (limited)
            pil_image = Image.open(file_path)
            # Convert to RGB if needed
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')
        
        return ImageData.from_pil_image(pil_image, file_path)
        
    except Exception as e:
        raise ValueError(f"Failed to load SVG image: {str(e)}")


def resize_image_with_quality(image_data: ImageData, 
                            new_size: Tuple[int, int], 
                            maintain_aspect: bool = True,
                            resample: int = Image.Resampling.LANCZOS) -> ImageData:
    """
    Resize image with quality preservation.
    
    Args:
        image_data: Original image data
        new_size: Target (width, height)
        maintain_aspect: Whether to maintain aspect ratio
        resample: Resampling algorithm
        
    Returns:
        Resized ImageData
    """
    if maintain_aspect:
        # Calculate size maintaining aspect ratio
        original_ratio = image_data.aspect_ratio
        target_width, target_height = new_size
        
        if target_width / target_height > original_ratio:
            # Fit to height
            new_width = int(target_height * original_ratio)
            new_height = target_height
        else:
            # Fit to width
            new_width = target_width
            new_height = int(target_width / original_ratio)
        
        new_size = (new_width, new_height)
    
    return image_data.resize(new_size, resample)


def extract_dominant_colors(image_data: ImageData, 
                          num_colors: int = 5,
                          quality: int = 10) -> List[ColorData]:
    """
    Extract dominant colors from image using k-means clustering.
    
    Args:
        image_data: Image to analyze
        num_colors: Number of dominant colors to extract
        quality: Quality factor (1=best, 10=good, higher=faster)
        
    Returns:
        List of dominant colors sorted by frequency
    """
    try:
        # Convert image to RGB if needed
        pil_image = image_data.pil_image
        if pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')
        
        # Resize image for faster processing if it's too large
        max_size = 200
        if max(pil_image.size) > max_size:
            ratio = max_size / max(pil_image.size)
            new_size = (int(pil_image.size[0] * ratio), int(pil_image.size[1] * ratio))
            pil_image = pil_image.resize(new_size, Image.Resampling.LANCZOS)
        
        # Convert to numpy array and sample pixels
        img_array = np.array(pil_image)
        pixels = img_array.reshape(-1, 3)
        
        # Sample pixels for performance (every 'quality' pixel)
        sampled_pixels = pixels[::quality]
        
        # Use k-means clustering to find dominant colors
        from sklearn.cluster import KMeans
        
        # Ensure we don't ask for more colors than we have pixels
        actual_num_colors = min(num_colors, len(sampled_pixels))
        
        kmeans = KMeans(n_clusters=actual_num_colors, random_state=42, n_init=10)
        kmeans.fit(sampled_pixels)
        
        # Get cluster centers (dominant colors) and their frequencies
        colors = kmeans.cluster_centers_.astype(int)
        labels = kmeans.labels_
        
        # Count frequency of each cluster
        label_counts = Counter(labels)
        
        # Create ColorData objects with frequency information
        dominant_colors = []
        for i, color in enumerate(colors):
            frequency = label_counts[i] / len(labels)
            color_data = ColorData(int(color[0]), int(color[1]), int(color[2]))
            # Store frequency in metadata (we'll need to add this to ColorData)
            dominant_colors.append((color_data, frequency))
        
        # Sort by frequency (most frequent first)
        dominant_colors.sort(key=lambda x: x[1], reverse=True)
        
        # Return just the ColorData objects
        return [color for color, _ in dominant_colors]
        
    except ImportError:
        # Fallback method without sklearn
        return _extract_dominant_colors_simple(image_data, num_colors)
    except Exception as e:
        raise ValueError(f"Failed to extract dominant colors: {str(e)}")


def _extract_dominant_colors_simple(image_data: ImageData, num_colors: int = 5) -> List[ColorData]:
    """
    Simple dominant color extraction without sklearn.
    Uses color quantization approach.
    """
    try:
        # Convert to RGB and reduce to smaller size for performance
        pil_image = image_data.pil_image
        if pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')
        
        # Resize for performance
        pil_image = pil_image.resize((150, 150), Image.Resampling.LANCZOS)
        
        # Quantize colors to reduce palette
        quantized = pil_image.quantize(colors=num_colors * 2)
        palette_image = quantized.convert('RGB')
        
        # Get all unique colors and their frequencies
        colors = palette_image.getcolors(maxcolors=256)
        if not colors:
            return []
        
        # Sort by frequency and take top colors
        colors.sort(key=lambda x: x[0], reverse=True)
        
        dominant_colors = []
        for count, (r, g, b) in colors[:num_colors]:
            dominant_colors.append(ColorData(r, g, b))
        
        return dominant_colors
        
    except Exception as e:
        raise ValueError(f"Failed to extract dominant colors (simple method): {str(e)}")


def get_pixel_color_safe(image_data: ImageData, x: int, y: int) -> Optional[ColorData]:
    """
    Get pixel color with bounds checking and error handling.
    
    Args:
        image_data: Image data
        x: X coordinate
        y: Y coordinate
        
    Returns:
        ColorData or None if coordinates are invalid
    """
    try:
        if not (0 <= x < image_data.width and 0 <= y < image_data.height):
            return None
        
        r, g, b, a = image_data.get_pixel_color(x, y)
        return ColorData(r, g, b, a / 255.0)
        
    except Exception:
        return None


def calculate_average_color(image_data: ImageData, 
                          region: Optional[Tuple[int, int, int, int]] = None) -> ColorData:
    """
    Calculate average color of image or region.
    
    Args:
        image_data: Image to analyze
        region: Optional (left, top, right, bottom) region
        
    Returns:
        Average color as ColorData
    """
    try:
        pil_image = image_data.pil_image
        
        # Crop to region if specified
        if region:
            left, top, right, bottom = region
            pil_image = pil_image.crop((left, top, right, bottom))
        
        # Convert to RGB if needed
        if pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')
        
        # Resize for performance if image is large
        if max(pil_image.size) > 500:
            ratio = 500 / max(pil_image.size)
            new_size = (int(pil_image.size[0] * ratio), int(pil_image.size[1] * ratio))
            pil_image = pil_image.resize(new_size, Image.Resampling.LANCZOS)
        
        # Calculate average using numpy
        img_array = np.array(pil_image)
        avg_color = np.mean(img_array, axis=(0, 1))
        
        return ColorData(int(avg_color[0]), int(avg_color[1]), int(avg_color[2]))
        
    except Exception as e:
        raise ValueError(f"Failed to calculate average color: {str(e)}")


def create_color_histogram(image_data: ImageData, bins: int = 256) -> Dict[str, List[int]]:
    """
    Create color histogram for RGB channels.
    
    Args:
        image_data: Image to analyze
        bins: Number of histogram bins
        
    Returns:
        Dictionary with 'r', 'g', 'b' histogram data
    """
    try:
        pil_image = image_data.pil_image
        if pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')
        
        # Get histograms for each channel
        r_hist = pil_image.histogram()[0:256]      # Red channel
        g_hist = pil_image.histogram()[256:512]    # Green channel  
        b_hist = pil_image.histogram()[512:768]    # Blue channel
        
        # Bin the data if different bin count requested
        if bins != 256:
            r_hist = _rebin_histogram(r_hist, bins)
            g_hist = _rebin_histogram(g_hist, bins)
            b_hist = _rebin_histogram(b_hist, bins)
        
        return {
            'r': r_hist,
            'g': g_hist,
            'b': b_hist
        }
        
    except Exception as e:
        raise ValueError(f"Failed to create color histogram: {str(e)}")


def _rebin_histogram(hist: List[int], new_bins: int) -> List[int]:
    """Rebin histogram to different number of bins."""
    if len(hist) == new_bins:
        return hist
    
    old_bins = len(hist)
    new_hist = [0] * new_bins
    
    for i, count in enumerate(hist):
        new_index = int(i * new_bins / old_bins)
        new_hist[new_index] += count
    
    return new_hist


def enhance_image_contrast(image_data: ImageData, factor: float = 1.2) -> ImageData:
    """
    Enhance image contrast.
    
    Args:
        image_data: Original image
        factor: Contrast factor (1.0 = no change, >1.0 = more contrast)
        
    Returns:
        Enhanced ImageData
    """
    try:
        enhancer = ImageEnhance.Contrast(image_data.pil_image)
        enhanced_image = enhancer.enhance(factor)
        
        return ImageData.from_pil_image(enhanced_image, image_data.file_path)
        
    except Exception as e:
        raise ValueError(f"Failed to enhance contrast: {str(e)}")


def apply_gaussian_blur(image_data: ImageData, radius: float = 1.0) -> ImageData:
    """
    Apply Gaussian blur to image.
    
    Args:
        image_data: Original image
        radius: Blur radius
        
    Returns:
        Blurred ImageData
    """
    try:
        blurred_image = image_data.pil_image.filter(ImageFilter.GaussianBlur(radius))
        
        return ImageData.from_pil_image(blurred_image, image_data.file_path)
        
    except Exception as e:
        raise ValueError(f"Failed to apply blur: {str(e)}")


def get_image_brightness(image_data: ImageData) -> float:
    """
    Calculate overall image brightness (0-1 scale).
    
    Args:
        image_data: Image to analyze
        
    Returns:
        Brightness value (0 = black, 1 = white)
    """
    try:
        # Convert to grayscale and calculate mean
        gray_image = image_data.pil_image.convert('L')
        
        # Resize for performance if large
        if max(gray_image.size) > 500:
            ratio = 500 / max(gray_image.size)
            new_size = (int(gray_image.size[0] * ratio), int(gray_image.size[1] * ratio))
            gray_image = gray_image.resize(new_size, Image.Resampling.LANCZOS)
        
        # Calculate average brightness
        img_array = np.array(gray_image)
        brightness = np.mean(img_array) / 255.0
        
        return float(brightness)
        
    except Exception as e:
        raise ValueError(f"Failed to calculate brightness: {str(e)}")


def detect_edges(image_data: ImageData) -> ImageData:
    """
    Detect edges in image using edge detection filter.
    
    Args:
        image_data: Original image
        
    Returns:
        Edge-detected ImageData
    """
    try:
        # Convert to grayscale for edge detection
        gray_image = image_data.pil_image.convert('L')
        
        # Apply edge detection filter
        edges = gray_image.filter(ImageFilter.FIND_EDGES)
        
        # Convert back to RGB
        edges_rgb = edges.convert('RGB')
        
        return ImageData.from_pil_image(edges_rgb, image_data.file_path)
        
    except Exception as e:
        raise ValueError(f"Failed to detect edges: {str(e)}")


def get_image_statistics(image_data: ImageData) -> Dict[str, Any]:
    """
    Get comprehensive image statistics.
    
    Args:
        image_data: Image to analyze
        
    Returns:
        Dictionary with various image statistics
    """
    try:
        stats = {
            'width': image_data.width,
            'height': image_data.height,
            'aspect_ratio': image_data.aspect_ratio,
            'total_pixels': image_data.total_pixels,
            'format': image_data.format,
            'mode': image_data.mode,
            'has_transparency': image_data.has_transparency,
            'file_size': image_data.file_size,
            'memory_usage': image_data.get_memory_usage(),
            'brightness': get_image_brightness(image_data)
        }
        
        # Add color statistics if possible
        try:
            avg_color = calculate_average_color(image_data)
            stats['average_color'] = {
                'rgb': avg_color.rgb,
                'hex': avg_color.hex
            }
        except:
            pass
        
        # Add dominant colors if possible
        try:
            dominant = extract_dominant_colors(image_data, 3)
            stats['dominant_colors'] = [
                {'rgb': color.rgb, 'hex': color.hex} 
                for color in dominant
            ]
        except:
            pass
        
        return stats
        
    except Exception as e:
        raise ValueError(f"Failed to get image statistics: {str(e)}")