# Enhanced Color Picker - User Manual

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Main Interface](#main-interface)
4. [Loading Images](#loading-images)
5. [Color Selection](#color-selection)
6. [Zoom and Navigation](#zoom-and-navigation)
7. [Color Formats and Copying](#color-formats-and-copying)
8. [Palette Management](#palette-management)
9. [Color Analysis](#color-analysis)
10. [Accessibility Features](#accessibility-features)
11. [Settings and Customization](#settings-and-customization)
12. [Export and Sharing](#export-and-sharing)
13. [Keyboard Shortcuts](#keyboard-shortcuts)
14. [Advanced Features](#advanced-features)

## Introduction

Enhanced Color Picker is a professional-grade color selection tool designed for designers, developers, and digital artists. It provides precise color picking from images with advanced features like palette management, color analysis, accessibility checking, and multi-format export capabilities.

### Key Features

- **Multi-format Image Support**: PNG, JPEG, GIF, BMP, TIFF, WebP, SVG
- **Precise Color Selection**: Pixel-perfect color picking with zoom compensation
- **Multiple Color Formats**: RGB, HEX, HSL, HSV, CMYK support
- **Palette Management**: Create, save, and organize color palettes
- **Color Analysis**: Dominant colors, histograms, and statistics
- **Accessibility Tools**: WCAG compliance checking and color blindness simulation
- **Advanced Zoom**: Up to 1000% zoom with pixel grid display
- **Export Options**: Multiple formats including CSS, programming languages, Adobe formats
- **Internationalization**: Turkish and English language support
- **Theme Support**: Dark, light, and auto themes

## Getting Started

### System Requirements

- Python 3.8 or higher
- 4GB RAM minimum (8GB recommended for large images)
- 100MB free disk space
- Display resolution: 1024x768 minimum

### Installation

1. Download the Enhanced Color Picker package
2. Extract to your desired location
3. Run the installation script or launch main.py
4. The application will create necessary configuration files on first run

### First Launch

When you first launch Enhanced Color Picker:

1. The application opens with the default dark theme
2. All panels are visible in their default layout
3. No image is loaded initially
4. Settings are configured with sensible defaults

## Main Interface

The Enhanced Color Picker interface consists of several main areas:

### Menu Bar
- **File**: Load images, save palettes, export options
- **Edit**: Copy colors, preferences, undo/redo
- **View**: Zoom controls, panel visibility, themes
- **Tools**: Color analysis, accessibility tools, batch operations
- **Help**: Documentation, about, keyboard shortcuts

### Toolbar
Quick access buttons for common operations:
- Load Image
- Zoom In/Out
- Fit to Screen
- Toggle Pixel Grid
- Copy Color
- Save Palette

### Main Canvas Area
The central area where loaded images are displayed with:
- Zoom and pan capabilities
- Pixel grid overlay (at high zoom levels)
- Mini-map for navigation
- Crosshair cursor for precise selection

### Side Panels

#### Color Panel
Displays selected color information:
- Color preview swatch
- RGB, HEX, HSL, HSV, CMYK values
- Copy buttons for each format
- WCAG compliance information

#### Palette Panel
Manage color palettes:
- Current palette colors
- Add/remove colors
- Save/load palettes
- Palette organization tools

#### History Panel
Track recently selected colors:
- Chronological color history
- Favorites management
- Search and filter options
- Quick color reselection

#### Analysis Panel
Color analysis tools:
- Dominant colors extraction
- Color histogram
- Color distribution statistics
- Average color calculation

## Loading Images

### Supported Formats

Enhanced Color Picker supports these image formats:
- **PNG**: Full transparency support
- **JPEG/JPG**: Standard and progressive
- **GIF**: Static and animated (first frame)
- **BMP**: Windows bitmap
- **TIFF**: Tagged Image File Format
- **WebP**: Google's WebP format
- **SVG**: Scalable Vector Graphics (rasterized)

### Loading Methods

#### Method 1: File Menu
1. Click **File** → **Load Image**
2. Browse and select your image file
3. Click **Open**

#### Method 2: Drag and Drop
1. Drag an image file from your file manager
2. Drop it onto the canvas area
3. The image loads automatically

#### Method 3: Keyboard Shortcut
1. Press **Ctrl+O** (Cmd+O on Mac)
2. Select your image file
3. Press Enter

### Loading Progress

For large images:
- A progress bar appears during loading
- Loading can be cancelled if needed
- Memory usage is monitored and displayed

### Image Information

Once loaded, you can view image details:
- File path and name
- Dimensions (width × height)
- File size
- Color mode (RGB, RGBA, etc.)
- Format information

## Color Selection

### Basic Color Picking

1. **Load an image** using any of the methods above
2. **Move your mouse** over the image - coordinates are shown in real-time
3. **Click** on any pixel to select its color
4. The color information appears in the Color Panel

### Precision Features

#### Zoom for Accuracy
- Use mouse wheel to zoom in/out
- Zoom centers on mouse cursor position
- Maximum zoom: 1000%
- Pixel grid appears at high zoom levels

#### Coordinate Display
- Real-time X,Y coordinates shown
- Coordinates are based on original image dimensions
- Helpful for precise pixel targeting

#### Color Preview
- Live color preview as you move the mouse
- Shows exact color before clicking
- Updates in real-time

### Advanced Selection

#### Multi-Point Selection
- Hold **Ctrl** while clicking to select multiple colors
- Each selection is added to history
- Useful for comparing colors

#### Area Sampling
- Hold **Shift** and drag to select an area
- Calculates average color of the selected region
- Useful for getting representative colors

## Zoom and Navigation

### Zoom Controls

#### Mouse Wheel Zoom
- **Scroll up**: Zoom in
- **Scroll down**: Zoom out
- Zoom centers on cursor position
- Smooth zoom transitions

#### Keyboard Zoom
- **Ctrl + Plus**: Zoom in
- **Ctrl + Minus**: Zoom out
- **Ctrl + 0**: Fit to screen
- **Ctrl + 1**: 100% zoom (actual size)

#### Toolbar Zoom
- Click zoom in/out buttons
- Use zoom slider for precise control
- Zoom percentage display

### Navigation

#### Panning
- **Right-click and drag**: Pan the image
- **Arrow keys**: Move in small increments
- **Shift + Arrow keys**: Move in larger increments

#### Mini-Map
- Small overview of entire image
- Shows current view area
- Click to jump to specific areas
- Toggle on/off in View menu

#### Fit Options
- **Fit to Screen**: Scales image to fit canvas
- **Fit Width**: Fits image width to canvas
- **Fit Height**: Fits image height to canvas
- **Actual Size**: Shows image at 100% scale

### Pixel Grid

At zoom levels above 800%:
- Pixel grid automatically appears
- Shows individual pixel boundaries
- Helps with precise pixel selection
- Can be toggled on/off manually

## Color Formats and Copying

### Supported Formats

Enhanced Color Picker displays colors in multiple formats:

#### RGB (Red, Green, Blue)
- Format: `rgb(255, 128, 0)`
- Range: 0-255 for each channel
- Most common format for digital displays

#### HEX (Hexadecimal)
- Format: `#FF8000`
- 6-digit hexadecimal representation
- Standard format for web development

#### HSL (Hue, Saturation, Lightness)
- Format: `hsl(30, 100%, 50%)`
- Intuitive color representation
- Useful for color adjustments

#### HSV (Hue, Saturation, Value)
- Format: `hsv(30, 100%, 100%)`
- Alternative to HSL
- Common in design software

#### CMYK (Cyan, Magenta, Yellow, Key/Black)
- Format: `cmyk(0%, 50%, 100%, 0%)`
- Print-oriented color space
- Used in professional printing

### Copying Colors

#### Single Format Copy
1. Select a color by clicking on the image
2. In the Color Panel, click the copy button next to desired format
3. Color is copied to clipboard in that format

#### Multiple Format Copy
1. Right-click on a color in the Color Panel
2. Select "Copy All Formats"
3. All formats are copied as formatted text

#### Programming Language Formats
Special copy options for developers:
- **CSS**: `color: #FF8000;`
- **Python**: `(255, 128, 0)`
- **JavaScript**: `"#FF8000"`
- **Java**: `new Color(255, 128, 0)`
- **C#**: `Color.FromArgb(255, 128, 0)`

### Copy Confirmation

When colors are copied:
- Brief notification appears
- Clipboard icon animation
- Status bar confirmation message

## Palette Management

### Creating Palettes

#### New Palette
1. Click **File** → **New Palette**
2. Enter a name for your palette
3. Start adding colors by selecting them from images

#### Adding Colors
- **Method 1**: Select color from image, click "Add to Palette"
- **Method 2**: Drag color from Color Panel to Palette Panel
- **Method 3**: Right-click color and select "Add to Palette"

### Organizing Palettes

#### Color Arrangement
- **Drag and drop** colors to reorder
- **Right-click** colors for context menu options
- **Double-click** to edit color properties

#### Color Management
- **Remove colors**: Right-click → Delete
- **Edit colors**: Double-click to open color editor
- **Duplicate colors**: Right-click → Duplicate

### Saving and Loading

#### Save Palette
1. Click **File** → **Save Palette**
2. Choose location and filename
3. Palette saved in JSON format

#### Load Palette
1. Click **File** → **Load Palette**
2. Browse to palette file
3. Palette loads into Palette Panel

#### Auto-Save
- Palettes can auto-save changes
- Configure in Settings → General
- Prevents data loss

### Palette Export

Export palettes in various formats:
- **JSON**: Native format with full metadata
- **CSS**: CSS custom properties
- **SCSS**: Sass variables
- **ASE**: Adobe Swatch Exchange
- **ACO**: Adobe Color format
- **GPL**: GIMP Palette format

## Color Analysis

### Dominant Colors

Extract the most prominent colors from images:

1. Load an image
2. Click **Tools** → **Analyze Colors**
3. Select number of colors to extract (5-20)
4. View results in Analysis Panel

#### Features
- Automatic color clustering
- Adjustable color count
- Percentage representation
- Add dominant colors to palette

### Color Histogram

Visualize color distribution:

#### RGB Histogram
- Shows distribution of Red, Green, Blue channels
- Helps understand image color balance
- Useful for photo analysis

#### HSV Histogram
- Hue, Saturation, Value distribution
- Better for artistic color analysis
- Shows color harmony patterns

### Color Statistics

#### Average Color
- Calculates mean color of entire image
- Useful for determining overall tone
- Can be added to palette

#### Color Distribution
- Shows percentage of different color ranges
- Identifies dominant color families
- Helps with color scheme planning

### Analysis Export

Export analysis results:
- **Report**: Detailed analysis report
- **Data**: Raw statistical data
- **Images**: Histogram visualizations

## Accessibility Features

### WCAG Compliance Checking

#### Contrast Ratio Calculation
1. Select a foreground color
2. Select a background color (or use white/black)
3. View contrast ratio in Color Panel
4. See WCAG AA/AAA compliance status

#### Compliance Levels
- **WCAG AA**: Minimum accessibility standard
- **WCAG AAA**: Enhanced accessibility standard
- **Pass/Fail indicators**: Clear visual feedback

### Color Blindness Simulation

#### Supported Types
- **Protanopia**: Red-blind
- **Deuteranopia**: Green-blind  
- **Tritanopia**: Blue-blind
- **Protanomaly**: Red-weak
- **Deuteranomaly**: Green-weak
- **Tritanomaly**: Blue-weak

#### Using Simulation
1. Select a color or load an image
2. Click **Tools** → **Color Blindness Simulation**
3. Choose simulation type
4. View how colors appear to color-blind users

### Accessibility Recommendations

The application provides:
- **Safe color suggestions**: Colors that work for color-blind users
- **Alternative palettes**: Color-blind friendly alternatives
- **Contrast improvements**: Suggestions for better contrast

## Settings and Customization

### General Settings

#### Theme Selection
- **Dark Theme**: Default dark interface
- **Light Theme**: Light interface option
- **Auto Theme**: Follows system theme

#### Language
- **English**: Full English interface
- **Turkish**: Complete Turkish localization
- **Auto-detect**: Uses system language

### Display Settings

#### Zoom Behavior
- **Zoom sensitivity**: Adjust mouse wheel sensitivity
- **Zoom center**: Cursor or center-based zooming
- **Smooth zoom**: Enable/disable zoom animations

#### Grid Settings
- **Pixel grid threshold**: Zoom level for grid display
- **Grid color**: Customize grid line color
- **Grid opacity**: Adjust grid transparency

### Performance Settings

#### Memory Management
- **Cache size**: Maximum memory for image cache
- **Auto-cleanup**: Automatic memory cleanup
- **Large image handling**: Optimization for big files

#### Background Processing
- **Thread count**: Number of background threads
- **Priority**: Processing priority level
- **Progress notifications**: Show/hide progress dialogs

### Keyboard Shortcuts

Customize keyboard shortcuts:
1. Go to **Edit** → **Preferences** → **Shortcuts**
2. Click on action to modify
3. Press new key combination
4. Click **Save**

## Export and Sharing

### Single Color Export

#### Quick Copy
- Click copy button next to any color format
- Color copied to clipboard immediately
- Paste into any application

#### Format Options
Choose from multiple export formats:
- **Web formats**: HEX, RGB, HSL for CSS
- **Programming**: Language-specific formats
- **Design tools**: Adobe, GIMP formats

### Palette Export

#### Export Formats
- **JSON**: Complete palette with metadata
- **CSS**: CSS custom properties file
- **SCSS/Sass**: Sass variable file
- **Adobe ASE**: For Photoshop, Illustrator
- **Adobe ACO**: Photoshop color swatches
- **GIMP GPL**: GIMP palette format

#### Export Process
1. Select palette to export
2. Click **File** → **Export Palette**
3. Choose format and location
4. Configure export options
5. Click **Export**

### Batch Operations

#### Bulk Color Copy
1. Select multiple colors (Ctrl+click)
2. Right-click → **Copy All Selected**
3. All colors copied in chosen format

#### Batch Export
1. Select multiple palettes
2. Choose **Tools** → **Batch Export**
3. Select export format
4. Choose destination folder
5. Click **Export All**

## Keyboard Shortcuts

### File Operations
- **Ctrl+O**: Load image
- **Ctrl+S**: Save palette
- **Ctrl+Shift+S**: Save palette as
- **Ctrl+N**: New palette
- **Ctrl+Q**: Quit application

### View Controls
- **Ctrl+Plus**: Zoom in
- **Ctrl+Minus**: Zoom out
- **Ctrl+0**: Fit to screen
- **Ctrl+1**: Actual size (100%)
- **F11**: Toggle fullscreen

### Color Operations
- **Ctrl+C**: Copy selected color
- **Ctrl+Shift+C**: Copy all formats
- **Ctrl+A**: Add color to palette
- **Delete**: Remove selected color

### Navigation
- **Arrow keys**: Pan image
- **Shift+Arrow**: Pan faster
- **Space+Drag**: Pan with mouse
- **Ctrl+Home**: Reset view

### Panels
- **F1**: Toggle Color Panel
- **F2**: Toggle Palette Panel
- **F3**: Toggle History Panel
- **F4**: Toggle Analysis Panel

### Tools
- **Ctrl+T**: Color analysis
- **Ctrl+B**: Color blindness simulation
- **Ctrl+H**: Show/hide pixel grid
- **Ctrl+M**: Toggle mini-map

## Advanced Features

### Color Harmony Generation

Generate harmonious color schemes:

#### Harmony Types
- **Complementary**: Opposite colors on color wheel
- **Analogous**: Adjacent colors on color wheel
- **Triadic**: Three evenly spaced colors
- **Split-complementary**: Base color plus two adjacent to complement
- **Tetradic**: Four colors forming rectangle on color wheel

#### Using Harmony Generator
1. Select a base color
2. Click **Tools** → **Generate Harmony**
3. Choose harmony type
4. Generated colors appear in Analysis Panel
5. Add desired colors to palette

### Batch Processing

#### Multiple Image Analysis
1. Click **Tools** → **Batch Analysis**
2. Select multiple image files
3. Choose analysis type (dominant colors, average, etc.)
4. Results exported to spreadsheet or report

#### Palette Generation from Multiple Images
1. Load multiple images
2. Extract dominant colors from each
3. Combine into master palette
4. Remove duplicates and similar colors

### Advanced Color Spaces

#### LAB Color Space
- Perceptually uniform color space
- Better for color difference calculations
- Available in advanced color panel

#### XYZ Color Space
- CIE standard color space
- Used for color science calculations
- Basis for other color space conversions

### Plugin System

Enhanced Color Picker supports plugins for extended functionality:

#### Available Plugins
- **Color Name Database**: Get common names for colors
- **Pantone Matching**: Find closest Pantone colors
- **Material Design**: Material Design color palette
- **Brand Colors**: Popular brand color collections

#### Installing Plugins
1. Download plugin file
2. Place in plugins directory
3. Restart application
4. Enable in Settings → Plugins

### API Integration

For developers, Enhanced Color Picker provides:

#### Command Line Interface
```bash
# Extract dominant colors
color-picker --extract-colors image.jpg --count 5

# Convert color formats
color-picker --convert "#FF8000" --to rgb

# Generate palette
color-picker --generate-palette image.jpg --output palette.json
```

#### Python API
```python
from enhanced_color_picker import ColorPicker

picker = ColorPicker()
colors = picker.extract_dominant_colors("image.jpg", count=5)
palette = picker.create_palette("My Palette", colors)
picker.export_palette(palette, "palette.css", format="css")
```

## Troubleshooting

For common issues and solutions, see the [Troubleshooting Guide](troubleshooting.md).

## Support

If you need additional help:
- Check the [FAQ](faq.md)
- Review [Troubleshooting Guide](troubleshooting.md)
- Visit the project documentation
- Contact support team

---

*Enhanced Color Picker User Manual - Version 1.0*