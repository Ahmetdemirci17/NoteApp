#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
services/gemini_service.py
==========================
Google Gemini API istemcisi ve gömülü API anahtarı yönetimi.

Anahtar öncelik sırası:
    1. GEMINI_API_KEY ortam değişkeni
    2. İşletim sistemi kasası (keyring)
    3. Kod içine gömülü XOR+base64 anahtarı (ilk çalıştırmada kasaya aktarılır)

Kullanıcılar kendi anahtarlarını girmek zorunda kalmaz.
"""

from __future__ import annotations

import base64
import json
import os
import threading
import urllib.error
import urllib.request
from typing import Any, Callable, Dict, List, Optional

try:
    import keyring
    _KEYRING_AVAILABLE = True
except ImportError:
    _KEYRING_AVAILABLE = False

# ──────────────────────────────────────────────────────────────────────
#  GÖMÜLܠANAHTAR KONFİGÜRASYONU
#  Kendi anahtarınızı gömmek için:
#      python -c "from services.gemini_service import _encode_key; print(_encode_key('BURAYA_ANAHTARINIZI_YAZIN'))"
#  Çıktıyı _EMBEDDED_KEY değişkenine yapıştırın.
# ──────────────────────────────────────────────────────────────────────
_KR_SERVICE  = "NoteFlowApp"
_KR_USER     = "GeminiAPI"
_XOR_SALT    = b"NoteFlow2024!"   # Obfuscation salt — değiştirmeyin

_EMBEDDED_KEY = "Dz5aJCRUPTkEeUsDbQ0JRwssGhcPVgJfB358KhMSExgFTlFaQ01gLxg2A3UeDVoHeltYEjk="
# ──────────────────────────────────────────────────────────────────────


def _xor_bytes(data: bytes, key: bytes) -> bytes:
    """XOR tabanlı byte karıştırma (obfuscation)."""
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))


def _encode_key(plaintext: str) -> str:
    """
    Düz metin anahtarı XOR+base64 ile kodlar.
    Geliştirici tarafından _EMBEDDED_KEY değerini üretmek için kullanılır.

    Args:
        plaintext: Gemini API anahtarı.

    Returns:
        Kodlanmış anahtar string'i.
    """
    return base64.b64encode(_xor_bytes(plaintext.encode(), _XOR_SALT)).decode()


def _decode_key(encoded: str) -> str:
    """
    XOR+base64 kodlu anahtarı çözer.

    Args:
        encoded: _encode_key() ile üretilmiş string.

    Returns:
        Düz metin API anahtarı.
    """
    return _xor_bytes(base64.b64decode(encoded), _XOR_SALT).decode()


# ──────────────────────────────────────────────────────────────────────
#  Özel istisna
# ──────────────────────────────────────────────────────────────────────

class GeminiError(Exception):
    """Gemini API iletişim hatalarını temsil eder."""


# ──────────────────────────────────────────────────────────────────────
#  Anahtar yönetimi
# ──────────────────────────────────────────────────────────────────────

def get_api_key() -> str:
    """
    API anahtarını öncelik sırasına göre bulur.

    Sıra:
        1. GEMINI_API_KEY ortam değişkeni
        2. keyring kasası
        3. Gömülü XOR+base64 anahtar (_EMBEDDED_KEY) — ilk kullanımda kasaya kaydedilir

    Returns:
        Bulunan API anahtarı; hiçbiri yoksa boş string.
    """
    # 1. Ortam değişkeni
    env_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if env_key:
        return env_key

    # 2. Keyring kasası
    if _KEYRING_AVAILABLE:
        try:
            stored = keyring.get_password(_KR_SERVICE, _KR_USER)
            if stored:
                return stored.strip()
        except Exception:
            pass

    # 3. Gömülü anahtar → çöz ve kasaya yaz
    if _EMBEDDED_KEY:
        try:
            key = _decode_key(_EMBEDDED_KEY)
            if key:
                # İlk çalıştırmada kasaya aktar; sonraki çalıştırmalarda 2. adımdan gelir
                if _KEYRING_AVAILABLE:
                    try:
                        keyring.set_password(_KR_SERVICE, _KR_USER, key)
                    except Exception:
                        pass
                return key
        except Exception:
            pass

    return ""


def save_api_key(api_key: str) -> bool:
    """
    API anahtarını keyring kasasına kaydeder (Ayarlar penceresinden manuel giriş için).

    Args:
        api_key: Kaydedilecek API anahtarı.

    Returns:
        Başarılıysa True.
    """
    if not _KEYRING_AVAILABLE:
        return False
    try:
        keyring.set_password(_KR_SERVICE, _KR_USER, api_key.strip())
        return True
    except Exception as exc:
        print(f"[GeminiService] Keyring yazma hatası: {exc}")
        return False


# ──────────────────────────────────────────────────────────────────────
#  Asenkron çalıştırıcı
# ──────────────────────────────────────────────────────────────────────

def run_async(
    widget: Any,
    fn: Callable,
    on_success: Callable,
    on_error: Optional[Callable] = None,
) -> None:
    """
    fn() işlevini arka planda daemon thread'de çalıştırır;
    sonucu widget.after() ile ana Tk thread'ine iletir.

    Args:
        widget:     Tk bileşeni (after metodu için).
        fn:         Arka planda çalışacak işlev.
        on_success: Başarı callback'i — fn() sonucunu alır.
        on_error:   Hata callback'i — Exception alır.
    """
    def _worker() -> None:
        try:
            result = fn()
        except Exception as exc:
            if on_error:
                widget.after(0, lambda e=exc: on_error(e))
            return
        widget.after(0, lambda r=result: on_success(r))

    threading.Thread(target=_worker, daemon=True).start()


# ──────────────────────────────────────────────────────────────────────
#  Gemini İstemcisi
# ──────────────────────────────────────────────────────────────────────

class GeminiClient:
    """
    Google Gemini REST API istemcisi.
    Sadece standart kütüphane urllib kullanır, harici HTTP paketi gerekmez.

    Attributes:
        model: Kullanılan Gemini model adı.
    """

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

    def __init__(self, model: str = "gemini-2.5-flash") -> None:
        """
        Args:
            model: Gemini model adı (örn. "gemini-2.5-flash").
        """
        self.model = model

    def is_configured(self) -> bool:
        """API anahtarının mevcut olup olmadığını kontrol eder."""
        return bool(get_api_key())

    def _post(
        self,
        contents: List[Dict],
        system_instruction: Optional[str] = None,
        temperature: float = 0.4,
    ) -> str:
        """
        Gemini uç noktasına POST isteği gönderir.

        Args:
            contents:           Gemini formatında mesaj listesi.
            system_instruction: İsteğe bağlı sistem talimatı.
            temperature:        Yanıt çeşitliliği (0.0–1.0).

        Returns:
            Modelin metin yanıtı.

        Raises:
            GeminiError: Anahtar eksik, HTTP hatası veya bağlantı sorunu.
        """
        api_key = get_api_key()
        if not api_key:
            raise GeminiError(
                "AI servisi şu an kullanılamıyor. Lütfen yöneticiyle iletişime geçin."
            )

        url  = f"{self.BASE_URL}/{self.model}:generateContent"
        body: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": {"temperature": temperature},
        }
        if system_instruction:
            body["systemInstruction"] = {"parts": [{"text": system_instruction}]}

        payload = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(url, data=payload, method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("x-goog-api-key", api_key)

        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body_text = ""
            try:
                body_text = exc.read().decode("utf-8", errors="ignore")
            except Exception:
                pass
            raise GeminiError(
                f"API hatası ({exc.code}): {(body_text or exc.reason)[:300]}"
            ) from exc
        except urllib.error.URLError as exc:
            raise GeminiError(f"Bağlantı hatası: {exc.reason}") from exc
        except TimeoutError as exc:
            raise GeminiError("İstek zaman aşımına uğradı (60 s).") from exc

        try:
            parts = result["candidates"][0]["content"]["parts"]
            return "".join(p.get("text", "") for p in parts).strip()
        except (KeyError, IndexError, TypeError) as exc:
            if "promptFeedback" in result:
                raise GeminiError(
                    "İstek güvenlik filtresine takıldı veya boş yanıt döndü."
                ) from exc
            raise GeminiError("Yanıt ayrıştırılamadı.") from exc

    def ask(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.4,
    ) -> str:
        """
        Tek turlu soru–yanıt isteği.

        Args:
            prompt:             Kullanıcı metni.
            system_instruction: İsteğe bağlı sistem talimatı.
            temperature:        Yanıt çeşitliliği.

        Returns:
            Modelin metin yanıtı.
        """
        contents = [{"role": "user", "parts": [{"text": prompt}]}]
        return self._post(contents, system_instruction=system_instruction,
                          temperature=temperature)

    def chat(
        self,
        history: List[Dict[str, str]],
        system_instruction: Optional[str] = None,
        temperature: float = 0.4,
    ) -> str:
        """
        Çok turlu sohbet isteği.

        Args:
            history:            [{"role": "user"|"model", "text": "..."}] listesi.
            system_instruction: İsteğe bağlı sistem talimatı.
            temperature:        Yanıt çeşitliliği.

        Returns:
            Modelin metin yanıtı.
        """
        contents = [
            {"role": h["role"], "parts": [{"text": h["text"]}]}
            for h in history
        ]
        return self._post(contents, system_instruction=system_instruction,
                          temperature=temperature)
