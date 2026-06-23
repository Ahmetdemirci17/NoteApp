#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ui/main_window.py
=================
NoteFlow ana uygulama penceresi.

3 panelli düzen:
    ┌──────────┬──────────────────┬──────────────────────────────┐
    │ Nav Rail │   Not Listesi    │   Editör                     │
    │  62 px   │   290 px         │   esnek                      │
    └──────────┴──────────────────┴──────────────────────────────┘
"""

from __future__ import annotations

import re
from tkinter import colorchooser, font as tkfont
import tkinter as tk
import tkinter.messagebox as messagebox
from typing import Any, Dict, List, Optional, Tuple

import customtkinter as ctk

from config.settings import load_settings, save_settings
from config.themes import get_theme
from services.gemini_service import GeminiClient
from services.note_manager import NoteManager, Note
from ui.toast import Toast

_AIAssistantWindow = None
_SettingsWindow    = None


def _lazy_imports() -> None:
    global _AIAssistantWindow, _SettingsWindow
    if _AIAssistantWindow is None:
        from ui.ai_assistant import AIAssistantWindow as _AI
        _AIAssistantWindow = _AI
    if _SettingsWindow is None:
        from ui.settings_window import SettingsWindow as _SW
        _SettingsWindow = _SW


class App(ctk.CTk):
    """NoteFlow ana penceresi."""

    def __init__(self) -> None:
        super().__init__()
        self.title("NoteFlow")
        self.geometry("1400x900")
        self._maximize()

        # Servisler
        self.manager = NoteManager()
        self.gemini  = GeminiClient()

        # Ayarlar & tema
        self.settings  = load_settings()
        self.dark_mode = self.settings.get("dark_mode", False)
        self.T         = get_theme(self.dark_mode)
        self.gemini.model = self.settings.get("gemini_model", "gemini-2.5-flash")

        # Pencere referansları
        self._ai_window:       Optional[Any] = None
        self._settings_window: Optional[Any] = None

        # Durum
        self.current_note_id: Optional[str] = None
        self.context_note_id: Optional[str] = None
        self.tag_meta:        Dict[str, Dict] = {}
        self.fmt_counter:     int  = 0
        self.cur_bold:        bool = False
        self.cur_italic:      bool = False
        self.cur_underline:   bool = False
        self.cur_color:       Optional[str] = None

        # Toolbar referansı (build sırasında atanır)
        self.toolbar: Optional[Any] = None

        self._build_ui()
        self._build_context_menu()
        self._bind_keys()
        self._apply_theme()

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._init_state()

    # ──────────────────────────────────────────────────────────────────
    # Pencere
    # ──────────────────────────────────────────────────────────────────

    def _maximize(self) -> None:
        try:
            self.attributes("-zoomed", True)
        except tk.TclError:
            try:
                self.state("zoomed")
            except tk.TclError:
                pass

    def _save_settings(self) -> None:
        save_settings(self.settings)

    # ──────────────────────────────────────────────────────────────────
    # Klavye kısayolları
    # ──────────────────────────────────────────────────────────────────

    def _bind_keys(self) -> None:
        self.bind_all("<Control-s>",       lambda e: self._save_note())
        self.bind_all("<Control-n>",       lambda e: self._new_note())
        self.bind_all("<Control-Shift-A>", lambda e: self.open_ai_assistant())
        self.content_text.bind("<Control-a>", self._select_all)
        self.content_text.bind("<Control-A>", self._select_all)

    def _select_all(self, e: Optional[tk.Event] = None) -> str:
        self.content_text.tag_add("sel", "1.0", "end")
        self.content_text.mark_set("insert", "end")
        return "break"

    # ──────────────────────────────────────────────────────────────────
    # Bağlam menüsü
    # ──────────────────────────────────────────────────────────────────

    def _build_context_menu(self) -> None:
        T = self.T
        self.ctx_menu = tk.Menu(
            self, tearoff=0,
            bg=T["sb_bg"], fg=T["body_fg"],
            activebackground=T["primary"], activeforeground="#FFFFFF",
            font=("Segoe UI", 10), relief="flat", bd=1,
        )
        self.ctx_menu.add_command(label="  🗑️  Notu Sil",        command=self._ctx_delete)
        self.ctx_menu.add_separator()
        self.ctx_menu.add_command(label="  📋  Başlığı Kopyala", command=self._ctx_copy_title)

    def _show_ctx(self, event: tk.Event, nid: str) -> None:
        self.context_note_id = nid
        try:
            self.ctx_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.ctx_menu.grab_release()

    def _ctx_delete(self) -> None:
        if self.context_note_id:
            self._delete_by_id(self.context_note_id)

    def _ctx_copy_title(self) -> None:
        note = self.manager.get_by_id(self.context_note_id or "")
        if note:
            self.clipboard_clear()
            self.clipboard_append(note["title"])

    # ──────────────────────────────────────────────────────────────────
    # Ana UI İnşası
    # ──────────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        """3 sütunlu düzeni kurar: Rail | Sidebar | Editör."""
        self.configure(fg_color="#FFFFFF")
        self.grid_columnconfigure(0, weight=0, minsize=62)
        self.grid_columnconfigure(1, weight=0, minsize=290)
        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_rail()
        self._build_sidebar()
        self._build_editor()   # content_text burada oluşturulur
        self._build_toolbar_widget()

    # ── NAV RAIL ──────────────────────────────────────────────────────

    def _build_rail(self) -> None:
        T = self.T
        self.rail = tk.Frame(self, bg=T["rail_bg"], width=62)
        self.rail.grid(row=0, column=0, sticky="nsew")
        self.rail.grid_propagate(False)
        self.rail.grid_rowconfigure(8, weight=1)

        logo_frame = tk.Frame(self.rail, bg=T["rail_bg"], pady=16)
        logo_frame.grid(row=0, column=0, sticky="ew")
        tk.Label(logo_frame, text="N", bg=T["primary"], fg="#FFFFFF",
                 font=("Georgia", 16, "bold"), width=2, pady=6, cursor="hand2").pack()

        icons = [
            ("📝", self._focus_notes),
            ("🔍", self._focus_search),
            ("⚙",  self.open_settings),
        ]
        self.rail_btns: List[tk.Label] = []
        for r, (icon, cmd) in enumerate(icons, start=1):
            f = tk.Frame(self.rail, bg=T["rail_bg"], pady=2)
            f.grid(row=r, column=0, sticky="ew", padx=6, pady=2)
            lbl = tk.Label(f, text=icon, bg=T["rail_bg"], fg=T["rail_icon"],
                           font=("Segoe UI", 18), cursor="hand2", pady=8, padx=10)
            lbl.pack(fill="x")
            lbl.bind("<Button-1>", lambda e, c=cmd: c())
            lbl.bind("<Enter>",    lambda e, l=lbl: l.configure(fg=self.T["rail_icon_active"]))
            lbl.bind("<Leave>",    lambda e, l=lbl: l.configure(fg=self.T["rail_icon"]))
            self.rail_btns.append(lbl)

        bottom = tk.Frame(self.rail, bg=T["rail_bg"])
        bottom.grid(row=9, column=0, sticky="sew", padx=6, pady=12)

        self.mode_lbl = tk.Label(bottom, text=T["mode_icon"], bg=T["rail_bg"],
                                 fg=T["rail_icon"], font=("Segoe UI", 16),
                                 cursor="hand2", pady=6)
        self.mode_lbl.pack(fill="x", pady=(4, 0))
        self.mode_lbl.bind("<Button-1>", lambda e: self._toggle_dark())
        self.mode_lbl.bind("<Enter>",    lambda e: self.mode_lbl.configure(fg=self.T["rail_icon_active"]))
        self.mode_lbl.bind("<Leave>",    lambda e: self.mode_lbl.configure(fg=self.T["rail_icon"]))

        self.new_btn_rail = tk.Label(bottom, text="+", bg=T["primary"], fg="#FFFFFF",
                                     font=("Segoe UI", 20, "bold"), cursor="hand2",
                                     pady=6, padx=10)
        self.new_btn_rail.pack(fill="x", pady=(4, 0))
        self.new_btn_rail.bind("<Button-1>", lambda e: self._new_note())
        self.new_btn_rail.bind("<Enter>",    lambda e: self.new_btn_rail.configure(bg=self.T["primary_hover"]))
        self.new_btn_rail.bind("<Leave>",    lambda e: self.new_btn_rail.configure(bg=self.T["primary"]))

        self.ai_fab = ctk.CTkButton(
            self, text="🤖", width=70, height=70, corner_radius=35,
            font=ctk.CTkFont(size=28),
            fg_color=T["primary"], hover_color=T["primary_hover"],
            command=self.open_ai_assistant,
        )
        self.ai_fab.place(relx=0.97, rely=0.94, anchor="se")

    def _focus_notes(self) -> None:
        self.search_entry.delete(0, "end")

    def _focus_search(self) -> None:
        self.search_entry.focus()

    # ── SIDEBAR ───────────────────────────────────────────────────────

    def _build_sidebar(self) -> None:
        T = self.T
        self.sidebar = tk.Frame(self, bg=T["sb_bg"], width=290)
        self.sidebar.grid(row=0, column=1, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_rowconfigure(2, weight=1)
        self.sidebar.grid_columnconfigure(0, weight=1)

        self.sidebar_header = tk.Frame(self.sidebar, bg=T["sb_bg"], pady=14, padx=14)
        self.sidebar_header.grid(row=0, column=0, sticky="ew")

        self.notlarim_lbl = tk.Label(self.sidebar_header, text="Notlarım",
                                     bg=T["sb_bg"], fg=T["title_fg"],
                                     font=("Georgia", 15, "bold"))
        self.notlarim_lbl.pack(side="left")

        self.note_count_lbl = tk.Label(self.sidebar_header, text="0 not",
                                       bg=T["sb_bg"], fg=T["muted"],
                                       font=("Segoe UI", 11))
        self.note_count_lbl.pack(side="right", pady=2)

        self.sidebar_divider1 = tk.Frame(self.sidebar, bg=T["sb_border"], height=1)
        self.sidebar_divider1.grid(row=1, column=0, sticky="ew")

        self.search_frame = tk.Frame(self.sidebar, bg=T["sb_bg"], pady=10, padx=12)
        self.search_frame.grid(row=1, column=0, sticky="ew")

        self.search_wrap = tk.Frame(self.search_frame, bg=T["card_hover"], padx=10)
        self.search_wrap.pack(fill="x")

        self.search_icon_lbl = tk.Label(self.search_wrap, text="🔍",
                                        bg=T["card_hover"], fg=T["muted"],
                                        font=("Segoe UI", 12))
        self.search_icon_lbl.pack(side="left")

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._on_search)
        self.search_entry = tk.Entry(self.search_wrap, textvariable=self.search_var,
                                     bg=T["card_hover"], fg=T["body_fg"], relief="flat",
                                     font=("Segoe UI", 12),
                                     insertbackground=T["primary"], bd=0)
        self.search_entry.pack(side="left", fill="x", expand=True, ipady=7)

        self.list_container = tk.Frame(self.sidebar, bg=T["sb_bg"])
        self.list_container.grid(row=2, column=0, sticky="nsew")
        self.list_container.grid_rowconfigure(0, weight=1)
        self.list_container.grid_columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(self.list_container, bg=T["sb_bg"], bd=0, highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")

        self.sidebar_scrollbar = tk.Scrollbar(
            self.list_container, orient="vertical", command=self.canvas.yview,
            bg=T["scrollbar"], troughcolor=T["sb_bg"],
            activebackground=T["primary"], highlightthickness=0, bd=0, width=10)
        self.sidebar_scrollbar.grid(row=0, column=1, sticky="ns")
        self.canvas.configure(yscrollcommand=self.sidebar_scrollbar.set)

        self.notes_list = tk.Frame(self.canvas, bg=T["sb_bg"])
        self._canvas_win = self.canvas.create_window((0, 0), window=self.notes_list, anchor="nw")

        self.notes_list.bind("<Configure>", self._on_list_resize)
        self.canvas.bind("<Configure>",     self._on_canvas_resize)
        self.canvas.bind("<MouseWheel>",    self._on_scroll)
        self.notes_list.bind("<MouseWheel>", self._on_scroll)

    def _on_list_resize(self, e: tk.Event) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_resize(self, e: tk.Event) -> None:
        self.canvas.itemconfig(self._canvas_win, width=e.width)

    def _on_scroll(self, e: tk.Event) -> None:
        self.canvas.yview_scroll(-1 * (e.delta // 120), "units")

    # ── EDİTÖR ────────────────────────────────────────────────────────

    def _build_editor(self) -> None:
        """
        Editör çerçevesini oluşturur.
        Araç çubuğu _build_toolbar_widget() ile ayrıca eklenir.
        """
        T = self.T

        self.editor_outer = tk.Frame(self, bg=T["editor_bg"])
        self.editor_outer.grid(row=0, column=2, sticky="nsew")
        self.editor_outer.grid_rowconfigure(0, weight=1)
        self.editor_outer.grid_columnconfigure(0, weight=1)

        # Boş karşılama ekranı
        self.empty_frame = tk.Frame(self.editor_outer, bg=T["editor_bg"])
        self._build_empty_state()

        # Editör ana çerçevesi — row 0: toolbar, 1: header, 2: content, 3: statusbar
        self.editor_frame = tk.Frame(self.editor_outer, bg=T["editor_bg"])
        self.editor_frame.grid_rowconfigure(2, weight=1)
        self.editor_frame.grid_columnconfigure(0, weight=1)

        # Araç çubuğu için yer tutucu (gerçek toolbar _build_toolbar_widget'ta)
        self.toolbar_border = tk.Frame(self.editor_frame, bg=T["editor_border"], height=1)
        self.toolbar_border.grid(row=0, column=0, sticky="sew")

        # Başlık alanı
        self.header_area = tk.Frame(self.editor_frame, bg=T["editor_bg"], padx=56)
        self.header_area.grid(row=1, column=0, sticky="ew")
        self.header_area.grid_columnconfigure(0, weight=1)

        self.meta_frame = tk.Frame(self.header_area, bg=T["editor_bg"])
        self.meta_frame.grid(row=0, column=0, sticky="ew", pady=(28, 0))

        self.meta_date_lbl = tk.Label(self.meta_frame, text="",
                                      bg=T["editor_bg"], fg=T["muted"],
                                      font=("Segoe UI", 11))
        self.meta_date_lbl.pack(side="left")

        self.title_entry = tk.Text(
            self.header_area,
            font=("Georgia", 30, "bold"), fg=T["title_fg"], bg=T["editor_bg"],
            relief="flat", bd=0, wrap="word", height=2,
            insertbackground=T["primary"], selectbackground=T["select_bg"],
            padx=0, pady=8, spacing1=2,
        )
        self.title_entry.grid(row=1, column=0, sticky="ew", pady=(4, 0))
        self.title_entry.bind("<KeyRelease>", self._auto_resize_title)

        # Etiketler
        self.tags_wrap = tk.Frame(self.header_area, bg=T["editor_bg"])
        self.tags_wrap.grid(row=2, column=0, sticky="ew", pady=(6, 0))

        self.tags_icon_lbl = tk.Label(self.tags_wrap, text="🏷",
                                      bg=T["editor_bg"], fg=T["muted"],
                                      font=("Segoe UI", 12))
        self.tags_icon_lbl.pack(side="left")

        self.tags_entry = tk.Entry(self.tags_wrap, bg=T["editor_bg"], fg=T["muted"],
                                   relief="flat", font=("Segoe UI", 12),
                                   insertbackground=T["primary"], bd=0)
        self.tags_entry.pack(side="left", fill="x", expand=True, ipady=2, padx=(4, 0))
        self._tags_placeholder = "Etiket ekle (virgülle ayır: fikir, kod, proje)"
        self.tags_entry.insert(0, self._tags_placeholder)
        self.tags_entry.configure(fg=T["placeholder"])
        self.tags_entry.bind("<FocusIn>",  self._tags_focus_in)
        self.tags_entry.bind("<FocusOut>", self._tags_focus_out)

        self.header_divider = tk.Frame(self.header_area, bg=T["editor_border"], height=1)
        self.header_divider.grid(row=3, column=0, sticky="ew", pady=(14, 0))

        # İçerik alanı — content_text burada oluşturulur
        self.content_wrap = tk.Frame(self.editor_frame, bg=T["editor_bg"], padx=56)
        self.content_wrap.grid(row=2, column=0, sticky="nsew")
        self.content_wrap.grid_rowconfigure(0, weight=1)
        self.content_wrap.grid_columnconfigure(0, weight=1)

        self.content_text = tk.Text(
            self.content_wrap,
            font=("Segoe UI", 14), fg=T["body_fg"], bg=T["editor_bg"],
            relief="flat", bd=0, wrap="word", undo=True, maxundo=-1,
            insertbackground=T["primary"],
            selectbackground=T["select_bg"], selectforeground=T["select_fg"],
            padx=0, pady=16, spacing1=3, spacing3=3,
        )
        self.content_text.grid(row=0, column=0, sticky="nsew")

        self.content_scrollbar = tk.Scrollbar(
            self.content_wrap, orient="vertical", command=self.content_text.yview,
            bg=T["scrollbar"], troughcolor=T["editor_bg"],
            activebackground=T["primary"], highlightthickness=0, bd=0, width=8)
        self.content_scrollbar.grid(row=0, column=1, sticky="ns")
        self.content_text.configure(yscrollcommand=self.content_scrollbar.set)

        # Durum çubuğu
        self.statusbar = tk.Frame(self.editor_frame, bg=T["editor_toolbar"],
                                  relief="flat", height=30)
        self.statusbar.grid(row=3, column=0, sticky="ew")
        self.statusbar.grid_propagate(False)

        self.status_lbl = tk.Label(self.statusbar, text="",
                                   bg=T["editor_toolbar"], fg=T["muted"],
                                   font=("Segoe UI", 10), padx=16)
        self.status_lbl.pack(side="left", fill="y")

        self.wordcount_lbl = tk.Label(self.statusbar, text="",
                                      bg=T["editor_toolbar"], fg=T["muted"],
                                      font=("Segoe UI", 10), padx=16)
        self.wordcount_lbl.pack(side="right", fill="y")
        self.content_text.bind("<KeyRelease>", self._update_wordcount)

        self.btn_delete = tk.Label(self.statusbar, text="Sil",
                                   bg=T["editor_toolbar"], fg=T["danger"],
                                   font=("Segoe UI", 10, "bold"),
                                   cursor="hand2", padx=12, pady=6)
        self.btn_delete.pack(side="right")
        self.btn_delete.bind("<Button-1>", lambda e: self._delete_note())
        self.btn_delete.bind("<Enter>",    lambda e: self.btn_delete.configure(bg=self.T["danger_hover"]))
        self.btn_delete.bind("<Leave>",    lambda e: self.btn_delete.configure(bg=self.T["editor_toolbar"]))

        self.btn_save = tk.Label(self.statusbar, text="  Kaydet  ",
                                 bg=T["primary"], fg="#FFFFFF",
                                 font=("Segoe UI", 10, "bold"),
                                 cursor="hand2", padx=4, pady=6)
        self.btn_save.pack(side="right", padx=(0, 4))
        self.btn_save.bind("<Button-1>", lambda e: self._save_note())
        self.btn_save.bind("<Enter>",    lambda e: self.btn_save.configure(bg=self.T["primary_hover"]))
        self.btn_save.bind("<Leave>",    lambda e: self.btn_save.configure(bg=self.T["primary"]))

    def _build_toolbar_widget(self) -> None:
        """
        Araç çubuğunu content_text oluştuktan SONRA ekler.
        (Toolbar, App üzerindeki callback'lere erişir.)
        """
        from ui.toolbar import Toolbar
        T = self.T
        self.toolbar = Toolbar(self.editor_frame, app=self)
        self.toolbar.grid(row=0, column=0, sticky="ew")
        # Kenarlık araç çubuğunun altına taşı
        self.toolbar_border.lift()

    def _build_empty_state(self) -> None:
        T = self.T
        self.empty_inner = tk.Frame(self.empty_frame, bg=T["editor_bg"])
        self.empty_inner.place(relx=0.5, rely=0.45, anchor="center")

        self.empty_logo_lbl = tk.Label(self.empty_inner, text="N",
                                       bg=T["primary"], fg="#FFFFFF",
                                       font=("Georgia", 48, "bold"), width=2, pady=12)
        self.empty_logo_lbl.pack()

        self.empty_title_lbl = tk.Label(self.empty_inner, text="NoteFlow'a Hoş Geldiniz",
                                        bg=T["editor_bg"], fg=T["title_fg"],
                                        font=("Georgia", 22, "bold"))
        self.empty_title_lbl.pack(pady=(20, 6))

        self.empty_desc_lbl = tk.Label(
            self.empty_inner,
            text="Yeni bir not oluşturun ya da sol listeden bir not seçin.",
            bg=T["editor_bg"], fg=T["muted"], font=("Segoe UI", 13))
        self.empty_desc_lbl.pack()

        self.empty_new_btn = tk.Label(self.empty_inner, text="  + Yeni Not  ",
                                      bg=T["primary"], fg="#FFFFFF",
                                      font=("Segoe UI", 13, "bold"),
                                      cursor="hand2", pady=10, padx=8)
        self.empty_new_btn.pack(pady=24)
        self.empty_new_btn.bind("<Button-1>", lambda e: self._new_note())
        self.empty_new_btn.bind("<Enter>",    lambda e: self.empty_new_btn.configure(bg=self.T["primary_hover"]))
        self.empty_new_btn.bind("<Leave>",    lambda e: self.empty_new_btn.configure(bg=self.T["primary"]))

    # ──────────────────────────────────────────────────────────────────
    # Etiket placeholder
    # ──────────────────────────────────────────────────────────────────

    def _tags_focus_in(self, e: tk.Event) -> None:
        if self.tags_entry.get() == self._tags_placeholder:
            self.tags_entry.delete(0, "end")
            self.tags_entry.configure(fg=self.T["muted"])

    def _tags_focus_out(self, e: tk.Event) -> None:
        if not self.tags_entry.get().strip():
            self.tags_entry.insert(0, self._tags_placeholder)
            self.tags_entry.configure(fg=self.T["placeholder"])

    def _get_tags(self) -> List[str]:
        val = self.tags_entry.get()
        if val == self._tags_placeholder:
            return []
        return [t.strip() for t in val.split(",") if t.strip()]

    def _set_tags(self, tags_list: List[str]) -> None:
        self.tags_entry.configure(fg=self.T["muted"])
        self.tags_entry.delete(0, "end")
        if tags_list:
            self.tags_entry.insert(0, ", ".join(tags_list))
        else:
            self.tags_entry.insert(0, self._tags_placeholder)
            self.tags_entry.configure(fg=self.T["placeholder"])

    def _auto_resize_title(self, e: Optional[tk.Event] = None) -> None:
        lines = int(self.title_entry.index("end-1c").split(".")[0])
        self.title_entry.configure(height=max(1, lines))

    def _update_wordcount(self, e: Optional[tk.Event] = None) -> None:
        text  = self.content_text.get("1.0", "end-1c")
        words = len(re.findall(r"\S+", text))
        chars = len(text)
        self.wordcount_lbl.configure(text=f"{words} kelime · {chars} karakter")

    # ──────────────────────────────────────────────────────────────────
    # Tema
    # ──────────────────────────────────────────────────────────────────

    def _apply_theme(self) -> None:
        """Tüm bileşenleri aktif temaya göre renklendirir."""
        T = self.T
        ctk.set_appearance_mode("Dark" if self.dark_mode else "Light")
        self.configure(fg_color=T["editor_bg"])

        # Rail
        self.rail.configure(bg=T["rail_bg"])
        self.new_btn_rail.configure(bg=T["primary"])
        self.mode_lbl.configure(text=T["mode_icon"], bg=T["rail_bg"], fg=T["rail_icon"])
        for lbl in self.rail_btns:
            lbl.configure(bg=T["rail_bg"], fg=T["rail_icon"])
        self.ai_fab.configure(fg_color=T["primary"], hover_color=T["primary_hover"])

        # Sidebar
        self.sidebar.configure(bg=T["sb_bg"])
        self.sidebar_header.configure(bg=T["sb_bg"])
        self.notlarim_lbl.configure(bg=T["sb_bg"], fg=T["title_fg"])
        self.note_count_lbl.configure(bg=T["sb_bg"], fg=T["muted"])
        self.sidebar_divider1.configure(bg=T["sb_border"])
        self.search_frame.configure(bg=T["sb_bg"])
        self.search_wrap.configure(bg=T["card_hover"])
        self.search_icon_lbl.configure(bg=T["card_hover"], fg=T["muted"])
        self.search_entry.configure(bg=T["card_hover"], fg=T["body_fg"],
                                    insertbackground=T["primary"])
        self.list_container.configure(bg=T["sb_bg"])
        self.canvas.configure(bg=T["sb_bg"])
        self.notes_list.configure(bg=T["sb_bg"])
        self.sidebar_scrollbar.configure(
            bg=T["scrollbar"], troughcolor=T["sb_bg"],
            activebackground=T["primary"], highlightbackground=T["sb_bg"])

        # Editör kabuk
        self.editor_outer.configure(bg=T["editor_bg"])
        self.editor_frame.configure(bg=T["editor_bg"])
        self.empty_frame.configure(bg=T["editor_bg"])
        self.toolbar_border.configure(bg=T["editor_border"])

        # Başlık
        self.header_area.configure(bg=T["editor_bg"])
        self.meta_frame.configure(bg=T["editor_bg"])
        self.meta_date_lbl.configure(bg=T["editor_bg"], fg=T["muted"])
        self.title_entry.configure(bg=T["editor_bg"], fg=T["title_fg"],
                                   insertbackground=T["primary"],
                                   selectbackground=T["select_bg"])
        self.tags_wrap.configure(bg=T["editor_bg"])
        self.tags_icon_lbl.configure(bg=T["editor_bg"], fg=T["muted"])
        is_ph = self.tags_entry.get() == self._tags_placeholder
        self.tags_entry.configure(bg=T["editor_bg"],
                                  fg=T["placeholder"] if is_ph else T["muted"],
                                  insertbackground=T["primary"])
        self.header_divider.configure(bg=T["editor_border"])

        # İçerik
        self.content_wrap.configure(bg=T["editor_bg"])
        self.content_text.configure(bg=T["editor_bg"], fg=T["body_fg"],
                                    insertbackground=T["primary"],
                                    selectbackground=T["select_bg"],
                                    selectforeground=T["select_fg"])
        self.content_scrollbar.configure(
            bg=T["scrollbar"], troughcolor=T["editor_bg"],
            activebackground=T["primary"], highlightbackground=T["editor_bg"])

        # Durum çubuğu
        self.statusbar.configure(bg=T["editor_toolbar"])
        self.status_lbl.configure(bg=T["editor_toolbar"], fg=T["muted"])
        self.wordcount_lbl.configure(bg=T["editor_toolbar"], fg=T["muted"])
        self.btn_save.configure(bg=T["primary"])
        self.btn_delete.configure(bg=T["editor_toolbar"], fg=T["danger"])

        # Araç çubuğu
        if self.toolbar:
            self.toolbar.apply_theme()

        # Boş ekran
        self.empty_inner.configure(bg=T["editor_bg"])
        self.empty_logo_lbl.configure(bg=T["primary"])
        self.empty_title_lbl.configure(bg=T["editor_bg"], fg=T["title_fg"])
        self.empty_desc_lbl.configure(bg=T["editor_bg"], fg=T["muted"])
        self.empty_new_btn.configure(bg=T["primary"])

        # Bağlam menüsü
        self.ctx_menu.configure(bg=T["sb_bg"], fg=T["body_fg"],
                                activebackground=T["primary"])

        # Açık alt pencereler
        if self._ai_window is not None and self._ai_window.winfo_exists():
            self._ai_window._apply_theme()
        if self._settings_window is not None and self._settings_window.winfo_exists():
            self._settings_window._apply_theme()

        self._refresh_sidebar()

    def _toggle_dark(self) -> None:
        self.dark_mode = not self.dark_mode
        self.T = get_theme(self.dark_mode)
        self.settings["dark_mode"] = self.dark_mode
        self._apply_theme()
        self._save_settings()

    # ──────────────────────────────────────────────────────────────────
    # Biçimlendirme
    # ──────────────────────────────────────────────────────────────────

    def _sel(self) -> Tuple[Optional[str], Optional[str]]:
        try:
            return (self.content_text.index("sel.first"),
                    self.content_text.index("sel.last"))
        except tk.TclError:
            return None, None

    def _apply_fmt(self) -> None:
        s, e = self._sel()
        if not s:
            Toast(self, "Önce metin seçin", color=self.T["warning"], duration=1500)
            return
        self.fmt_counter += 1
        tag = f"fmt_{self.fmt_counter}"
        fam = self.toolbar.font_family_var.get() if self.toolbar else "Segoe UI"
        sz  = int(self.toolbar.font_size_var.get() if self.toolbar else 14)
        w   = "bold"   if self.cur_bold      else "normal"
        sl  = "italic" if self.cur_italic    else "roman"
        ul  = 1        if self.cur_underline else 0
        f   = tkfont.Font(family=fam, size=sz, weight=w, slant=sl, underline=ul)
        cfg: Dict = {"font": f}
        if self.cur_color:
            cfg["foreground"] = self.cur_color
        self.content_text.tag_configure(tag, **cfg)
        self.content_text.tag_add(tag, s, e)
        self.content_text.tag_raise(tag)
        self.tag_meta[tag] = dict(family=fam, size=sz, bold=self.cur_bold,
                                   italic=self.cur_italic, underline=self.cur_underline,
                                   color=self.cur_color)

    def _toggle_bold(self) -> None:
        self.cur_bold = not self.cur_bold
        if self.toolbar: self.toolbar.update_tb_states()
        self._apply_fmt()

    def _toggle_italic(self) -> None:
        self.cur_italic = not self.cur_italic
        if self.toolbar: self.toolbar.update_tb_states()
        self._apply_fmt()

    def _toggle_underline(self) -> None:
        self.cur_underline = not self.cur_underline
        if self.toolbar: self.toolbar.update_tb_states()
        self._apply_fmt()

    def _choose_color(self) -> None:
        result = colorchooser.askcolor(title="Yazı Rengi")
        if result and result[1]:
            self.cur_color = result[1]
            self._apply_fmt()

    def _toggle_highlight(self) -> None:
        s, e = self._sel()
        if not s:
            Toast(self, "Önce metin seçin", color=self.T["warning"], duration=1500)
            return
        if "highlight" in self.content_text.tag_names(s):
            self.content_text.tag_remove("highlight", s, e)
        else:
            self.content_text.tag_configure("highlight", background=self.T["highlight_bg"])
            self.content_text.tag_add("highlight", s, e)
            self.content_text.tag_raise("highlight")

    def _on_font_family(self, _: str) -> None:
        self._apply_fmt()

    def _on_font_size(self, _: str) -> None:
        self._apply_fmt()

    def _clear_fmt(self) -> None:
        for t in list(self.content_text.tag_names()):
            if t.startswith("fmt_") or t == "highlight":
                self.content_text.tag_delete(t)
        self.tag_meta = {}

    def _collect_fmt(self) -> Tuple[List[Dict], List]:
        fmt: List[Dict] = []
        for tag, meta in self.tag_meta.items():
            rng = self.content_text.tag_ranges(tag)
            if not rng:
                continue
            rl = [[str(rng[i]), str(rng[i + 1])] for i in range(0, len(rng), 2)]
            fmt.append({"tag": tag, "ranges": rl, **meta})
        hl: List = []
        if "highlight" in self.content_text.tag_names():
            hr = self.content_text.tag_ranges("highlight")
            hl = [[str(hr[i]), str(hr[i + 1])] for i in range(0, len(hr), 2)]
        return fmt, hl

    def _restore_fmt(self, note: Note) -> None:
        for f in note.get("formatting", []):
            tag = f["tag"]
            w   = "bold"   if f.get("bold")      else "normal"
            sl  = "italic" if f.get("italic")    else "roman"
            ul  = 1        if f.get("underline") else 0
            fnt = tkfont.Font(family=f["family"], size=f["size"],
                              weight=w, slant=sl, underline=ul)
            cfg: Dict = {"font": fnt}
            if f.get("color"):
                cfg["foreground"] = f["color"]
            self.content_text.tag_configure(tag, **cfg)
            for s, e in f["ranges"]:
                self.content_text.tag_add(tag, s, e)
            self.tag_meta[tag] = {k: f.get(k)
                                   for k in ("family","size","bold","italic","underline","color")}
            try:
                num = int(tag.split("_")[1])
                self.fmt_counter = max(self.fmt_counter, num)
            except (IndexError, ValueError):
                pass
        if note.get("highlights"):
            self.content_text.tag_configure("highlight", background=self.T["highlight_bg"])
            for s, e in note["highlights"]:
                self.content_text.tag_add("highlight", s, e)

    # ──────────────────────────────────────────────────────────────────
    # Not işlemleri
    # ──────────────────────────────────────────────────────────────────

    def _init_state(self) -> None:
        self._refresh_sidebar()
        if self.manager.notes:
            self._load_note(self.manager.notes[0])
        else:
            self._show_empty()

    def _show_empty(self) -> None:
        self.editor_frame.place_forget()
        self.empty_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.current_note_id = None

    def _show_editor(self) -> None:
        self.empty_frame.place_forget()
        self.editor_frame.place(relx=0, rely=0, relwidth=1, relheight=1)

    def _on_search(self, *_: Any) -> None:
        self._refresh_sidebar(self.manager.search(self.search_var.get()))

    def _refresh_sidebar(self, notes: Optional[List[Note]] = None) -> None:
        for w in self.notes_list.winfo_children():
            w.destroy()
        notes = notes if notes is not None else self.manager.notes
        T     = self.T
        tag_colors = T["tag_colors"]
        self.note_count_lbl.configure(text=f"{len(notes)} not", bg=T["sb_bg"])

        for note in notes:
            sel          = note["id"] == self.current_note_id
            color_idx    = note.get("color_idx", 0) % len(tag_colors)
            accent_color = tag_colors[color_idx]
            bg           = T["card_selected"] if sel else T["card_bg"]

            card = tk.Frame(self.notes_list, bg=bg, cursor="hand2")
            card.pack(fill="x", padx=6, pady=2)
            accent = tk.Frame(card, bg=accent_color, width=4)
            accent.pack(side="left", fill="y")
            body = tk.Frame(card, bg=bg, padx=10, pady=10)
            body.pack(side="left", fill="both", expand=True)

            ttxt = note["title"]
            if len(ttxt) > 34: ttxt = ttxt[:31] + "…"
            title_lbl = tk.Label(body, text=ttxt, bg=bg, fg=T["title_fg"],
                                 font=("Segoe UI", 12, "bold"), anchor="w")
            title_lbl.pack(fill="x")

            preview = note.get("content", "").replace("\n", " ").strip()
            if len(preview) > 52: preview = preview[:49] + "…"
            prev_lbl = None
            if preview:
                prev_lbl = tk.Label(body, text=preview, bg=bg, fg=T["muted"],
                                    font=("Segoe UI", 10), anchor="w")
                prev_lbl.pack(fill="x", pady=(1, 0))

            tags_str  = "  ·  " + ", ".join(note["tags"]) if note["tags"] else ""
            meta_text = note["timestamp"] + tags_str
            if len(meta_text) > 40: meta_text = meta_text[:37] + "…"
            meta_lbl = tk.Label(body, text=meta_text, bg=bg, fg=T["muted"],
                                font=("Segoe UI", 9), anchor="w")
            meta_lbl.pack(fill="x", pady=(3, 0))

            if sel:
                tk.Frame(card, bg=T["primary"], width=3).pack(side="right", fill="y")

            all_w = [card, accent, body, title_lbl, meta_lbl]
            if prev_lbl: all_w.append(prev_lbl)
            hover_targets = [card, body, title_lbl, meta_lbl] + ([prev_lbl] if prev_lbl else [])

            def _mk(tgts, nbg, hbg, aw, ac):
                def _e(e):
                    for w in tgts:
                        try: w.configure(bg=hbg)
                        except Exception: pass
                    aw.configure(bg=ac)
                def _l(e):
                    for w in tgts:
                        try: w.configure(bg=nbg)
                        except Exception: pass
                    aw.configure(bg=ac)
                return _e, _l

            enter_fn, leave_fn = _mk(
                hover_targets, bg,
                T["card_hover"] if not sel else T["card_selected"],
                accent, accent_color)

            for w in all_w:
                w.bind("<Enter>",    enter_fn)
                w.bind("<Leave>",    leave_fn)
                w.bind("<Button-1>", lambda e, n=note: self._load_note(n))
                w.bind("<Button-3>", lambda e, nid=note["id"]: self._show_ctx(e, nid))

    def _new_note(self) -> None:
        self._show_editor()
        self.current_note_id = None
        self.title_entry.configure(state="normal")
        self.title_entry.delete("1.0", "end")
        self.title_entry.configure(height=2)
        self._set_tags([])
        self.content_text.delete("1.0", "end")
        self._clear_fmt()
        self.content_text.edit_reset()
        self.meta_date_lbl.configure(text="Yeni not")
        self.status_lbl.configure(text="")
        self.wordcount_lbl.configure(text="")
        try: self.btn_delete.pack_forget()
        except Exception: pass
        self._refresh_sidebar()
        self.title_entry.focus()

    def _load_note(self, note: Note) -> None:
        self._show_editor()
        self.current_note_id = note["id"]
        self.title_entry.configure(state="normal")
        self.title_entry.delete("1.0", "end")
        self.title_entry.insert("1.0", note["title"])
        self._auto_resize_title()
        self._set_tags(note["tags"])
        self.content_text.delete("1.0", "end")
        self._clear_fmt()
        self.content_text.insert("1.0", note["content"])
        self.content_text.edit_reset()
        self._restore_fmt(note)
        self.meta_date_lbl.configure(text=f"Son düzenleme: {note['timestamp']}")
        self._update_wordcount()
        try: self.btn_delete.pack_forget()
        except Exception: pass
        self.btn_delete.pack(side="right", padx=(0, 8))
        self._refresh_sidebar()

    def _get_title(self) -> str:
        return self.title_entry.get("1.0", "end-1c").strip()

    def _save_note(self) -> None:
        title   = self._get_title()
        content = self.content_text.get("1.0", "end-1c").strip()
        if not title and not content:
            Toast(self, "Boş not kaydedilmedi", color=self.T["warning"], duration=2000)
            return
        tags    = self._get_tags()
        fmt, hl = self._collect_fmt()
        try:
            if self.current_note_id:
                upd = self.manager.update(self.current_note_id, title, content, tags, fmt, hl)
                if upd:
                    self.meta_date_lbl.configure(text=f"Kaydedildi: {upd['timestamp']}")
                Toast(self, "✓  Kaydedildi", color=self.T["primary"])
            else:
                new = self.manager.create(title, content, tags, fmt, hl)
                self.current_note_id = new["id"]
                self.meta_date_lbl.configure(text=f"Oluşturuldu: {new['timestamp']}")
                try: self.btn_delete.pack_forget()
                except Exception: pass
                self.btn_delete.pack(side="right", padx=(0, 8))
                Toast(self, "✓  Not oluşturuldu", color=self.T["primary"])
            self.search_var.set("")
            self._refresh_sidebar()
        except Exception as exc:
            messagebox.showerror("Hata", f"Kaydetme başarısız:\n{exc}")

    def _delete_note(self) -> None:
        if self.current_note_id:
            self._delete_by_id(self.current_note_id)

    def _delete_by_id(self, nid: str) -> None:
        if not messagebox.askyesno("Notu Sil",
                                    "Bu notu kalıcı olarak silmek istediğinize emin misiniz?",
                                    icon="warning"):
            return
        try:
            self.manager.delete(nid)
            self.search_var.set("")
            if self.current_note_id == nid:
                if self.manager.notes:
                    self._load_note(self.manager.notes[0])
                else:
                    self._show_empty()
            self._refresh_sidebar()
        except Exception as exc:
            messagebox.showerror("Hata", f"Silme başarısız:\n{exc}")

    # ──────────────────────────────────────────────────────────────────
    # Alt pencereler
    # ──────────────────────────────────────────────────────────────────

    def open_ai_assistant(self) -> None:
        _lazy_imports()
        if self._ai_window is not None and self._ai_window.winfo_exists():
            self._ai_window.lift(); self._ai_window.focus()
            self._ai_window.refresh_note_lists(); return
        self._ai_window = _AIAssistantWindow(self)

    def open_settings(self) -> None:
        _lazy_imports()
        if self._settings_window is not None and self._settings_window.winfo_exists():
            self._settings_window.lift(); self._settings_window.focus(); return
        self._settings_window = _SettingsWindow(self)

    # ──────────────────────────────────────────────────────────────────
    # Kapanış
    # ──────────────────────────────────────────────────────────────────

    def _on_close(self) -> None:
        try:
            title   = self._get_title()
            content = self.content_text.get("1.0", "end-1c").strip()
            if title or content:
                tags    = self._get_tags()
                fmt, hl = self._collect_fmt()
                if self.current_note_id:
                    self.manager.update(self.current_note_id, title, content, tags, fmt, hl)
                else:
                    self.manager.create(title, content, tags, fmt, hl)
        except Exception as exc:
            print(f"[App] Otomatik kayıt hatası: {exc}")
        finally:
            self.destroy()
