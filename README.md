# Renk Seçici (Color Picker) Uygulaması

Bu uygulama, yüklediğiniz bir resim üzerinde mouse ile tıklayarak o noktanın renk kodlarını öğrenmenizi sağlar.

## Özellikler

- 🖼️ Resim yükleme (PNG, JPEG, GIF, BMP, TIFF formatları desteklenir)
- 🎯 Mouse ile resim üzerinde renk seçimi
- 📊 RGB ve HEX renk kodlarını gösterme
- 🎨 Seçilen rengin görsel önizlemesi
- 📋 HEX kodunu panoya kopyalama
- 📍 Mouse koordinatlarını gösterme
- 🗑️ Resmi temizleme

## Kurulum

1. Gerekli Python kütüphanelerini yükleyin:
```bash
pip install -r requirements.txt
```

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

5. HEX kodunu panoya kopyalamak için "HEX Kodu Kopyala" butonuna tıklayın

## Teknik Detaylar

- **Python Version**: 3.7+
- **GUI Framework**: tkinter (Python built-in)
- **Resim İşleme**: PIL/Pillow
- **Desteklenen Formatlar**: PNG, JPEG, GIF, BMP, TIFF

## Önemli Notlar

- Uygulama, resimlerinizi orijinal kalitelerinde korur
- Renk seçimi orijinal resim üzerinden yapılır, böylece doğru renk kodları alırsınız
- Resim otomatik olarak ekran boyutuna göre ölçeklenir ancak renk bilgileri orijinal resimden alınır

## Sorun Giderme

Eğer uygulama çalışmıyorsa:

1. Python 3.7+ kurulu olduğundan emin olun
2. Pillow kütüphanesinin yüklü olduğunu kontrol edin: `pip show Pillow`
3. Resim dosyasının desteklenen bir formatta olduğundan emin olun
