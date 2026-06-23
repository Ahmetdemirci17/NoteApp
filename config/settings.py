#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
config/settings.py
==================
Uygulama ayarlarının varsayılan değerlerini, yüklenmesini ve
kaydedilmesini yönetir.

Ayarlar ``data/settings.json`` dosyasında saklanır.
Dosya yoksa veya bozuksa DEFAULT_SETTINGS kullanılır.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict

# ---------------------------------------------------------------------------
#  Sabitler
# ---------------------------------------------------------------------------
DATA_DIR: str = "data"
DATA_FILE: str = os.path.join(DATA_DIR, "notes.json")
SETTINGS_FILE: str = os.path.join(DATA_DIR, "settings.json")

DEFAULT_SETTINGS: Dict[str, Any] = {
    "dark_mode":    False,
    "gemini_model": "gemini-2.5-flash",
}


# ---------------------------------------------------------------------------
#  Fonksiyonlar
# ---------------------------------------------------------------------------

def load_settings() -> Dict[str, Any]:
    """
    Ayarları ``data/settings.json`` dosyasından yükler.

    Dosya bulunamazsa veya JSON ayrıştırma hatası oluşursa
    DEFAULT_SETTINGS değerleri döner.

    Returns:
        Ayar anahtarlarından oluşan sözlük.
    """
    settings: Dict[str, Any] = dict(DEFAULT_SETTINGS)
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r", encoding="utf-8") as fh:
                loaded = json.load(fh)
                if isinstance(loaded, dict):
                    settings.update(loaded)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[settings] Ayarlar yüklenemedi, varsayılanlar kullanılıyor: {exc}")
    return settings


def save_settings(settings: Dict[str, Any]) -> None:
    """
    Verilen ayarları ``data/settings.json`` dosyasına yazar.

    Dizin yoksa oluşturulur. Yazma hatalarında konsola uyarı yazdırılır
    ve uygulama çalışmaya devam eder.

    Args:
        settings: Kaydedilecek ayar sözlüğü.
    """
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(SETTINGS_FILE, "w", encoding="utf-8") as fh:
            json.dump(settings, fh, indent=2, ensure_ascii=False)
    except OSError as exc:
        print(f"[settings] Ayarlar kaydedilemedi: {exc}")
