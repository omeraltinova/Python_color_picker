"""
Palette class for color palette management.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from .color_data import ColorData


@dataclass
class Palette:
    """
    Color palette data structure for managing collections of colors.
    
    Supports metadata, tagging, and various operations for color management.
    """
    
    name: str
    colors: List[ColorData] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    modified_at: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize palette after creation."""
        if not self.colors:
            self.colors = []
        if not self.tags:
            self.tags = []
        if not self.metadata:
            self.metadata = {}
    
    def add_color(self, color: ColorData) -> None:
        """Add a color to the palette."""
        if color not in self.colors:
            self.colors.append(color)
            self.modified_at = datetime.now()
    
    def remove_color(self, color: ColorData) -> bool:
        """Remove a color from the palette. Returns True if removed."""
        try:
            self.colors.remove(color)
            self.modified_at = datetime.now()
            return True
        except ValueError:
            return False
    
    def remove_color_at_index(self, index: int) -> bool:
        """Remove color at specific index. Returns True if removed."""
        if 0 <= index < len(self.colors):
            self.colors.pop(index)
            self.modified_at = datetime.now()
            return True
        return False    

    def clear_colors(self) -> None:
        """Remove all colors from the palette."""
        self.colors.clear()
        self.modified_at = datetime.now()
    
    def insert_color(self, index: int, color: ColorData) -> None:
        """Insert color at specific index."""
        if 0 <= index <= len(self.colors):
            self.colors.insert(index, color)
            self.modified_at = datetime.now()
    
    def move_color(self, from_index: int, to_index: int) -> bool:
        """Move color from one index to another. Returns True if successful."""
        if (0 <= from_index < len(self.colors) and 
            0 <= to_index < len(self.colors)):
            color = self.colors.pop(from_index)
            self.colors.insert(to_index, color)
            self.modified_at = datetime.now()
            return True
        return False
    
    def add_tag(self, tag: str) -> None:
        """Add a tag to the palette."""
        tag = tag.strip().lower()
        if tag and tag not in self.tags:
            self.tags.append(tag)
            self.modified_at = datetime.now()
    
    def remove_tag(self, tag: str) -> bool:
        """Remove a tag from the palette. Returns True if removed."""
        tag = tag.strip().lower()
        try:
            self.tags.remove(tag)
            self.modified_at = datetime.now()
            return True
        except ValueError:
            return False
    
    def has_tag(self, tag: str) -> bool:
        """Check if palette has a specific tag."""
        return tag.strip().lower() in self.tags
    
    @property
    def color_count(self) -> int:
        """Get the number of colors in the palette."""
        return len(self.colors)
    
    @property
    def is_empty(self) -> bool:
        """Check if the palette is empty."""
        return len(self.colors) == 0
    
    def get_color_at_index(self, index: int) -> Optional[ColorData]:
        """Get color at specific index."""
        if 0 <= index < len(self.colors):
            return self.colors[index]
        return None
    
    def find_color_index(self, color: ColorData) -> int:
        """Find the index of a color. Returns -1 if not found."""
        try:
            return self.colors.index(color)
        except ValueError:
            return -1
    
    def contains_color(self, color: ColorData) -> bool:
        """Check if palette contains a specific color."""
        return color in self.colors
    
    def get_unique_colors(self) -> List[ColorData]:
        """Get list of unique colors (removes duplicates)."""
        unique_colors = []
        for color in self.colors:
            if color not in unique_colors:
                unique_colors.append(color)
        return unique_colors
    
    def remove_duplicates(self) -> int:
        """Remove duplicate colors. Returns number of duplicates removed."""
        original_count = len(self.colors)
        self.colors = self.get_unique_colors()
        removed_count = original_count - len(self.colors)
        if removed_count > 0:
            self.modified_at = datetime.now()
        return removed_count
    
    def copy(self) -> 'Palette':
        """Create a copy of the palette."""
        return Palette(
            name=f"{self.name} (Copy)",
            colors=self.colors.copy(),
            created_at=datetime.now(),
            modified_at=datetime.now(),
            tags=self.tags.copy(),
            description=self.description,
            metadata=self.metadata.copy()
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert palette to dictionary for serialization."""
        return {
            'name': self.name,
            'colors': [
                {
                    'r': color.r,
                    'g': color.g,
                    'b': color.b,
                    'alpha': color.alpha
                }
                for color in self.colors
            ],
            'created_at': self.created_at.isoformat(),
            'modified_at': self.modified_at.isoformat(),
            'tags': self.tags,
            'description': self.description,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Palette':
        """Create palette from dictionary."""
        colors = [
            ColorData(
                r=color_data['r'],
                g=color_data['g'],
                b=color_data['b'],
                alpha=color_data.get('alpha', 1.0)
            )
            for color_data in data.get('colors', [])
        ]
        
        return cls(
            name=data['name'],
            colors=colors,
            created_at=datetime.fromisoformat(data.get('created_at', datetime.now().isoformat())),
            modified_at=datetime.fromisoformat(data.get('modified_at', datetime.now().isoformat())),
            tags=data.get('tags', []),
            description=data.get('description', ''),
            metadata=data.get('metadata', {})
        )
    
    def __str__(self) -> str:
        """String representation of the palette."""
        return f"Palette('{self.name}', {len(self.colors)} colors)"
    
    def __len__(self) -> int:
        """Get the number of colors in the palette."""
        return len(self.colors)
    
    def __iter__(self):
        """Make palette iterable over colors."""
        return iter(self.colors)
    
    def __getitem__(self, index: int) -> ColorData:
        """Get color by index."""
        return self.colors[index]