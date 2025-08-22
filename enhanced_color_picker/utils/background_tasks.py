"""
Common background task implementations for the color picker application.
"""

import time
from typing import List, Tuple, Optional, Callable
from PIL import Image

from ..core.task_manager import ProgressCallback, get_task_manager
from ..models.color_data import ColorData
from ..models.image_data import ImageData
from ..utils.color_utils import extract_dominant_colors, analyze_color_distribution
from ..utils.image_utils import resize_image_with_quality


def load_image_background(
    progress_callback: ProgressCallback,
    file_path: str,
    max_size: Optional[Tuple[int, int]] = None
) -> ImageData:
    """
    Load and process image in background.
    
    Args:
        progress_callback: Progress callback for updates
        file_path: Path to image file
        max_size: Maximum size for resizing (width, height)
    
    Returns:
        Processed ImageData object
    """
    progress_callback.update(0, 100, "Loading image...")
    
    # Load image
    try:
        pil_image = Image.open(file_path)
        progress_callback.update(20, 100, "Image loaded, processing...")
        
        # Convert to RGB if necessary
        if pil_image.mode not in ('RGB', 'RGBA'):
            pil_image = pil_image.convert('RGB')
        
        progress_callback.update(40, 100, "Converting color mode...")
        
        # Resize if needed
        if max_size and (pil_image.width > max_size[0] or pil_image.height > max_size[1]):
            progress_callback.update(60, 100, "Resizing image...")
            pil_image = resize_image_with_quality(pil_image, max_size)
        
        progress_callback.update(80, 100, "Creating image data...")
        
        # Create ImageData object
        image_data = ImageData(
            pil_image=pil_image,
            file_path=file_path,
            format=pil_image.format or 'Unknown',
            size=(pil_image.width, pil_image.height),
            mode=pil_image.mode,
            has_transparency=pil_image.mode in ('RGBA', 'LA') or 'transparency' in pil_image.info
        )
        
        progress_callback.update(100, 100, "Image processing complete")
        return image_data
        
    except Exception as e:
        progress_callback.update(0, 100, f"Failed to load image: {str(e)}")
        raise


def extract_palette_background(
    progress_callback: ProgressCallback,
    image_data: ImageData,
    num_colors: int = 8,
    quality: int = 1
) -> List[ColorData]:
    """
    Extract color palette from image in background.
    
    Args:
        progress_callback: Progress callback for updates
        image_data: Image to analyze
        num_colors: Number of colors to extract
        quality: Quality setting (1=best, 10=fastest)
    
    Returns:
        List of dominant colors
    """
    progress_callback.update(0, 100, "Analyzing image colors...")
    
    try:
        # Extract dominant colors
        colors = extract_dominant_colors(
            image_data.pil_image,
            num_colors=num_colors,
            quality=quality,
            progress_callback=lambda p: progress_callback.update(
                int(p * 100), 100, f"Extracting colors... {p:.1%}"
            )
        )
        
        progress_callback.update(100, 100, f"Extracted {len(colors)} colors")
        return colors
        
    except Exception as e:
        progress_callback.update(0, 100, f"Failed to extract palette: {str(e)}")
        raise


def analyze_image_background(
    progress_callback: ProgressCallback,
    image_data: ImageData
) -> dict:
    """
    Perform comprehensive image color analysis in background.
    
    Args:
        progress_callback: Progress callback for updates
        image_data: Image to analyze
    
    Returns:
        Dictionary with analysis results
    """
    progress_callback.update(0, 100, "Starting image analysis...")
    
    try:
        results = {}
        
        # Extract dominant colors
        progress_callback.update(10, 100, "Extracting dominant colors...")
        results['dominant_colors'] = extract_dominant_colors(
            image_data.pil_image,
            num_colors=10,
            quality=1
        )
        
        # Analyze color distribution
        progress_callback.update(40, 100, "Analyzing color distribution...")
        results['color_distribution'] = analyze_color_distribution(image_data.pil_image)
        
        # Calculate average color
        progress_callback.update(70, 100, "Calculating average color...")
        pixels = list(image_data.pil_image.getdata())
        if image_data.pil_image.mode == 'RGBA':
            # Filter out transparent pixels
            pixels = [p for p in pixels if p[3] > 128]
            if pixels:
                avg_r = sum(p[0] for p in pixels) // len(pixels)
                avg_g = sum(p[1] for p in pixels) // len(pixels)
                avg_b = sum(p[2] for p in pixels) // len(pixels)
            else:
                avg_r = avg_g = avg_b = 0
        else:
            avg_r = sum(p[0] for p in pixels) // len(pixels)
            avg_g = sum(p[1] for p in pixels) // len(pixels)
            avg_b = sum(p[2] for p in pixels) // len(pixels)
        
        results['average_color'] = ColorData.from_rgb(avg_r, avg_g, avg_b)
        
        # Color statistics
        progress_callback.update(90, 100, "Calculating statistics...")
        results['statistics'] = {
            'total_pixels': len(pixels),
            'unique_colors': len(set(pixels)),
            'has_transparency': image_data.has_transparency,
            'color_diversity': len(set(pixels)) / len(pixels) if pixels else 0
        }
        
        progress_callback.update(100, 100, "Analysis complete")
        return results
        
    except Exception as e:
        progress_callback.update(0, 100, f"Analysis failed: {str(e)}")
        raise


def batch_color_conversion_background(
    progress_callback: ProgressCallback,
    colors: List[ColorData],
    target_formats: List[str]
) -> dict:
    """
    Convert multiple colors to multiple formats in background.
    
    Args:
        progress_callback: Progress callback for updates
        colors: List of colors to convert
        target_formats: List of target format names
    
    Returns:
        Dictionary with conversion results
    """
    progress_callback.update(0, 100, "Starting batch conversion...")
    
    try:
        results = {}
        total_operations = len(colors) * len(target_formats)
        completed = 0
        
        for i, color in enumerate(colors):
            color_results = {}
            
            for format_name in target_formats:
                progress_callback.update(
                    int((completed / total_operations) * 100),
                    100,
                    f"Converting color {i+1}/{len(colors)} to {format_name}..."
                )
                
                # Convert color to target format
                if format_name.lower() == 'hex':
                    color_results[format_name] = color.hex
                elif format_name.lower() == 'rgb':
                    color_results[format_name] = f"rgb({color.rgb[0]}, {color.rgb[1]}, {color.rgb[2]})"
                elif format_name.lower() == 'hsl':
                    color_results[format_name] = f"hsl({color.hsl[0]:.0f}, {color.hsl[1]:.0f}%, {color.hsl[2]:.0f}%)"
                elif format_name.lower() == 'hsv':
                    color_results[format_name] = f"hsv({color.hsv[0]:.0f}, {color.hsv[1]:.0f}%, {color.hsv[2]:.0f}%)"
                elif format_name.lower() == 'cmyk':
                    color_results[format_name] = f"cmyk({color.cmyk[0]:.0f}%, {color.cmyk[1]:.0f}%, {color.cmyk[2]:.0f}%, {color.cmyk[3]:.0f}%)"
                
                completed += 1
                
                # Check for cancellation
                if progress_callback.is_cancelled():
                    return results
            
            results[f"color_{i}"] = color_results
        
        progress_callback.update(100, 100, f"Converted {len(colors)} colors to {len(target_formats)} formats")
        return results
        
    except Exception as e:
        progress_callback.update(0, 100, f"Batch conversion failed: {str(e)}")
        raise


def export_palette_background(
    progress_callback: ProgressCallback,
    colors: List[ColorData],
    file_path: str,
    format_type: str
) -> bool:
    """
    Export color palette to file in background.
    
    Args:
        progress_callback: Progress callback for updates
        colors: List of colors to export
        file_path: Output file path
        format_type: Export format (json, css, ase, etc.)
    
    Returns:
        True if export successful
    """
    progress_callback.update(0, 100, f"Exporting palette to {format_type.upper()}...")
    
    try:
        if format_type.lower() == 'json':
            import json
            
            progress_callback.update(20, 100, "Converting to JSON format...")
            
            palette_data = {
                'name': 'Exported Palette',
                'colors': [
                    {
                        'hex': color.hex,
                        'rgb': color.rgb,
                        'hsl': color.hsl,
                        'hsv': color.hsv,
                        'cmyk': color.cmyk
                    }
                    for color in colors
                ]
            }
            
            progress_callback.update(60, 100, "Writing JSON file...")
            
            with open(file_path, 'w') as f:
                json.dump(palette_data, f, indent=2)
        
        elif format_type.lower() == 'css':
            progress_callback.update(20, 100, "Converting to CSS format...")
            
            css_content = ":root {\n"
            for i, color in enumerate(colors):
                css_content += f"  --color-{i+1}: {color.hex};\n"
            css_content += "}\n"
            
            progress_callback.update(60, 100, "Writing CSS file...")
            
            with open(file_path, 'w') as f:
                f.write(css_content)
        
        elif format_type.lower() == 'txt':
            progress_callback.update(20, 100, "Converting to text format...")
            
            text_content = "Color Palette\n" + "="*20 + "\n\n"
            for i, color in enumerate(colors):
                text_content += f"Color {i+1}:\n"
                text_content += f"  HEX: {color.hex}\n"
                text_content += f"  RGB: {color.rgb}\n"
                text_content += f"  HSL: {color.hsl}\n\n"
            
            progress_callback.update(60, 100, "Writing text file...")
            
            with open(file_path, 'w') as f:
                f.write(text_content)
        
        else:
            raise ValueError(f"Unsupported export format: {format_type}")
        
        progress_callback.update(100, 100, "Export complete")
        return True
        
    except Exception as e:
        progress_callback.update(0, 100, f"Export failed: {str(e)}")
        raise


def simulate_heavy_operation(
    progress_callback: ProgressCallback,
    duration: float = 5.0,
    steps: int = 100
) -> str:
    """
    Simulate a heavy operation for testing purposes.
    
    Args:
        progress_callback: Progress callback for updates
        duration: Total duration in seconds
        steps: Number of progress steps
    
    Returns:
        Result message
    """
    step_duration = duration / steps
    
    for i in range(steps):
        # Check for cancellation
        if progress_callback.is_cancelled():
            return "Operation cancelled"
        
        # Simulate work
        time.sleep(step_duration)
        
        # Update progress
        progress_callback.update(
            i + 1, 
            steps, 
            f"Processing step {i + 1} of {steps}..."
        )
    
    return f"Heavy operation completed in {duration:.1f} seconds"


# Convenience functions for common operations

def load_image_async(
    file_path: str,
    max_size: Optional[Tuple[int, int]] = None,
    progress_callback: Callable = None,
    completion_callback: Callable = None
) -> str:
    """
    Load image asynchronously.
    
    Returns:
        Task ID for tracking
    """
    task_manager = get_task_manager()
    return task_manager.submit_task(
        load_image_background,
        file_path,
        max_size,
        name=f"Load Image: {file_path}",
        progress_callback=progress_callback,
        completion_callback=completion_callback
    )


def extract_palette_async(
    image_data: ImageData,
    num_colors: int = 8,
    quality: int = 1,
    progress_callback: Callable = None,
    completion_callback: Callable = None
) -> str:
    """
    Extract color palette asynchronously.
    
    Returns:
        Task ID for tracking
    """
    task_manager = get_task_manager()
    return task_manager.submit_task(
        extract_palette_background,
        image_data,
        num_colors,
        quality,
        name="Extract Color Palette",
        progress_callback=progress_callback,
        completion_callback=completion_callback
    )


def analyze_image_async(
    image_data: ImageData,
    progress_callback: Callable = None,
    completion_callback: Callable = None
) -> str:
    """
    Analyze image colors asynchronously.
    
    Returns:
        Task ID for tracking
    """
    task_manager = get_task_manager()
    return task_manager.submit_task(
        analyze_image_background,
        image_data,
        name="Analyze Image Colors",
        progress_callback=progress_callback,
        completion_callback=completion_callback
    )