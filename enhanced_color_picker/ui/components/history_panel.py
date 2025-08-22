"""
Color History and Favorites Panel Component

Enhanced history panel with search and filtering, favorites management with categories,
history persistence across sessions, and export functionality.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from typing import Optional, List, Dict, Any, Callable, Set
import json
import os
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

from ...models.color_data import ColorData
from ...core.event_bus import EventBus, EventData
from ...storage.settings_storage import SettingsStorage


class HistoryFilterType(Enum):
    """Filter types for color history."""
    ALL = "all"
    TODAY = "today"
    WEEK = "week"
    MONTH = "month"
    FAVORITES = "favorites"
    CUSTOM = "custom"


@dataclass
class ColorHistoryEntry:
    """Entry in color history with metadata."""
    color: ColorData
    timestamp: datetime
    source: str = "unknown"
    image_path: Optional[str] = None
    position: Optional[tuple] = None
    is_favorite: bool = False
    category: str = "default"
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "color": {
                "r": self.color.r,
                "g": self.color.g,
                "b": self.color.b,
                "alpha": self.color.alpha
            },
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "image_path": self.image_path,
            "position": self.position,
            "is_favorite": self.is_favorite,
            "category": self.category,
            "notes": self.notes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ColorHistoryEntry':
        """Create from dictionary."""
        color_data = data["color"]
        color = ColorData.from_rgb(
            color_data["r"], color_data["g"], color_data["b"], color_data.get("alpha", 1.0)
        )
        
        return cls(
            color=color,
            timestamp=datetime.fromisoformat(data["timestamp"]),
            source=data.get("source", "unknown"),
            image_path=data.get("image_path"),
            position=data.get("position"),
            is_favorite=data.get("is_favorite", False),
            category=data.get("category", "default"),
            notes=data.get("notes", "")
        )


class ColorHistoryStorage:
    """Storage manager for color history and favorites."""
    
    def __init__(self, storage_dir: str = ".kiro/data"):
        self.storage_dir = storage_dir
        self.history_file = os.path.join(storage_dir, "color_history.json")
        self.favorites_file = os.path.join(storage_dir, "color_favorites.json")
        
        # Ensure storage directory exists
        os.makedirs(storage_dir, exist_ok=True)
    
    def save_history(self, history: List[ColorHistoryEntry]):
        """Save color history to file."""
        try:
            data = [entry.to_dict() for entry in history]
            with open(self.history_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            raise Exception(f"Failed to save history: {str(e)}")
    
    def load_history(self) -> List[ColorHistoryEntry]:
        """Load color history from file."""
        if not os.path.exists(self.history_file):
            return []
        
        try:
            with open(self.history_file, 'r') as f:
                data = json.load(f)
            
            return [ColorHistoryEntry.from_dict(entry) for entry in data]
        except Exception as e:
            print(f"Warning: Failed to load history: {str(e)}")
            return []
    
    def save_favorites(self, favorites: List[ColorHistoryEntry]):
        """Save favorites to file."""
        try:
            data = [entry.to_dict() for entry in favorites if entry.is_favorite]
            with open(self.favorites_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            raise Exception(f"Failed to save favorites: {str(e)}")
    
    def load_favorites(self) -> List[ColorHistoryEntry]:
        """Load favorites from file."""
        if not os.path.exists(self.favorites_file):
            return []
        
        try:
            with open(self.favorites_file, 'r') as f:
                data = json.load(f)
            
            return [ColorHistoryEntry.from_dict(entry) for entry in data]
        except Exception as e:
            print(f"Warning: Failed to load favorites: {str(e)}")
            return []
    
    def export_history(self, history: List[ColorHistoryEntry], file_path: str, format_type: str = "json"):
        """Export history to file in specified format."""
        if format_type.lower() == "json":
            data = [entry.to_dict() for entry in history]
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
        
        elif format_type.lower() == "csv":
            import csv
            with open(file_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Timestamp", "Hex", "RGB", "Source", "Category", "Notes", "Is Favorite"])
                
                for entry in history:
                    writer.writerow([
                        entry.timestamp.isoformat(),
                        entry.color.hex,
                        f"rgb({entry.color.r}, {entry.color.g}, {entry.color.b})",
                        entry.source,
                        entry.category,
                        entry.notes,
                        entry.is_favorite
                    ])
        
        elif format_type.lower() == "txt":
            with open(file_path, 'w') as f:
                for entry in history:
                    f.write(f"{entry.timestamp.strftime('%Y-%m-%d %H:%M:%S')} - {entry.color.hex} - {entry.source}\n")
        
        else:
            raise ValueError(f"Unsupported export format: {format_type}")


class ColorHistoryWidget(tk.Frame):
    """Widget for displaying a single color history entry."""
    
    def __init__(self, parent, entry: ColorHistoryEntry, 
                 on_click: Optional[Callable] = None,
                 on_favorite_toggle: Optional[Callable] = None,
                 on_context_menu: Optional[Callable] = None,
                 **kwargs):
        super().__init__(parent, relief=tk.RAISED, borderwidth=1, **kwargs)
        
        self.entry = entry
        self.on_click = on_click
        self.on_favorite_toggle = on_favorite_toggle
        self.on_context_menu = on_context_menu
        
        self._setup_ui()
        self._bind_events()
    
    def _setup_ui(self):
        """Setup the widget UI."""
        # Color swatch
        self.color_canvas = tk.Canvas(self, width=30, height=30, highlightthickness=0)
        self.color_canvas.grid(row=0, column=0, rowspan=2, padx=5, pady=5)
        
        # Draw color
        hex_color = self.entry.color.hex
        self.color_canvas.create_rectangle(0, 0, 30, 30, fill=hex_color, outline="#ccc")
        
        # Color info
        info_frame = tk.Frame(self)
        info_frame.grid(row=0, column=1, sticky="ew", padx=5)
        
        # Hex value
        hex_label = tk.Label(info_frame, text=self.entry.color.hex, font=("TkDefaultFont", 10, "bold"))
        hex_label.pack(anchor="w")
        
        # RGB value
        rgb_text = f"RGB({self.entry.color.r}, {self.entry.color.g}, {self.entry.color.b})"
        rgb_label = tk.Label(info_frame, text=rgb_text, font=("TkDefaultFont", 8))
        rgb_label.pack(anchor="w")
        
        # Metadata
        meta_frame = tk.Frame(self)
        meta_frame.grid(row=1, column=1, sticky="ew", padx=5)
        
        # Timestamp and source
        time_text = self.entry.timestamp.strftime("%m/%d %H:%M")
        source_text = f"{time_text} • {self.entry.source}"
        if self.entry.category != "default":
            source_text += f" • {self.entry.category}"
        
        meta_label = tk.Label(meta_frame, text=source_text, font=("TkDefaultFont", 7), fg="gray")
        meta_label.pack(anchor="w")
        
        # Favorite button
        self.favorite_var = tk.BooleanVar(value=self.entry.is_favorite)
        self.favorite_button = tk.Checkbutton(
            self, text="★", variable=self.favorite_var,
            command=self._on_favorite_toggle,
            font=("TkDefaultFont", 12),
            fg="gold" if self.entry.is_favorite else "gray",
            selectcolor="white", indicatoron=False,
            width=2, height=1
        )
        self.favorite_button.grid(row=0, column=2, padx=5, pady=2, sticky="n")
        
        # Configure grid
        self.grid_columnconfigure(1, weight=1)
    
    def _bind_events(self):
        """Bind events."""
        # Click events
        self.bind("<Button-1>", self._on_click)
        self.color_canvas.bind("<Button-1>", self._on_click)
        
        # Right-click context menu
        self.bind("<Button-3>", self._on_right_click)
        self.color_canvas.bind("<Button-3>", self._on_right_click)
        
        # Hover effects
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
    
    def _on_click(self, event):
        """Handle click event."""
        if self.on_click:
            self.on_click(self.entry)
    
    def _on_right_click(self, event):
        """Handle right-click event."""
        if self.on_context_menu:
            self.on_context_menu(self.entry, event)
    
    def _on_favorite_toggle(self):
        """Handle favorite toggle."""
        self.entry.is_favorite = self.favorite_var.get()
        
        # Update button appearance
        self.favorite_button.configure(
            fg="gold" if self.entry.is_favorite else "gray"
        )
        
        if self.on_favorite_toggle:
            self.on_favorite_toggle(self.entry)
    
    def _on_enter(self, event):
        """Handle mouse enter."""
        self.configure(bg="#f0f0f0")
    
    def _on_leave(self, event):
        """Handle mouse leave."""
        self.configure(bg="white")
    
    def update_entry(self, entry: ColorHistoryEntry):
        """Update the displayed entry."""
        self.entry = entry
        
        # Update color swatch
        hex_color = entry.color.hex
        self.color_canvas.delete("all")
        self.color_canvas.create_rectangle(0, 0, 30, 30, fill=hex_color, outline="#ccc")
        
        # Update favorite state
        self.favorite_var.set(entry.is_favorite)
        self.favorite_button.configure(
            fg="gold" if entry.is_favorite else "gray"
        )


class ColorHistoryAndFavoritesPanel(ttk.Frame):
    """
    Enhanced color history and favorites management panel.
    
    Features:
    - Color history with timestamps and metadata
    - Favorites management with categories
    - Search and filtering capabilities
    - History persistence across sessions
    - Export functionality
    """
    
    def __init__(self, parent, event_bus: EventBus, max_history: int = 500, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.event_bus = event_bus
        self.max_history = max_history
        
        # Storage
        self.storage = ColorHistoryStorage()
        
        # Data
        self.history: List[ColorHistoryEntry] = []
        self.filtered_history: List[ColorHistoryEntry] = []
        self.categories: Set[str] = {"default"}
        
        # UI state
        self.current_filter = HistoryFilterType.ALL
        self.search_text = ""
        self.selected_category = "all"
        
        # Load data
        self._load_data()
        
        self._setup_ui()
        self._setup_event_subscriptions()
        
        # Auto-save timer
        self._setup_auto_save()
    
    def _setup_ui(self):
        """Setup the user interface."""
        # Create notebook for history and favorites
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # History tab
        self.history_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.history_frame, text="History")
        self._setup_history_tab()
        
        # Favorites tab
        self.favorites_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.favorites_frame, text="Favorites")
        self._setup_favorites_tab()
    
    def _setup_history_tab(self):
        """Setup the history tab."""
        # Search and filter controls
        controls_frame = ttk.Frame(self.history_frame)
        controls_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Search
        search_frame = ttk.Frame(controls_frame)
        search_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=20)
        self.search_entry.pack(side=tk.LEFT, padx=(5, 10), fill=tk.X, expand=True)
        self.search_entry.bind("<KeyRelease>", self._on_search_changed)
        
        ttk.Button(search_frame, text="Clear", command=self._clear_search).pack(side=tk.LEFT)
        
        # Filters
        filter_frame = ttk.Frame(controls_frame)
        filter_frame.pack(fill=tk.X)
        
        ttk.Label(filter_frame, text="Filter:").pack(side=tk.LEFT)
        
        self.filter_var = tk.StringVar(value="all")
        filter_combo = ttk.Combobox(filter_frame, textvariable=self.filter_var,
                                   values=["all", "today", "week", "month", "favorites"],
                                   state="readonly", width=10)
        filter_combo.pack(side=tk.LEFT, padx=(5, 10))
        filter_combo.bind("<<ComboboxSelected>>", self._on_filter_changed)
        
        ttk.Label(filter_frame, text="Category:").pack(side=tk.LEFT, padx=(10, 0))
        
        self.category_var = tk.StringVar(value="all")
        self.category_combo = ttk.Combobox(filter_frame, textvariable=self.category_var,
                                         state="readonly", width=12)
        self.category_combo.pack(side=tk.LEFT, padx=(5, 10))
        self.category_combo.bind("<<ComboboxSelected>>", self._on_category_changed)
        
        # Action buttons
        ttk.Button(filter_frame, text="Export", command=self._export_history).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(filter_frame, text="Clear History", command=self._clear_history).pack(side=tk.RIGHT, padx=5)
        
        # History list
        self._setup_history_list()
        
        # Update category combo
        self._update_category_combo()
    
    def _setup_favorites_tab(self):
        """Setup the favorites tab."""
        # Favorites controls
        fav_controls_frame = ttk.Frame(self.favorites_frame)
        fav_controls_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Category management
        cat_frame = ttk.Frame(fav_controls_frame)
        cat_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(cat_frame, text="Category:").pack(side=tk.LEFT)
        
        self.fav_category_var = tk.StringVar(value="all")
        self.fav_category_combo = ttk.Combobox(cat_frame, textvariable=self.fav_category_var,
                                             state="readonly", width=15)
        self.fav_category_combo.pack(side=tk.LEFT, padx=(5, 10))
        self.fav_category_combo.bind("<<ComboboxSelected>>", self._on_favorites_category_changed)
        
        ttk.Button(cat_frame, text="New Category", command=self._create_category).pack(side=tk.LEFT, padx=5)
        ttk.Button(cat_frame, text="Export Favorites", command=self._export_favorites).pack(side=tk.RIGHT)
        
        # Favorites list
        self._setup_favorites_list()
    
    def _setup_history_list(self):
        """Setup the scrollable history list."""
        # Create scrollable frame
        list_frame = ttk.Frame(self.history_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Canvas and scrollbar
        self.history_canvas = tk.Canvas(list_frame, bg="white")
        h_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.history_canvas.yview)
        
        self.history_canvas.configure(yscrollcommand=h_scrollbar.set)
        
        # Scrollable frame
        self.history_list_frame = tk.Frame(self.history_canvas, bg="white")
        self.history_canvas_window = self.history_canvas.create_window(0, 0, anchor="nw", window=self.history_list_frame)
        
        # Pack
        self.history_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        h_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind events
        self.history_canvas.bind("<Configure>", self._on_history_canvas_configure)
        self.history_list_frame.bind("<Configure>", self._on_history_frame_configure)
        self.history_canvas.bind("<MouseWheel>", self._on_history_mousewheel)
        
        # Info label
        self.history_info_label = ttk.Label(self.history_frame, text="", font=("TkDefaultFont", 8))
        self.history_info_label.pack(pady=2)
    
    def _setup_favorites_list(self):
        """Setup the scrollable favorites list."""
        # Create scrollable frame
        fav_list_frame = ttk.Frame(self.favorites_frame)
        fav_list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Canvas and scrollbar
        self.favorites_canvas = tk.Canvas(fav_list_frame, bg="white")
        fav_scrollbar = ttk.Scrollbar(fav_list_frame, orient=tk.VERTICAL, command=self.favorites_canvas.yview)
        
        self.favorites_canvas.configure(yscrollcommand=fav_scrollbar.set)
        
        # Scrollable frame
        self.favorites_list_frame = tk.Frame(self.favorites_canvas, bg="white")
        self.favorites_canvas_window = self.favorites_canvas.create_window(0, 0, anchor="nw", window=self.favorites_list_frame)
        
        # Pack
        self.favorites_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        fav_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind events
        self.favorites_canvas.bind("<Configure>", self._on_favorites_canvas_configure)
        self.favorites_list_frame.bind("<Configure>", self._on_favorites_frame_configure)
        self.favorites_canvas.bind("<MouseWheel>", self._on_favorites_mousewheel)
        
        # Info label
        self.favorites_info_label = ttk.Label(self.favorites_frame, text="", font=("TkDefaultFont", 8))
        self.favorites_info_label.pack(pady=2)
    
    def _setup_event_subscriptions(self):
        """Setup event bus subscriptions."""
        self.event_bus.subscribe("color_picked", self._on_color_picked)
        self.event_bus.subscribe("color_selected", self._on_color_selected)
    
    def _setup_auto_save(self):
        """Setup automatic saving."""
        def auto_save():
            try:
                self._save_data()
            except Exception as e:
                print(f"Auto-save failed: {e}")
            
            # Schedule next auto-save
            self.after(30000, auto_save)  # Every 30 seconds
        
        # Start auto-save
        self.after(30000, auto_save)
    
    def _load_data(self):
        """Load history and favorites data."""
        try:
            self.history = self.storage.load_history()
            
            # Extract categories
            for entry in self.history:
                if entry.category:
                    self.categories.add(entry.category)
            
            # Apply initial filter
            self._apply_filters()
            
        except Exception as e:
            print(f"Failed to load history data: {e}")
            self.history = []
            self.filtered_history = []
    
    def _save_data(self):
        """Save history and favorites data."""
        try:
            self.storage.save_history(self.history)
            
            # Save favorites separately
            favorites = [entry for entry in self.history if entry.is_favorite]
            self.storage.save_favorites(favorites)
            
        except Exception as e:
            print(f"Failed to save history data: {e}")
    
    def add_color_to_history(self, color: ColorData, source: str = "manual", 
                           image_path: Optional[str] = None, position: Optional[tuple] = None):
        """Add a color to the history."""
        # Check if color already exists in recent history (last 10 entries)
        recent_colors = self.history[-10:] if len(self.history) >= 10 else self.history
        for entry in recent_colors:
            if (entry.color.r == color.r and entry.color.g == color.g and 
                entry.color.b == color.b and abs(entry.color.alpha - color.alpha) < 0.01):
                # Update timestamp of existing entry
                entry.timestamp = datetime.now()
                self._apply_filters()
                self._update_history_display()
                return
        
        # Create new entry
        entry = ColorHistoryEntry(
            color=color,
            timestamp=datetime.now(),
            source=source,
            image_path=image_path,
            position=position
        )
        
        # Add to history
        self.history.append(entry)
        
        # Limit history size
        if len(self.history) > self.max_history:
            # Remove oldest non-favorite entries
            non_favorites = [e for e in self.history if not e.is_favorite]
            if non_favorites:
                oldest_non_favorite = min(non_favorites, key=lambda e: e.timestamp)
                self.history.remove(oldest_non_favorite)
        
        # Update display
        self._apply_filters()
        self._update_history_display()
        
        # Auto-save
        self._save_data()
    
    def _apply_filters(self):
        """Apply current filters to history."""
        filtered = self.history.copy()
        
        # Apply time filter
        now = datetime.now()
        if self.current_filter == HistoryFilterType.TODAY:
            start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
            filtered = [e for e in filtered if e.timestamp >= start_of_day]
        elif self.current_filter == HistoryFilterType.WEEK:
            week_ago = now - timedelta(days=7)
            filtered = [e for e in filtered if e.timestamp >= week_ago]
        elif self.current_filter == HistoryFilterType.MONTH:
            month_ago = now - timedelta(days=30)
            filtered = [e for e in filtered if e.timestamp >= month_ago]
        elif self.current_filter == HistoryFilterType.FAVORITES:
            filtered = [e for e in filtered if e.is_favorite]
        
        # Apply category filter
        if self.selected_category != "all":
            filtered = [e for e in filtered if e.category == self.selected_category]
        
        # Apply search filter
        if self.search_text:
            search_lower = self.search_text.lower()
            filtered = [e for e in filtered if (
                search_lower in e.color.hex.lower() or
                search_lower in e.source.lower() or
                search_lower in e.category.lower() or
                search_lower in e.notes.lower()
            )]
        
        # Sort by timestamp (newest first)
        filtered.sort(key=lambda e: e.timestamp, reverse=True)
        
        self.filtered_history = filtered
    
    def _update_history_display(self):
        """Update the history display."""
        # Clear existing widgets
        for widget in self.history_list_frame.winfo_children():
            widget.destroy()
        
        # Create widgets for filtered history
        for i, entry in enumerate(self.filtered_history):
            widget = ColorHistoryWidget(
                self.history_list_frame, entry,
                on_click=self._on_history_item_click,
                on_favorite_toggle=self._on_favorite_toggle,
                on_context_menu=self._on_history_context_menu
            )
            widget.pack(fill=tk.X, padx=2, pady=1)
        
        # Update info
        total_count = len(self.history)
        filtered_count = len(self.filtered_history)
        favorites_count = len([e for e in self.history if e.is_favorite])
        
        info_text = f"Showing {filtered_count} of {total_count} colors ({favorites_count} favorites)"
        self.history_info_label.configure(text=info_text)
        
        # Update scroll region
        self.history_list_frame.update_idletasks()
        self.history_canvas.configure(scrollregion=self.history_canvas.bbox("all"))
    
    def _update_favorites_display(self):
        """Update the favorites display."""
        # Clear existing widgets
        for widget in self.favorites_list_frame.winfo_children():
            widget.destroy()
        
        # Get favorites
        favorites = [e for e in self.history if e.is_favorite]
        
        # Apply category filter
        if self.fav_category_var.get() != "all":
            favorites = [e for e in favorites if e.category == self.fav_category_var.get()]
        
        # Sort by timestamp (newest first)
        favorites.sort(key=lambda e: e.timestamp, reverse=True)
        
        # Create widgets
        for entry in favorites:
            widget = ColorHistoryWidget(
                self.favorites_list_frame, entry,
                on_click=self._on_history_item_click,
                on_favorite_toggle=self._on_favorite_toggle,
                on_context_menu=self._on_favorites_context_menu
            )
            widget.pack(fill=tk.X, padx=2, pady=1)
        
        # Update info
        self.favorites_info_label.configure(text=f"{len(favorites)} favorite colors")
        
        # Update scroll region
        self.favorites_list_frame.update_idletasks()
        self.favorites_canvas.configure(scrollregion=self.favorites_canvas.bbox("all"))
    
    def _update_category_combo(self):
        """Update category combo boxes."""
        categories = ["all"] + sorted(list(self.categories))
        
        self.category_combo.configure(values=categories)
        self.fav_category_combo.configure(values=categories)
    
    # Event handlers
    def _on_search_changed(self, event=None):
        """Handle search text change."""
        self.search_text = self.search_var.get()
        self._apply_filters()
        self._update_history_display()
    
    def _clear_search(self):
        """Clear search text."""
        self.search_var.set("")
        self.search_text = ""
        self._apply_filters()
        self._update_history_display()
    
    def _on_filter_changed(self, event=None):
        """Handle filter change."""
        filter_map = {
            "all": HistoryFilterType.ALL,
            "today": HistoryFilterType.TODAY,
            "week": HistoryFilterType.WEEK,
            "month": HistoryFilterType.MONTH,
            "favorites": HistoryFilterType.FAVORITES
        }
        
        self.current_filter = filter_map.get(self.filter_var.get(), HistoryFilterType.ALL)
        self._apply_filters()
        self._update_history_display()
    
    def _on_category_changed(self, event=None):
        """Handle category filter change."""
        self.selected_category = self.category_var.get()
        self._apply_filters()
        self._update_history_display()
    
    def _on_favorites_category_changed(self, event=None):
        """Handle favorites category change."""
        self._update_favorites_display()
    
    def _on_history_item_click(self, entry: ColorHistoryEntry):
        """Handle history item click."""
        # Publish color selected event
        self.event_bus.publish("color_selected", {
            "color": entry.color,
            "source": "history",
            "entry": entry
        }, source="history_panel")
    
    def _on_favorite_toggle(self, entry: ColorHistoryEntry):
        """Handle favorite toggle."""
        # Update displays
        self._update_history_display()
        self._update_favorites_display()
        
        # Auto-save
        self._save_data()
        
        # Publish event
        self.event_bus.publish("favorite_toggled", {
            "entry": entry,
            "is_favorite": entry.is_favorite
        }, source="history_panel")
    
    def _on_history_context_menu(self, entry: ColorHistoryEntry, event):
        """Handle history item context menu."""
        menu = tk.Menu(self, tearoff=0)
        
        menu.add_command(label="Copy Hex", command=lambda: self._copy_color(entry.color.hex))
        menu.add_command(label="Copy RGB", command=lambda: self._copy_color(f"rgb({entry.color.r}, {entry.color.g}, {entry.color.b})"))
        menu.add_separator()
        
        if entry.is_favorite:
            menu.add_command(label="Remove from Favorites", command=lambda: self._toggle_favorite(entry))
        else:
            menu.add_command(label="Add to Favorites", command=lambda: self._toggle_favorite(entry))
        
        menu.add_command(label="Set Category", command=lambda: self._set_category(entry))
        menu.add_command(label="Add Notes", command=lambda: self._add_notes(entry))
        menu.add_separator()
        menu.add_command(label="Remove from History", command=lambda: self._remove_from_history(entry))
        
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
    
    def _on_favorites_context_menu(self, entry: ColorHistoryEntry, event):
        """Handle favorites item context menu."""
        menu = tk.Menu(self, tearoff=0)
        
        menu.add_command(label="Copy Hex", command=lambda: self._copy_color(entry.color.hex))
        menu.add_command(label="Copy RGB", command=lambda: self._copy_color(f"rgb({entry.color.r}, {entry.color.g}, {entry.color.b})"))
        menu.add_separator()
        menu.add_command(label="Remove from Favorites", command=lambda: self._toggle_favorite(entry))
        menu.add_command(label="Set Category", command=lambda: self._set_category(entry))
        menu.add_command(label="Add Notes", command=lambda: self._add_notes(entry))
        
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
    
    def _copy_color(self, text: str):
        """Copy color to clipboard."""
        try:
            import pyperclip
            pyperclip.copy(text)
            messagebox.showinfo("Copied", f"'{text}' copied to clipboard!")
        except ImportError:
            messagebox.showerror("Error", "pyperclip not available for clipboard operations.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy: {str(e)}")
    
    def _toggle_favorite(self, entry: ColorHistoryEntry):
        """Toggle favorite status."""
        entry.is_favorite = not entry.is_favorite
        self._on_favorite_toggle(entry)
    
    def _set_category(self, entry: ColorHistoryEntry):
        """Set category for entry."""
        current_categories = list(self.categories)
        
        # Create dialog
        dialog = tk.Toplevel(self)
        dialog.title("Set Category")
        dialog.geometry("300x150")
        dialog.transient(self)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Category:").pack(pady=10)
        
        category_var = tk.StringVar(value=entry.category)
        category_combo = ttk.Combobox(dialog, textvariable=category_var, values=current_categories)
        category_combo.pack(pady=5, padx=20, fill=tk.X)
        
        def save_category():
            new_category = category_var.get().strip()
            if new_category:
                entry.category = new_category
                self.categories.add(new_category)
                self._update_category_combo()
                self._update_history_display()
                self._update_favorites_display()
                self._save_data()
            dialog.destroy()
        
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text="Save", command=save_category).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def _add_notes(self, entry: ColorHistoryEntry):
        """Add notes to entry."""
        notes = simpledialog.askstring("Add Notes", "Notes:", initialvalue=entry.notes)
        if notes is not None:
            entry.notes = notes
            self._update_history_display()
            self._update_favorites_display()
            self._save_data()
    
    def _remove_from_history(self, entry: ColorHistoryEntry):
        """Remove entry from history."""
        if messagebox.askyesno("Confirm", "Remove this color from history?"):
            self.history.remove(entry)
            self._apply_filters()
            self._update_history_display()
            self._update_favorites_display()
            self._save_data()
    
    def _create_category(self):
        """Create a new category."""
        category = simpledialog.askstring("New Category", "Category name:")
        if category and category.strip():
            self.categories.add(category.strip())
            self._update_category_combo()
    
    def _clear_history(self):
        """Clear all history."""
        if messagebox.askyesno("Confirm", "Clear all color history? This cannot be undone."):
            self.history.clear()
            self._apply_filters()
            self._update_history_display()
            self._update_favorites_display()
            self._save_data()
    
    def _export_history(self):
        """Export history to file."""
        if not self.filtered_history:
            messagebox.showwarning("No Data", "No history to export.")
            return
        
        # File dialog
        file_path = filedialog.asksaveasfilename(
            title="Export History",
            defaultextension=".json",
            filetypes=[
                ("JSON files", "*.json"),
                ("CSV files", "*.csv"),
                ("Text files", "*.txt"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            try:
                ext = os.path.splitext(file_path)[1].lower()
                format_type = {".json": "json", ".csv": "csv", ".txt": "txt"}.get(ext, "json")
                
                self.storage.export_history(self.filtered_history, file_path, format_type)
                messagebox.showinfo("Success", f"History exported to {file_path}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export history: {str(e)}")
    
    def _export_favorites(self):
        """Export favorites to file."""
        favorites = [e for e in self.history if e.is_favorite]
        
        if not favorites:
            messagebox.showwarning("No Data", "No favorites to export.")
            return
        
        # File dialog
        file_path = filedialog.asksaveasfilename(
            title="Export Favorites",
            defaultextension=".json",
            filetypes=[
                ("JSON files", "*.json"),
                ("CSV files", "*.csv"),
                ("Text files", "*.txt"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            try:
                ext = os.path.splitext(file_path)[1].lower()
                format_type = {".json": "json", ".csv": "csv", ".txt": "txt"}.get(ext, "json")
                
                self.storage.export_history(favorites, file_path, format_type)
                messagebox.showinfo("Success", f"Favorites exported to {file_path}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export favorites: {str(e)}")
    
    # Canvas event handlers
    def _on_history_canvas_configure(self, event):
        """Handle history canvas configure."""
        self.history_canvas.configure(scrollregion=self.history_canvas.bbox("all"))
    
    def _on_history_frame_configure(self, event):
        """Handle history frame configure."""
        self.history_canvas.configure(scrollregion=self.history_canvas.bbox("all"))
    
    def _on_history_mousewheel(self, event):
        """Handle history mouse wheel."""
        self.history_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def _on_favorites_canvas_configure(self, event):
        """Handle favorites canvas configure."""
        self.favorites_canvas.configure(scrollregion=self.favorites_canvas.bbox("all"))
    
    def _on_favorites_frame_configure(self, event):
        """Handle favorites frame configure."""
        self.favorites_canvas.configure(scrollregion=self.favorites_canvas.bbox("all"))
    
    def _on_favorites_mousewheel(self, event):
        """Handle favorites mouse wheel."""
        self.favorites_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    # Event bus handlers
    def _on_color_picked(self, event_data: EventData):
        """Handle color picked event."""
        data = event_data.data
        if "color" in data:
            self.add_color_to_history(
                data["color"],
                source="color_picker",
                image_path=data.get("image_path"),
                position=data.get("image_position")
            )
    
    def _on_color_selected(self, event_data: EventData):
        """Handle color selected event."""
        data = event_data.data
        if "color" in data and data.get("source") != "history":
            self.add_color_to_history(
                data["color"],
                source=data.get("source", "selection")
            )
    
    def get_history(self) -> List[ColorHistoryEntry]:
        """Get the color history."""
        return self.history.copy()
    
    def get_favorites(self) -> List[ColorHistoryEntry]:
        """Get favorite colors."""
        return [e for e in self.history if e.is_favorite]
    
    def cleanup(self):
        """Cleanup and save data."""
        self._save_data()