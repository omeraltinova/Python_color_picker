"""
Light theme definition for Enhanced Color Picker.

Provides a clean light theme with good contrast and accessibility features.
"""

# Light theme color palette
LIGHT_THEME = {
    # Base colors
    'bg': '#ffffff',                    # Main background
    'fg': '#000000',                    # Main foreground text
    'bg_secondary': '#f5f5f5',          # Secondary background
    'fg_secondary': '#333333',          # Secondary foreground text
    'bg_tertiary': '#e0e0e0',           # Tertiary background
    'fg_tertiary': '#666666',           # Tertiary foreground text
    
    # Accent colors
    'accent': '#0078d4',                # Primary accent color
    'accent_hover': '#106ebe',          # Accent hover state
    'accent_pressed': '#005a9e',        # Accent pressed state
    'accent_disabled': '#cccccc',       # Disabled accent
    
    # Status colors
    'success': '#107c10',               # Success/positive actions
    'warning': '#ff8c00',               # Warning/caution
    'error': '#d13438',                 # Error/danger
    'info': '#0078d4',                  # Information
    
    # Button colors
    'button_bg': '#f0f0f0',             # Default button background
    'button_fg': '#000000',             # Default button text
    'button_hover_bg': '#e0e0e0',       # Button hover background
    'button_hover_fg': '#000000',       # Button hover text
    'button_pressed_bg': '#d0d0d0',     # Button pressed background
    'button_disabled_bg': '#f8f8f8',    # Disabled button background
    'button_disabled_fg': '#cccccc',    # Disabled button text
    
    # Primary button colors
    'button_primary_bg': '#0078d4',     # Primary button background
    'button_primary_fg': '#ffffff',     # Primary button text
    'button_primary_hover_bg': '#106ebe', # Primary button hover
    'button_primary_pressed_bg': '#005a9e', # Primary button pressed
    
    # Input/Entry colors
    'entry_bg': '#ffffff',              # Entry field background
    'entry_fg': '#000000',              # Entry field text
    'entry_border': '#cccccc',          # Entry field border
    'entry_border_focus': '#0078d4',    # Entry field focused border
    'entry_placeholder': '#999999',     # Placeholder text
    'entry_selection_bg': '#0078d4',    # Text selection background
    'entry_selection_fg': '#ffffff',    # Text selection text
    
    # Text widget colors
    'text_bg': '#ffffff',               # Text widget background
    'text_fg': '#000000',               # Text widget text
    'text_select_bg': '#0078d4',        # Text selection background
    'text_select_fg': '#ffffff',        # Text selection text
    'text_cursor': '#000000',           # Text cursor color
    
    # Panel colors
    'panel_bg': '#f8f8f8',              # Panel background
    'panel_border': '#e0e0e0',          # Panel border
    'panel_header_bg': '#f0f0f0',       # Panel header background
    'panel_header_fg': '#333333',       # Panel header text
    
    # Menu colors
    'menu_bg': '#ffffff',               # Menu background
    'menu_fg': '#000000',               # Menu text
    'menu_hover_bg': '#e0e0e0',         # Menu item hover
    'menu_hover_fg': '#000000',         # Menu item hover text
    'menu_separator': '#e0e0e0',        # Menu separator
    'menu_disabled_fg': '#cccccc',      # Disabled menu item
    
    # Toolbar colors
    'toolbar_bg': '#f0f0f0',            # Toolbar background
    'toolbar_border': '#e0e0e0',        # Toolbar border
    'toolbar_button_hover': '#e0e0e0',  # Toolbar button hover
    
    # Canvas colors
    'canvas_bg': '#ffffff',             # Canvas background
    'canvas_grid': '#e0e0e0',           # Canvas grid lines
    'canvas_selection': '#0078d4',      # Canvas selection
    'canvas_crosshair': '#000000',      # Canvas crosshair
    
    # Color picker specific
    'color_preview_border': '#cccccc',  # Color preview border
    'color_swatch_border': '#999999',   # Color swatch border
    'color_swatch_hover': '#0078d4',    # Color swatch hover
    'palette_bg': '#f8f8f8',            # Palette background
    'palette_border': '#e0e0e0',        # Palette border
    
    # History and favorites
    'history_bg': '#f8f8f8',            # History panel background
    'history_item_hover': '#f0f0f0',    # History item hover
    'favorite_star': '#ffb900',         # Favorite star color
    
    # Analysis panel
    'analysis_bg': '#f8f8f8',           # Analysis panel background
    'chart_bg': '#ffffff',              # Chart background
    'chart_grid': '#e0e0e0',            # Chart grid lines
    'chart_text': '#333333',            # Chart text
    
    # Scrollbar colors
    'scrollbar_bg': '#f0f0f0',          # Scrollbar background
    'scrollbar_thumb': '#cccccc',       # Scrollbar thumb
    'scrollbar_thumb_hover': '#b0b0b0', # Scrollbar thumb hover
    'scrollbar_thumb_pressed': '#999999', # Scrollbar thumb pressed
    
    # Border colors
    'border': '#cccccc',                # Default border
    'border_light': '#e0e0e0',          # Light border
    'border_dark': '#999999',           # Dark border
    'border_focus': '#0078d4',          # Focused element border
    
    # Shadow colors
    'shadow': 'rgba(0, 0, 0, 0.2)',     # Drop shadow
    'shadow_light': 'rgba(0, 0, 0, 0.1)', # Light shadow
    'shadow_heavy': 'rgba(0, 0, 0, 0.3)', # Heavy shadow
    
    # Overlay colors
    'overlay': 'rgba(0, 0, 0, 0.3)',    # Modal overlay
    'tooltip_bg': '#333333',            # Tooltip background
    'tooltip_fg': '#ffffff',            # Tooltip text
    'tooltip_border': '#666666',        # Tooltip border
    
    # Progress and loading
    'progress_bg': '#e0e0e0',           # Progress bar background
    'progress_fill': '#0078d4',         # Progress bar fill
    'loading_spinner': '#0078d4',       # Loading spinner color
    
    # Accessibility colors (high contrast variants)
    'high_contrast_bg': '#ffffff',      # High contrast background
    'high_contrast_fg': '#000000',      # High contrast foreground
    'high_contrast_accent': '#0000ff',  # High contrast accent
    'high_contrast_border': '#000000',  # High contrast border
    
    # Theme metadata
    '_metadata': {
        'name': 'Light',
        'description': 'Clean light theme with good contrast',
        'version': '1.0',
        'author': 'Enhanced Color Picker',
        'accessibility_compliant': True,
        'supports_high_contrast': True
    }
}

# Color scheme variations for different contexts
LIGHT_THEME_VARIANTS = {
    'high_contrast': {
        **LIGHT_THEME,
        'bg': '#ffffff',
        'fg': '#000000',
        'accent': '#0000ff',
        'border': '#000000',
        'button_bg': '#ffffff',
        'button_fg': '#000000',
        'entry_bg': '#ffffff',
        'entry_fg': '#000000',
        'entry_border': '#000000',
        'panel_border': '#000000',
        'color_swatch_border': '#000000',
    },
    
    'blue_accent': {
        **LIGHT_THEME,
        'accent': '#2196f3',
        'accent_hover': '#1976d2',
        'accent_pressed': '#1565c0',
        'button_primary_bg': '#2196f3',
        'button_primary_hover_bg': '#1976d2',
        'button_primary_pressed_bg': '#1565c0',
    },
    
    'green_accent': {
        **LIGHT_THEME,
        'accent': '#4caf50',
        'accent_hover': '#388e3c',
        'accent_pressed': '#2e7d32',
        'button_primary_bg': '#4caf50',
        'button_primary_hover_bg': '#388e3c',
        'button_primary_pressed_bg': '#2e7d32',
    },
    
    'purple_accent': {
        **LIGHT_THEME,
        'accent': '#9c27b0',
        'accent_hover': '#7b1fa2',
        'accent_pressed': '#6a1b9a',
        'button_primary_bg': '#9c27b0',
        'button_primary_hover_bg': '#7b1fa2',
        'button_primary_pressed_bg': '#6a1b9a',
    },
    
    'warm': {
        **LIGHT_THEME,
        'bg': '#fefefe',
        'bg_secondary': '#f9f9f9',
        'bg_tertiary': '#f0f0f0',
        'panel_bg': '#fcfcfc',
        'entry_bg': '#fefefe',
        'text_bg': '#fefefe',
        'canvas_bg': '#fefefe',
        'chart_bg': '#fefefe',
    },
    
    'cool': {
        **LIGHT_THEME,
        'bg': '#fafbfc',
        'bg_secondary': '#f1f3f4',
        'bg_tertiary': '#e8eaed',
        'panel_bg': '#f8f9fa',
        'entry_bg': '#fafbfc',
        'text_bg': '#fafbfc',
        'canvas_bg': '#fafbfc',
        'chart_bg': '#fafbfc',
    }
}

def get_light_theme_variant(variant_name: str = 'default') -> dict:
    """Get a specific variant of the light theme."""
    if variant_name == 'default' or variant_name not in LIGHT_THEME_VARIANTS:
        return LIGHT_THEME.copy()
    return LIGHT_THEME_VARIANTS[variant_name].copy()

def create_custom_light_theme(accent_color: str, name: str = 'custom_light') -> dict:
    """Create a custom light theme with specified accent color."""
    custom_theme = LIGHT_THEME.copy()
    
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
        'description': f'Custom light theme with {accent_color} accent',
        'custom': True
    }
    
    return custom_theme

def get_complementary_theme_colors(base_color: str) -> dict:
    """Generate complementary colors for theme creation."""
    try:
        # Parse hex color
        r = int(base_color[1:3], 16)
        g = int(base_color[3:5], 16)
        b = int(base_color[5:7], 16)
        
        # Calculate complementary and related colors
        comp_r = 255 - r
        comp_g = 255 - g
        comp_b = 255 - b
        
        # Generate color variations
        return {
            'base': base_color,
            'complementary': f'#{comp_r:02x}{comp_g:02x}{comp_b:02x}',
            'lighter': f'#{min(255, r + 40):02x}{min(255, g + 40):02x}{min(255, b + 40):02x}',
            'darker': f'#{max(0, r - 40):02x}{max(0, g - 40):02x}{max(0, b - 40):02x}',
            'muted': f'#{r // 2 + 64:02x}{g // 2 + 64:02x}{b // 2 + 64:02x}'
        }
    except Exception:
        # Fallback colors
        return {
            'base': '#0078d4',
            'complementary': '#d47800',
            'lighter': '#4fc3f7',
            'darker': '#005a9e',
            'muted': '#87ceeb'
        }