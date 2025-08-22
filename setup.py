"""
Enhanced Color Picker Setup Script

This script provides packaging and distribution setup for Enhanced Color Picker.
It can be used to create distributable packages for different platforms.
"""

from setuptools import setup, find_packages
import os
from pathlib import Path

# Read version from version file
version_file = Path(__file__).parent / "enhanced_color_picker" / "__version__.py"
version_info = {}
if version_file.exists():
    with open(version_file) as f:
        exec(f.read(), version_info)
    version = version_info.get('__version__', '1.0.0')
else:
    version = '1.0.0'

# Read long description from README
readme_file = Path(__file__).parent / "README.md"
long_description = ""
if readme_file.exists():
    with open(readme_file, 'r', encoding='utf-8') as f:
        long_description = f.read()

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    with open(requirements_file, 'r') as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="enhanced-color-picker",
    version=version,
    author="Enhanced Color Picker Team",
    author_email="contact@enhanced-color-picker.com",
    description="Professional color selection tool for designers and developers",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/enhanced-color-picker/enhanced-color-picker",
    project_urls={
        "Bug Reports": "https://github.com/enhanced-color-picker/enhanced-color-picker/issues",
        "Source": "https://github.com/enhanced-color-picker/enhanced-color-picker",
        "Documentation": "https://enhanced-color-picker.readthedocs.io/",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Multimedia :: Graphics",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Environment :: X11 Applications :: GTK",
        "Environment :: Win32 (MS Windows)",
        "Environment :: MacOS X",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.8",
            "mypy>=0.800",
            "pre-commit>=2.0",
        ],
        "docs": [
            "sphinx>=4.0",
            "sphinx-rtd-theme>=1.0",
            "myst-parser>=0.15",
        ],
        "build": [
            "pyinstaller>=4.0",
            "cx_Freeze>=6.0",
            "py2app>=0.24",  # macOS
            "py2exe>=0.10",  # Windows
        ],
    },
    entry_points={
        "console_scripts": [
            "enhanced-color-picker=enhanced_color_picker.main:main",
            "color-picker=enhanced_color_picker.main:main",
        ],
        "gui_scripts": [
            "enhanced-color-picker-gui=enhanced_color_picker.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "enhanced_color_picker": [
            "assets/icons/*",
            "assets/themes/*",
            "assets/samples/*",
            "localization/translations/*",
            "ui/themes/*",
        ],
    },
    data_files=[
        ("share/applications", ["desktop/enhanced-color-picker.desktop"]),
        ("share/icons/hicolor/48x48/apps", ["enhanced_color_picker/assets/icons/app.png"]),
        ("share/pixmaps", ["enhanced_color_picker/assets/icons/app.png"]),
        ("share/doc/enhanced-color-picker", ["README.md", "LICENSE"]),
    ],
    zip_safe=False,
    keywords="color picker, color selection, design tools, graphics, image processing",
    platforms=["Windows", "macOS", "Linux"],
)