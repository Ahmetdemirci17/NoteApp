#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ui/toolbar.py
=============
Metin biçimlendirme araç çubuğu bileşeni.

``Toolbar`` sınıfı, ``tk.Frame`` içine sarılmış Kalın / İtalik /
Altı Çizili / Vurgulama / Renk seçimi ve yazı tipi / boyutu seçeneklerini
barındırır. Biçimlendirme işlemlerini doğrudan gerçekleştirmez; bunları
``App`` (ana pencere) üzerinden delege eder.
"""

from __future__ import annotations

from tkinter import font as tkfont
import tkinter as tk
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional

import customtkinter as ctk

if TYPE_CHECKING:
    from ui.main_window import App


class Toolbar(tk.Frame):
    """
    Metin editörünün üstünde yer alan biçimlendirme araç çubuğu.

    Attributes:
        app:        Ana uygulama penceresi referansı.
        font_family_var: Seçili yazı tipi ailesi.
        font_size_var:   Seçili yazı boyutu.
    """

    FONT_FAMILIES = [
        "Segoe UI", "Arial", "Georgia", "Times New Roman",
        "Verdana", "Courier New", "Consolas", "Comic Sans MS",
    ]
    FONT_SIZES = [
        "10", "11", "12", "13", "14", "15",
        "16", "18", "20", "24", "28", "32", "36",
    ]

    def __init__(self, parent: tk.Widget, app: "App") -> None:
        """
        Araç çubuğunu oluşturur.

        Args:
            parent: Üst bileşen (genellikle ``editor_frame``).
            app:    Biçimlendirme callback'lerini barındıran ana pencere.
        """
        T = app.T
        super().__init__(parent, bg=T["editor_toolbar"], relief="flat", bd=0, height=46)
        self.app = app
        self.grid_propagate(False)

        self.font_family_var = tk.StringVar(value="Segoe UI")
        self.font_size_var   = tk.StringVar(value="14")

        self._build()

    # ------------------------------------------------------------------
    # İnşa
    # ------------------------------------------------------------------

    def _tb_btn(
        self,
        text: str,
        cmd: Callable,
        font_kw: tuple,
        active_attr: Optional[str] = None,
    ) -> tk.Label:
        """
        Araç çubuğu için tıklanabilir bir Label düğmesi oluşturur.

        Args:
            text:        Düğme metni veya emoji.
            cmd:         Tıklanınca çağrılacak işlev.
            font_kw:     ``(aile, boyut[, stil])`` biçiminde yazı tipi tuple'ı.
            active_attr: Aktif durumu ``App`` üzerinde kontrol edecek öznitelik adı.

        Returns:
            Yapılandırılmış ``tk.Label`` bileşeni.
        """
        T = self.app.T
        lbl = tk.Label(
            self, text=text, bg=T["editor_toolbar"], fg=T["body_fg"],
            font=font_kw, cursor="hand2", padx=8, pady=4, relief="flat",
        )
        lbl.pack(side="left", padx=3, pady=8)
        lbl.bind("<Button-1>", lambda e: cmd())

        def _enter(e: tk.Event, l: tk.Label = lbl) -> None:
            l.configure(bg=self.app.T["card_hover"])

        def _leave(e: tk.Event, l: tk.Label = lbl, attr: Optional[str] = active_attr) -> None:
            active = getattr(self.app, attr, False) if attr else False
            l.configure(
                bg=self.app.T["primary_light"] if active else self.app.T["editor_toolbar"],
                fg=self.app.T["primary"] if active else self.app.T["body_fg"],
            )

        lbl.bind("<Enter>", _enter)
        lbl.bind("<Leave>", _leave)
        return lbl

    def _build(self) -> None:
        """Tüm araç çubuğu bileşenlerini oluşturur ve yerleştirir."""
        T = self.app.T

        self.btn_bold      = self._tb_btn("B",  self.app._toggle_bold,      ("Georgia",  13, "bold"),      "cur_bold")
        self.btn_italic    = self._tb_btn("I",  self.app._toggle_italic,    ("Georgia",  13, "italic"),    "cur_italic")
        self.btn_underline = self._tb_btn("U",  self.app._toggle_underline, ("Segoe UI", 13, "underline"), "cur_underline")
        self.btn_highlight = self._tb_btn("🖊", self.app._toggle_highlight,  ("Segoe UI", 13, "bold"))
        self.btn_color     = self._tb_btn("🎨", self.app._choose_color,      ("Segoe UI", 13, "bold"))

        # Ayraç
        self.sep = tk.Frame(self, bg=T["sb_border"], width=1, height=22)
        self.sep.pack(side="left", padx=8, pady=10)

        # Yazı tipi seçici
        self.font_menu = ctk.CTkOptionMenu(
            self,
            values=self.FONT_FAMILIES,
            variable=self.font_family_var,
            width=138, height=28,
            fg_color=T["editor_toolbar"],
            button_color=T["sb_border"],
            button_hover_color=T["primary"],
            text_color=T["body_fg"],
            command=lambda _: self.app._on_font_family(_),
        )
        self.font_menu.pack(side="left", padx=3, pady=8)

        # Yazı boyutu seçici
        self.size_menu = ctk.CTkOptionMenu(
            self,
            values=self.FONT_SIZES,
            variable=self.font_size_var,
            width=64, height=28,
            fg_color=T["editor_toolbar"],
            button_color=T["sb_border"],
            button_hover_color=T["primary"],
            text_color=T["body_fg"],
            command=lambda _: self.app._on_font_size(_),
        )
        self.size_menu.pack(side="left", padx=3, pady=8)

    # ------------------------------------------------------------------
    # Tema güncelleme
    # ------------------------------------------------------------------

    def apply_theme(self) -> None:
        """
        Araç çubuğunun tüm bileşenlerini mevcut temaya göre yeniden renklendirir.
        """
        T = self.app.T
        self.configure(bg=T["editor_toolbar"])
        self.sep.configure(bg=T["sb_border"])

        for btn in (self.btn_bold, self.btn_italic, self.btn_underline,
                    self.btn_highlight, self.btn_color):
            btn.configure(bg=T["editor_toolbar"], fg=T["body_fg"])

        for menu in (self.font_menu, self.size_menu):
            menu.configure(
                fg_color=T["editor_toolbar"],
                button_color=T["sb_border"],
                button_hover_color=T["primary"],
                text_color=T["body_fg"],
            )
        self.update_tb_states()

    def update_tb_states(self) -> None:
        """
        Kalın / İtalik / Altı Çizili düğmelerini aktif durumlarına göre
        vurgular veya normal hâle getirir.
        """
        T = self.app.T
        states = [
            (self.btn_bold,      self.app.cur_bold),
            (self.btn_italic,    self.app.cur_italic),
            (self.btn_underline, self.app.cur_underline),
        ]
        for btn, active in states:
            btn.configure(
                bg=T["primary_light"] if active else T["editor_toolbar"],
                fg=T["primary"]       if active else T["body_fg"],
            )
