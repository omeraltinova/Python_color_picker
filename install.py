#!/usr/bin/env python3
"""
Enhanced Color Picker Installation Script

This script handles the installation and setup of Enhanced Color Picker,
including dependency installation, configuration, and desktop integration.
"""

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path
import json
import argparse
from typing import List, Dict, Optional


class ColorPickerInstaller:
    """Handles installation of Enhanced Color Picker."""
    
    def __init__(self):
        self.system = platform.system().lower()
        self.python_executable = sys.executable
        self.install_dir = Path.cwd()
        self.user_data_dir = self._get_user_data_dir()
        self.desktop_file_created = False
        self.shortcut_created = False
        
    def _get_user_data_dir(self) -> Path:
        """Get user data directory based on platform."""
        if self.system == "windows":
            return Path(os.environ.get('APPDATA', '')) / "Enhanced Color Picker"
        elif self.system == "darwin":  # macOS
            return Path.home() / "Library" / "Application Support" / "Enhanced Color Picker"
        else:  # Linux and others
            return Path.home() / ".config" / "enhanced-color-picker"
    
    def check_python_version(self) -> bool:
        """Check if Python version is compatible."""
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 8):
            print(f"❌ Python 3.8+ required. Current version: {version.major}.{version.minor}.{version.micro}")
            return False
        
        print(f"✅ Python version {version.major}.{version.minor}.{version.micro} is compatible")
        return True
    
    def install_dependencies(self, upgrade: bool = False) -> bool:
        """Install required Python dependencies."""
        print("📦 Installing dependencies...")
        
        requirements_file = self.install_dir / "requirements.txt"
        if not requirements_file.exists():
            print("❌ requirements.txt not found")
            return False
        
        try:
            cmd = [self.python_executable, "-m", "pip", "install", "-r", str(requirements_file)]
            if upgrade:
                cmd.append("--upgrade")
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Dependencies installed successfully")
                return True
            else:
                print(f"❌ Failed to install dependencies: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error installing dependencies: {e}")
            return False
    
    def create_user_directories(self) -> bool:
        """Create necessary user directories."""
        print("📁 Creating user directories...")
        
        directories = [
            self.user_data_dir,
            self.user_data_dir / "palettes",
            self.user_data_dir / "settings",
            self.user_data_dir / "cache",
            self.user_data_dir / "logs",
            self.user_data_dir / "backups"
        ]
        
        try:
            for directory in directories:
                directory.mkdir(parents=True, exist_ok=True)
            
            print(f"✅ User directories created at: {self.user_data_dir}")
            return True
            
        except Exception as e:
            print(f"❌ Error creating directories: {e}")
            return False
    
    def create_default_config(self) -> bool:
        """Create default configuration files."""
        print("⚙️ Creating default configuration...")
        
        try:
            # Default application settings
            default_settings = {
                "version": "1.0.0",
                "theme": "dark",
                "language": "en",
                "default_color_format": "hex",
                "auto_save_palettes": True,
                "max_history_items": 50,
                "zoom_sensitivity": 1.1,
                "enable_pixel_grid": True,
                "pixel_grid_threshold": 8.0,
                "cache_size_mb": 100,
                "auto_cleanup": True,
                "show_tooltips": True,
                "check_updates": True
            }
            
            settings_file = self.user_data_dir / "settings" / "app_settings.json"
            with open(settings_file, 'w') as f:
                json.dump(default_settings, f, indent=2)
            
            # Default keyboard shortcuts
            default_shortcuts = {
                "load_image": "Ctrl+O",
                "save_palette": "Ctrl+S",
                "save_palette_as": "Ctrl+Shift+S",
                "new_palette": "Ctrl+N",
                "copy_color": "Ctrl+C",
                "zoom_in": "Ctrl+Plus",
                "zoom_out": "Ctrl+Minus",
                "fit_to_screen": "Ctrl+0",
                "actual_size": "Ctrl+1",
                "toggle_fullscreen": "F11",
                "show_help": "F1",
                "quit": "Ctrl+Q"
            }
            
            shortcuts_file = self.user_data_dir / "settings" / "shortcuts.json"
            with open(shortcuts_file, 'w') as f:
                json.dump(default_shortcuts, f, indent=2)
            
            print("✅ Default configuration created")
            return True
            
        except Exception as e:
            print(f"❌ Error creating configuration: {e}")
            return False
    
    def create_desktop_integration(self) -> bool:
        """Create desktop integration (shortcuts, menu entries)."""
        if self.system == "linux":
            return self._create_linux_desktop_entry()
        elif self.system == "windows":
            return self._create_windows_shortcut()
        elif self.system == "darwin":
            return self._create_macos_app_bundle()
        else:
            print("⚠️ Desktop integration not supported on this platform")
            return True
    
    def _create_linux_desktop_entry(self) -> bool:
        """Create Linux desktop entry."""
        print("🐧 Creating Linux desktop entry...")
        
        try:
            desktop_entry = f"""[Desktop Entry]
Name=Enhanced Color Picker
Comment=Professional color selection tool
Exec={self.python_executable} {self.install_dir / 'main.py'}
Icon={self.install_dir / 'enhanced_color_picker' / 'assets' / 'icons' / 'app.png'}
Terminal=false
Type=Application
Categories=Graphics;Photography;
MimeType=image/png;image/jpeg;image/gif;image/bmp;image/tiff;image/webp;image/svg+xml;
"""
            
            # User desktop entry
            desktop_dir = Path.home() / ".local" / "share" / "applications"
            desktop_dir.mkdir(parents=True, exist_ok=True)
            
            desktop_file = desktop_dir / "enhanced-color-picker.desktop"
            with open(desktop_file, 'w') as f:
                f.write(desktop_entry)
            
            # Make executable
            os.chmod(desktop_file, 0o755)
            
            # Update desktop database
            try:
                subprocess.run(["update-desktop-database", str(desktop_dir)], 
                             capture_output=True, check=False)
            except FileNotFoundError:
                pass  # update-desktop-database not available
            
            self.desktop_file_created = True
            print("✅ Linux desktop entry created")
            return True
            
        except Exception as e:
            print(f"❌ Error creating desktop entry: {e}")
            return False
    
    def _create_windows_shortcut(self) -> bool:
        """Create Windows shortcut."""
        print("🪟 Creating Windows shortcut...")
        
        try:
            # Try to create shortcut using pywin32 if available
            try:
                import win32com.client
                
                desktop = Path.home() / "Desktop"
                shortcut_path = desktop / "Enhanced Color Picker.lnk"
                
                shell = win32com.client.Dispatch("WScript.Shell")
                shortcut = shell.CreateShortCut(str(shortcut_path))
                shortcut.Targetpath = self.python_executable
                shortcut.Arguments = f'"{self.install_dir / "main.py"}"'
                shortcut.WorkingDirectory = str(self.install_dir)
                shortcut.IconLocation = str(self.install_dir / "enhanced_color_picker" / "assets" / "icons" / "app.ico")
                shortcut.Description = "Enhanced Color Picker - Professional color selection tool"
                shortcut.save()
                
                self.shortcut_created = True
                print("✅ Windows shortcut created on desktop")
                return True
                
            except ImportError:
                # Fallback: create batch file
                batch_content = f"""@echo off
cd /d "{self.install_dir}"
"{self.python_executable}" main.py
pause
"""
                batch_file = Path.home() / "Desktop" / "Enhanced Color Picker.bat"
                with open(batch_file, 'w') as f:
                    f.write(batch_content)
                
                print("✅ Windows batch file created on desktop")
                return True
                
        except Exception as e:
            print(f"❌ Error creating Windows shortcut: {e}")
            return False
    
    def _create_macos_app_bundle(self) -> bool:
        """Create macOS app bundle."""
        print("🍎 Creating macOS app bundle...")
        
        try:
            app_name = "Enhanced Color Picker.app"
            app_path = Path.home() / "Applications" / app_name
            
            # Create app bundle structure
            contents_dir = app_path / "Contents"
            macos_dir = contents_dir / "MacOS"
            resources_dir = contents_dir / "Resources"
            
            for directory in [contents_dir, macos_dir, resources_dir]:
                directory.mkdir(parents=True, exist_ok=True)
            
            # Create Info.plist
            info_plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>enhanced-color-picker</string>
    <key>CFBundleIdentifier</key>
    <string>com.enhanced-color-picker.app</string>
    <key>CFBundleName</key>
    <string>Enhanced Color Picker</string>
    <key>CFBundleVersion</key>
    <string>1.0.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0.0</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleSignature</key>
    <string>ECPK</string>
</dict>
</plist>"""
            
            with open(contents_dir / "Info.plist", 'w') as f:
                f.write(info_plist)
            
            # Create launcher script
            launcher_script = f"""#!/bin/bash
cd "{self.install_dir}"
"{self.python_executable}" main.py
"""
            
            launcher_path = macos_dir / "enhanced-color-picker"
            with open(launcher_path, 'w') as f:
                f.write(launcher_script)
            
            os.chmod(launcher_path, 0o755)
            
            # Copy icon if available
            icon_source = self.install_dir / "enhanced_color_picker" / "assets" / "icons" / "app.icns"
            if icon_source.exists():
                shutil.copy2(icon_source, resources_dir / "app.icns")
            
            print("✅ macOS app bundle created")
            return True
            
        except Exception as e:
            print(f"❌ Error creating macOS app bundle: {e}")
            return False
    
    def test_installation(self) -> bool:
        """Test if the installation works correctly."""
        print("🧪 Testing installation...")
        
        try:
            # Test importing main modules
            sys.path.insert(0, str(self.install_dir))
            
            import enhanced_color_picker
            from enhanced_color_picker.core.application import EnhancedColorPickerApp
            
            print("✅ Installation test passed")
            return True
            
        except Exception as e:
            print(f"❌ Installation test failed: {e}")
            return False
    
    def create_uninstaller(self) -> bool:
        """Create uninstaller script."""
        print("🗑️ Creating uninstaller...")
        
        try:
            uninstall_script = f"""#!/usr/bin/env python3
\"\"\"
Enhanced Color Picker Uninstaller
\"\"\"

import os
import shutil
from pathlib import Path
import sys

def uninstall():
    print("Uninstalling Enhanced Color Picker...")
    
    # Remove user data directory
    user_data_dir = Path("{self.user_data_dir}")
    if user_data_dir.exists():
        response = input(f"Remove user data directory {{user_data_dir}}? (y/N): ")
        if response.lower() == 'y':
            shutil.rmtree(user_data_dir)
            print("✅ User data removed")
        else:
            print("⚠️ User data preserved")
    
    # Remove desktop integration
"""
            
            if self.system == "linux" and self.desktop_file_created:
                uninstall_script += f"""
    # Remove Linux desktop entry
    desktop_file = Path.home() / ".local" / "share" / "applications" / "enhanced-color-picker.desktop"
    if desktop_file.exists():
        desktop_file.unlink()
        print("✅ Desktop entry removed")
"""
            
            elif self.system == "windows" and self.shortcut_created:
                uninstall_script += f"""
    # Remove Windows shortcut
    shortcut_path = Path.home() / "Desktop" / "Enhanced Color Picker.lnk"
    if shortcut_path.exists():
        shortcut_path.unlink()
        print("✅ Desktop shortcut removed")
    
    batch_path = Path.home() / "Desktop" / "Enhanced Color Picker.bat"
    if batch_path.exists():
        batch_path.unlink()
        print("✅ Batch file removed")
"""
            
            uninstall_script += """
    print("\\n✅ Enhanced Color Picker uninstalled successfully")
    print("You can manually remove the application directory if desired.")

if __name__ == "__main__":
    uninstall()
"""
            
            uninstaller_path = self.install_dir / "uninstall.py"
            with open(uninstaller_path, 'w') as f:
                f.write(uninstall_script)
            
            os.chmod(uninstaller_path, 0o755)
            
            print("✅ Uninstaller created")
            return True
            
        except Exception as e:
            print(f"❌ Error creating uninstaller: {e}")
            return False
    
    def install(self, upgrade: bool = False, skip_desktop: bool = False) -> bool:
        """Run the complete installation process."""
        print("🎨 Enhanced Color Picker Installation")
        print("=" * 40)
        
        steps = [
            ("Checking Python version", self.check_python_version),
            ("Installing dependencies", lambda: self.install_dependencies(upgrade)),
            ("Creating user directories", self.create_user_directories),
            ("Creating default configuration", self.create_default_config),
            ("Testing installation", self.test_installation),
            ("Creating uninstaller", self.create_uninstaller)
        ]
        
        if not skip_desktop:
            steps.insert(-2, ("Creating desktop integration", self.create_desktop_integration))
        
        for step_name, step_func in steps:
            print(f"\\n{step_name}...")
            if not step_func():
                print(f"\\n❌ Installation failed at: {step_name}")
                return False
        
        print("\\n" + "=" * 40)
        print("✅ Enhanced Color Picker installed successfully!")
        print(f"\\n📁 Installation directory: {self.install_dir}")
        print(f"📁 User data directory: {self.user_data_dir}")
        
        if not skip_desktop:
            if self.system == "linux" and self.desktop_file_created:
                print("🐧 Desktop entry created - check your applications menu")
            elif self.system == "windows" and self.shortcut_created:
                print("🪟 Desktop shortcut created")
            elif self.system == "darwin":
                print("🍎 App bundle created in ~/Applications")
        
        print(f"\\n🚀 To start: python {self.install_dir / 'main.py'}")
        print(f"🗑️ To uninstall: python {self.install_dir / 'uninstall.py'}")
        
        return True


def main():
    """Main installation function."""
    parser = argparse.ArgumentParser(description="Enhanced Color Picker Installer")
    parser.add_argument("--upgrade", action="store_true", 
                       help="Upgrade existing dependencies")
    parser.add_argument("--skip-desktop", action="store_true",
                       help="Skip desktop integration")
    parser.add_argument("--user-data-dir", type=str,
                       help="Custom user data directory")
    
    args = parser.parse_args()
    
    installer = ColorPickerInstaller()
    
    if args.user_data_dir:
        installer.user_data_dir = Path(args.user_data_dir)
    
    success = installer.install(
        upgrade=args.upgrade,
        skip_desktop=args.skip_desktop
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()