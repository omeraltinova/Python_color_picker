# Renk Seçici (Color Picker) Uygulaması

Bu uygulama, yüklediğiniz bir resim üzerinde mouse ile tıklayarak o noktanın renk kodlarını öğrenmenizi sağlar.

## Özellikler

- 🖼️ Resim yükleme (PNG, JPEG, GIF, BMP, TIFF)
- 🎯 Mouse ile resim üzerinde renk seçimi
- 📊 RGB ve HEX renk kodlarını gösterme
- 🎨 Seçilen rengin görsel önizlemesi
- 📋 HEX ve RGB kodunu panoya kopyalama
- 📍 Mouse koordinatlarını gösterme
- 🗑️ Resmi temizleme
- 🌗 Modern arayüz (açık/koyu tema)
- 🧭 Menü çubuğu (Dosya, Görünüm, Yardım)
- 🧩 Esnek düzen (PanedWindow ile sürükle-bırak genişlik ayarı)
- 🔔 Minimal toast bildirimleri ve durum çubuğu
- 🖱️ Hover efektli butonlar

## Kurulum

1. Gerekli Python kütüphanelerini yükleyin:
```bash
pip install -r requirements.txt
```

Notlar:
- `sv-ttk` modern ttk temasıdır ve isteğe bağlıdır. Kurulu değilse uygulama standart ttk ile çalışır.

## Kullanım

1. Uygulamayı çalıştırın:
```bash
python color_picker.py
```

2. "Resim Yükle" butonuna tıklayarak bir resim seçin

3. Resim yüklendikten sonra, renk kodunu öğrenmek istediğiniz noktaya tıklayın

4. Sağ panelde aşağıdaki bilgileri görebilirsiniz:
   - Mouse koordinatları
   - RGB değerleri (R, G, B)
   - HEX renk kodu
   - Seçilen rengin görsel önizlemesi

5. Kopyalamak için ilgili kopyalama butonlarını veya kısayolları kullanın

### Kısayollar
- Ctrl+O: Resim yükle
- Ctrl+Q: Uygulamadan çık
- Ctrl+= / Ctrl+-: Yakınlaştır / Uzaklaştır
- Ctrl+0: Zoom sıfırla
- Ctrl+C: Aktif renk kodunu kopyala (HEX)
- F1: Yardım sekmesini aç

## Teknik Detaylar

- **Python Version**: 3.7+
- **GUI Framework**: tkinter (Python built-in)
- **Resim İşleme**: PIL/Pillow
- **Desteklenen Formatlar**: PNG, JPEG, GIF, BMP, TIFF
 - **Tema**: Varsayılan ttk; varsa `sv-ttk` ile modern açık/koyu tema

## Önemli Notlar

- Uygulama, resimlerinizi orijinal kalitelerinde korur
- Renk seçimi orijinal resim üzerinden yapılır, böylece doğru renk kodları alırsınız
- Resim otomatik olarak ekran boyutuna göre ölçeklenir ancak renk bilgileri orijinal resimden alınır

## Sorun Giderme

Eğer uygulama çalışmıyorsa:

1. Python 3.7+ kurulu olduğundan emin olun
2. Pillow kütüphanesinin yüklü olduğunu kontrol edin: `pip show Pillow`
3. Resim dosyasının desteklenen bir formatta olduğundan emin olun
