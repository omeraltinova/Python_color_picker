"""Version information for Enhanced Color Picker."""

__version__ = "1.0.0"
__version_info__ = (1, 0, 0)

# Build information
__build__ = "stable"
__build_date__ = "2024-01-01"

# Application metadata
__app_name__ = "Enhanced Color Picker"
__app_description__ = "Professional color selection tool for designers and developers"
__author__ = "Enhanced Color Picker Team"
__author_email__ = "contact@enhanced-color-picker.com"
__url__ = "https://github.com/enhanced-color-picker/enhanced-color-picker"
__license__ = "MIT"

# Minimum requirements
__python_requires__ = ">=3.8"
__platform__ = "cross-platform"

def get_version():
    """Get the current version string."""
    return __version__

def get_version_info():
    """Get version information as a tuple."""
    return __version_info__

def get_full_version():
    """Get full version string with build information."""
    if __build__ == "stable":
        return __version__
    else:
        return f"{__version__}-{__build__}"

def get_app_info():
    """Get complete application information."""
    return {
        "name": __app_name__,
        "version": __version__,
        "description": __app_description__,
        "author": __author__,
        "author_email": __author_email__,
        "url": __url__,
        "license": __license__,
        "python_requires": __python_requires__,
        "platform": __platform__,
        "build": __build__,
        "build_date": __build_date__
    }