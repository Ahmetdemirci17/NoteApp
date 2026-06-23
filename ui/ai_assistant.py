#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ui/ai_assistant.py
==================
Gemini AI Asistan penceresi — dört sekme:

    💬 Sohbet        — bağlam destekli serbest sohbet
    📝 Özetle        — seçili notu özetle ve notun sonuna ekle
    ✓  Yazım Denetimi — yazım & dilbilgisi düzeltme (TR / EN)
    🔗 Birleştir     — birden fazla notu tek kapsamlı nota dönüştür
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List, Optional

import customtkinter as ctk
import tkinter.messagebox as messagebox

from services.gemini_service import run_async
from ui.toast import Toast

if TYPE_CHECKING:
    from ui.main_window import App

# ---------------------------------------------------------------------------
#  Sistem talimatları
# ---------------------------------------------------------------------------
_SYS_CHAT = """\
You are NoteFlow AI.
Purpose: Help users manage, study and organize notes.
Capabilities: Explain notes, summarize, merge, generate flashcards/quizzes/study guides, improve grammar.
Rules:
- Prioritize note content.
- Never invent information.
- Use markdown headings.
- Be concise when chatting, detailed when studying.
"""

_SYS_SUMMARY = """\
Sen bir öğrenci not asistanısın. Verilen ders notunu, ana kavramları ve önemli \
noktaları koruyarak kısa ve anlaşılır biçimde özetle. \
Not Türkçe ise özet Türkçe, İngilizce ise İngilizce olsun. \
Sadece özeti döndür, başka açıklama ekleme.\
"""

_SYS_FIX = """\
Sen bir yazım ve dilbilgisi denetleyicisisin. Verilen metindeki yazım ve dilbilgisi \
hatalarını düzelt. Metnin anlamını ve yapısını değiştirme, sadece hataları düzelt. \
Metin Türkçe ise düzeltilmiş hali Türkçe, İngilizce ise İngilizce olsun; \
karışık metni her bölümde kendi dilinde düzelt. \
Sadece düzeltilmiş metni döndür, açıklama ekleme.\
"""

_SYS_MERGE = """\
Sen bir not düzenleme asistanısın. Aynı konuyla ilgili birden fazla not verilecek. \
Kurallar:
- ASLA özetleme yapma.
- ASLA içerik kısaltma.
- ASLA bilgi çıkarma.
Yapılacaklar:
1. Tüm notları tek belgede birleştir.
2. Birebir tekrarları kaldır, benzersiz bilgileri koru.
3. Başlıklar ve alt başlıklar oluştur.
4. Konuları mantıksal sıraya koy.
5. Tüm detayları muhafaza et.
Notların dili Türkçe ise çıktı Türkçe, İngilizce ise İngilizce olsun. \
Sadece birleştirilmiş notu döndür.\
"""


class AIAssistantWindow(ctk.CTkToplevel):
    """
    Gemini destekli AI Asistan penceresi.

    Attributes:
        app:           Ana uygulama penceresi referansı.
        chat_history:  Sohbet geçmişi (Gemini formatında).
    """

    def __init__(self, app: "App") -> None:
        """
        AI Asistan penceresini başlatır.

        Args:
            app: Ana uygulama penceresi.
        """
        super().__init__(app)
        self.app = app
        self.title("🤖 NoteFlow AI Asistan")
        self.geometry("860x720")
        self.minsize(660, 500)
        self.transient(app)

        self.chat_history: List[Dict[str, str]] = []
        self._note_lookup: Dict[str, Dict] = {}
        self._last_summarized_note_id: Optional[str] = None
        self._last_fixed_note_id:      Optional[str] = None
        self._last_merge_sources:      List[str] = []

        self._build_ui()
        self._apply_theme()
        self.refresh_note_lists()

    # ------------------------------------------------------------------
    # Ana UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        """Sekme yapısını ve içeriklerini oluşturur."""
        self.tabs = ctk.CTkTabview(self)
        self.tabs.pack(fill="both", expand=True, padx=14, pady=14)

        self.tab_chat    = self.tabs.add("💬 Sohbet")
        self.tab_summary = self.tabs.add("📝 Özetle")
        self.tab_fix     = self.tabs.add("✓ Yazım Denetimi")
        self.tab_merge   = self.tabs.add("🔗 Birleştir")

        self._build_chat_tab()
        self._build_summary_tab()
        self._build_fix_tab()
        self._build_merge_tab()

    # ------------------------------------------------------------------
    # 💬 SOHBET SEKMESİ
    # ------------------------------------------------------------------

    def _build_chat_tab(self) -> None:
        """Sohbet arayüzünü oluşturur."""
        tab = self.tab_chat
        tab.grid_rowconfigure(0, weight=1)
        tab.grid_columnconfigure(0, weight=1)

        self.chat_scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        self.chat_scroll.grid(row=0, column=0, sticky="nsew", pady=(0, 8))
        self.chat_scroll.grid_columnconfigure(0, weight=1)

        opts_row = ctk.CTkFrame(tab, fg_color="transparent")
        opts_row.grid(row=1, column=0, sticky="ew")

        self.use_context_var = ctk.BooleanVar(value=True)
        self.context_chk = ctk.CTkCheckBox(
            opts_row, text="Açık notu bağlam olarak kullan",
            variable=self.use_context_var, font=ctk.CTkFont(size=12),
        )
        self.context_chk.pack(side="left")

        self.clear_chat_btn = ctk.CTkButton(
            opts_row, text="Sohbeti Temizle", width=130, height=28,
            fg_color="transparent", command=self._clear_chat,
        )
        self.clear_chat_btn.pack(side="right")

        input_row = ctk.CTkFrame(tab, fg_color="transparent")
        input_row.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        input_row.grid_columnconfigure(0, weight=1)

        self.chat_entry = ctk.CTkEntry(
            input_row,
            placeholder_text="Bir şey sor… (Enter ile gönder)",
            height=40,
        )
        self.chat_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.chat_entry.bind("<Return>", lambda e: self._send_chat())

        self.chat_send_btn = ctk.CTkButton(
            input_row, text="Gönder", width=90, height=40,
            command=self._send_chat,
        )
        self.chat_send_btn.grid(row=0, column=1)

        self._add_bubble(
            "model",
            "Merhaba! Notlarınla ilgili sorular sorabilir; özet çıkarmamı, "
            "yazım hatalarını düzeltmemi ya da birden fazla notunu birleştirmemi "
            "isteyebilirsin. 🙂",
        )

    def _add_bubble(self, role: str, text: str) -> ctk.CTkLabel:
        """
        Sohbet alanına kullanıcı veya model mesaj balonu ekler.

        Args:
            role: ``"user"`` veya ``"model"``.
            text: Gösterilecek metin.

        Returns:
            Oluşturulan ``ctk.CTkLabel`` balonu.
        """
        T = self.app.T
        is_user = role == "user"
        row = ctk.CTkFrame(self.chat_scroll, fg_color="transparent")
        row.pack(fill="x", pady=4)

        bubble = ctk.CTkLabel(
            row, text=text, justify="left", anchor="w", wraplength=580,
            font=ctk.CTkFont(size=13),
            fg_color=T["bubble_user_bg"]  if is_user else T["bubble_model_bg"],
            text_color=T["bubble_user_fg"] if is_user else T["bubble_model_fg"],
            corner_radius=12, padx=14, pady=10,
        )
        bubble.pack(
            side="right" if is_user else "left",
            anchor="e"   if is_user else "w",
        )
        self.after(50, self._scroll_chat_bottom)
        return bubble

    def _scroll_chat_bottom(self) -> None:
        """Sohbet bölümünü en alta kaydırır."""
        try:
            self.chat_scroll._parent_canvas.yview_moveto(1.0)
        except Exception:
            pass

    def _send_chat(self) -> None:
        """
        Kullanıcı mesajını gönderir, Gemini'ye iletir ve yanıtı gösterir.
        Gemini yapılandırılmamışsa hata balonu gösterir.
        """
        text = self.chat_entry.get().strip()
        if not text:
            return
        if not self.app.gemini.is_configured():
            self._add_bubble("model", "⚠ AI servisi yapılandırılmamış. Lütfen Ayarlar'dan API anahtarını girin.")
            return

        self.chat_entry.delete(0, "end")
        self._add_bubble("user", text)
        self.chat_history.append({"role": "user", "text": text})

        loading = self._add_bubble("model", "Yazıyor…")
        self.chat_send_btn.configure(state="disabled")

        sys_instr = _SYS_CHAT
        if self.use_context_var.get():
            note = self._current_open_note()
            if note:
                sys_instr += (
                    f"\n\nKullanıcının açık notu:\nBaşlık: {note['title']}\n"
                    f"İçerik:\n{note['content'][:4000]}"
                )

        history_copy = list(self.chat_history)

        def task() -> str:
            return self.app.gemini.chat(history_copy, system_instruction=sys_instr)

        def on_success(answer: str) -> None:
            loading.master.destroy()
            self._add_bubble("model", answer)
            self.chat_history.append({"role": "model", "text": answer})
            self.chat_send_btn.configure(state="normal")

        def on_error(exc: Exception) -> None:
            loading.master.destroy()
            self._add_bubble("model", f"⚠ Hata: {exc}")
            self.chat_send_btn.configure(state="normal")

        run_async(self, task, on_success, on_error)

    def _clear_chat(self) -> None:
        """Sohbet geçmişini ve görsel alanı temizler."""
        self.chat_history = []
        for w in self.chat_scroll.winfo_children():
            w.destroy()
        self._add_bubble("model", "Sohbet temizlendi. Nasıl yardımcı olabilirim?")

    def _current_open_note(self) -> Optional[Dict]:
        """Editörde açık olan notu döndürür; yoksa ``None``."""
        if not self.app.current_note_id:
            return None
        return self.app.manager.get_by_id(self.app.current_note_id)

    # ------------------------------------------------------------------
    # 📝 ÖZETLE SEKMESİ
    # ------------------------------------------------------------------

    def _build_summary_tab(self) -> None:
        """Özetleme arayüzünü oluşturur."""
        tab = self.tab_summary
        tab.grid_rowconfigure(2, weight=1)
        tab.grid_columnconfigure(0, weight=1)

        top = ctk.CTkFrame(tab, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        ctk.CTkLabel(top, text="Not seç:", font=ctk.CTkFont(size=13)).pack(side="left", padx=(0, 8))

        self.summary_note_combo = ctk.CTkComboBox(top, width=380, values=["(not yok)"])
        self.summary_note_combo.pack(side="left", fill="x", expand=True)

        self.summary_btn = ctk.CTkButton(top, text="Özetle", width=100, command=self._do_summarize)
        self.summary_btn.pack(side="left", padx=(8, 0))

        self.summary_status = ctk.CTkLabel(tab, text="", font=ctk.CTkFont(size=11))
        self.summary_status.grid(row=1, column=0, sticky="w")

        self.summary_text = ctk.CTkTextbox(tab, wrap="word", font=ctk.CTkFont(size=13))
        self.summary_text.grid(row=2, column=0, sticky="nsew", pady=(6, 10))

        bottom = ctk.CTkFrame(tab, fg_color="transparent")
        bottom.grid(row=3, column=0, sticky="ew")

        self.summary_append_btn = ctk.CTkButton(
            bottom, text="Notun Sonuna Ekle", command=self._apply_summary,
        )
        self.summary_append_btn.pack(side="right")

    def _do_summarize(self) -> None:
        """Seçili notu Gemini'ye özetletir ve sonucu metin kutusuna yazar."""
        note = self._note_from_combo(self.summary_note_combo)
        if not note:
            Toast(self.app, "Önce bir not seçin", color=self.app.T["warning"]); return
        if not self.app.gemini.is_configured():
            Toast(self.app, "AI servisi kullanılamıyor. Ayarlar'dan yapılandırın.",
                  color=self.app.T["warning"]); return

        self.summary_status.configure(text="Özetleniyor…")
        self.summary_btn.configure(state="disabled")
        prompt = f"Başlık: {note['title']}\n\nİçerik:\n{note['content']}"

        def task() -> str:
            return self.app.gemini.ask(prompt, system_instruction=_SYS_SUMMARY)

        def on_success(result: str) -> None:
            self.summary_text.delete("1.0", "end")
            self.summary_text.insert("1.0", result)
            self.summary_status.configure(text="Hazır.")
            self.summary_btn.configure(state="normal")
            self._last_summarized_note_id = note["id"]

        def on_error(exc: Exception) -> None:
            self.summary_status.configure(text=f"Hata: {exc}")
            self.summary_btn.configure(state="normal")

        run_async(self, task, on_success, on_error)

    def _apply_summary(self) -> None:
        """Özeti ilgili notun içeriğine ekler ve notu kaydeder."""
        summary = self.summary_text.get("1.0", "end-1c").strip()
        if not summary or not self._last_summarized_note_id:
            Toast(self.app, "Önce bir özet oluşturun", color=self.app.T["warning"]); return

        note = self.app.manager.get_by_id(self._last_summarized_note_id)
        if not note:
            return

        new_content = note["content"].rstrip() + "\n\n--- 🤖 AI Özeti ---\n" + summary
        self.app.manager.update(
            self._last_summarized_note_id,
            note["title"], new_content, note["tags"],
            note.get("formatting", []), note.get("highlights", []),
        )
        if self.app.current_note_id == self._last_summarized_note_id:
            self.app._load_note(self.app.manager.get_by_id(self._last_summarized_note_id))
        else:
            self.app._refresh_sidebar()
        Toast(self.app, "✓ Özet nota eklendi", color=self.app.T["primary"])

    # ------------------------------------------------------------------
    # ✓ YAZIM DENETİMİ SEKMESİ
    # ------------------------------------------------------------------

    def _build_fix_tab(self) -> None:
        """Yazım denetimi arayüzünü oluşturur."""
        tab = self.tab_fix
        tab.grid_rowconfigure(2, weight=1)
        tab.grid_columnconfigure(0, weight=1)

        top = ctk.CTkFrame(tab, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        ctk.CTkLabel(top, text="Not seç:", font=ctk.CTkFont(size=13)).pack(side="left", padx=(0, 8))

        self.fix_note_combo = ctk.CTkComboBox(top, width=380, values=["(not yok)"])
        self.fix_note_combo.pack(side="left", fill="x", expand=True)

        self.fix_btn = ctk.CTkButton(top, text="Düzelt", width=100, command=self._do_fix)
        self.fix_btn.pack(side="left", padx=(8, 0))

        self.fix_status = ctk.CTkLabel(
            tab,
            text="Yazım ve dilbilgisi hataları (Türkçe / İngilizce) otomatik tespit edilip düzeltilir.",
            font=ctk.CTkFont(size=11),
        )
        self.fix_status.grid(row=1, column=0, sticky="w")

        self.fix_text = ctk.CTkTextbox(tab, wrap="word", font=ctk.CTkFont(size=13))
        self.fix_text.grid(row=2, column=0, sticky="nsew", pady=(6, 10))

        bottom = ctk.CTkFrame(tab, fg_color="transparent")
        bottom.grid(row=3, column=0, sticky="ew")

        self.fix_apply_btn = ctk.CTkButton(
            bottom, text="Notu Güncelle", command=self._apply_fix,
        )
        self.fix_apply_btn.pack(side="right")

    def _do_fix(self) -> None:
        """Seçili notun içeriğini Gemini'ye yazım denetimi için gönderir."""
        note = self._note_from_combo(self.fix_note_combo)
        if not note:
            Toast(self.app, "Önce bir not seçin", color=self.app.T["warning"]); return
        if not self.app.gemini.is_configured():
            Toast(self.app, "AI servisi kullanılamıyor. Ayarlar'dan yapılandırın.",
                  color=self.app.T["warning"]); return

        self.fix_status.configure(text="Denetleniyor…")
        self.fix_btn.configure(state="disabled")

        def task() -> str:
            return self.app.gemini.ask(note["content"], system_instruction=_SYS_FIX)

        def on_success(result: str) -> None:
            self.fix_text.delete("1.0", "end")
            self.fix_text.insert("1.0", result)
            self.fix_status.configure(text="Hazır — uygulamadan önce gözden geçirebilirsin.")
            self.fix_btn.configure(state="normal")
            self._last_fixed_note_id = note["id"]

        def on_error(exc: Exception) -> None:
            self.fix_status.configure(text=f"Hata: {exc}")
            self.fix_btn.configure(state="normal")

        run_async(self, task, on_success, on_error)

    def _apply_fix(self) -> None:
        """Düzeltilmiş içeriği ilgili nota uygular (onay sonrası)."""
        fixed = self.fix_text.get("1.0", "end-1c").strip()
        if not fixed or not self._last_fixed_note_id:
            Toast(self.app, "Önce bir düzeltme oluşturun", color=self.app.T["warning"]); return

        if not messagebox.askyesno(
            "Notu Güncelle",
            "Notun içeriği düzeltilmiş metinle değiştirilecek.\n"
            "Not: mevcutt biçimlendirme (kalın/renk vb.) sıfırlanacak. Onaylıyor musun?",
        ):
            return

        note = self.app.manager.get_by_id(self._last_fixed_note_id)
        if not note:
            return

        self.app.manager.update(self._last_fixed_note_id, note["title"], fixed, note["tags"], [], [])
        updated = self.app.manager.get_by_id(self._last_fixed_note_id)
        if self.app.current_note_id == self._last_fixed_note_id and updated:
            self.app._load_note(updated)
        else:
            self.app._refresh_sidebar()
        Toast(self.app, "✓ Not güncellendi", color=self.app.T["primary"])

    # ------------------------------------------------------------------
    # 🔗 BİRLEŞTİR SEKMESİ
    # ------------------------------------------------------------------

    def _build_merge_tab(self) -> None:
        """Not birleştirme arayüzünü oluşturur."""
        tab = self.tab_merge
        tab.grid_rowconfigure(1, weight=1)
        tab.grid_rowconfigure(3, weight=1)
        tab.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            tab,
            text="Birleştirilecek notları seç (örn. aynı dersin farklı haftalardaki notları):",
            font=ctk.CTkFont(size=13),
        ).grid(row=0, column=0, sticky="w", pady=(0, 8))

        self.merge_list_frame = ctk.CTkScrollableFrame(tab, fg_color="transparent", height=170)
        self.merge_list_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 10))
        self.merge_checks: Dict[str, tuple] = {}

        action_row = ctk.CTkFrame(tab, fg_color="transparent")
        action_row.grid(row=2, column=0, sticky="ew")

        self.merge_btn = ctk.CTkButton(
            action_row, text="Seçilenleri Birleştir", command=self._do_merge,
        )
        self.merge_btn.pack(side="left")

        self.merge_status = ctk.CTkLabel(action_row, text="", font=ctk.CTkFont(size=11))
        self.merge_status.pack(side="left", padx=12)

        self.merge_text = ctk.CTkTextbox(tab, wrap="word", font=ctk.CTkFont(size=13), height=200)
        self.merge_text.grid(row=3, column=0, sticky="nsew", pady=(0, 10))

        bottom = ctk.CTkFrame(tab, fg_color="transparent")
        bottom.grid(row=4, column=0, sticky="ew")

        ctk.CTkLabel(bottom, text="Yeni not başlığı:", font=ctk.CTkFont(size=12)).pack(side="left")

        self.merge_title_entry = ctk.CTkEntry(bottom, width=260)
        self.merge_title_entry.pack(side="left", padx=8)

        self.merge_delete_originals_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            bottom, text="Kaynak notları sil",
            variable=self.merge_delete_originals_var, font=ctk.CTkFont(size=11),
        ).pack(side="left", padx=8)

        self.merge_save_btn = ctk.CTkButton(
            bottom, text="Yeni Not Olarak Kaydet", command=self._save_merged_note,
        )
        self.merge_save_btn.pack(side="right")

    def _rebuild_merge_checklist(self, notes: List[Dict]) -> None:
        """
        Birleştirme listesini güncel notlarla yeniden oluşturur.

        Args:
            notes: Gösterilecek not listesi.
        """
        for w in self.merge_list_frame.winfo_children():
            w.destroy()
        self.merge_checks = {}

        for note in notes:
            var = ctk.BooleanVar(value=False)
            label = f"{note['title']}   ·   {note['timestamp']}"
            if note["tags"]:
                label += f"   ·   {', '.join(note['tags'])}"
            chk = ctk.CTkCheckBox(
                self.merge_list_frame, text=label, variable=var,
                font=ctk.CTkFont(size=12),
            )
            chk.pack(anchor="w", pady=3, padx=4)
            self.merge_checks[note["id"]] = (var, note)

    def _do_merge(self) -> None:
        """Seçili notları Gemini'ye birleştirme için gönderir."""
        selected = [n for (var, n) in self.merge_checks.values() if var.get()]
        if len(selected) < 2:
            Toast(self.app, "En az 2 not seçmelisin", color=self.app.T["warning"]); return
        if not self.app.gemini.is_configured():
            Toast(self.app, "AI servisi kullanılamıyor. Ayarlar'dan yapılandırın.",
                  color=self.app.T["warning"]); return

        self.merge_status.configure(text="Birleştiriliyor…")
        self.merge_btn.configure(state="disabled")

        parts = [f"### {n['title']} ({n['timestamp']})\n{n['content']}" for n in selected]
        prompt = "\n\n".join(parts)

        def task() -> str:
            return self.app.gemini.ask(prompt, system_instruction=_SYS_MERGE)

        def on_success(result: str) -> None:
            self.merge_text.delete("1.0", "end")
            self.merge_text.insert("1.0", result)
            self.merge_status.configure(text="Hazır.")
            self.merge_btn.configure(state="normal")
            if not self.merge_title_entry.get().strip():
                self.merge_title_entry.insert(0, f"{selected[0]['title']} (Birleştirilmiş)")
            self._last_merge_sources = [n["id"] for n in selected]

        def on_error(exc: Exception) -> None:
            self.merge_status.configure(text=f"Hata: {exc}")
            self.merge_btn.configure(state="normal")

        run_async(self, task, on_success, on_error)

    def _save_merged_note(self) -> None:
        """Birleştirilen içeriği yeni bir not olarak kaydeder."""
        content = self.merge_text.get("1.0", "end-1c").strip()
        title   = self.merge_title_entry.get().strip() or "Birleştirilmiş Not"
        if not content:
            Toast(self.app, "Önce birleştirme yapmalısın", color=self.app.T["warning"]); return

        # Kaynak notlardan etiketleri topla
        tags: List[str] = []
        for nid in self._last_merge_sources:
            note = self.app.manager.get_by_id(nid)
            if note:
                for t in note["tags"]:
                    if t not in tags:
                        tags.append(t)

        new_note = self.app.manager.create(title, content, tags)

        # İsteğe bağlı: kaynak notları sil
        if self.merge_delete_originals_var.get():
            for nid in self._last_merge_sources:
                if nid != new_note["id"]:
                    self.app.manager.delete(nid)
            if self.app.current_note_id in self._last_merge_sources:
                self.app._show_empty()

        self.app._refresh_sidebar()
        self.refresh_note_lists()
        Toast(self.app, "✓ Birleştirilmiş not kaydedildi", color=self.app.T["primary"])

        # Alanları temizle
        self.merge_text.delete("1.0", "end")
        self.merge_title_entry.delete(0, "end")
        for var, _ in self.merge_checks.values():
            var.set(False)

    # ------------------------------------------------------------------
    # Paylaşılan yardımcılar
    # ------------------------------------------------------------------

    def _note_from_combo(self, combo: ctk.CTkComboBox) -> Optional[Dict]:
        """
        ComboBox'taki seçili etiketten ilgili not sözlüğünü döndürür.

        Args:
            combo: Notları listeleyen ComboBox.

        Returns:
            Not sözlüğü; seçim geçersizse ``None``.
        """
        return self._note_lookup.get(combo.get())

    def refresh_note_lists(self) -> None:
        """
        Tüm sekmelerdeki not listelerini (ComboBox ve onay kutuları)
        mevcut notlarla günceller.
        """
        notes = self.app.manager.notes
        self._note_lookup = {}
        display_values: List[str] = []

        for note in notes:
            label = f"{note['title']} · {note['timestamp']}"
            if label in self._note_lookup:
                label = f"{label} ({note['id'][:4]})"
            self._note_lookup[label] = note
            display_values.append(label)

        if not display_values:
            display_values = ["(henüz not yok)"]

        # Açık notun etiketi (varsa)
        default_label = display_values[0]
        if self.app.current_note_id:
            for lbl, note in self._note_lookup.items():
                if note["id"] == self.app.current_note_id:
                    default_label = lbl
                    break

        for combo in (self.summary_note_combo, self.fix_note_combo):
            combo.configure(values=display_values)
            combo.set(default_label)

        self._rebuild_merge_checklist(notes)

    # ------------------------------------------------------------------
    # Tema
    # ------------------------------------------------------------------

    def _apply_theme(self) -> None:
        """Pencereyi ve tüm bileşenleri geçerli temaya göre renklendirir."""
        T = self.app.T
        self.configure(fg_color=T["editor_bg"])

        try:
            self.tabs.configure(
                fg_color=T["editor_bg"],
                segmented_button_fg_color=T["editor_toolbar"],
                segmented_button_selected_color=T["primary"],
                segmented_button_selected_hover_color=T["primary_hover"],
                segmented_button_unselected_color=T["editor_toolbar"],
                text_color=T["body_fg"],
            )
        except Exception:
            pass

        for tbx in (self.summary_text, self.fix_text, self.merge_text):
            tbx.configure(fg_color=T["editor_bg"], text_color=T["body_fg"])

        for btn in (
            self.summary_btn, self.fix_btn, self.merge_btn,
            self.summary_append_btn, self.fix_apply_btn,
            self.merge_save_btn, self.chat_send_btn,
        ):
            btn.configure(fg_color=T["primary"], hover_color=T["primary_hover"])
