#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ui/settings_window.py
=====================
Uygulama ayarları iletişim kutusu.
Kullanıcıdan API anahtarı istenmez — anahtar zaten gömülüdür.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

import customtkinter as ctk
from ui.toast import Toast

if TYPE_CHECKING:
    from ui.main_window import App


class SettingsWindow(ctk.CTkToplevel):
    """Modal ayarlar penceresi."""

    GEMINI_MODELS = [
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-2.5-pro",
        "gemini-1.5-flash",
    ]

    def __init__(self, app: "App") -> None:
        super().__init__(app)
        self.app = app
        self.title("⚙ Ayarlar")
        self.geometry("460x260")
        self.resizable(False, False)
        self.transient(app)
        self.grab_set()
        self._build_ui()
        self._apply_theme()

    def _build_ui(self) -> None:
        self.lbl_title = ctk.CTkLabel(self, text="⚙ Ayarlar",
                                       font=ctk.CTkFont(size=20, weight="bold"))
        self.lbl_title.pack(anchor="w", padx=24, pady=(20, 4))

        self.lbl_section = ctk.CTkLabel(self, text="Gemini AI Modeli",
                                         font=ctk.CTkFont(size=14, weight="bold"))
        self.lbl_section.pack(anchor="w", padx=24, pady=(14, 2))

        self.model_combo = ctk.CTkComboBox(self, width=400, values=self.GEMINI_MODELS)
        self.model_combo.pack(padx=24, pady=(0, 8))
        self.model_combo.set(self.app.settings.get("gemini_model", "gemini-2.5-flash"))

        self.lbl_hint = ctk.CTkLabel(
            self, text="✓ AI özelliği yerleşik olarak etkindir, ek kurulum gerekmez.",
            font=ctk.CTkFont(size=11))
        self.lbl_hint.pack(anchor="w", padx=24, pady=(0, 16))

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=24, pady=(0, 20))

        self.btn_cancel = ctk.CTkButton(btn_row, text="Kapat",
                                         fg_color="transparent", width=100,
                                         command=self.destroy)
        self.btn_cancel.pack(side="right", padx=(8, 0))

        self.btn_save = ctk.CTkButton(btn_row, text="Kaydet",
                                       width=100, command=self._save)
        self.btn_save.pack(side="right")

    def _apply_theme(self) -> None:
        T = self.app.T
        self.configure(fg_color=T["editor_bg"])
        self.lbl_title.configure(text_color=T["title_fg"])
        self.lbl_section.configure(text_color=T["title_fg"])
        self.lbl_hint.configure(text_color=T["muted"])
        self.btn_save.configure(fg_color=T["primary"], hover_color=T["primary_hover"])

    def _save(self) -> None:
        model = self.model_combo.get().strip() or "gemini-2.5-flash"
        self.app.settings["gemini_model"] = model
        self.app._save_settings()
        self.app.gemini.model = model
        Toast(self.app, "✓ Ayarlar kaydedildi", color=self.app.T["primary"])
        self.after(800, self.destroy)
