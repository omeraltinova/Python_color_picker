#!/usr/bin/env python3
"""
Enhanced Color Picker Build Script

This script creates distributable packages for different platforms using
various packaging tools like PyInstaller, cx_Freeze, py2app, etc.
"""

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path
import argparse
import json
from typing import List, Dict, Optional


class PackageBuilder:
    """Handles building distributable packages."""
    
    def __init__(self):
        self.system = platform.system().lower()
        self.project_root = Path(__file__).parent
        self.build_dir = self.project_root / "build"
        self.dist_dir = self.project_root / "dist"
        self.spec_file = self.project_root / "enhanced_color_picker.spec"
        
        # Application metadata
        self.app_name = "Enhanced Color Picker"
        self.app_version = self._get_version()
        self.app_description = "Professional color selection tool"
        self.app_author = "Enhanced Color Picker Team"
        
    def _get_version(self) -> str:
        """Get application version."""
        try:
            version_file = self.project_root / "enhanced_color_picker" / "__version__.py"
            version_info = {}
            with open(version_file) as f:
                exec(f.read(), version_info)
            return version_info.get('__version__', '1.0.0')
        except Exception:
            return '1.0.0'
    
    def clean_build(self):
        """Clean previous build artifacts."""
        print("🧹 Cleaning previous build artifacts...")
        
        dirs_to_clean = [self.build_dir, self.dist_dir]
        files_to_clean = [self.spec_file]
        
        for directory in dirs_to_clean:
            if directory.exists():
                shutil.rmtree(directory)
                print(f"   Removed: {directory}")
        
        for file_path in files_to_clean:
            if file_path.exists():
                file_path.unlink()
                print(f"   Removed: {file_path}")
    
    def build_pyinstaller(self, onefile: bool = False, console: bool = False) -> bool:
        """Build using PyInstaller."""
        print("📦 Building with PyInstaller...")
        
        try:
            # Check if PyInstaller is available
            subprocess.run(["pyinstaller", "--version"], 
                         capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ PyInstaller not found. Install with: pip install pyinstaller")
            return False
        
        # Build command
        cmd = [
            "pyinstaller",
            "--name", "enhanced-color-picker",
            "--distpath", str(self.dist_dir),
            "--workpath", str(self.build_dir),
        ]
        
        if onefile:
            cmd.append("--onefile")
        else:
            cmd.append("--onedir")
        
        if not console:
            cmd.append("--windowed")
        
        # Add icon
        icon_path = self.project_root / "enhanced_color_picker" / "assets" / "icons"
        if self.system == "windows":
            icon_file = icon_path / "app.ico"
            if icon_file.exists():
                cmd.extend(["--icon", str(icon_file)])
        elif self.system == "darwin":
            icon_file = icon_path / "app.icns"
            if icon_file.exists():
                cmd.extend(["--icon", str(icon_file)])
        
        # Add data files
        data_dirs = [
            ("enhanced_color_picker/assets", "assets"),
            ("enhanced_color_picker/localization/translations", "localization/translations"),
            ("enhanced_color_picker/ui/themes", "ui/themes"),
            ("docs", "docs")
        ]
        
        for src, dst in data_dirs:
            src_path = self.project_root / src
            if src_path.exists():
                cmd.extend(["--add-data", f"{src_path}{os.pathsep}{dst}"])
        
        # Hidden imports
        hidden_imports = [
            "PIL._tkinter_finder",
            "tkinter",
            "tkinter.ttk",
            "tkinter.filedialog",
            "tkinter.messagebox",
            "tkinter.colorchooser",
            "numpy",
            "json",
            "pathlib"
        ]
        
        for module in hidden_imports:
            cmd.extend(["--hidden-import", module])
        
        # Main script
        cmd.append(str(self.project_root / "main.py"))
        
        try:
            print(f"   Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, cwd=self.project_root)
            
            if result.returncode == 0:
                print("✅ PyInstaller build completed successfully")
                return True
            else:
                print("❌ PyInstaller build failed")
                return False
                
        except Exception as e:
            print(f"❌ PyInstaller build error: {e}")
            return False
    
    def build_cx_freeze(self) -> bool:
        """Build using cx_Freeze."""
        print("📦 Building with cx_Freeze...")
        
        try:
            import cx_Freeze
        except ImportError:
            print("❌ cx_Freeze not found. Install with: pip install cx_Freeze")
            return False
        
        # Create setup script for cx_Freeze
        setup_script = f'''
import sys
from cx_Freeze import setup, Executable
from pathlib import Path

# Dependencies
build_exe_options = {{
    "packages": ["tkinter", "PIL", "numpy", "json", "pathlib"],
    "excludes": ["test", "unittest", "email", "html", "http", "urllib", "xml"],
    "include_files": [
        ("enhanced_color_picker/assets", "assets"),
        ("enhanced_color_picker/localization/translations", "localization/translations"),
        ("enhanced_color_picker/ui/themes", "ui/themes"),
        ("docs", "docs")
    ],
    "optimize": 2
}}

# Executable
base = None
if sys.platform == "win32":
    base = "Win32GUI"

executable = Executable(
    "main.py",
    base=base,
    target_name="enhanced-color-picker{''.exe' if sys.platform == 'win32' else ''}",
    icon="enhanced_color_picker/assets/icons/app.{'ico' if sys.platform == 'win32' else 'png'}"
)

setup(
    name="{self.app_name}",
    version="{self.app_version}",
    description="{self.app_description}",
    options={{"build_exe": build_exe_options}},
    executables=[executable]
)
'''
        
        setup_file = self.project_root / "setup_cx_freeze.py"
        with open(setup_file, 'w') as f:
            f.write(setup_script)
        
        try:
            cmd = [sys.executable, "setup_cx_freeze.py", "build"]
            result = subprocess.run(cmd, cwd=self.project_root)
            
            # Clean up
            setup_file.unlink()
            
            if result.returncode == 0:
                print("✅ cx_Freeze build completed successfully")
                return True
            else:
                print("❌ cx_Freeze build failed")
                return False
                
        except Exception as e:
            print(f"❌ cx_Freeze build error: {e}")
            if setup_file.exists():
                setup_file.unlink()
            return False
    
    def build_py2app(self) -> bool:
        """Build macOS app bundle using py2app."""
        if self.system != "darwin":
            print("⚠️ py2app is only available on macOS")
            return False
        
        print("📦 Building macOS app with py2app...")
        
        try:
            import py2app
        except ImportError:
            print("❌ py2app not found. Install with: pip install py2app")
            return False
        
        # Create setup script for py2app
        setup_script = f'''
from setuptools import setup
import py2app

APP = ['main.py']
DATA_FILES = [
    ('assets', ['enhanced_color_picker/assets']),
    ('localization/translations', ['enhanced_color_picker/localization/translations']),
    ('ui/themes', ['enhanced_color_picker/ui/themes']),
    ('docs', ['docs'])
]

OPTIONS = {{
    'argv_emulation': True,
    'iconfile': 'enhanced_color_picker/assets/icons/app.icns',
    'plist': {{
        'CFBundleName': "{self.app_name}",
        'CFBundleDisplayName': "{self.app_name}",
        'CFBundleGetInfoString': "{self.app_description}",
        'CFBundleVersion': "{self.app_version}",
        'CFBundleShortVersionString': "{self.app_version}",
        'NSHumanReadableCopyright': "© 2024 {self.app_author}"
    }}
}}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={{'py2app': OPTIONS}},
    setup_requires=['py2app'],
)
'''
        
        setup_file = self.project_root / "setup_py2app.py"
        with open(setup_file, 'w') as f:
            f.write(setup_script)
        
        try:
            cmd = [sys.executable, "setup_py2app.py", "py2app"]
            result = subprocess.run(cmd, cwd=self.project_root)
            
            # Clean up
            setup_file.unlink()
            
            if result.returncode == 0:
                print("✅ py2app build completed successfully")
                return True
            else:
                print("❌ py2app build failed")
                return False
                
        except Exception as e:
            print(f"❌ py2app build error: {e}")
            if setup_file.exists():
                setup_file.unlink()
            return False
    
    def create_linux_package(self, package_type: str = "deb") -> bool:
        """Create Linux package (deb, rpm, etc.)."""
        if self.system != "linux":
            print("⚠️ Linux packaging is only available on Linux")
            return False
        
        print(f"📦 Creating Linux {package_type.upper()} package...")
        
        if package_type == "deb":
            return self._create_deb_package()
        elif package_type == "rpm":
            return self._create_rpm_package()
        elif package_type == "appimage":
            return self._create_appimage()
        else:
            print(f"❌ Unsupported package type: {package_type}")
            return False
    
    def _create_deb_package(self) -> bool:
        """Create Debian package."""
        try:
            # Check for required tools
            subprocess.run(["dpkg-deb", "--version"], 
                         capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ dpkg-deb not found. Install with: sudo apt install dpkg-dev")
            return False
        
        # Create package structure
        package_name = f"enhanced-color-picker_{self.app_version}_all"
        package_dir = self.dist_dir / package_name
        
        # Create directories
        dirs = [
            package_dir / "DEBIAN",
            package_dir / "usr" / "local" / "bin" / "enhanced-color-picker",
            package_dir / "usr" / "share" / "applications",
            package_dir / "usr" / "share" / "icons" / "hicolor" / "48x48" / "apps",
            package_dir / "usr" / "share" / "doc" / "enhanced-color-picker"
        ]
        
        for directory in dirs:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Copy application files
        app_dest = package_dir / "usr" / "local" / "bin" / "enhanced-color-picker"
        shutil.copytree(self.project_root / "enhanced_color_picker", 
                       app_dest / "enhanced_color_picker")
        shutil.copy2(self.project_root / "main.py", app_dest)
        shutil.copy2(self.project_root / "requirements.txt", app_dest)
        
        # Copy documentation
        doc_dest = package_dir / "usr" / "share" / "doc" / "enhanced-color-picker"
        if (self.project_root / "docs").exists():
            shutil.copytree(self.project_root / "docs", doc_dest / "docs")
        shutil.copy2(self.project_root / "README.md", doc_dest)
        
        # Copy desktop file
        shutil.copy2(self.project_root / "desktop" / "enhanced-color-picker.desktop",
                    package_dir / "usr" / "share" / "applications")
        
        # Copy icon
        icon_src = self.project_root / "enhanced_color_picker" / "assets" / "icons" / "app.png"
        if icon_src.exists():
            shutil.copy2(icon_src, 
                        package_dir / "usr" / "share" / "icons" / "hicolor" / "48x48" / "apps" / "enhanced-color-picker.png")
        
        # Create control file
        control_content = f"""Package: enhanced-color-picker
Version: {self.app_version}
Section: graphics
Priority: optional
Architecture: all
Depends: python3 (>= 3.8), python3-tk, python3-pil
Maintainer: {self.app_author} <contact@enhanced-color-picker.com>
Description: {self.app_description}
 Enhanced Color Picker is a professional color selection tool designed for
 designers, developers, and digital artists. It provides precise color picking
 from images with advanced features like palette management, color analysis,
 accessibility checking, and multi-format export capabilities.
"""
        
        with open(package_dir / "DEBIAN" / "control", 'w') as f:
            f.write(control_content)
        
        # Create postinst script
        postinst_content = """#!/bin/bash
# Update desktop database
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database /usr/share/applications
fi

# Update icon cache
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -f -t /usr/share/icons/hicolor
fi
"""
        
        postinst_file = package_dir / "DEBIAN" / "postinst"
        with open(postinst_file, 'w') as f:
            f.write(postinst_content)
        os.chmod(postinst_file, 0o755)
        
        # Build package
        try:
            cmd = ["dpkg-deb", "--build", str(package_dir)]
            result = subprocess.run(cmd, cwd=self.dist_dir)
            
            if result.returncode == 0:
                print(f"✅ Debian package created: {package_name}.deb")
                return True
            else:
                print("❌ Debian package creation failed")
                return False
                
        except Exception as e:
            print(f"❌ Debian package error: {e}")
            return False
    
    def _create_rpm_package(self) -> bool:
        """Create RPM package."""
        print("⚠️ RPM package creation not yet implemented")
        return False
    
    def _create_appimage(self) -> bool:
        """Create AppImage."""
        print("⚠️ AppImage creation not yet implemented")
        return False
    
    def create_source_distribution(self) -> bool:
        """Create source distribution."""
        print("📦 Creating source distribution...")
        
        try:
            # Create source archive
            archive_name = f"enhanced-color-picker-{self.app_version}-source"
            archive_path = self.dist_dir / f"{archive_name}.tar.gz"
            
            # Files to include
            include_patterns = [
                "enhanced_color_picker/**/*",
                "docs/**/*",
                "desktop/*",
                "*.py",
                "*.txt",
                "*.md",
                "LICENSE"
            ]
            
            # Files to exclude
            exclude_patterns = [
                "**/__pycache__/**",
                "**/*.pyc",
                "**/.*",
                "build/**",
                "dist/**",
                "*.egg-info/**"
            ]
            
            import tarfile
            
            with tarfile.open(archive_path, 'w:gz') as tar:
                for pattern in include_patterns:
                    for file_path in self.project_root.glob(pattern):
                        if file_path.is_file():
                            # Check if file should be excluded
                            should_exclude = False
                            for exclude_pattern in exclude_patterns:
                                if file_path.match(exclude_pattern):
                                    should_exclude = True
                                    break
                            
                            if not should_exclude:
                                arcname = f"{archive_name}/{file_path.relative_to(self.project_root)}"
                                tar.add(file_path, arcname=arcname)
            
            print(f"✅ Source distribution created: {archive_path}")
            return True
            
        except Exception as e:
            print(f"❌ Source distribution error: {e}")
            return False
    
    def create_installer(self) -> bool:
        """Create platform-specific installer."""
        if self.system == "windows":
            return self._create_windows_installer()
        elif self.system == "darwin":
            return self._create_macos_installer()
        elif self.system == "linux":
            return self._create_linux_installer()
        else:
            print(f"⚠️ Installer creation not supported for {self.system}")
            return False
    
    def _create_windows_installer(self) -> bool:
        """Create Windows installer using NSIS or similar."""
        print("⚠️ Windows installer creation not yet implemented")
        print("   Consider using NSIS, Inno Setup, or WiX Toolset")
        return False
    
    def _create_macos_installer(self) -> bool:
        """Create macOS installer package."""
        print("⚠️ macOS installer creation not yet implemented")
        print("   Consider using pkgbuild and productbuild")
        return False
    
    def _create_linux_installer(self) -> bool:
        """Create Linux installer script."""
        print("📦 Creating Linux installer script...")
        
        installer_script = f'''#!/bin/bash
# Enhanced Color Picker Linux Installer
# Version {self.app_version}

set -e

echo "Enhanced Color Picker Installer"
echo "==============================="

# Check Python version
python3 -c "import sys; assert sys.version_info >= (3, 8)" 2>/dev/null || {{
    echo "Error: Python 3.8 or higher is required"
    exit 1
}}

# Install directory
INSTALL_DIR="/opt/enhanced-color-picker"
BIN_DIR="/usr/local/bin"
DESKTOP_DIR="/usr/share/applications"
ICON_DIR="/usr/share/icons/hicolor/48x48/apps"

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    echo "This installer requires root privileges"
    echo "Please run with sudo: sudo $0"
    exit 1
fi

echo "Installing Enhanced Color Picker to $INSTALL_DIR..."

# Create directories
mkdir -p "$INSTALL_DIR"
mkdir -p "$BIN_DIR"
mkdir -p "$DESKTOP_DIR"
mkdir -p "$ICON_DIR"

# Extract and install files (this would be replaced with actual extraction)
echo "Extracting files..."
# tar -xzf enhanced-color-picker-{self.app_version}.tar.gz -C "$INSTALL_DIR" --strip-components=1

# Install dependencies
echo "Installing Python dependencies..."
pip3 install -r "$INSTALL_DIR/requirements.txt"

# Create launcher script
cat > "$BIN_DIR/enhanced-color-picker" << 'EOF'
#!/bin/bash
cd "$INSTALL_DIR"
python3 main.py "$@"
EOF

chmod +x "$BIN_DIR/enhanced-color-picker"

# Install desktop file
cp "$INSTALL_DIR/desktop/enhanced-color-picker.desktop" "$DESKTOP_DIR/"
sed -i "s|/usr/local/bin/enhanced-color-picker/main.py|$BIN_DIR/enhanced-color-picker|" "$DESKTOP_DIR/enhanced-color-picker.desktop"

# Install icon
if [ -f "$INSTALL_DIR/enhanced_color_picker/assets/icons/app.png" ]; then
    cp "$INSTALL_DIR/enhanced_color_picker/assets/icons/app.png" "$ICON_DIR/enhanced-color-picker.png"
fi

# Update desktop database
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$DESKTOP_DIR"
fi

# Update icon cache
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -f -t /usr/share/icons/hicolor
fi

echo "Installation completed successfully!"
echo "You can now run Enhanced Color Picker from:"
echo "  - Command line: enhanced-color-picker"
echo "  - Applications menu: Enhanced Color Picker"

# Create uninstaller
cat > "$INSTALL_DIR/uninstall.sh" << 'EOF'
#!/bin/bash
echo "Uninstalling Enhanced Color Picker..."
rm -rf "$INSTALL_DIR"
rm -f "$BIN_DIR/enhanced-color-picker"
rm -f "$DESKTOP_DIR/enhanced-color-picker.desktop"
rm -f "$ICON_DIR/enhanced-color-picker.png"
echo "Uninstallation completed."
EOF

chmod +x "$INSTALL_DIR/uninstall.sh"
echo "To uninstall, run: sudo $INSTALL_DIR/uninstall.sh"
'''
        
        installer_path = self.dist_dir / "install-linux.sh"
        with open(installer_path, 'w') as f:
            f.write(installer_script)
        
        os.chmod(installer_path, 0o755)
        
        print(f"✅ Linux installer created: {installer_path}")
        return True
    
    def build_all(self, platforms: Optional[List[str]] = None) -> Dict[str, bool]:
        """Build for all specified platforms."""
        if platforms is None:
            platforms = ["pyinstaller", "source"]
        
        results = {}
        
        print(f"🚀 Building Enhanced Color Picker v{self.app_version}")
        print("=" * 50)
        
        # Clean previous builds
        self.clean_build()
        
        # Ensure dist directory exists
        self.dist_dir.mkdir(exist_ok=True)
        
        for platform in platforms:
            print(f"\\n📦 Building for: {platform}")
            
            if platform == "pyinstaller":
                results[platform] = self.build_pyinstaller()
            elif platform == "cx_freeze":
                results[platform] = self.build_cx_freeze()
            elif platform == "py2app":
                results[platform] = self.build_py2app()
            elif platform == "deb":
                results[platform] = self.create_linux_package("deb")
            elif platform == "rpm":
                results[platform] = self.create_linux_package("rpm")
            elif platform == "appimage":
                results[platform] = self.create_linux_package("appimage")
            elif platform == "source":
                results[platform] = self.create_source_distribution()
            elif platform == "installer":
                results[platform] = self.create_installer()
            else:
                print(f"⚠️ Unknown platform: {platform}")
                results[platform] = False
        
        # Summary
        print("\\n" + "=" * 50)
        print("📊 Build Summary:")
        
        for platform, success in results.items():
            status = "✅ Success" if success else "❌ Failed"
            print(f"   {platform}: {status}")
        
        successful_builds = sum(1 for success in results.values() if success)
        total_builds = len(results)
        
        print(f"\\n🎯 {successful_builds}/{total_builds} builds completed successfully")
        
        if successful_builds > 0:
            print(f"📁 Output directory: {self.dist_dir}")
        
        return results


def main():
    """Main build function."""
    parser = argparse.ArgumentParser(description="Enhanced Color Picker Build Script")
    parser.add_argument("--platforms", nargs="+", 
                       choices=["pyinstaller", "cx_freeze", "py2app", "deb", "rpm", 
                               "appimage", "source", "installer"],
                       default=["pyinstaller", "source"],
                       help="Platforms to build for")
    parser.add_argument("--clean", action="store_true",
                       help="Clean build artifacts only")
    parser.add_argument("--onefile", action="store_true",
                       help="Create single-file executable (PyInstaller only)")
    parser.add_argument("--console", action="store_true",
                       help="Show console window (PyInstaller only)")
    
    args = parser.parse_args()
    
    builder = PackageBuilder()
    
    if args.clean:
        builder.clean_build()
        print("✅ Build artifacts cleaned")
        return
    
    # Build for specified platforms
    results = builder.build_all(args.platforms)
    
    # Exit with error code if any builds failed
    if not all(results.values()):
        sys.exit(1)


if __name__ == "__main__":
    main()