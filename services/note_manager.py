#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
services/note_manager.py
========================
Not verilerinin CRUD (Oluştur / Oku / Güncelle / Sil) işlemlerini ve
JSON tabanlı kalıcı depolamayı yönetir.

Bu katman UI'dan tamamen bağımsızdır; tkinter veya herhangi bir
görsel bileşen içermez.
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from config.settings import DATA_DIR, DATA_FILE

# Not sözlüğünün tip takma adı
Note = Dict[str, Any]


class NoteManager:
    """
    Not verilerini bellekte tutar ve JSON dosyasıyla senkronize eder.

    Attributes:
        notes: Bellekteki not listesi (en yeni önce sıralı).
    """

    def __init__(self) -> None:
        """
        NoteManager'ı başlatır: veri dizinini ve dosyasını oluşturur,
        ardından mevcut notları yükler.
        """
        self.notes: List[Note] = []
        self._ensure_storage()
        self._load()

    # ------------------------------------------------------------------
    # Dahili yardımcılar
    # ------------------------------------------------------------------

    def _ensure_storage(self) -> None:
        """
        Veri dizinini ve boş notes.json dosyasını (yoksa) oluşturur.

        Raises:
            OSError: Dizin veya dosya oluşturulamazsa.
        """
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            if not os.path.exists(DATA_FILE):
                with open(DATA_FILE, "w", encoding="utf-8") as fh:
                    json.dump([], fh)
        except OSError as exc:
            print(f"[NoteManager] Depolama alanı hazırlanamadı: {exc}")
            raise

    def _load(self) -> None:
        """
        ``notes.json`` dosyasından notları belleğe yükler.

        Dosya bozuksa veya okunamazsa ``self.notes`` boş liste olarak
        başlatılır ve hata konsola yazdırılır.
        """
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as fh:
                data = json.load(fh)
                if isinstance(data, list):
                    self.notes = data
                else:
                    self.notes = []
        except (OSError, json.JSONDecodeError) as exc:
            print(f"[NoteManager] Notlar yüklenemedi: {exc}")
            self.notes = []

    def _save(self) -> None:
        """
        Bellekteki not listesini zaman damgasına göre tersten sıralar
        ve ``notes.json`` dosyasına yazar.

        Raises:
            OSError: Dosya yazılamazsa.
        """
        self.notes.sort(
            key=lambda n: n.get("timestamp", ""),
            reverse=True,
        )
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as fh:
                json.dump(self.notes, fh, indent=2, ensure_ascii=False)
        except OSError as exc:
            print(f"[NoteManager] Notlar kaydedilemedi: {exc}")
            raise

    @staticmethod
    def _now() -> str:
        """Şimdiki zamanı ``GG.AA.YYYY SS:DD`` biçiminde döndürür."""
        return datetime.now().strftime("%d.%m.%Y %H:%M")

    # ------------------------------------------------------------------
    # Genel API
    # ------------------------------------------------------------------

    def create(
        self,
        title: str,
        content: str,
        tags: List[str],
        fmt: Optional[List[Dict]] = None,
        hl: Optional[List] = None,
    ) -> Note:
        """
        Yeni bir not oluşturur, listeye ekler ve diske kaydeder.

        Args:
            title:   Not başlığı. Boşsa ``"İsimsiz Not"`` kullanılır.
            content: Not içeriği.
            tags:    Etiket listesi.
            fmt:     Biçimlendirme meta verisi (isteğe bağlı).
            hl:      Vurgulama aralıkları (isteğe bağlı).

        Returns:
            Oluşturulan not sözlüğü.
        """
        note: Note = {
            "id":         str(uuid.uuid4()),
            "title":      title.strip() or "İsimsiz Not",
            "content":    content,
            "tags":       tags,
            "formatting": fmt or [],
            "highlights": hl or [],
            "timestamp":  self._now(),
            "color_idx":  len(self.notes) % 7,
        }
        self.notes.append(note)
        self._save()
        return note

    def update(
        self,
        note_id: str,
        title: str,
        content: str,
        tags: List[str],
        fmt: Optional[List[Dict]] = None,
        hl: Optional[List] = None,
    ) -> Optional[Note]:
        """
        Var olan bir notu günceller ve diske kaydeder.

        Args:
            note_id: Güncellenecek notun UUID'si.
            title:   Yeni başlık.
            content: Yeni içerik.
            tags:    Yeni etiket listesi.
            fmt:     Yeni biçimlendirme meta verisi (isteğe bağlı).
            hl:      Yeni vurgulama aralıkları (isteğe bağlı).

        Returns:
            Güncellenen not sözlüğü; not bulunamazsa ``None``.
        """
        for note in self.notes:
            if note["id"] == note_id:
                note.update(
                    title=title.strip() or "İsimsiz Not",
                    content=content,
                    tags=tags,
                    formatting=fmt or [],
                    highlights=hl or [],
                    timestamp=self._now(),
                )
                self._save()
                return note
        print(f"[NoteManager] Güncellenecek not bulunamadı: {note_id}")
        return None

    def delete(self, note_id: str) -> None:
        """
        Belirtilen UUID'ye sahip notu listeden kaldırır ve diske kaydeder.

        Args:
            note_id: Silinecek notun UUID'si.
        """
        before = len(self.notes)
        self.notes = [n for n in self.notes if n["id"] != note_id]
        if len(self.notes) == before:
            print(f"[NoteManager] Silinecek not bulunamadı: {note_id}")
        self._save()

    def search(self, query: str) -> List[Note]:
        """
        Başlık, içerik veya etiketlerde büyük/küçük harf duyarsız arama yapar.

        Args:
            query: Aranacak metin. Boşsa tüm notlar döner.

        Returns:
            Eşleşen not listesi.
        """
        q = query.strip().lower()
        if not q:
            return self.notes
        return [
            n for n in self.notes
            if q in n["title"].lower()
            or q in n.get("content", "").lower()
            or any(q in t.lower() for t in n.get("tags", []))
        ]

    def get_by_id(self, note_id: str) -> Optional[Note]:
        """
        UUID'ye göre tek bir notu döndürür.

        Args:
            note_id: Aranan notun UUID'si.

        Returns:
            Not sözlüğü; bulunamazsa ``None``.
        """
        return next((n for n in self.notes if n["id"] == note_id), None)
