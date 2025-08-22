"""
Help menu integration for Enhanced Color Picker.
Provides access to documentation, tutorials, and support resources.
"""

import tkinter as tk
from tkinter import messagebox
import webbrowser
import os
from pathlib import Path
from typing import Optional
from ..core.event_bus import EventBus
from .components.help_system import HelpSystem


class HelpMenu:
    """Manages the Help menu and related functionality."""
    
    def __init__(self, menubar: tk.Menu, parent: tk.Widget, event_bus: EventBus):
        self.menubar = menubar
        self.parent = parent
        self.event_bus = event_bus
        self.help_system = HelpSystem(parent, event_bus)
        
        self._create_help_menu()
        self._setup_keyboard_shortcuts()
    
    def _create_help_menu(self):
        """Create the Help menu."""
        self.help_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Help", menu=self.help_menu)
        
        # Quick Help
        self.help_menu.add_command(
            label="Quick Start Guide",
            command=lambda: self.help_system.show_help('getting_started'),
            accelerator="F1"
        )
        
        self.help_menu.add_separator()
        
        # Documentation
        self.help_menu.add_command(
            label="User Manual",
            command=self._open_user_manual
        )
        
        self.help_menu.add_command(
            label="Tutorials",
            command=self._open_tutorials
        )
        
        self.help_menu.add_command(
            label="FAQ",
            command=self._open_faq
        )
        
        self.help_menu.add_command(
            label="Troubleshooting",
            command=lambda: self.help_system.show_help('troubleshooting')
        )
        
        self.help_menu.add_separator()
        
        # Feature Help
        feature_menu = tk.Menu(self.help_menu, tearoff=0)
        self.help_menu.add_cascade(label="Feature Help", menu=feature_menu)
        
        feature_menu.add_command(
            label="Color Selection",
            command=lambda: self.help_system.show_help('color_selection')
        )
        
        feature_menu.add_command(
            label="Palette Management",
            command=lambda: self.help_system.show_help('palette_management')
        )
        
        feature_menu.add_command(
            label="Zoom & Navigation",
            command=lambda: self.help_system.show_help('zoom_navigation')
        )
        
        feature_menu.add_command(
            label="Keyboard Shortcuts",
            command=lambda: self.help_system.show_help('keyboard_shortcuts')
        )
        
        self.help_menu.add_separator()
        
        # Online Resources
        online_menu = tk.Menu(self.help_menu, tearoff=0)
        self.help_menu.add_cascade(label="Online Resources", menu=online_menu)
        
        online_menu.add_command(
            label="Project Website",
            command=self._open_website
        )
        
        online_menu.add_command(
            label="Report Bug",
            command=self._report_bug
        )
        
        online_menu.add_command(
            label="Request Feature",
            command=self._request_feature
        )
        
        online_menu.add_command(
            label="Community Forum",
            command=self._open_forum
        )
        
        self.help_menu.add_separator()
        
        # System Info
        self.help_menu.add_command(
            label="System Information",
            command=self._show_system_info
        )
        
        self.help_menu.add_command(
            label="Check for Updates",
            command=self._check_updates
        )
        
        self.help_menu.add_separator()
        
        # About
        self.help_menu.add_command(
            label="About Enhanced Color Picker",
            command=self._show_about
        )
    
    def _setup_keyboard_shortcuts(self):
        """Set up keyboard shortcuts for help functions."""
        self.parent.bind('<F1>', lambda e: self.help_system.show_help('getting_started'))
        self.parent.bind('<Control-F1>', lambda e: self.help_system.show_help('keyboard_shortcuts'))
    
    def _open_user_manual(self):
        """Open the user manual."""
        docs_path = self._get_docs_path()
        manual_path = docs_path / "user-manual.md"
        
        if manual_path.exists():
            self._open_file(manual_path)
        else:
            self.help_system.show_help('getting_started')
    
    def _open_tutorials(self):
        """Open the tutorials directory."""
        docs_path = self._get_docs_path()
        tutorials_path = docs_path / "tutorials"
        
        if tutorials_path.exists():
            self._open_file(tutorials_path)
        else:
            messagebox.showinfo(
                "Tutorials",
                "Tutorials are available in the documentation folder.\n"
                "Check the project directory for the 'docs/tutorials' folder."
            )
    
    def _open_faq(self):
        """Open the FAQ."""
        docs_path = self._get_docs_path()
        faq_path = docs_path / "faq.md"
        
        if faq_path.exists():
            self._open_file(faq_path)
        else:
            messagebox.showinfo(
                "FAQ",
                "Frequently Asked Questions are available in the documentation.\n"
                "Check the project directory for the 'docs/faq.md' file."
            )
    
    def _get_docs_path(self) -> Path:
        """Get the path to the documentation directory."""
        # Try to find docs relative to the application
        current_path = Path(__file__).parent.parent.parent.parent
        docs_path = current_path / "docs"
        
        if not docs_path.exists():
            # Alternative locations
            alternative_paths = [
                Path.cwd() / "docs",
                Path.home() / "Enhanced Color Picker" / "docs",
                Path("/usr/share/enhanced-color-picker/docs"),  # Linux
                Path("/Applications/Enhanced Color Picker.app/Contents/Resources/docs")  # macOS
            ]
            
            for path in alternative_paths:
                if path.exists():
                    return path
        
        return docs_path
    
    def _open_file(self, file_path: Path):
        """Open a file or directory with the default system application."""
        try:
            if os.name == 'nt':  # Windows
                os.startfile(str(file_path))
            elif os.name == 'posix':  # macOS and Linux
                if os.uname().sysname == 'Darwin':  # macOS
                    os.system(f'open "{file_path}"')
                else:  # Linux
                    os.system(f'xdg-open "{file_path}"')
        except Exception as e:
            messagebox.showerror(
                "Error Opening File",
                f"Could not open {file_path.name}:\n{str(e)}\n\n"
                f"Please navigate to: {file_path}"
            )
    
    def _open_website(self):
        """Open the project website."""
        # Placeholder URL - replace with actual project website
        url = "https://github.com/enhanced-color-picker/enhanced-color-picker"
        try:
            webbrowser.open(url)
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Could not open website:\n{str(e)}\n\nURL: {url}"
            )
    
    def _report_bug(self):
        """Open bug reporting page."""
        url = "https://github.com/enhanced-color-picker/enhanced-color-picker/issues/new?template=bug_report.md"
        try:
            webbrowser.open(url)
        except Exception as e:
            messagebox.showinfo(
                "Report Bug",
                f"Please report bugs at:\n{url}\n\n"
                "Include:\n"
                "• Steps to reproduce the issue\n"
                "• Expected vs actual behavior\n"
                "• System information\n"
                "• Screenshots if applicable"
            )
    
    def _request_feature(self):
        """Open feature request page."""
        url = "https://github.com/enhanced-color-picker/enhanced-color-picker/issues/new?template=feature_request.md"
        try:
            webbrowser.open(url)
        except Exception as e:
            messagebox.showinfo(
                "Request Feature",
                f"Please request features at:\n{url}\n\n"
                "Include:\n"
                "• Detailed description of the feature\n"
                "• Use case and benefits\n"
                "• Examples or mockups if applicable"
            )
    
    def _open_forum(self):
        """Open community forum."""
        url = "https://github.com/enhanced-color-picker/enhanced-color-picker/discussions"
        try:
            webbrowser.open(url)
        except Exception as e:
            messagebox.showinfo(
                "Community Forum",
                f"Join the community discussion at:\n{url}\n\n"
                "• Ask questions\n"
                "• Share tips and tricks\n"
                "• Connect with other users\n"
                "• Get help from the community"
            )
    
    def _show_system_info(self):
        """Show system information dialog."""
        import sys
        import platform
        from tkinter import scrolledtext
        
        # Collect system information
        info = []
        info.append(f"Enhanced Color Picker Version: 1.0.0")
        info.append(f"Python Version: {sys.version}")
        info.append(f"Platform: {platform.platform()}")
        info.append(f"Architecture: {platform.architecture()[0]}")
        info.append(f"Processor: {platform.processor()}")
        info.append(f"System: {platform.system()} {platform.release()}")
        
        # Try to get additional info
        try:
            import psutil
            memory = psutil.virtual_memory()
            info.append(f"Total Memory: {memory.total // (1024**3)} GB")
            info.append(f"Available Memory: {memory.available // (1024**3)} GB")
        except ImportError:
            info.append("Memory info: Not available (psutil not installed)")
        
        try:
            from PIL import Image
            info.append(f"PIL/Pillow Version: {Image.__version__}")
        except ImportError:
            info.append("PIL/Pillow: Not available")
        
        # Create info window
        info_window = tk.Toplevel(self.parent)
        info_window.title("System Information")
        info_window.geometry("500x400")
        info_window.resizable(True, True)
        
        # Create text widget with scrollbar
        text_widget = scrolledtext.ScrolledText(info_window, wrap=tk.WORD, padx=10, pady=10)
        text_widget.pack(fill=tk.BOTH, expand=True)
        
        # Insert system information
        text_widget.insert(tk.END, "\\n".join(info))
        text_widget.config(state=tk.DISABLED)
        
        # Add copy button
        button_frame = tk.Frame(info_window)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def copy_info():
            info_window.clipboard_clear()
            info_window.clipboard_append("\\n".join(info))
            messagebox.showinfo("Copied", "System information copied to clipboard")
        
        tk.Button(button_frame, text="Copy to Clipboard", command=copy_info).pack(side=tk.LEFT)
        tk.Button(button_frame, text="Close", command=info_window.destroy).pack(side=tk.RIGHT)
    
    def _check_updates(self):
        """Check for application updates."""
        # Placeholder for update checking functionality
        messagebox.showinfo(
            "Check for Updates",
            "Update checking is not yet implemented.\\n\\n"
            "Please check the project website for the latest version:\\n"
            "https://github.com/enhanced-color-picker/enhanced-color-picker"
        )
    
    def _show_about(self):
        """Show about dialog."""
        about_text = """Enhanced Color Picker v1.0.0

A professional color selection tool for designers and developers.

Features:
• Pixel-perfect color picking from images
• Multiple color format support (RGB, HEX, HSL, HSV, CMYK)
• Advanced palette management
• Color analysis and accessibility tools
• Zoom and navigation capabilities
• Export to various formats

Developed with Python and Tkinter
© 2024 Enhanced Color Picker Team

This software is open source and free to use.
"""
        
        messagebox.showinfo("About Enhanced Color Picker", about_text)
    
    def get_help_system(self) -> HelpSystem:
        """Get the help system instance."""
        return self.help_system