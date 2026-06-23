#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
main.py — NoteFlow Giriş Noktası
=================================
Bu dosya yalnızca uygulamayı başlatan bir orkestratördür.
İş mantığı, veri katmanı ve UI'nin hiçbiri burada yer almaz.

Çalıştırma:
    python main.py

Ortam değişkeni (isteğe bağlı):
    GEMINI_API_KEY=<anahtarınız> python main.py
"""

import sys
import os

# Proje kökünü Python yoluna ekle (paket içe aktarmalarının çalışması için)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import customtkinter as ctk


def main() -> None:
    """
    Uygulamayı başlatır.

    customtkinter görünümünü ayarlar ve ana pencereyi oluşturur.
    Başlatma sırasında kritik bir hata oluşursa mesajı ekrana yazdırır
    ve çıkış kodu 1 ile sonlanır.
    """
    try:
        ctk.set_appearance_mode("Light")
        ctk.set_default_color_theme("green")

        from ui.main_window import App
        app = App()
        app.mainloop()

    except ImportError as exc:
        print(f"[NoteFlow] Gerekli paket bulunamadı: {exc}")
        print("Lütfen 'pip install -r requirements.txt' komutunu çalıştırın.")
        sys.exit(1)
    except Exception as exc:
        print(f"[NoteFlow] Beklenmedik hata: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
