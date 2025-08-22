"""
AnalysisService - Comprehensive color analysis and statistics service.

This service provides advanced color analysis including dominant color extraction,
histogram generation, color distribution analysis, and statistical calculations.
"""

import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from collections import Counter
import math
from PIL import Image

from ..models.image_data import ImageData
from ..models.color_data import ColorData
from ..models.palette import Palette
from ..core.exceptions import ImageLoadError, ValidationError


class ColorHistogram:
    """Color histogram data structure."""
    
    def __init__(self, red_hist: List[int], green_hist: List[int], blue_hist: List[int]):
        """
        Initialize color histogram.
        
        Args:
            red_hist: Red channel histogram (256 bins)
            green_hist: Green channel histogram (256 bins)
            blue_hist: Blue channel histogram (256 bins)
        """
        self.red = red_hist
        self.green = green_hist
        self.blue = blue_hist
        self.total_pixels = sum(red_hist)
    
    def get_channel_stats(self, channel: str) -> Dict[str, float]:
        """Get statistics for a specific channel."""
        if channel.lower() == 'red':
            hist = self.red
        elif channel.lower() == 'green':
            hist = self.green
        elif channel.lower() == 'blue':
            hist = self.blue
        else:
            raise ValueError(f"Invalid channel: {channel}")
        
        # Calculate statistics
        total = sum(hist)
        if total == 0:
            return {'mean': 0, 'std': 0, 'min': 0, 'max': 0, 'median': 0}
        
        # Calculate mean
        mean = sum(i * count for i, count in enumerate(hist)) / total
        
        # Calculate standard deviation
        variance = sum(count * (i - mean) ** 2 for i, count in enumerate(hist)) / total
        std = math.sqrt(variance)
        
        # Find min and max values
        min_val = next((i for i, count in enumerate(hist) if count > 0), 0)
        max_val = next((255 - i for i, count in enumerate(reversed(hist)) if count > 0), 255)
        
        # Calculate median
        cumulative = 0
        median = 0
        for i, count in enumerate(hist):
            cumulative += count
            if cumulative >= total / 2:
                median = i
                break
        
        return {
            'mean': mean,
            'std': std,
            'min': min_val,
            'max': max_val,
            'median': median
        }
    
    def get_dominant_values(self, channel: str, count: int = 5) -> List[Tuple[int, int]]:
        """Get dominant values for a channel."""
        if channel.lower() == 'red':
            hist = self.red
        elif channel.lower() == 'green':
            hist = self.green
        elif channel.lower() == 'blue':
            hist = self.blue
        else:
            raise ValueError(f"Invalid channel: {channel}")
        
        # Get top values by frequency
        indexed_hist = [(i, count) for i, count in enumerate(hist) if count > 0]
        indexed_hist.sort(key=lambda x: x[1], reverse=True)
        
        return indexed_hist[:count]


class ColorDistribution:
    """Color distribution analysis results."""
    
    def __init__(self, colors: List[ColorData], frequencies: List[int]):
        """
        Initialize color distribution.
        
        Args:
            colors: List of unique colors
            frequencies: Frequency count for each color
        """
        self.colors = colors
        self.frequencies = frequencies
        self.total_pixels = sum(frequencies)
    
    def get_percentages(self) -> List[float]:
        """Get percentage distribution of colors."""
        if self.total_pixels == 0:
            return [0.0] * len(self.colors)
        return [(freq / self.total_pixels) * 100 for freq in self.frequencies]
    
    def get_dominant_colors(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get dominant colors with their statistics."""
        # Sort by frequency
        color_data = list(zip(self.colors, self.frequencies, self.get_percentages()))
        color_data.sort(key=lambda x: x[1], reverse=True)
        
        dominant = []
        for i, (color, freq, percentage) in enumerate(color_data[:count]):
            dominant.append({
                'rank': i + 1,
                'color': color,
                'frequency': freq,
                'percentage': percentage,
                'hex': color.hex,
                'rgb': color.rgb
            })
        
        return dominant
    
    def get_color_diversity_index(self) -> float:
        """Calculate Shannon diversity index for colors."""
        if self.total_pixels == 0:
            return 0.0
        
        diversity = 0.0
        for freq in self.frequencies:
            if freq > 0:
                p = freq / self.total_pixels
                diversity -= p * math.log2(p)
        
        return diversity


class AnalysisService:
    """
    Comprehensive color analysis service.
    
    Features:
    - Dominant color extraction with multiple algorithms
    - Color histogram generation and analysis
    - Color distribution statistics
    - Average color calculation
    - Color clustering and grouping
    - Image color analysis and insights
    """
    
    def __init__(self):
        """Initialize AnalysisService."""
        pass
    
    def extract_dominant_colors(self, image_data: ImageData, count: int = 5, 
                              method: str = 'kmeans') -> List[Dict[str, Any]]:
        """
        Extract dominant colors from image using specified method.
        
        Args:
            image_data: Source image
            count: Number of dominant colors to extract
            method: Extraction method ('kmeans', 'quantize', 'histogram')
            
        Returns:
            List of dominant colors with metadata
            
        Raises:
            ImageLoadError: If image processing fails
            ValidationError: If parameters are invalid
        """
        if count <= 0:
            raise ValidationError("Color count must be positive", field_name="count")
        
        if count > 50:
            raise ValidationError("Color count too high (max 50)", field_name="count")
        
        try:
            if method == 'kmeans':
                return self._extract_dominant_kmeans(image_data, count)
            elif method == 'quantize':
                return self._extract_dominant_quantize(image_data, count)
            elif method == 'histogram':
                return self._extract_dominant_histogram(image_data, count)
            else:
                raise ValidationError(f"Unknown extraction method: {method}", field_name="method")
                
        except Exception as e:
            raise ImageLoadError(f"Failed to extract dominant colors: {str(e)}")
    
    def _extract_dominant_kmeans(self, image_data: ImageData, count: int) -> List[Dict[str, Any]]:
        """Extract dominant colors using K-means clustering."""
        try:
            # Convert image to RGB array
            pil_image = image_data.pil_image
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')
            
            # Get pixel data
            pixels = np.array(pil_image)
            pixel_data = pixels.reshape(-1, 3)
            
            # Simple K-means implementation (basic version)
            # For production, consider using sklearn.cluster.KMeans
            centroids = self._simple_kmeans(pixel_data, count)
            
            # Calculate frequencies for each centroid
            dominant_colors = []
            for i, centroid in enumerate(centroids):
                r, g, b = [int(c) for c in centroid]
                color = ColorData(r, g, b)
                
                # Calculate how many pixels are closest to this centroid
                distances = np.sum((pixel_data - centroid) ** 2, axis=1)
                closest_pixels = np.sum(distances == np.min(distances.reshape(-1, 1), axis=0))
                frequency = int(closest_pixels)
                percentage = (frequency / len(pixel_data)) * 100
                
                dominant_colors.append({
                    'rank': i + 1,
                    'color': color,
                    'frequency': frequency,
                    'percentage': percentage,
                    'method': 'kmeans'
                })
            
            # Sort by frequency
            dominant_colors.sort(key=lambda x: x['frequency'], reverse=True)
            
            # Update ranks
            for i, color_info in enumerate(dominant_colors):
                color_info['rank'] = i + 1
            
            return dominant_colors
            
        except Exception as e:
            raise ImageLoadError(f"K-means extraction failed: {str(e)}")
    
    def _simple_kmeans(self, data: np.ndarray, k: int, max_iterations: int = 100) -> np.ndarray:
        """Simple K-means clustering implementation."""
        # Initialize centroids randomly
        centroids = data[np.random.choice(data.shape[0], k, replace=False)]
        
        for _ in range(max_iterations):
            # Assign points to closest centroid
            distances = np.sqrt(((data - centroids[:, np.newaxis])**2).sum(axis=2))
            closest_cluster = np.argmin(distances, axis=0)
            
            # Update centroids
            new_centroids = np.array([data[closest_cluster == i].mean(axis=0) for i in range(k)])
            
            # Check for convergence
            if np.allclose(centroids, new_centroids):
                break
                
            centroids = new_centroids
        
        return centroids
    
    def _extract_dominant_quantize(self, image_data: ImageData, count: int) -> List[Dict[str, Any]]:
        """Extract dominant colors using PIL quantization."""
        try:
            pil_image = image_data.pil_image
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')
            
            # Quantize image
            quantized = pil_image.quantize(colors=count)
            palette = quantized.getpalette()
            
            # Get color frequencies
            histogram = quantized.histogram()
            
            dominant_colors = []
            total_pixels = sum(histogram)
            
            for i in range(count):
                if i * 3 + 2 < len(palette):
                    r = palette[i * 3]
                    g = palette[i * 3 + 1]
                    b = palette[i * 3 + 2]
                    
                    color = ColorData(r, g, b)
                    frequency = histogram[i] if i < len(histogram) else 0
                    percentage = (frequency / total_pixels) * 100 if total_pixels > 0 else 0
                    
                    dominant_colors.append({
                        'rank': i + 1,
                        'color': color,
                        'frequency': frequency,
                        'percentage': percentage,
                        'method': 'quantize'
                    })
            
            # Sort by frequency
            dominant_colors.sort(key=lambda x: x['frequency'], reverse=True)
            
            # Update ranks
            for i, color_info in enumerate(dominant_colors):
                color_info['rank'] = i + 1
            
            return dominant_colors
            
        except Exception as e:
            raise ImageLoadError(f"Quantization extraction failed: {str(e)}")
    
    def _extract_dominant_histogram(self, image_data: ImageData, count: int) -> List[Dict[str, Any]]:
        """Extract dominant colors using histogram analysis."""
        try:
            pil_image = image_data.pil_image
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')
            
            # Get all pixel colors
            pixels = list(pil_image.getdata())
            color_counts = Counter(pixels)
            
            # Get most common colors
            most_common = color_counts.most_common(count)
            total_pixels = len(pixels)
            
            dominant_colors = []
            for i, ((r, g, b), frequency) in enumerate(most_common):
                color = ColorData(r, g, b)
                percentage = (frequency / total_pixels) * 100
                
                dominant_colors.append({
                    'rank': i + 1,
                    'color': color,
                    'frequency': frequency,
                    'percentage': percentage,
                    'method': 'histogram'
                })
            
            return dominant_colors
            
        except Exception as e:
            raise ImageLoadError(f"Histogram extraction failed: {str(e)}")
    
    def generate_color_histogram(self, image_data: ImageData, bins: int = 256) -> ColorHistogram:
        """
        Generate color histogram for image.
        
        Args:
            image_data: Source image
            bins: Number of histogram bins (default 256)
            
        Returns:
            ColorHistogram object
            
        Raises:
            ImageLoadError: If histogram generation fails
        """
        try:
            pil_image = image_data.pil_image
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')
            
            # Get pixel data
            pixels = np.array(pil_image)
            
            # Calculate histograms for each channel
            red_hist = np.histogram(pixels[:, :, 0], bins=bins, range=(0, 256))[0].tolist()
            green_hist = np.histogram(pixels[:, :, 1], bins=bins, range=(0, 256))[0].tolist()
            blue_hist = np.histogram(pixels[:, :, 2], bins=bins, range=(0, 256))[0].tolist()
            
            return ColorHistogram(red_hist, green_hist, blue_hist)
            
        except Exception as e:
            raise ImageLoadError(f"Failed to generate histogram: {str(e)}")
    
    def analyze_color_distribution(self, image_data: ImageData, 
                                 max_colors: int = 1000) -> ColorDistribution:
        """
        Analyze color distribution in image.
        
        Args:
            image_data: Source image
            max_colors: Maximum number of unique colors to analyze
            
        Returns:
            ColorDistribution object
            
        Raises:
            ImageLoadError: If analysis fails
        """
        try:
            pil_image = image_data.pil_image
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')
            
            # Get all pixel colors
            pixels = list(pil_image.getdata())
            color_counts = Counter(pixels)
            
            # Limit to max_colors most common
            most_common = color_counts.most_common(max_colors)
            
            colors = []
            frequencies = []
            
            for (r, g, b), freq in most_common:
                colors.append(ColorData(r, g, b))
                frequencies.append(freq)
            
            return ColorDistribution(colors, frequencies)
            
        except Exception as e:
            raise ImageLoadError(f"Failed to analyze color distribution: {str(e)}")
    
    def calculate_average_color(self, image_data: ImageData, 
                              method: str = 'arithmetic') -> Dict[str, Any]:
        """
        Calculate average color of image.
        
        Args:
            image_data: Source image
            method: Calculation method ('arithmetic', 'weighted', 'median')
            
        Returns:
            Dictionary with average color information
            
        Raises:
            ImageLoadError: If calculation fails
        """
        try:
            pil_image = image_data.pil_image
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')
            
            pixels = np.array(pil_image)
            
            if method == 'arithmetic':
                # Simple arithmetic mean
                avg_r = np.mean(pixels[:, :, 0])
                avg_g = np.mean(pixels[:, :, 1])
                avg_b = np.mean(pixels[:, :, 2])
                
            elif method == 'weighted':
                # Weighted by luminance
                luminance = 0.299 * pixels[:, :, 0] + 0.587 * pixels[:, :, 1] + 0.114 * pixels[:, :, 2]
                weights = luminance / np.sum(luminance)
                
                avg_r = np.average(pixels[:, :, 0], weights=weights)
                avg_g = np.average(pixels[:, :, 1], weights=weights)
                avg_b = np.average(pixels[:, :, 2], weights=weights)
                
            elif method == 'median':
                # Median values
                avg_r = np.median(pixels[:, :, 0])
                avg_g = np.median(pixels[:, :, 1])
                avg_b = np.median(pixels[:, :, 2])
                
            else:
                raise ValidationError(f"Unknown method: {method}", field_name="method")
            
            # Create average color
            avg_color = ColorData(int(avg_r), int(avg_g), int(avg_b))
            
            return {
                'color': avg_color,
                'method': method,
                'rgb': avg_color.rgb,
                'hex': avg_color.hex,
                'hsl': avg_color.hsl,
                'hsv': avg_color.hsv,
                'luminance': avg_color.get_luminance()
            }
            
        except Exception as e:
            raise ImageLoadError(f"Failed to calculate average color: {str(e)}")
    
    def analyze_image_colors(self, image_data: ImageData) -> Dict[str, Any]:
        """
        Perform comprehensive color analysis of image.
        
        Args:
            image_data: Source image
            
        Returns:
            Comprehensive analysis results
        """
        try:
            analysis = {
                'image_info': {
                    'size': image_data.size,
                    'total_pixels': image_data.total_pixels,
                    'format': image_data.format,
                    'mode': image_data.mode
                }
            }
            
            # Dominant colors
            analysis['dominant_colors'] = self.extract_dominant_colors(image_data, 10, 'quantize')
            
            # Color histogram
            histogram = self.generate_color_histogram(image_data)
            analysis['histogram'] = {
                'red_stats': histogram.get_channel_stats('red'),
                'green_stats': histogram.get_channel_stats('green'),
                'blue_stats': histogram.get_channel_stats('blue'),
                'total_pixels': histogram.total_pixels
            }
            
            # Color distribution
            distribution = self.analyze_color_distribution(image_data, 100)
            analysis['distribution'] = {
                'unique_colors': len(distribution.colors),
                'diversity_index': distribution.get_color_diversity_index(),
                'top_colors': distribution.get_dominant_colors(5)
            }
            
            # Average colors
            analysis['average_colors'] = {
                'arithmetic': self.calculate_average_color(image_data, 'arithmetic'),
                'median': self.calculate_average_color(image_data, 'median')
            }
            
            # Color temperature analysis
            avg_color = analysis['average_colors']['arithmetic']['color']
            analysis['color_temperature'] = {
                'estimated_temperature': self._estimate_color_temperature(avg_color),
                'warmth_coolness': self._analyze_warmth_coolness(analysis['dominant_colors'])
            }
            
            return analysis
            
        except Exception as e:
            raise ImageLoadError(f"Failed to analyze image colors: {str(e)}")
    
    def _estimate_color_temperature(self, color: ColorData) -> Dict[str, Any]:
        """Estimate color temperature from color."""
        r, g, b = color.r / 255.0, color.g / 255.0, color.b / 255.0
        
        # Simple temperature estimation
        if b == 0:
            temp = 6500  # Default daylight
        else:
            ratio = r / b
            if ratio > 1.0:
                temp = 2000 + (ratio - 1.0) * 2000
                temp = min(6500, temp)
            else:
                temp = 6500 + (1.0 - ratio) * 3500
                temp = min(10000, temp)
        
        # Classify temperature
        if temp < 3000:
            classification = "Very Warm"
        elif temp < 4000:
            classification = "Warm"
        elif temp < 5000:
            classification = "Neutral Warm"
        elif temp < 6500:
            classification = "Neutral"
        elif temp < 8000:
            classification = "Cool"
        else:
            classification = "Very Cool"
        
        return {
            'temperature_k': int(temp),
            'classification': classification
        }
    
    def _analyze_warmth_coolness(self, dominant_colors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze overall warmth/coolness of dominant colors."""
        warm_weight = 0
        cool_weight = 0
        
        for color_info in dominant_colors:
            color = color_info['color']
            weight = color_info['percentage']
            
            h, s, v = color.hsv
            
            # Classify hue as warm or cool
            if (h >= 0 and h <= 60) or (h >= 300 and h <= 360):
                # Red, orange, yellow range
                warm_weight += weight
            elif h >= 180 and h <= 240:
                # Blue range
                cool_weight += weight
            elif h >= 60 and h <= 180:
                # Green range (neutral to cool)
                cool_weight += weight * 0.7
            else:
                # Purple range (neutral)
                pass
        
        total_weight = warm_weight + cool_weight
        if total_weight > 0:
            warm_ratio = warm_weight / total_weight
            cool_ratio = cool_weight / total_weight
        else:
            warm_ratio = cool_ratio = 0.5
        
        if warm_ratio > 0.6:
            overall = "Warm"
        elif cool_ratio > 0.6:
            overall = "Cool"
        else:
            overall = "Neutral"
        
        return {
            'warm_percentage': warm_ratio * 100,
            'cool_percentage': cool_ratio * 100,
            'overall_tone': overall
        }
    
    def create_palette_from_analysis(self, image_data: ImageData, 
                                   method: str = 'dominant', count: int = 8) -> Palette:
        """
        Create a color palette from image analysis.
        
        Args:
            image_data: Source image
            method: Palette creation method ('dominant', 'distributed', 'harmonic')
            count: Number of colors in palette
            
        Returns:
            Generated palette
        """
        try:
            if method == 'dominant':
                # Use dominant colors
                dominant = self.extract_dominant_colors(image_data, count, 'quantize')
                colors = [color_info['color'] for color_info in dominant]
                
            elif method == 'distributed':
                # Use evenly distributed colors
                distribution = self.analyze_color_distribution(image_data, count * 10)
                # Select colors that are well distributed across the color space
                colors = self._select_distributed_colors(distribution.colors, count)
                
            elif method == 'harmonic':
                # Create harmonic palette based on average color
                avg_info = self.calculate_average_color(image_data, 'arithmetic')
                base_color = avg_info['color']
                
                # Generate harmonic colors
                from ..services.color_service import ColorService
                color_service = ColorService()
                harmony = color_service.generate_color_harmony(base_color, 'analogous', count - 1)
                colors = [base_color] + harmony['colors']
                
            else:
                raise ValidationError(f"Unknown palette method: {method}", field_name="method")
            
            # Create palette
            palette_name = f"Palette from {image_data.file_name}"
            palette = Palette(
                name=palette_name,
                colors=colors[:count],
                description=f"Generated using {method} method from image analysis",
                tags=['generated', 'image-analysis', method]
            )
            
            return palette
            
        except Exception as e:
            raise ImageLoadError(f"Failed to create palette: {str(e)}")
    
    def _select_distributed_colors(self, colors: List[ColorData], count: int) -> List[ColorData]:
        """Select colors that are well distributed in color space."""
        if len(colors) <= count:
            return colors
        
        selected = [colors[0]]  # Start with first color
        
        for _ in range(count - 1):
            best_color = None
            best_min_distance = 0
            
            for candidate in colors:
                if candidate in selected:
                    continue
                
                # Calculate minimum distance to already selected colors
                min_distance = float('inf')
                for selected_color in selected:
                    # Simple Euclidean distance in RGB space
                    distance = math.sqrt(
                        (candidate.r - selected_color.r) ** 2 +
                        (candidate.g - selected_color.g) ** 2 +
                        (candidate.b - selected_color.b) ** 2
                    )
                    min_distance = min(min_distance, distance)
                
                # Select color with maximum minimum distance
                if min_distance > best_min_distance:
                    best_min_distance = min_distance
                    best_color = candidate
            
            if best_color:
                selected.append(best_color)
        
        return selected