"""
Dark theme definition for Enhanced Color Picker.

Provides a modern dark theme with high contrast and accessibility features.
"""

# Dark theme color palette
DARK_THEME = {
    # Base colors
    'bg': '#1e1e1e',                    # Main background
    'fg': '#ffffff',                    # Main foreground text
    'bg_secondary': '#2d2d2d',          # Secondary background
    'fg_secondary': '#cccccc',          # Secondary foreground text
    'bg_tertiary': '#3c3c3c',           # Tertiary background
    'fg_tertiary': '#999999',           # Tertiary foreground text
    
    # Accent colors
    'accent': '#0078d4',                # Primary accent color
    'accent_hover': '#106ebe',          # Accent hover state
    'accent_pressed': '#005a9e',        # Accent pressed state
    'accent_disabled': '#4c4c4c',       # Disabled accent
    
    # Status colors
    'success': '#107c10',               # Success/positive actions
    'warning': '#ff8c00',               # Warning/caution
    'error': '#d13438',                 # Error/danger
    'info': '#0078d4',                  # Information
    
    # Button colors
    'button_bg': '#333333',             # Default button background
    'button_fg': '#ffffff',             # Default button text
    'button_hover_bg': '#404040',       # Button hover background
    'button_hover_fg': '#ffffff',       # Button hover text
    'button_pressed_bg': '#2a2a2a',     # Button pressed background
    'button_disabled_bg': '#1a1a1a',    # Disabled button background
    'button_disabled_fg': '#666666',    # Disabled button text
    
    # Primary button colors
    'button_primary_bg': '#0078d4',     # Primary button background
    'button_primary_fg': '#ffffff',     # Primary button text
    'button_primary_hover_bg': '#106ebe', # Primary button hover
    'button_primary_pressed_bg': '#005a9e', # Primary button pressed
    
    # Input/Entry colors
    'entry_bg': '#2d2d2d',              # Entry field background
    'entry_fg': '#ffffff',              # Entry field text
    'entry_border': '#404040',          # Entry field border
    'entry_border_focus': '#0078d4',    # Entry field focused border
    'entry_placeholder': '#999999',     # Placeholder text
    'entry_selection_bg': '#0078d4',    # Text selection background
    'entry_selection_fg': '#ffffff',    # Text selection text
    
    # Text widget colors
    'text_bg': '#1e1e1e',               # Text widget background
    'text_fg': '#ffffff',               # Text widget text
    'text_select_bg': '#0078d4',        # Text selection background
    'text_select_fg': '#ffffff',        # Text selection text
    'text_cursor': '#ffffff',           # Text cursor color
    
    # Panel colors
    'panel_bg': '#252526',              # Panel background
    'panel_border': '#3c3c3c',          # Panel border
    'panel_header_bg': '#2d2d2d',       # Panel header background
    'panel_header_fg': '#cccccc',       # Panel header text
    
    # Menu colors
    'menu_bg': '#2d2d2d',               # Menu background
    'menu_fg': '#ffffff',               # Menu text
    'menu_hover_bg': '#404040',         # Menu item hover
    'menu_hover_fg': '#ffffff',         # Menu item hover text
    'menu_separator': '#404040',        # Menu separator
    'menu_disabled_fg': '#666666',      # Disabled menu item
    
    # Toolbar colors
    'toolbar_bg': '#2d2d2d',            # Toolbar background
    'toolbar_border': '#404040',        # Toolbar border
    'toolbar_button_hover': '#404040',  # Toolbar button hover
    
    # Canvas colors
    'canvas_bg': '#1e1e1e',             # Canvas background
    'canvas_grid': '#333333',           # Canvas grid lines
    'canvas_selection': '#0078d4',      # Canvas selection
    'canvas_crosshair': '#ffffff',      # Canvas crosshair
    
    # Color picker specific
    'color_preview_border': '#404040',  # Color preview border
    'color_swatch_border': '#666666',   # Color swatch border
    'color_swatch_hover': '#0078d4',    # Color swatch hover
    'palette_bg': '#252526',            # Palette background
    'palette_border': '#3c3c3c',        # Palette border
    
    # History and favorites
    'history_bg': '#252526',            # History panel background
    'history_item_hover': '#333333',    # History item hover
    'favorite_star': '#ffb900',         # Favorite star color
    
    # Analysis panel
    'analysis_bg': '#252526',           # Analysis panel background
    'chart_bg': '#1e1e1e',              # Chart background
    'chart_grid': '#333333',            # Chart grid lines
    'chart_text': '#cccccc',            # Chart text
    
    # Scrollbar colors
    'scrollbar_bg': '#2d2d2d',          # Scrollbar background
    'scrollbar_thumb': '#404040',       # Scrollbar thumb
    'scrollbar_thumb_hover': '#4c4c4c', # Scrollbar thumb hover
    'scrollbar_thumb_pressed': '#555555', # Scrollbar thumb pressed
    
    # Border colors
    'border': '#404040',                # Default border
    'border_light': '#4c4c4c',          # Light border
    'border_dark': '#2a2a2a',           # Dark border
    'border_focus': '#0078d4',          # Focused element border
    
    # Shadow colors
    'shadow': 'rgba(0, 0, 0, 0.3)',     # Drop shadow
    'shadow_light': 'rgba(0, 0, 0, 0.1)', # Light shadow
    'shadow_heavy': 'rgba(0, 0, 0, 0.5)', # Heavy shadow
    
    # Overlay colors
    'overlay': 'rgba(0, 0, 0, 0.5)',    # Modal overlay
    'tooltip_bg': '#2d2d2d',            # Tooltip background
    'tooltip_fg': '#ffffff',            # Tooltip text
    'tooltip_border': '#404040',        # Tooltip border
    
    # Progress and loading
    'progress_bg': '#2d2d2d',           # Progress bar background
    'progress_fill': '#0078d4',         # Progress bar fill
    'loading_spinner': '#0078d4',       # Loading spinner color
    
    # Accessibility colors (high contrast variants)
    'high_contrast_bg': '#000000',      # High contrast background
    'high_contrast_fg': '#ffffff',      # High contrast foreground
    'high_contrast_accent': '#00ff00',  # High contrast accent
    'high_contrast_border': '#ffffff',  # High contrast border
    
    # Theme metadata
    '_metadata': {
        'name': 'Dark',
        'description': 'Modern dark theme with high contrast',
        'version': '1.0',
        'author': 'Enhanced Color Picker',
        'accessibility_compliant': True,
        'supports_high_contrast': True
    }
}

# Color scheme variations for different contexts
DARK_THEME_VARIANTS = {
    'high_contrast': {
        **DARK_THEME,
        'bg': '#000000',
        'fg': '#ffffff',
        'accent': '#00ff00',
        'border': '#ffffff',
        'button_bg': '#000000',
        'button_fg': '#ffffff',
        'entry_bg': '#000000',
        'entry_fg': '#ffffff',
        'entry_border': '#ffffff',
    },
    
    'blue_accent': {
        **DARK_THEME,
        'accent': '#4fc3f7',
        'accent_hover': '#29b6f6',
        'accent_pressed': '#0288d1',
        'button_primary_bg': '#4fc3f7',
        'button_primary_hover_bg': '#29b6f6',
        'button_primary_pressed_bg': '#0288d1',
    },
    
    'green_accent': {
        **DARK_THEME,
        'accent': '#66bb6a',
        'accent_hover': '#4caf50',
        'accent_pressed': '#388e3c',
        'button_primary_bg': '#66bb6a',
        'button_primary_hover_bg': '#4caf50',
        'button_primary_pressed_bg': '#388e3c',
    },
    
    'purple_accent': {
        **DARK_THEME,
        'accent': '#ab47bc',
        'accent_hover': '#9c27b0',
        'accent_pressed': '#7b1fa2',
        'button_primary_bg': '#ab47bc',
        'button_primary_hover_bg': '#9c27b0',
        'button_primary_pressed_bg': '#7b1fa2',
    }
}

def get_dark_theme_variant(variant_name: str = 'default') -> dict:
    """Get a specific variant of the dark theme."""
    if variant_name == 'default' or variant_name not in DARK_THEME_VARIANTS:
        return DARK_THEME.copy()
    return DARK_THEME_VARIANTS[variant_name].copy()

def create_custom_dark_theme(accent_color: str, name: str = 'custom_dark') -> dict:
    """Create a custom dark theme with specified accent color."""
    custom_theme = DARK_THEME.copy()
    
    # Update accent colors
    custom_theme['accent'] = accent_color
    custom_theme['button_primary_bg'] = accent_color
    custom_theme['entry_border_focus'] = accent_color
    custom_theme['border_focus'] = accent_color
    custom_theme['text_select_bg'] = accent_color
    custom_theme['progress_fill'] = accent_color
    custom_theme['loading_spinner'] = accent_color
    
    # Update metadata
    custom_theme['_metadata'] = {
        **custom_theme['_metadata'],
        'name': name,
        'description': f'Custom dark theme with {accent_color} accent',
        'custom': True
    }
    
    return custom_theme