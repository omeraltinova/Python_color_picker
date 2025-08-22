"""
Accessibility Panel for displaying WCAG compliance information and accessibility features.

This panel provides:
- Contrast ratio display
- WCAG AA/AAA compliance indicators
- Color accessibility recommendations
- Alternative color suggestions
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, List, Callable
import threading

from ...models.color_data import ColorData
from ...services.accessibility_service import (
    AccessibilityService, ContrastResult, AccessibilityReport, WCAGLevel
)
from ...core.event_bus import EventBus


class AccessibilityPanel(ttk.Frame):
    """Panel for displaying accessibility and WCAG compliance information"""
    
    def __init__(self, parent, event_bus: EventBus):
        super().__init__(parent)
        self.event_bus = event_bus
        self.accessibility_service = AccessibilityService()
        
        # Current colors for analysis
        self.foreground_color: Optional[ColorData] = None
        self.background_color: Optional[ColorData] = None
        self.current_report: Optional[AccessibilityReport] = None
        
        # UI Variables
        self.contrast_ratio_var = tk.StringVar(value="N/A")
        self.aa_normal_var = tk.StringVar(value="❌")
        self.aa_large_var = tk.StringVar(value="❌")
        self.aaa_normal_var = tk.StringVar(value="❌")
        self.aaa_large_var = tk.StringVar(value="❌")
        self.overall_grade_var = tk.StringVar(value="N/A")
        self.recommendation_var = tk.StringVar(value="Select colors to analyze")
        
        self._setup_ui()
        self._setup_event_handlers()
    
    def _setup_ui(self):
        """Setup the accessibility panel UI"""
        # Main title
        title_label = ttk.Label(self, text="Accessibility Analysis", 
                               font=('Arial', 12, 'bold'))
        title_label.pack(pady=(0, 10), anchor='w')
        
        # Color selection frame
        self._create_color_selection_frame()
        
        # Contrast ratio display
        self._create_contrast_ratio_frame()
        
        # WCAG compliance indicators
        self._create_wcag_compliance_frame()
        
        # Recommendations
        self._create_recommendations_frame()
        
        # Alternative colors
        self._create_alternatives_frame()
        
        # Action buttons
        self._create_action_buttons()
    
    def _create_color_selection_frame(self):
        """Create color selection controls"""
        color_frame = ttk.LabelFrame(self, text="Colors to Analyze", padding=10)
        color_frame.pack(fill='x', pady=(0, 10))
        
        # Foreground color
        fg_frame = ttk.Frame(color_frame)
        fg_frame.pack(fill='x', pady=(0, 5))
        
        ttk.Label(fg_frame, text="Foreground:").pack(side='left')
        self.fg_color_canvas = tk.Canvas(fg_frame, width=30, height=20, 
                                        relief='solid', borderwidth=1)
        self.fg_color_canvas.pack(side='left', padx=(10, 5))
        
        self.fg_color_label = ttk.Label(fg_frame, text="Not selected")
        self.fg_color_label.pack(side='left', padx=(5, 0))
        
        ttk.Button(fg_frame, text="Set from Current", 
                  command=self._set_foreground_from_current).pack(side='right')
        
        # Background color
        bg_frame = ttk.Frame(color_frame)
        bg_frame.pack(fill='x')
        
        ttk.Label(bg_frame, text="Background:").pack(side='left')
        self.bg_color_canvas = tk.Canvas(bg_frame, width=30, height=20,
                                        relief='solid', borderwidth=1)
        self.bg_color_canvas.pack(side='left', padx=(10, 5))
        
        self.bg_color_label = ttk.Label(bg_frame, text="Not selected")
        self.bg_color_label.pack(side='left', padx=(5, 0))
        
        ttk.Button(bg_frame, text="Set from Current",
                  command=self._set_background_from_current).pack(side='right')
    
    def _create_contrast_ratio_frame(self):
        """Create contrast ratio display"""
        contrast_frame = ttk.LabelFrame(self, text="Contrast Ratio", padding=10)
        contrast_frame.pack(fill='x', pady=(0, 10))
        
        # Large contrast ratio display
        ratio_frame = ttk.Frame(contrast_frame)
        ratio_frame.pack(fill='x')
        
        ttk.Label(ratio_frame, text="Ratio:", font=('Arial', 10)).pack(side='left')
        
        self.contrast_ratio_label = ttk.Label(ratio_frame, textvariable=self.contrast_ratio_var,
                                             font=('Arial', 16, 'bold'))
        self.contrast_ratio_label.pack(side='left', padx=(10, 0))
        
        # Overall grade
        self.grade_label = ttk.Label(ratio_frame, textvariable=self.overall_grade_var,
                                    font=('Arial', 12, 'bold'))
        self.grade_label.pack(side='right')
    
    def _create_wcag_compliance_frame(self):
        """Create WCAG compliance indicators"""
        wcag_frame = ttk.LabelFrame(self, text="WCAG Compliance", padding=10)
        wcag_frame.pack(fill='x', pady=(0, 10))
        
        # Create grid for compliance indicators
        compliance_grid = ttk.Frame(wcag_frame)
        compliance_grid.pack(fill='x')
        
        # Headers
        ttk.Label(compliance_grid, text="Level", font=('Arial', 10, 'bold')).grid(
            row=0, column=0, sticky='w', padx=(0, 20))
        ttk.Label(compliance_grid, text="Normal Text", font=('Arial', 10, 'bold')).grid(
            row=0, column=1, sticky='w', padx=(0, 20))
        ttk.Label(compliance_grid, text="Large Text", font=('Arial', 10, 'bold')).grid(
            row=0, column=2, sticky='w')
        
        # AA Level
        ttk.Label(compliance_grid, text="AA", font=('Arial', 10)).grid(
            row=1, column=0, sticky='w', padx=(0, 20), pady=2)
        self.aa_normal_label = ttk.Label(compliance_grid, textvariable=self.aa_normal_var,
                                        font=('Arial', 12))
        self.aa_normal_label.grid(row=1, column=1, sticky='w', padx=(0, 20), pady=2)
        self.aa_large_label = ttk.Label(compliance_grid, textvariable=self.aa_large_var,
                                       font=('Arial', 12))
        self.aa_large_label.grid(row=1, column=2, sticky='w', pady=2)
        
        # AAA Level
        ttk.Label(compliance_grid, text="AAA", font=('Arial', 10)).grid(
            row=2, column=0, sticky='w', padx=(0, 20), pady=2)
        self.aaa_normal_label = ttk.Label(compliance_grid, textvariable=self.aaa_normal_var,
                                         font=('Arial', 12))
        self.aaa_normal_label.grid(row=2, column=1, sticky='w', padx=(0, 20), pady=2)
        self.aaa_large_label = ttk.Label(compliance_grid, textvariable=self.aaa_large_var,
                                        font=('Arial', 12))
        self.aaa_large_label.grid(row=2, column=2, sticky='w', pady=2)
    
    def _create_recommendations_frame(self):
        """Create recommendations display"""
        rec_frame = ttk.LabelFrame(self, text="Recommendations", padding=10)
        rec_frame.pack(fill='x', pady=(0, 10))
        
        self.recommendation_label = ttk.Label(rec_frame, textvariable=self.recommendation_var,
                                             wraplength=300, justify='left')
        self.recommendation_label.pack(anchor='w')
        
        # Additional recommendations list
        self.recommendations_listbox = tk.Listbox(rec_frame, height=3, 
                                                 font=('Arial', 9))
        self.recommendations_listbox.pack(fill='x', pady=(10, 0))
    
    def _create_alternatives_frame(self):
        """Create alternative colors display"""
        alt_frame = ttk.LabelFrame(self, text="Accessible Alternatives", padding=10)
        alt_frame.pack(fill='x', pady=(0, 10))
        
        # Scrollable frame for alternative colors
        canvas = tk.Canvas(alt_frame, height=60)
        scrollbar = ttk.Scrollbar(alt_frame, orient="horizontal", command=canvas.xview)
        self.alternatives_frame = ttk.Frame(canvas)
        
        self.alternatives_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.alternatives_frame, anchor="nw")
        canvas.configure(xscrollcommand=scrollbar.set)
        
        canvas.pack(side="top", fill="x", expand=True)
        scrollbar.pack(side="bottom", fill="x")
        
        self.alternatives_canvas = canvas
    
    def _create_action_buttons(self):
        """Create action buttons"""
        button_frame = ttk.Frame(self)
        button_frame.pack(fill='x', pady=(10, 0))
        
        ttk.Button(button_frame, text="Generate Report",
                  command=self._generate_full_report).pack(side='left', padx=(0, 5))
        
        ttk.Button(button_frame, text="Clear Analysis",
                  command=self._clear_analysis).pack(side='left', padx=(0, 5))
        
        ttk.Button(button_frame, text="Export Report",
                  command=self._export_report).pack(side='right')
    
    def _setup_event_handlers(self):
        """Setup event handlers for color updates"""
        self.event_bus.subscribe('color_selected', self._on_color_selected)
        self.event_bus.subscribe('color_changed', self._on_color_changed)
    
    def _on_color_selected(self, color_data: ColorData):
        """Handle color selection events"""
        # Store the current color for potential use
        self.current_selected_color = color_data
    
    def _on_color_changed(self, color_data: ColorData):
        """Handle color change events"""
        self.current_selected_color = color_data
    
    def _set_foreground_from_current(self):
        """Set foreground color from currently selected color"""
        if hasattr(self, 'current_selected_color') and self.current_selected_color:
            self.foreground_color = self.current_selected_color
            self._update_color_display(self.fg_color_canvas, self.fg_color_label, 
                                     self.foreground_color)
            self._analyze_colors()
        else:
            messagebox.showwarning("No Color Selected", 
                                 "Please select a color first")
    
    def _set_background_from_current(self):
        """Set background color from currently selected color"""
        if hasattr(self, 'current_selected_color') and self.current_selected_color:
            self.background_color = self.current_selected_color
            self._update_color_display(self.bg_color_canvas, self.bg_color_label,
                                     self.background_color)
            self._analyze_colors()
        else:
            messagebox.showwarning("No Color Selected",
                                 "Please select a color first")
    
    def _update_color_display(self, canvas: tk.Canvas, label: ttk.Label, color: ColorData):
        """Update color display in canvas and label"""
        canvas.configure(bg=color.hex)
        label.configure(text=color.hex)
    
    def _analyze_colors(self):
        """Analyze the selected color combination"""
        if not self.foreground_color or not self.background_color:
            return
        
        # Run analysis in background thread to avoid UI blocking
        threading.Thread(target=self._perform_analysis, daemon=True).start()
    
    def _perform_analysis(self):
        """Perform accessibility analysis in background thread"""
        try:
            # Generate accessibility report
            report = self.accessibility_service.generate_accessibility_report(
                self.foreground_color, self.background_color
            )
            
            # Update UI in main thread
            self.after(0, lambda: self._update_analysis_display(report))
            
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Analysis Error", 
                                                      f"Failed to analyze colors: {str(e)}"))
    
    def _update_analysis_display(self, report: AccessibilityReport):
        """Update the UI with analysis results"""
        self.current_report = report
        contrast = report.contrast_result
        
        # Update contrast ratio
        self.contrast_ratio_var.set(f"{contrast.ratio}:1")
        
        # Update compliance indicators
        self.aa_normal_var.set("✅" if contrast.passes_aa_normal else "❌")
        self.aa_large_var.set("✅" if contrast.passes_aa_large else "❌")
        self.aaa_normal_var.set("✅" if contrast.passes_aaa_normal else "❌")
        self.aaa_large_var.set("✅" if contrast.passes_aaa_large else "❌")
        
        # Update overall grade with color coding
        grade = self.accessibility_service._calculate_overall_grade(contrast)
        self.overall_grade_var.set(grade)
        
        # Color code the grade
        if grade == "AAA":
            self.grade_label.configure(foreground='green')
        elif grade == "AA":
            self.grade_label.configure(foreground='orange')
        else:
            self.grade_label.configure(foreground='red')
        
        # Update recommendation
        self.recommendation_var.set(contrast.recommendation)
        
        # Update recommendations list
        self.recommendations_listbox.delete(0, tk.END)
        for rec in report.recommendations:
            self.recommendations_listbox.insert(tk.END, rec)
        
        # Update alternative colors
        self._display_alternative_colors(report.alternative_colors)
    
    def _display_alternative_colors(self, alternatives: List[ColorData]):
        """Display alternative color suggestions"""
        # Clear existing alternatives
        for widget in self.alternatives_frame.winfo_children():
            widget.destroy()
        
        if not alternatives:
            ttk.Label(self.alternatives_frame, 
                     text="No alternatives needed - colors are accessible").pack()
            return
        
        ttk.Label(self.alternatives_frame, 
                 text="Suggested accessible alternatives:").pack(anchor='w')
        
        colors_frame = ttk.Frame(self.alternatives_frame)
        colors_frame.pack(fill='x', pady=(5, 0))
        
        for i, color in enumerate(alternatives):
            color_frame = ttk.Frame(colors_frame)
            color_frame.pack(side='left', padx=(0, 10))
            
            # Color swatch
            canvas = tk.Canvas(color_frame, width=40, height=30, 
                             bg=color.hex, relief='solid', borderwidth=1)
            canvas.pack()
            
            # Color code
            ttk.Label(color_frame, text=color.hex, font=('Arial', 8)).pack()
            
            # Use button
            ttk.Button(color_frame, text="Use", 
                      command=lambda c=color: self._use_alternative_color(c)).pack()
        
        # Update scroll region
        self.alternatives_frame.update_idletasks()
        self.alternatives_canvas.configure(scrollregion=self.alternatives_canvas.bbox("all"))
    
    def _use_alternative_color(self, color: ColorData):
        """Use an alternative color as the foreground"""
        self.foreground_color = color
        self._update_color_display(self.fg_color_canvas, self.fg_color_label, color)
        self._analyze_colors()
        
        # Notify other components about the color change
        self.event_bus.publish('color_selected', color)
    
    def _generate_full_report(self):
        """Generate and display full accessibility report"""
        if not self.current_report:
            messagebox.showwarning("No Analysis", "Please analyze colors first")
            return
        
        # Create report window
        self._show_full_report_window()
    
    def _show_full_report_window(self):
        """Show detailed accessibility report in new window"""
        report_window = tk.Toplevel(self)
        report_window.title("Accessibility Report")
        report_window.geometry("600x500")
        
        # Create scrollable text widget
        text_frame = ttk.Frame(report_window)
        text_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        text_widget = tk.Text(text_frame, wrap='word', font=('Arial', 10))
        scrollbar = ttk.Scrollbar(text_frame, orient='vertical', command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Generate report content
        report_content = self._generate_report_content()
        text_widget.insert('1.0', report_content)
        text_widget.configure(state='disabled')
        
        # Close button
        ttk.Button(report_window, text="Close", 
                  command=report_window.destroy).pack(pady=10)
    
    def _generate_report_content(self) -> str:
        """Generate detailed report content"""
        if not self.current_report:
            return "No analysis available"
        
        report = self.current_report
        contrast = report.contrast_result
        
        content = f"""ACCESSIBILITY ANALYSIS REPORT
{'=' * 50}

COLORS ANALYZED:
Foreground: {report.foreground_color.hex} (RGB: {report.foreground_color.rgb})
Background: {report.background_color.hex} (RGB: {report.background_color.rgb})

CONTRAST ANALYSIS:
Contrast Ratio: {contrast.ratio}:1

WCAG COMPLIANCE:
AA Normal Text (4.5:1): {'✅ PASS' if contrast.passes_aa_normal else '❌ FAIL'}
AA Large Text (3:1): {'✅ PASS' if contrast.passes_aa_large else '❌ FAIL'}
AAA Normal Text (7:1): {'✅ PASS' if contrast.passes_aaa_normal else '❌ FAIL'}
AAA Large Text (4.5:1): {'✅ PASS' if contrast.passes_aaa_large else '❌ FAIL'}

Overall Grade: {self.accessibility_service._calculate_overall_grade(contrast)}

RECOMMENDATION:
{contrast.recommendation}

ADDITIONAL RECOMMENDATIONS:
"""
        
        for i, rec in enumerate(report.recommendations, 1):
            content += f"{i}. {rec}\n"
        
        if report.alternative_colors:
            content += f"\nACCESSIBLE ALTERNATIVES:\n"
            for i, color in enumerate(report.alternative_colors, 1):
                alt_contrast = self.accessibility_service.calculate_contrast_ratio(
                    color, report.background_color
                )
                content += f"{i}. {color.hex} (Contrast: {alt_contrast}:1)\n"
        
        content += f"\nCOLOR BLIND SAFETY: {'✅ Safe' if report.color_blind_safe else '⚠️ May be difficult'}\n"
        
        return content
    
    def _export_report(self):
        """Export accessibility report to file"""
        if not self.current_report:
            messagebox.showwarning("No Analysis", "Please analyze colors first")
            return
        
        from tkinter import filedialog
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="Export Accessibility Report"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self._generate_report_content())
                messagebox.showinfo("Export Successful", 
                                  f"Report exported to {filename}")
            except Exception as e:
                messagebox.showerror("Export Error", 
                                   f"Failed to export report: {str(e)}")
    
    def _clear_analysis(self):
        """Clear current analysis"""
        self.foreground_color = None
        self.background_color = None
        self.current_report = None
        
        # Reset UI
        self.fg_color_canvas.configure(bg='white')
        self.bg_color_canvas.configure(bg='white')
        self.fg_color_label.configure(text="Not selected")
        self.bg_color_label.configure(text="Not selected")
        
        self.contrast_ratio_var.set("N/A")
        self.aa_normal_var.set("❌")
        self.aa_large_var.set("❌")
        self.aaa_normal_var.set("❌")
        self.aaa_large_var.set("❌")
        self.overall_grade_var.set("N/A")
        self.grade_label.configure(foreground='black')
        self.recommendation_var.set("Select colors to analyze")
        
        self.recommendations_listbox.delete(0, tk.END)
        
        # Clear alternatives
        for widget in self.alternatives_frame.winfo_children():
            widget.destroy()
    
    def set_colors_for_analysis(self, foreground: ColorData, background: ColorData):
        """Set colors for analysis programmatically"""
        self.foreground_color = foreground
        self.background_color = background
        
        self._update_color_display(self.fg_color_canvas, self.fg_color_label, foreground)
        self._update_color_display(self.bg_color_canvas, self.bg_color_label, background)
        
        self._analyze_colors()
    
    def get_current_analysis(self) -> Optional[AccessibilityReport]:
        """Get current accessibility analysis report"""
        return self.current_report