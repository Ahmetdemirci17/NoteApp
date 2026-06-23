#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ui/toast.py
===========
Ekranın sağ alt köşesinde kısa süre görünen bildirim penceresi (Toast).

Kullanım::

    Toast(parent_window, "✓ Kaydedildi", color="#00A86B")
    Toast(parent_window, "Hata oluştu", color="#EF4444", duration=3000)
"""

import tkinter as tk


class Toast(tk.Toplevel):
    """
    Otomatik kapanan, hafif bir bildirim penceresi.

    Attributes:
        parent:   Üst Tk penceresi.
        msg:      Gösterilecek mesaj metni.
        color:    Arka plan rengi (hex, örn. ``"#00A86B"``).
        duration: Görünür kalma süresi (milisaniye).
    """

    def __init__(
        self,
        parent: tk.BaseWidget,
        msg: str,
        color: str = "#10B981",
        duration: int = 2000,
    ) -> None:
        """
        Toast penceresini oluşturur ve konumlandırır.

        Args:
            parent:   Üst pencere bileşeni.
            msg:      Gösterilecek kısa metin.
            color:    Arka plan rengi.
            duration: Otomatik kapanma süresi (ms). Varsayılan: 2000.
        """
        super().__init__(parent)
        self.overrideredirect(True)
        self.attributes("-topmost", True)

        try:
            self.attributes("-alpha", 0.93)
        except tk.TclError:
            pass  # Bazı platformlarda şeffaflık desteklenmez

        lbl = tk.Label(
            self,
            text=msg,
            bg=color,
            fg="#FFFFFF",
            font=("Segoe UI", 11),
            padx=20,
            pady=10,
        )
        lbl.pack()
        self.update_idletasks()

        # Sağ alt köşeye konumlandir
        try:
            pw = parent.winfo_rootx() + parent.winfo_width()
            ph = parent.winfo_rooty() + parent.winfo_height()
            w, h = self.winfo_width(), self.winfo_height()
            self.geometry(f"+{pw - w - 30}+{ph - h - 50}")
        except Exception:
            pass  # Konum hesaplanamazsa varsayılan konumda açılır

        self.after(duration, self._close)

    def _close(self) -> None:
        """Pencereyi güvenli biçimde kapatır."""
        try:
            self.destroy()
        except Exception:
            pass
