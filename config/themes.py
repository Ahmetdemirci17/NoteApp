#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
config/themes.py
================
NoteFlow renk token sözlükleri.

Tüm UI bileşenleri renkleri doğrudan kodlamak yerine buradan okur.
Yeni tema eklemek için bu modüle yeni bir sözlük eklemek yeterlidir.
"""

from typing import Dict

# ---------------------------------------------------------------------------
#  AÇIK TEMA
# ---------------------------------------------------------------------------
LIGHT: Dict[str, str] = {
    # Nav Rail
    "rail_bg":           "#1A1A2E",
    "rail_icon":         "#8892A4",
    "rail_icon_active":  "#FFFFFF",
    "rail_active_bg":    "#252540",

    # Sidebar / Kart
    "sb_bg":             "#F7F6F3",
    "sb_border":         "#E8E6E1",
    "card_bg":           "#F7F6F3",
    "card_hover":        "#EFEDE8",
    "card_selected":     "#FFFFFF",
    "card_border_sel":   "#00A86B",

    # Editör
    "editor_bg":         "#FFFFFF",
    "editor_toolbar":    "#F7F6F3",
    "editor_border":     "#E8E6E1",
    "title_fg":          "#1A1A2E",
    "body_fg":           "#2D2D2D",
    "muted":             "#8892A4",
    "placeholder":       "#B8B4AC",

    # Vurgu renkleri
    "primary":           "#00A86B",
    "primary_hover":     "#008F5A",
    "primary_light":     "#E8F5EF",
    "danger":            "#EF4444",
    "danger_hover":      "#FEE2E2",
    "warning":           "#F59E0B",

    # Seçim / vurgulama
    "select_bg":         "#C6EAD8",
    "select_fg":         "#1A1A2E",
    "highlight_bg":      "#FEF3C7",
    "scrollbar":         "#D4D0C8",

    # AI sohbet balonları
    "bubble_user_bg":    "#00C97E",
    "bubble_user_fg":    "#000000",
    "bubble_model_bg":   "#252535",
    "bubble_model_fg":   "#FFFFFF",

    # Diğer
    "mode_icon":         "🌙",
    "tag_colors":        [
        "#00A86B", "#3B82F6", "#F59E0B",
        "#EF4444", "#8B5CF6", "#EC4899", "#06B6D4",
    ],
}

# ---------------------------------------------------------------------------
#  KARANLIK TEMA
# ---------------------------------------------------------------------------
DARK: Dict[str, str] = {
    # Nav Rail
    "rail_bg":           "#0D0D14",
    "rail_icon":         "#5A6478",
    "rail_icon_active":  "#FFFFFF",
    "rail_active_bg":    "#1A1A2E",

    # Sidebar / Kart
    "sb_bg":             "#161620",
    "sb_border":         "#252535",
    "card_bg":           "#161620",
    "card_hover":        "#1E1E30",
    "card_selected":     "#1E1E30",
    "card_border_sel":   "#00C97E",

    # Editör
    "editor_bg":         "#12121C",
    "editor_toolbar":    "#1A1A28",
    "editor_border":     "#252535",
    "title_fg":          "#E8E6F0",
    "body_fg":           "#C8C5D5",
    "muted":             "#7A7E94",
    "placeholder":       "#4A4A60",

    # Vurgu renkleri
    "primary":           "#00C97E",
    "primary_hover":     "#00E08C",
    "primary_light":     "#0D2B1E",
    "danger":            "#F87171",
    "danger_hover":      "#3D1414",
    "warning":           "#FBBF24",

    # Seçim / vurgulama
    "select_bg":         "#1A3D2B",
    "select_fg":         "#E8E6F0",
    "highlight_bg":      "#3D2E00",
    "scrollbar":         "#33334A",

    # AI sohbet balonları
    "bubble_user_bg":    "#00C97E",
    "bubble_user_fg":    "#0D0D14",
    "bubble_model_bg":   "#1E1E30",
    "bubble_model_fg":   "#C8C5D5",

    # Diğer
    "mode_icon":         "☀️",
    "tag_colors":        [
        "#00C97E", "#60A5FA", "#FBBF24",
        "#F87171", "#A78BFA", "#F472B6", "#22D3EE",
    ],
}

# ---------------------------------------------------------------------------
#  Yardımcı fonksiyon
# ---------------------------------------------------------------------------

def get_theme(dark_mode: bool) -> Dict[str, str]:
    """
    Karanlık mod bayrağına göre doğru tema sözlüğünü döndürür.

    Args:
        dark_mode: True ise DARK, False ise LIGHT tema döner.

    Returns:
        Renk token sözlüğü (Dict[str, str]).
    """
    return DARK if dark_mode else LIGHT
