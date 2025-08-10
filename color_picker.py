import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import os
import json
import platform
try:
    import sv_ttk  # Opsiyonel modern ttk teması
except Exception:
    sv_ttk = None
try:
    import ctypes  # Windows DPI farkındalığı
except Exception:
    ctypes = None

class ColorPicker:
    def __init__(self, root):
        self.root = root
        self.root.title("Gelişmiş Renk Seçici - Advanced Color Picker")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 600)
        self.setup_high_dpi()
        
        # Tema paletleri
        self.dark_colors = {
            'bg': '#1e1e1e',
            'fg': '#ffffff',
            'panel_bg': '#2d2d2d',
            'button_bg': '#3a3a3a',
            'button_hover': '#4a4a4a',
            'accent': '#0078d4',
            'success': '#107c10',
            'danger': '#d13438',
            'warning': '#ff8c00',
            'canvas_bg': '#3c3c3c',
            'entry_bg': '#3c3c3c',
            'entry_fg': '#ffffff',
            'border': '#555555'
        }
        self.light_colors = {
            'bg': '#f5f6f7',
            'fg': '#1e1e1e',
            'panel_bg': '#ffffff',
            'button_bg': '#e9e9e9',
            'button_hover': '#dedede',
            'accent': '#0078d4',
            'success': '#107c10',
            'danger': '#d13438',
            'warning': '#ff8c00',
            'canvas_bg': '#f0f0f0',
            'entry_bg': '#ffffff',
            'entry_fg': '#1e1e1e',
            'border': '#d0d0d0'
        }
        self.current_theme = 'dark'
        self.colors = dict(self.dark_colors)
        self.sv_ttk_available = sv_ttk is not None
        
        self.root.configure(bg=self.colors['bg'])
        self.create_style()
        
        # Ana değişkenler
        self.original_image = None
        self.display_image = None
        self.photo = None
        self.canvas = None
        self.zoom_level = 1.0
        self.color_history = []
        self.max_history = 20
        
        # Pan (kaydırma) değişkenleri
        self.pan_offset_x = 0
        self.pan_offset_y = 0
        self.last_pan_x = 0
        self.last_pan_y = 0
        self.is_panning = False
        
        # Menü ve UI oluştur
        self.create_menubar()
        self.create_widgets()
        self.bind_common_shortcuts()
        
        # Responsive design için event binding
        self.root.bind('<Configure>', self.on_window_resize)
    
    def create_widgets(self):
        # Başlık
        self.title_label = tk.Label(self.root, text="🎨 Gelişmiş Renk Seçici - Advanced Color Picker", 
                              font=("Segoe UI", 18, "bold"), bg=self.colors['bg'], fg=self.colors['fg'])
        self.title_label.pack(pady=12)
        
        # Üst çerçeve - butonlar
        top_frame = tk.Frame(self.root, bg=self.colors['bg'])
        top_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        self.top_frame = top_frame
        
        # Resim yükleme butonu
        self.load_btn = tk.Button(top_frame, text="🖼️ Resim Yükle", 
                                 command=self.load_image,
                                 font=("Segoe UI", 12, "bold"),
                                 bg=self.colors['success'], fg='white',
                                 padx=20, pady=8,
                                 cursor='hand2', relief=tk.FLAT)
        self.load_btn.pack(side=tk.LEFT, padx=10)
        self.bind_button_hover(self.load_btn, self.colors['success'])
        
        # Zoom butonları
        zoom_frame = tk.Frame(top_frame, bg=self.colors['bg'])
        zoom_frame.pack(side=tk.LEFT, padx=20)
        self.zoom_frame = zoom_frame
        
        self.zoom_in_btn = tk.Button(zoom_frame, text="🔍+", 
                                    command=self.zoom_in,
                                    font=("Segoe UI", 10, "bold"),
                                    bg=self.colors['accent'], fg='white',
                                    padx=15, pady=5,
                                    cursor='hand2', relief=tk.FLAT)
        self.zoom_in_btn.pack(side=tk.LEFT, padx=5)
        self.bind_button_hover(self.zoom_in_btn, self.colors['accent'])
        
        self.zoom_out_btn = tk.Button(zoom_frame, text="🔍-", 
                                     command=self.zoom_out,
                                     font=("Segoe UI", 10, "bold"),
                                     bg=self.colors['accent'], fg='white',
                                     padx=15, pady=5,
                                     cursor='hand2', relief=tk.FLAT)
        self.zoom_out_btn.pack(side=tk.LEFT, padx=5)
        self.bind_button_hover(self.zoom_out_btn, self.colors['accent'])
        
        self.zoom_reset_btn = tk.Button(zoom_frame, text="🔄 Sıfırla", 
                                       command=self.zoom_reset,
                                       font=("Segoe UI", 10, "bold"),
                                       bg=self.colors['warning'], fg='white',
                                       padx=15, pady=5,
                                       cursor='hand2', relief=tk.FLAT)
        self.zoom_reset_btn.pack(side=tk.LEFT, padx=5)
        self.bind_button_hover(self.zoom_reset_btn, self.colors['warning'])
        
        # Temizle butonu
        self.clear_btn = tk.Button(top_frame, text="🗑️ Temizle", 
                                  command=self.clear_image,
                                  font=("Segoe UI", 12, "bold"),
                                  bg=self.colors['danger'], fg='white',
                                  padx=20, pady=8,
                                  cursor='hand2', relief=tk.FLAT)
        self.clear_btn.pack(side=tk.RIGHT, padx=10)
        self.bind_button_hover(self.clear_btn, self.colors['danger'])

        # Tema butonu
        self.theme_btn = tk.Button(top_frame, text="🌗 Tema", 
                                   command=self.toggle_theme,
                                   font=("Segoe UI", 12, "bold"),
                                   bg=self.colors['button_bg'], fg='white',
                                   padx=16, pady=8,
                                   cursor='hand2', relief=tk.FLAT)
        self.theme_btn.pack(side=tk.RIGHT, padx=10)
        self.bind_button_hover(self.theme_btn, self.colors['button_bg'])
        
        # Ana bölücü (PanedWindow) - modern, yeniden boyutlandırılabilir düzen
        self.main_paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, sashwidth=8, sashrelief=tk.FLAT, bg=self.colors['bg'])
        self.main_paned.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Sol taraf - resim görüntüleme
        self.left_frame = tk.Frame(self.main_paned, bg=self.colors['bg'])
        self.main_paned.add(self.left_frame, minsize=280, stretch="always")
        
        # Canvas çerçevesi
        self.canvas_frame = tk.Frame(self.left_frame, bg=self.colors['border'], relief=tk.SUNKEN, bd=2)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True, padx=(0, 20))
        
        # Canvas
        self.canvas = tk.Canvas(self.canvas_frame, bg=self.colors['canvas_bg'], cursor='crosshair', highlightthickness=0, bd=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Canvas olayları
        self.canvas.bind("<Button-1>", self.get_color)
        self.canvas.bind("<Motion>", self.show_coordinates)
        
        # Pan (kaydırma) olayları - sağ tık ile
        self.canvas.bind("<Button-3>", self.start_pan)
        self.canvas.bind("<B3-Motion>", self.do_pan)
        self.canvas.bind("<ButtonRelease-3>", self.end_pan)
        
        # Mouse wheel ile zoom
        self.canvas.bind("<MouseWheel>", self.mouse_wheel_zoom)
        
        # Klavye kısayolları
        self.canvas.bind("<Control-c>", self.copy_current_color)
        self.canvas.focus_set()
        
        # Sağ taraf - kontrol paneli
        self.right_frame = tk.Frame(self.main_paned, bg=self.colors['bg'], width=360)
        self.main_paned.add(self.right_frame, minsize=300)
        self.right_frame.pack_propagate(False)
        
        # Notebook için tab sistemi (özel stil)
        self.notebook = ttk.Notebook(self.right_frame, style='Modern.TNotebook', takefocus=0, padding=0)
        try:
            self.notebook.configure(highlightthickness=0)
        except Exception:
            pass
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=10)
        # Klavye odağını notebook'tan uzak tut (noktalı odak çerçevesini gizler)
        self.notebook.bind('<FocusIn>', lambda e: (self.canvas.focus_set() if hasattr(self, 'canvas') else None))
        self.notebook.bind('<Button-1>', lambda e: self.root.after(1, lambda: (self.canvas.focus_set() if hasattr(self, 'canvas') else None)))
        
        # Stil ayarları (temel) - Modern stil zaten oluşturuldu
        
        # Renk bilgileri sekmesi
        self.color_info_tab = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(self.color_info_tab, text="🎨 Renk Bilgileri")
        
        # Renk geçmişi sekmesi  
        self.history_tab = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(self.history_tab, text="📋 Geçmiş")
        
        # Yardım sekmesi
        self.help_tab = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(self.help_tab, text="❓ Yardım")
        
        # Renk bilgileri tab içeriği
        self.create_color_info_tab()
        
        # Renk geçmişi tab içeriği
        self.create_history_tab()
        
        # Yardım tab içeriği
        self.create_help_tab()
        
        # Durum çubuğu
        if not hasattr(self, 'status_var'):
            self.status_var = tk.StringVar(value="Hazır")
        self.status_bar = tk.Label(self.root, textvariable=self.status_var, anchor=tk.W,
                                   font=("Segoe UI", 10), bg=self.colors['panel_bg'], fg=self.colors['fg'])
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
    
    def create_color_info_tab(self):
        """Renk bilgileri sekmesi içeriğini oluştur"""
        # Ana container
        main_container = tk.Frame(self.color_info_tab, bg=self.colors['bg'])
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Scrollable frame yapısı
        canvas_scroll = tk.Canvas(main_container, bg=self.colors['bg'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=canvas_scroll.yview)
        scrollable_frame = tk.Frame(canvas_scroll, bg=self.colors['bg'])
        
        # Scrollable frame'i canvas'a bağla
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas_scroll.configure(scrollregion=canvas_scroll.bbox("all"))
        )
        
        # Canvas'a frame'i ekle
        canvas_window = canvas_scroll.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas_scroll.configure(yscrollcommand=scrollbar.set)
        
        # Canvas genişliğini frame genişliğine uyarla
        def configure_canvas(event):
            canvas_scroll.itemconfig(canvas_window, width=event.width)
        
        canvas_scroll.bind('<Configure>', configure_canvas)
        
        # Mouse wheel desteği
        def on_mousewheel(event):
            canvas_scroll.yview_scroll(int(-1*(event.delta/120)), "units")
            return "break"  # Event propagation'ı durdur
        
        # Tüm widget'lara mouse wheel desteği ekle
        def bind_mousewheel(widget):
            widget.bind("<MouseWheel>", on_mousewheel)
            for child in widget.winfo_children():
                bind_mousewheel(child)
        
        canvas_scroll.bind("<MouseWheel>", on_mousewheel)
        scrollable_frame.bind("<MouseWheel>", on_mousewheel)
        
        # Focus event'leri ile mouse wheel'i aktif et
        def on_enter(event):
            canvas_scroll.focus_set()
        
        def on_leave(event):
            self.root.focus_set()
        
        canvas_scroll.bind("<Enter>", on_enter)
        canvas_scroll.bind("<Leave>", on_leave)
        scrollable_frame.bind("<Enter>", on_enter)
        
        # Pack scrollbar ve canvas
        scrollbar.pack(side="right", fill="y")
        canvas_scroll.pack(side="left", fill="both", expand=True)
        
        # Koordinat bilgisi
        coord_frame = tk.LabelFrame(scrollable_frame, text="📍 Koordinat Bilgisi", 
                                   font=("Segoe UI", 12, "bold"),
                                   bg=self.colors['panel_bg'], fg=self.colors['fg'])
        coord_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(coord_frame, text="Mouse Koordinatları:", 
                font=("Segoe UI", 10, "bold"), bg=self.colors['panel_bg'], fg=self.colors['fg']).pack(anchor=tk.W, padx=10, pady=5)
        
        self.coord_label = tk.Label(coord_frame, text="X: -, Y: -", 
                                   font=("Segoe UI", 10), bg=self.colors['panel_bg'], fg=self.colors['fg'])
        self.coord_label.pack(anchor=tk.W, padx=10, pady=5)
        
        # Zoom bilgisi
        zoom_info_frame = tk.LabelFrame(scrollable_frame, text="🔍 Zoom Bilgisi", 
                                       font=("Segoe UI", 12, "bold"),
                                       bg=self.colors['panel_bg'], fg=self.colors['fg'])
        zoom_info_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(zoom_info_frame, text="Zoom Seviyesi:", 
                font=("Segoe UI", 10, "bold"), bg=self.colors['panel_bg'], fg=self.colors['fg']).pack(anchor=tk.W, padx=10, pady=5)
        
        self.zoom_label = tk.Label(zoom_info_frame, text="100%", 
                                  font=("Segoe UI", 10), bg=self.colors['panel_bg'], fg=self.colors['fg'])
        self.zoom_label.pack(anchor=tk.W, padx=10, pady=5)
        
        # Seçilen renk gösterimi
        color_display_frame = tk.LabelFrame(scrollable_frame, text="🎨 Seçilen Renk", 
                                           font=("Segoe UI", 12, "bold"),
                                           bg=self.colors['panel_bg'], fg=self.colors['fg'])
        color_display_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.color_display = tk.Frame(color_display_frame, height=80, bg='white', relief=tk.SUNKEN, bd=2)
        self.color_display.pack(fill=tk.X, padx=10, pady=10)
        
        # RGB değerleri
        rgb_frame = tk.LabelFrame(scrollable_frame, text="📊 RGB Değerleri", 
                                 font=("Segoe UI", 12, "bold"),
                                 bg=self.colors['panel_bg'], fg=self.colors['fg'])
        rgb_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.rgb_label = tk.Label(rgb_frame, text="R: -, G: -, B: -", 
                                 font=("Segoe UI", 12, "bold"), bg=self.colors['panel_bg'], fg=self.colors['fg'])
        self.rgb_label.pack(anchor=tk.W, padx=10, pady=10)
        
        # RGB kopyalama butonu
        self.copy_rgb_btn = tk.Button(rgb_frame, text="📋 RGB Kopyala", 
                                     command=self.copy_rgb,
                                     font=("Segoe UI", 10, "bold"),
                                     bg=self.colors['accent'], fg='white',
                                     cursor='hand2', relief=tk.FLAT)
        self.copy_rgb_btn.pack(fill=tk.X, padx=10, pady=5)
        
        # HEX değeri
        hex_frame = tk.LabelFrame(scrollable_frame, text="🔢 HEX Kodu", 
                                 font=("Segoe UI", 12, "bold"),
                                 bg=self.colors['panel_bg'], fg=self.colors['fg'])
        hex_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.hex_entry = tk.Entry(hex_frame, font=("Segoe UI", 12, "bold"), justify=tk.CENTER,
                                 bg=self.colors['entry_bg'], fg=self.colors['entry_fg'],
                                 insertbackground=self.colors['entry_fg'])
        self.hex_entry.pack(fill=tk.X, padx=10, pady=10)
        
        # HEX kopyalama butonu
        self.copy_hex_btn = tk.Button(hex_frame, text="📋 HEX Kopyala", 
                                     command=self.copy_hex,
                                     font=("Segoe UI", 10, "bold"),
                                     bg=self.colors['success'], fg='white',
                                     cursor='hand2', relief=tk.FLAT)
        self.copy_hex_btn.pack(fill=tk.X, padx=10, pady=5)
        
        # Tüm child widget'lara mouse wheel desteği ekle
        def apply_mousewheel_to_children(widget):
            try:
                widget.bind("<MouseWheel>", on_mousewheel)
            except:
                pass
            for child in widget.winfo_children():
                apply_mousewheel_to_children(child)
        
        # Scrollable frame ve tüm children'a mouse wheel uygula
        self.color_info_tab.after(100, lambda: apply_mousewheel_to_children(scrollable_frame))
    
    def create_history_tab(self):
        """Renk geçmişi sekmesi içeriğini oluştur"""
        # Başlık
        title_label = tk.Label(self.history_tab, text="🕒 Renk Geçmişi", 
                              font=("Segoe UI", 14, "bold"), bg=self.colors['bg'], fg=self.colors['fg'])
        title_label.pack(pady=10)
        
        # Temizle butonu
        clear_history_btn = tk.Button(self.history_tab, text="🗑️ Geçmişi Temizle", 
                                     command=self.clear_history,
                                     font=("Segoe UI", 10, "bold"),
                                     bg=self.colors['danger'], fg='white',
                                     cursor='hand2', relief=tk.FLAT)
        clear_history_btn.pack(pady=5)
        
        # Açıklama
        info_label = tk.Label(self.history_tab, text="Renk seçmek için listedeki öğeye tıklayın:", 
                             font=("Segoe UI", 9), bg=self.colors['bg'], fg=self.colors['fg'])
        info_label.pack(pady=5)
        
        # Ana container
        main_container = tk.Frame(self.history_tab, bg=self.colors['bg'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Scrollable liste için frame
        list_frame = tk.Frame(main_container, bg=self.colors['panel_bg'], relief=tk.SUNKEN, bd=1)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar
        scrollbar_history = ttk.Scrollbar(list_frame, orient=tk.VERTICAL)
        scrollbar_history.pack(side=tk.RIGHT, fill=tk.Y)
        
        # History listbox
        self.history_listbox = tk.Listbox(list_frame, 
                                         yscrollcommand=scrollbar_history.set,
                                         bg=self.colors['panel_bg'], 
                                         fg=self.colors['fg'],
                                         font=("Segoe UI", 10),
                                         selectbackground=self.colors['accent'],
                                         selectforeground='white',
                                         relief=tk.FLAT,
                                         highlightthickness=0,
                                         activestyle='none')
        self.history_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar_history.config(command=self.history_listbox.yview)
        
        # Event'leri bind et
        self.history_listbox.bind('<<ListboxSelect>>', self.on_history_select)
        
        # Mouse wheel event'ini sadece listbox'a bind et
        def on_history_mousewheel(event):
            self.history_listbox.yview_scroll(int(-1*(event.delta/120)), "units")
            return "break"  # Event propagation'ı durdur
        
        self.history_listbox.bind("<MouseWheel>", on_history_mousewheel)
        
        # Çift tıklama ile renk seçimi
        self.history_listbox.bind('<Double-Button-1>', self.on_history_double_click)
    
    def create_help_tab(self):
        """Yardım sekmesi içeriğini oluştur"""
        # Scrollable text
        help_frame = tk.Frame(self.help_tab, bg=self.colors['bg'])
        help_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        help_text = tk.Text(help_frame, wrap=tk.WORD, 
                           bg=self.colors['panel_bg'], fg=self.colors['fg'],
                           font=("Segoe UI", 10), relief=tk.FLAT)
        help_text.pack(fill=tk.BOTH, expand=True)
        
        help_content = """
🎨 GELIŞMIŞ RENK SEÇİCİ KULLANIM KILAVUZU

📋 TEMEL KULLANIM:
1. "Resim Yükle" butonuna tıklayın
2. Desteklenen formatlardan bir resim seçin
   (PNG, JPEG, GIF, BMP, TIFF)
3. Resim yüklendikten sonra istediğiniz noktaya tıklayın
4. Renk kodları otomatik olarak gösterilecek

🔍 ZOOM ÖZELLİKLERİ:
• 🔍+ : Resmi büyütür (maksimum %500)
• 🔍- : Resmi küçültür (minimum %10)
• 🔄 Sıfırla : Orijinal boyuta döner ve pan sıfırlar
• 🖱️ Mouse Wheel : Tekerlek ile zoom yapın

🎯 PAN (KAYDIRMA) ÖZELLİKLERİ:
• Sağ tık + sürükle ile resmi kaydırın
• Büyütülmüş resimlerde gezinmek için kullanın
• Zoom sıfırlandığında pan da sıfırlanır

📊 RENK BİLGİLERİ:
• RGB değerleri (0-255 arası)
• HEX kodu (#RRGGBB formatında)
• Renk önizlemesi (büyük gösterim)
• Koordinat bilgisi (gerçek zamanlı)
• Zoom seviyesi gösterimi

📋 KOPYALAMA ÖZELLİKLERİ:
• RGB kodunu kopyalayın
• HEX kodunu kopyalayın
• Ctrl+C ile hızlı kopyalama
• Tek tıkla panoya kopyalama

🕒 RENK GEÇMİŞİ:
• Son 20 seçtiğiniz renk otomatik kaydedilir
• Çift tıklama ile geçmişten renk seçebilirsiniz
• Geçmişi temizleyebilirsiniz
• Renk bilgileri listelenir (HEX ve RGB)
• Seçim yapıldığında otomatik olarak Renk Bilgileri sekmesine geçer

⚡ KISAYOLLAR:
• 🖱️ Mouse Wheel: Zoom in/out
• 🖱️ Sağ Tık + Sürükle: Pan (kaydırma)
• Ctrl+C: Aktif renk kodunu kopyala
• 🖱️ Sol Tık: Renk seç

🎯 İPUÇLARI:
• Yüksek çözünürlüklü resimler daha doğru renk seçimi sağlar
• Zoom özelliği ile piksel seviyesinde hassas seçim yapabilirsiniz
• Pan özelliği ile büyük resimlerde kolayca gezinebilirsiniz
• Renk geçmişi özelliği ile önceki seçimlerinizi takip edebilirsiniz

🎨 GELİŞMİŞ ÖZELLİKLER:
• Responsive tasarım - pencere boyutuna uyum sağlar
• Koyu tema - göz dostu arayüz
• Sekmeli düzen - organize edilmiş kontroller
• Çoklu format desteği - tüm popüler resim formatları

❓ SORUN GİDERME:
• Resim yüklenmiyorsa format kontrolü yapın
• Büyük resimler yüklenirken biraz bekleyin
• Zoom seviyesi çok yüksekse "Sıfırla" butonunu kullanın
• Pan ile resim kaybolursa "Sıfırla" butonunu kullanın

💡 Daha fazla bilgi için: github.com/yourproject
        """
        
        help_text.insert(tk.END, help_content)
        help_text.config(state=tk.DISABLED)
        
        # Yardım text widget'ına mouse wheel desteği
        def on_help_mousewheel(event):
            help_text.yview_scroll(int(-1*(event.delta/120)), "units")
            return "break"
        
        help_text.bind("<MouseWheel>", on_help_mousewheel)
        help_frame.bind("<MouseWheel>", on_help_mousewheel)
    
    def on_window_resize(self, event):
        """Pencere boyutu değiştiğinde çağrılır"""
        if event.widget == self.root and self.original_image:
            self.root.after(100, self.display_image_on_canvas)
    
    def zoom_in(self):
        """Resmi büyüt"""
        if self.original_image:
            self.zoom_level = min(self.zoom_level * 1.2, 5.0)
            self.display_image_on_canvas()
            self.update_zoom_label()
    
    def zoom_out(self):
        """Resmi küçült"""
        if self.original_image:
            self.zoom_level = max(self.zoom_level / 1.2, 0.1)
            self.display_image_on_canvas()
            self.update_zoom_label()
    
    def zoom_reset(self):
        """Zoom seviyesini sıfırla"""
        if self.original_image:
            self.zoom_level = 1.0
            self.pan_offset_x = 0
            self.pan_offset_y = 0
            self.display_image_on_canvas()
            self.update_zoom_label()
    
    def update_zoom_label(self):
        """Zoom label'ını güncelle"""
        if hasattr(self, 'zoom_label'):
            self.zoom_label.config(text=f"{int(self.zoom_level * 100)}%")
    
    def start_pan(self, event):
        """Pan (kaydırma) işlemini başlat"""
        if self.original_image and self.display_image and self.canvas:
            self.is_panning = True
            self.last_pan_x = event.x
            self.last_pan_y = event.y
            self.canvas.config(cursor="fleur")  # Hareket cursor'u
    
    def do_pan(self, event):
        """Pan (kaydırma) işlemini gerçekleştir"""
        if self.is_panning and self.original_image:
            # Hareket miktarını hesapla
            dx = event.x - self.last_pan_x
            dy = event.y - self.last_pan_y
            
            # Pan offset'lerini güncelle
            self.pan_offset_x += dx
            self.pan_offset_y += dy
            
            # Son konumu kaydet
            self.last_pan_x = event.x
            self.last_pan_y = event.y
            
            # Resmi yeniden çiz
            self.display_image_on_canvas()
    
    def end_pan(self, event):
        """Pan (kaydırma) işlemini bitir"""
        self.is_panning = False
        if self.canvas:
            self.canvas.config(cursor="crosshair")  # Normal cursor'a dön
    
    def mouse_wheel_zoom(self, event):
        """Mouse wheel ile zoom yap"""
        if self.original_image:
            # Mouse wheel yönünü kontrol et
            if event.delta > 0:
                # Yukarı - büyüt
                self.zoom_level = min(self.zoom_level * 1.1, 5.0)
            else:
                # Aşağı - küçült
                self.zoom_level = max(self.zoom_level / 1.1, 0.1)
            
            self.display_image_on_canvas()
            self.update_zoom_label()
    
    def copy_current_color(self, event):
        """Ctrl+C ile aktif renk kodunu kopyala"""
        if hasattr(self, 'hex_entry'):
            hex_value = self.hex_entry.get()
            if hex_value:
                self.root.clipboard_clear()
                self.root.clipboard_append(hex_value)
                self.show_toast(f"Renk kodu kopyalandı: {hex_value}", kind="success")
                self.update_status(f"Kopyalandı: {hex_value}")
    
    def copy_rgb(self):
        """RGB kodunu panoya kopyala"""
        if hasattr(self, 'rgb_label'):
            rgb_text = self.rgb_label.cget('text')
            if rgb_text and rgb_text != "R: -, G: -, B: -":
                self.root.clipboard_clear()
                self.root.clipboard_append(rgb_text)
                self.show_toast(f"RGB kopyalandı: {rgb_text}", kind="success")
                self.update_status(f"Kopyalandı: {rgb_text}")
    
    def clear_history(self):
        """Renk geçmişini temizle"""
        try:
            self.color_history = []
            self.update_history_display()
            self.show_toast("Renk geçmişi temizlendi.")
            self.update_status("Renk geçmişi temizlendi.")
        except Exception as e:
            print(f"Geçmiş temizleme hatası: {e}")
    
    def on_history_select(self, event):
        """Geçmişten renk seçildiğinde"""
        # Sadece çift tıklama ile seçim yapalım, tek tıklama ile sadece highlight
        pass
    
    def on_history_double_click(self, event):
        """Geçmişten çift tıklama ile renk seçimi"""
        selection = self.history_listbox.curselection()
        if selection:
            index = selection[0]
            if index < len(self.color_history):
                color_info = self.color_history[index]
                self.update_color_info(color_info['rgb'])
                # Renk Bilgileri sekmesine geç
                self.notebook.select(0)
    
    def add_to_history(self, color_rgb, hex_code):
        """Renk geçmişine ekle"""
        try:
            color_info = {
                'rgb': color_rgb,
                'hex': hex_code,
                'timestamp': f"{len(self.color_history) + 1:02d}"
            }
            
            # Aynı renk varsa çıkar
            self.color_history = [c for c in self.color_history if c['hex'] != hex_code]
            
            # Başa ekle
            self.color_history.insert(0, color_info)
            
            # Maksimum sayıyı aşma
            if len(self.color_history) > self.max_history:
                self.color_history = self.color_history[:self.max_history]
            
            # Listbox'u güncelle
            self.update_history_display()
            
        except Exception as e:
            print(f"Geçmiş ekleme hatası: {e}")
    
    def update_history_display(self):
        """Geçmiş listesini güncelle"""
        if hasattr(self, 'history_listbox') and self.history_listbox:
            try:
                # Mevcut selection'ı koru
                current_selection = self.history_listbox.curselection()
                
                # Listeyi temizle
                self.history_listbox.delete(0, tk.END)
                
                # Yeni öğeleri ekle
                for i, color in enumerate(self.color_history):
                    r, g, b = color['rgb']
                    display_text = f"🎨 {color['hex']} • RGB({r}, {g}, {b})"
                    self.history_listbox.insert(tk.END, display_text)
                
                # Eğer liste boş değilse en son eklenen öğeyi göster
                if self.color_history:
                    self.history_listbox.selection_set(0)
                    self.history_listbox.see(0)
                    
            except Exception as e:
                print(f"Geçmiş güncelleme hatası: {e}")
    
    def load_image(self):
        """Resim yükleme fonksiyonu"""
        file_path = filedialog.askopenfilename(
            title="Resim Seçin",
            filetypes=[
                ("Resim Dosyaları", "*.png *.jpg *.jpeg *.gif *.bmp *.tiff"),
                ("PNG", "*.png"),
                ("JPEG", "*.jpg *.jpeg"),
                ("Tüm Dosyalar", "*.*")
            ]
        )
        
        if file_path:
            try:
                # Resmi yükle
                self.original_image = Image.open(file_path)
                self.display_image_on_canvas()
                self.show_toast("Resim yüklendi. Renk seçmek için tıklayın.", kind="success")
                self.update_status(f"Yüklendi: {os.path.basename(file_path)}")
                
            except Exception as e:
                messagebox.showerror("Hata", f"Resim yüklenirken hata oluştu:\n{str(e)}")
    
    def display_image_on_canvas(self):
        """Resmi canvas üzerinde göster"""
        if self.original_image and self.canvas:
            # Canvas boyutlarını al
            self.canvas.update()
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            
            if canvas_width <= 1 or canvas_height <= 1:
                return
            
            # Resmi canvas boyutlarına göre ölçeklendir
            img_width, img_height = self.original_image.size
            
            # Zoom faktörünü uygula
            effective_width = int(img_width * self.zoom_level)
            effective_height = int(img_height * self.zoom_level)
            
            # Orantılı ölçeklendirme
            scale_w = canvas_width / effective_width
            scale_h = canvas_height / effective_height
            scale = min(scale_w, scale_h, 1.0)
            
            new_width = int(effective_width * scale)
            new_height = int(effective_height * scale)
            
            # Resmi ölçeklendir
            self.display_image = self.original_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Tkinter için PhotoImage'e çevir
            self.photo = ImageTk.PhotoImage(self.display_image)
            
            # Canvas'ı temizle ve resmi pan offset'leri ile birlikte yerleştir
            self.canvas.delete("all")
            base_x = (canvas_width - new_width) // 2
            base_y = (canvas_height - new_height) // 2
            
            # Pan offset'lerini uygula
            x = base_x + self.pan_offset_x
            y = base_y + self.pan_offset_y
            
            self.canvas.create_image(x, y, anchor=tk.NW, image=self.photo)
            
            # Resmin gerçek konumunu kaydet
            self.image_x = x
            self.image_y = y
            self.base_x = base_x
            self.base_y = base_y
            self.scale_factor = scale * self.zoom_level
    
    def get_color(self, event):
        """Tıklanan noktanın rengini al"""
        if self.original_image and self.display_image:
            try:
                # Canvas üzerindeki koordinatları al
                canvas_x = event.x
                canvas_y = event.y
                
                # Resmin gerçek konumunu kontrol et
                if (canvas_x >= self.image_x and canvas_x < self.image_x + self.display_image.width and
                    canvas_y >= self.image_y and canvas_y < self.image_y + self.display_image.height):
                    
                    # Resim üzerindeki göreli koordinatları hesapla
                    rel_x = canvas_x - self.image_x
                    rel_y = canvas_y - self.image_y
                    
                    # Orijinal resim koordinatlarına çevir
                    orig_x = int(rel_x / self.scale_factor)
                    orig_y = int(rel_y / self.scale_factor)
                    
                    # Koordinatları sınırla
                    orig_x = max(0, min(orig_x, self.original_image.width - 1))
                    orig_y = max(0, min(orig_y, self.original_image.height - 1))
                    
                    # Renk değerini al
                    color = self.original_image.getpixel((orig_x, orig_y))
                    
                    # RGB formatında değilse dönüştür
                    if isinstance(color, int):  # Grayscale
                        color = (color, color, color)
                    elif isinstance(color, tuple) and len(color) == 4:  # RGBA
                        color = color[:3]  # Alpha kanalını kaldır
                    elif not isinstance(color, tuple):
                        color = (0, 0, 0)  # Varsayılan renk
                    
                    # Renk bilgilerini güncelle
                    self.update_color_info(color)
                    
            except Exception as e:
                messagebox.showerror("Hata", f"Renk alınırken hata oluştu:\n{str(e)}")
    
    def show_coordinates(self, event):
        """Mouse koordinatlarını göster"""
        if self.original_image and self.display_image:
            canvas_x = event.x
            canvas_y = event.y
            
            # Resmin içinde mi kontrol et
            if (canvas_x >= self.image_x and canvas_x < self.image_x + self.display_image.width and
                canvas_y >= self.image_y and canvas_y < self.image_y + self.display_image.height):
                
                rel_x = canvas_x - self.image_x
                rel_y = canvas_y - self.image_y
                
                # Orijinal resim koordinatlarına çevir
                orig_x = int(rel_x / self.scale_factor)
                orig_y = int(rel_y / self.scale_factor)
                
                self.coord_label.config(text=f"X: {orig_x}, Y: {orig_y}")
            else:
                self.coord_label.config(text="X: -, Y: -")
        else:
            self.coord_label.config(text="X: -, Y: -")
    
    def update_color_info(self, color):
        """Renk bilgilerini güncelle"""
        r, g, b = color
        
        # RGB değerleri
        if hasattr(self, 'rgb_label'):
            self.rgb_label.config(text=f"R: {r}, G: {g}, B: {b}")
        
        # HEX değeri
        hex_color = f"#{r:02X}{g:02X}{b:02X}"
        if hasattr(self, 'hex_entry'):
            self.hex_entry.delete(0, tk.END)
            self.hex_entry.insert(0, hex_color)
        
        # Renk gösterimi
        if hasattr(self, 'color_display'):
            self.color_display.config(bg=hex_color)
        
        # Renk geçmişine ekle
        self.add_to_history(color, hex_color)
    
    def copy_hex(self):
        """HEX kodunu panoya kopyala"""
        if hasattr(self, 'hex_entry'):
            hex_value = self.hex_entry.get()
            if hex_value and hex_value != "#000000":
                self.root.clipboard_clear()
                self.root.clipboard_append(hex_value)
                self.show_toast(f"HEX kopyalandı: {hex_value}", kind="success")
                self.update_status(f"Kopyalandı: {hex_value}")
    
    def clear_image(self):
        """Resmi temizle"""
        self.original_image = None
        self.display_image = None
        self.photo = None
        
        # Pan ve zoom ayarlarını sıfırla
        self.zoom_level = 1.0
        self.pan_offset_x = 0
        self.pan_offset_y = 0
        
        if self.canvas:
            self.canvas.delete("all")
        
        # Bilgileri sıfırla
        if hasattr(self, 'coord_label'):
            self.coord_label.config(text="X: -, Y: -")
        if hasattr(self, 'rgb_label'):
            self.rgb_label.config(text="R: -, G: -, B: -")
        if hasattr(self, 'hex_entry'):
            self.hex_entry.delete(0, tk.END)
        if hasattr(self, 'color_display'):
            self.color_display.config(bg='white')
        
        # Zoom label'ını güncelle
        self.update_zoom_label()
        
        self.show_toast("Resim ve renk bilgileri temizlendi.")
        self.update_status("Temizlendi")

    # ==== Modernizasyon: Tema, Stil, Menü, Kısayol, Toast ve Yardımcılar ====
    def setup_high_dpi(self):
        try:
            if platform.system() == 'Windows' and ctypes is not None:
                try:
                    ctypes.windll.shcore.SetProcessDpiAwareness(1)
                except Exception:
                    pass
            # Tk ölçeklendirme (hafif artırılmış)
            try:
                self.root.tk.call('tk', 'scaling', 1.15)
            except Exception:
                pass
        except Exception:
            pass

    def create_style(self):
        # Opsiyonel modern ttk teması
        if self.sv_ttk_available:
            try:
                sv_ttk.set_theme(self.current_theme)
            except Exception:
                pass
        style = ttk.Style()
        # sv_ttk yoksa daha iyi özelleştirilebilen 'clam' temasını kullan
        if not self.sv_ttk_available:
            try:
                style.theme_use('clam')
            except Exception:
                pass
        # Temel arka plan ve yazılar
        style.configure('TFrame', background=self.colors['bg'])
        style.configure('TLabel', background=self.colors['bg'], foreground=self.colors['fg'])
        if self.sv_ttk_available:
            # Sun Valley teması için doğrudan TNotebook stilleri
            style.configure('TNotebook', background=self.colors['bg'], borderwidth=0, tabmargins=(10, 6, 10, 0))
            style.configure('TNotebook.Tab', background=self.colors['button_bg'], foreground=self.colors['fg'], padding=(16, 9), borderwidth=0)
            style.map('TNotebook.Tab',
                      background=[('selected', self.colors['panel_bg']),
                                  ('active', self.colors['button_hover']),
                                  ('!selected', self.colors['button_bg'])],
                      foreground=[('selected', self.colors['fg']),
                                  ('!selected', self.colors['fg'])])
            try:
                style.configure('TNotebook.Tab', focuscolor=self.colors['panel_bg'])
            except Exception:
                pass
        else:
            # Özel Notebook stili (clam tabanlı)
            style.layout('Modern.TNotebook', [('Notebook.client', {'sticky': 'nswe'})])
            style.configure('Modern.TNotebook', background=self.colors['bg'], borderwidth=0, padding=0, tabmargins=(10, 6, 10, 0), relief='flat')
            style.configure('Modern.TNotebook.Tab', background=self.colors['button_bg'], foreground=self.colors['fg'], padding=(16, 9), borderwidth=0, relief='flat', focuscolor=self.colors['panel_bg'])
            # Sekme durum eşlemeleri (seçili/aktif/normal)
            style.map('Modern.TNotebook.Tab',
                      background=[('selected', self.colors['panel_bg']),
                                  ('active', self.colors['button_hover']),
                                  ('!selected', self.colors['button_bg'])],
                      foreground=[('selected', self.colors['fg']),
                                  ('!selected', self.colors['fg'])])
            # Odak çerçevesini kaldırmak için özel sekme yerleşimi (Notebook.focus elemanını çıkar)
            style.layout('Modern.TNotebook.Tab', [
                ('Notebook.tab', {
                    'sticky': 'nswe',
                    'children': [
                        ('Notebook.padding', {
                            'side': 'top', 'sticky': 'nswe',
                            'children': [
                                ('Notebook.label', {'side': 'top', 'sticky': ''})
                            ]
                        })
                    ]
                })
            ])
        style.configure('TLabelframe', background=self.colors['panel_bg'], foreground=self.colors['fg'])
        style.configure('TLabelframe.Label', background=self.colors['panel_bg'], foreground=self.colors['fg'])
        style.configure('Vertical.TScrollbar', background=self.colors['panel_bg'])

    def create_menubar(self):
        menubar = tk.Menu(self.root)
        # Dosya
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Resim Yükle", command=self.load_image, accelerator="Ctrl+O")
        file_menu.add_command(label="Temizle", command=self.clear_image, accelerator="Ctrl+Shift+C")
        file_menu.add_separator()
        file_menu.add_command(label="Çıkış", command=self.root.destroy, accelerator="Ctrl+Q")
        menubar.add_cascade(label="Dosya", menu=file_menu)
        # Görünüm
        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="Koyu Tema", command=lambda: self.set_theme('dark'))
        view_menu.add_command(label="Açık Tema", command=lambda: self.set_theme('light'))
        menubar.add_cascade(label="Görünüm", menu=view_menu)
        # Yardım
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Hakkında", command=lambda: messagebox.showinfo(
            "Hakkında", "Gelişmiş Renk Seçici\nModern arayüz + tema desteği"))
        menubar.add_cascade(label="Yardım", menu=help_menu)
        self.root.config(menu=menubar)

    def bind_common_shortcuts(self):
        self.root.bind('<Control-o>', lambda e: self.load_image())
        self.root.bind('<Control-O>', lambda e: self.load_image())
        self.root.bind('<Control-q>', lambda e: self.root.destroy())
        self.root.bind('<Control-Q>', lambda e: self.root.destroy())
        self.root.bind('<Control-Key-minus>', lambda e: self.zoom_out())
        self.root.bind('<Control-Key-=>', lambda e: self.zoom_in())
        self.root.bind('<Control-Key-0>', lambda e: self.zoom_reset())
        self.root.bind('<F1>', lambda e: (self.notebook.select(self.help_tab) if hasattr(self, 'notebook') else None))
        # Menü hızlandırıcıları için görsel
        # Not: Tk menüde accelerator yalnızca görsel; bind ile aktif ettik

    def set_theme(self, theme_mode: str):
        theme_mode = 'dark' if theme_mode not in ('dark', 'light') else theme_mode
        self.current_theme = theme_mode
        # Tema kaynakları
        self.colors = dict(self.dark_colors if theme_mode == 'dark' else self.light_colors)
        if self.sv_ttk_available:
            try:
                sv_ttk.set_theme(theme_mode)
            except Exception:
                pass
        self.rebuild_ui()

    def toggle_theme(self):
        self.set_theme('light' if self.current_theme == 'dark' else 'dark')

    def rebuild_ui(self):
        # Tüm UI öğelerini yeniden oluştur (tema geçişi için güvenli yaklaşım)
        for child in list(self.root.winfo_children()):
            # Tk menü root seviyesinde kalır; sadece çocukları temizliyoruz
            try:
                child.destroy()
            except Exception:
                pass
        self.root.configure(bg=self.colors['bg'])
        self.create_style()
        self.create_menubar()
        self.create_widgets()
        self.bind_common_shortcuts()
        # Görsel varsa yeniden göster
        if self.original_image is not None:
            self.display_image_on_canvas()

    def update_status(self, text: str):
        try:
            if hasattr(self, 'status_var') and self.status_var is not None:
                self.status_var.set(text)
        except Exception:
            pass

    def bind_button_hover(self, button: tk.Button, base_bg: str):
        hover_bg = self.colors['button_hover']
        try:
            button.configure(activebackground=hover_bg)
        except Exception:
            pass
        def _enter(_):
            try:
                button.configure(bg=hover_bg)
            except Exception:
                pass
        def _leave(_):
            try:
                button.configure(bg=base_bg)
            except Exception:
                pass
        button.bind('<Enter>', _enter)
        button.bind('<Leave>', _leave)

    def show_toast(self, message: str, kind: str = 'info', duration_ms: int = 1600):
        # Basit toast bildirimi (modern his)
        try:
            # Önceki toast'ı kapat
            if hasattr(self, '_toast_window') and self._toast_window is not None:
                try:
                    self._toast_window.destroy()
                except Exception:
                    pass
        except Exception:
            pass
        bg_map = {
            'info': self.colors['panel_bg'],
            'success': self.colors['success'],
            'error': self.colors['danger'],
            'warn': self.colors['warning']
        }
        fg = 'white' if kind in ('success', 'error', 'warn') or self.current_theme == 'dark' else '#000000'
        bg = bg_map.get(kind, self.colors['panel_bg'])
        top = tk.Toplevel(self.root)
        self._toast_window = top
        try:
            top.overrideredirect(True)
            top.attributes('-topmost', True)
            if platform.system() != 'Darwin':
                # Mac'te alpha sorun çıkarabiliyor; Windows/Linux'ta uygula
                top.attributes('-alpha', 0.95)
        except Exception:
            pass
        frm = tk.Frame(top, bg=bg, bd=0)
        frm.pack(fill=tk.BOTH, expand=True)
        lbl = tk.Label(frm, text=message, bg=bg, fg=fg, font=("Segoe UI", 10), padx=14, pady=10)
        lbl.pack()
        self.root.update_idletasks()
        top.update_idletasks()
        # Konum: sağ-alt
        try:
            rx = self.root.winfo_rootx()
            ry = self.root.winfo_rooty()
            rw = self.root.winfo_width()
            rh = self.root.winfo_height()
            tw = top.winfo_reqwidth()
            th = top.winfo_reqheight()
            x = rx + rw - tw - 24
            y = ry + rh - th - 24
            top.geometry(f"+{x}+{y}")
        except Exception:
            pass
        top.after(duration_ms, lambda: (top.destroy() if top.winfo_exists() else None))

def main():
    root = tk.Tk()
    app = ColorPicker(root)
    root.mainloop()

if __name__ == "__main__":
    main() 