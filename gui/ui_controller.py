"""
Centralized theme / color controller for BlueVault.

Every other ``gui/ui_*.py`` file should import :data:`theme` from this
module and pull its colors / style kwargs from there instead of using
hard-coded hex literals. This gives us:

* one place to change the palette (so a future visual overhaul is a
  single-file edit instead of a sprawling search-and-replace);
* a working light / dark mode toggle: when the user picks a new theme,
  every window that has registered a rebuild callback gets re-rendered
  with the new palette;
* per-user persistence -- the chosen theme is stored on the
  :class:`~services.settings.SettingsManager` for the logged-in user.

Typical usage in another ``ui_*.py`` file::

    from ui_controller import theme

    self.configure(bg=theme["app_bg"])

    tk.Label(self, text="Hi", **theme.label_style()).pack()
    tk.Entry(self, **theme.entry_style()).pack()
    tk.Button(self, text="OK", **theme.primary_button_style()).pack()

    # Live updates: subscribe a callback that rebuilds the window.
    theme.subscribe(self._apply_theme)

    # On window destroy, unsubscribe so we don't leak.
    self.bind("<Destroy>", lambda e: theme.unsubscribe(self._apply_theme))
"""

from __future__ import annotations

import json
import os
import re
import shutil
import tkinter as tk
from tkinter import ttk
from typing import Callable, Dict, List, Optional, Tuple


# -----------------------------------------------------------------------------
# Palettes
# -----------------------------------------------------------------------------
# Each theme is a mapping of *semantic* role -> hex color. The keys are the
# same across themes so that callers can do ``theme["app_bg"]`` without caring
# which palette is currently active.
#
# When adding a new role, add it to BOTH dictionaries.

LIGHT_THEME: Dict[str, str] = {
    # Surfaces
    "app_bg":            "#f0f0f0",  # outer window background
    "surface_bg":        "#ffffff",  # card / panel background
    "surface_alt_bg":    "#f9f9f9",  # alternate panel background
    "header_bg":         "#e8eaed",  # main-menu header bar
    "section_bg":        "#ffffff",  # settings section card
    "section_border":    "#2196F3",  # accent border around sections

    # Text
    "text_primary":      "#202124",
    "text_secondary":    "#666666",
    "text_muted":        "#888888",
    "text_inverse":      "#ffffff",

    # Accent + brand
    "accent":            "#2196F3",
    "accent_active":     "#1976D2",
    "logo_accent":       "#2196F3",

    # Inputs
    "input_bg":          "#ffffff",
    "input_fg":          "#202124",
    "input_caret":       "#202124",
    "input_border":      "#cccccc",

    # Buttons
    "btn_primary_bg":    "#2196F3",
    "btn_primary_fg":    "#ffffff",
    "btn_primary_active":"#1976D2",
    "btn_secondary_bg":  "#9E9E9E",
    "btn_secondary_fg":  "#ffffff",
    "btn_secondary_active":"#757575",
    "btn_success_bg":    "#4CAF50",
    "btn_warn_bg":       "#FF9800",
    "btn_danger_bg":     "#F44336",

    # Status / scoring (kept consistent across both themes for clarity)
    "status_success":    "#4CAF50",
    "status_warning":    "#FF9800",
    "status_danger":     "#F44336",
    "status_yellow":     "#F9A825",
    "status_orange":     "#FB8C00",
    "status_neutral":    "#666666",

    "score_weak":        "#F44336",
    "score_moderate":    "#FF9800",
    "score_strong":      "#4CAF50",

    # Card overrides used by main-menu account cards
    "card_bg":           "#f9f9f9",
    "card_inner_bg":     "#ffffff",
    "card_label_fg":     "#202124",
}

DARK_THEME: Dict[str, str] = {
    # Surfaces
    "app_bg":            "#23272a",
    "surface_bg":        "#2c2f33",
    "surface_alt_bg":    "#23272a",
    "header_bg":         "#2c2f33",
    "section_bg":        "#2c2f33",
    "section_border":    "#7289da",

    # Text
    "text_primary":      "#ffffff",
    "text_secondary":    "#bbbbbb",
    "text_muted":        "#888888",
    "text_inverse":      "#ffffff",

    # Accent + brand
    "accent":            "#7289da",
    "accent_active":     "#5a6fb5",
    "logo_accent":       "#7289da",

    # Inputs
    "input_bg":          "#2c2f33",
    "input_fg":          "#ffffff",
    "input_caret":       "#ffffff",
    "input_border":      "#444444",

    # Buttons
    "btn_primary_bg":    "#2196F3",
    "btn_primary_fg":    "#ffffff",
    "btn_primary_active":"#1976D2",
    "btn_secondary_bg":  "#4f545c",
    "btn_secondary_fg":  "#ffffff",
    "btn_secondary_active":"#3a3d42",
    "btn_success_bg":    "#43b581",
    "btn_warn_bg":       "#FF9800",
    "btn_danger_bg":     "#F44336",

    # Status / scoring
    "status_success":    "#4CAF50",
    "status_warning":    "#FF9800",
    "status_danger":     "#F44336",
    "status_yellow":     "#F9A825",
    "status_orange":     "#FB8C00",
    "status_neutral":    "#bbbbbb",

    "score_weak":        "#F44336",
    "score_moderate":    "#FF9800",
    "score_strong":      "#4CAF50",

    # Card overrides
    "card_bg":           "#2c2f33",
    "card_inner_bg":     "#23272a",
    "card_label_fg":     "#ffffff",
}

THEMES: Dict[str, Dict[str, str]] = {
    "light": LIGHT_THEME,
    "dark":  DARK_THEME,
}

DEFAULT_THEME_NAME = "dark"


# -----------------------------------------------------------------------------
# ThemeController
# -----------------------------------------------------------------------------
class ThemeController:
    """
    Holds the currently-active palette plus a list of subscribers that
    want to be notified whenever the theme changes.

    Subscribers are simple zero-arg callables (typically a ``rebuild``
    method on a window). On theme change every subscriber is invoked;
    if a subscriber raises ``tk.TclError`` we assume its widget was
    already destroyed and silently drop it.
    """

    def __init__(self, initial: str = DEFAULT_THEME_NAME):
        self._current_name: str = initial if initial in THEMES else DEFAULT_THEME_NAME
        self._subscribers: List[Callable[[], None]] = []
        self._settings_manager = None  # type: ignore[var-annotated]
        # Track which theme names came from user-imported files so we
        # can list/label them separately from the built-ins.
        self._imported_names: List[str] = []
        # Lazily load any previously-imported themes from disk.
        self._load_imported_themes()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def attach_settings(self, settings_manager) -> None:
        """
        Bind the controller to a SettingsManager so that the chosen
        theme is loaded once on attach and persisted on every change.

        Safe to call repeatedly (e.g. on every login).
        """
        self._settings_manager = settings_manager

        try:
            saved = settings_manager.get_theme()
        except Exception as e:
            print(f"[theme] could not read theme from settings: {e}")
            return

        if saved in THEMES and saved != self._current_name:
            self._current_name = saved
            self._notify()

    def detach_settings(self) -> None:
        self._settings_manager = None

    # ------------------------------------------------------------------
    # Imported themes (user-supplied JSON palettes)
    # ------------------------------------------------------------------
    @staticmethod
    def _project_root() -> str:
        # gui/ui_controller.py -> project root is two dirs up.
        return os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..")
        )

    @classmethod
    def _imported_themes_dir(cls) -> str:
        path = os.path.join(cls._project_root(), "user_data", "themes")
        os.makedirs(path, exist_ok=True)
        return path

    @staticmethod
    def _normalize_name(raw: str) -> str:
        """Slugify a theme name -> safe storage key (a-z0-9_)."""
        slug = re.sub(r"[^a-zA-Z0-9_-]+", "_", raw.strip().lower())
        slug = slug.strip("_")
        return slug or "imported"

    @staticmethod
    def _format_label(name: str) -> str:
        """Pretty-cased dropdown label for a theme name."""
        if name in ("light", "dark"):
            return name.capitalize()
        # Replace separators with spaces and title-case.
        return re.sub(r"[_\-]+", " ", name).strip().title()

    def available_themes(self) -> Dict[str, str]:
        """
        Returns an ordered ``{label: name}`` mapping for the theme
        dropdown. Built-ins come first, then any imported themes
        sorted alphabetically.
        """
        out: Dict[str, str] = {}
        for name in ("dark", "light"):
            out[self._format_label(name)] = name
        for name in sorted(self._imported_names):
            out[self._format_label(name)] = name
        return out

    def imported_theme_names(self) -> List[str]:
        return list(self._imported_names)

    def _load_imported_themes(self) -> None:
        """Scan user_data/themes/ on startup and register every JSON."""
        try:
            d = self._imported_themes_dir()
        except Exception as e:
            print(f"[theme] could not access themes dir: {e}")
            return

        for fname in sorted(os.listdir(d)):
            if not fname.lower().endswith(".json"):
                continue
            path = os.path.join(d, fname)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except (OSError, json.JSONDecodeError) as e:
                print(f"[theme] skipping {fname}: {e}")
                continue
            name = self._normalize_name(
                data.get("name") or os.path.splitext(fname)[0]
            )
            palette = self._coerce_palette(data.get("palette") or data)
            if palette is None:
                print(f"[theme] {fname}: invalid palette, skipped.")
                continue
            THEMES[name] = palette
            if name not in self._imported_names and name not in ("light", "dark"):
                self._imported_names.append(name)

    @staticmethod
    def _coerce_palette(raw) -> Optional[Dict[str, str]]:
        """
        Accept a partial palette dict and fill missing keys from the
        DARK_THEME defaults. Reject anything that isn't a dict of
        string-like color values.
        """
        if not isinstance(raw, dict):
            return None
        merged = dict(DARK_THEME)  # safe baseline so missing keys don't crash UI
        for k, v in raw.items():
            if not isinstance(k, str):
                continue
            if not isinstance(v, str):
                continue
            # Light validation: looks like a CSS color (#hex or named)
            if not (v.startswith("#") and 4 <= len(v) <= 9) and not v.isalpha():
                continue
            merged[k] = v
        return merged

    def import_theme(self, json_path: str) -> Tuple[bool, str]:
        """
        Import a theme from a JSON file. Returns (ok, message_or_name).

        Expected format::

            {
                "name": "Solarized Dark",   # optional; falls back to filename
                "palette": {                # required (or top-level keys)
                    "app_bg":   "#002b36",
                    "accent":   "#268bd2",
                    ...
                }
            }

        Missing palette keys are filled from the dark default, so
        partial palettes work. The file is copied into
        ``user_data/themes/`` so the imported theme survives restarts.
        """
        if not os.path.isfile(json_path):
            return False, f"File not found: {json_path}"

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            return False, f"Could not parse JSON: {e}"

        raw_name = data.get("name") or os.path.splitext(
            os.path.basename(json_path)
        )[0]
        name = self._normalize_name(raw_name)
        if name in ("light", "dark"):
            return False, (
                "'light' and 'dark' are reserved theme names; "
                "rename your imported theme."
            )

        palette = self._coerce_palette(data.get("palette") or data)
        if palette is None:
            return False, "Invalid palette: must be a dict of color strings."

        # Persist a normalized copy.
        try:
            dest = os.path.join(self._imported_themes_dir(), f"{name}.json")
            with open(dest, "w", encoding="utf-8") as f:
                json.dump(
                    {"name": name, "palette": palette}, f, indent=2
                )
        except OSError as e:
            return False, f"Could not save imported theme: {e}"

        # Register and notify (so any open settings UI refreshes its
        # dropdown options on the next theme change).
        THEMES[name] = palette
        if name not in self._imported_names:
            self._imported_names.append(name)

        print(f"[theme] imported {name!r} from {json_path}")
        return True, name

    # ------------------------------------------------------------------
    # Palette access
    # ------------------------------------------------------------------
    @property
    def current_name(self) -> str:
        return self._current_name

    @property
    def palette(self) -> Dict[str, str]:
        return THEMES[self._current_name]

    def color(self, key: str, default: str = "#000000") -> str:
        return self.palette.get(key, default)

    # Allow ``theme["app_bg"]`` shorthand.
    def __getitem__(self, key: str) -> str:
        return self.color(key)

    def is_dark(self) -> bool:
        return self._current_name == "dark"

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------
    def set_theme(self, name: str) -> bool:
        """Switch to a named theme. Returns True if the theme is known."""
        if name not in THEMES:
            print(f"[theme] unknown theme {name!r}; ignoring.")
            return False
        if name == self._current_name:
            return True

        print(f"[theme] switching theme: {self._current_name!r} -> {name!r}")
        self._current_name = name
        self._persist()
        self._notify()
        return True

    def toggle(self) -> str:
        """Switch dark <-> light. Returns the new theme's name."""
        new = "light" if self._current_name == "dark" else "dark"
        self.set_theme(new)
        return new

    def _persist(self) -> None:
        if self._settings_manager is None:
            return
        try:
            self._settings_manager.set("theme", self._current_name)
            self._settings_manager.save()
        except Exception as e:
            print(f"[theme] failed to persist theme: {e}")

    # ------------------------------------------------------------------
    # Subscriber registry
    # ------------------------------------------------------------------
    def subscribe(self, callback: Callable[[], None]) -> None:
        """Register a callback that will be invoked on every theme change."""
        if callback not in self._subscribers:
            self._subscribers.append(callback)

    def unsubscribe(self, callback: Callable[[], None]) -> None:
        try:
            self._subscribers.remove(callback)
        except ValueError:
            pass

    def _notify(self) -> None:
        # Copy so subscribers can unsubscribe themselves during the loop.
        for cb in list(self._subscribers):
            try:
                cb()
            except tk.TclError:
                # Widget gone; drop the dead subscriber.
                self.unsubscribe(cb)
            except Exception as e:
                print(f"[theme] subscriber raised {type(e).__name__}: {e}")

    # ------------------------------------------------------------------
    # Style kwarg helpers -- these return dicts you can splat into
    # widget constructors with ``**theme.entry_style()`` etc.
    # ------------------------------------------------------------------
    def label_style(self, *, on: str = "app_bg",
                    fg_role: str = "text_primary") -> dict:
        return {"bg": self[on], "fg": self[fg_role]}

    def entry_style(self) -> dict:
        return {
            "bg": self["input_bg"],
            "fg": self["input_fg"],
            "insertbackground": self["input_caret"],
            "relief": tk.FLAT,
            "highlightthickness": 1,
            "highlightbackground": self["input_border"],
        }

    def text_style(self) -> dict:
        return self.entry_style()

    def primary_button_style(self) -> dict:
        return {
            "font": ("Arial", 12, "bold"),
            "bg": self["btn_primary_bg"],
            "fg": self["btn_primary_fg"],
            "activebackground": self["btn_primary_active"],
            "activeforeground": self["btn_primary_fg"],
            "cursor": "hand2",
            "relief": tk.FLAT,
            "bd": 0,
            "highlightbackground": self["app_bg"],
            "highlightthickness": 0,
        }

    def secondary_button_style(self) -> dict:
        return {
            "font": ("Arial", 11),
            "bg": self["btn_secondary_bg"],
            "fg": self["btn_secondary_fg"],
            "activebackground": self["btn_secondary_active"],
            "activeforeground": self["btn_secondary_fg"],
            "cursor": "hand2",
            "relief": tk.FLAT,
            "bd": 0,
            "highlightbackground": self["app_bg"],
            "highlightthickness": 0,
        }

    def success_button_style(self) -> dict:
        style = self.primary_button_style()
        style["bg"] = self["btn_success_bg"]
        style["activebackground"] = self["btn_success_bg"]
        return style

    def warn_button_style(self) -> dict:
        style = self.primary_button_style()
        style["bg"] = self["btn_warn_bg"]
        style["activebackground"] = self["btn_warn_bg"]
        return style

    def danger_button_style(self) -> dict:
        style = self.primary_button_style()
        style["bg"] = self["btn_danger_bg"]
        style["activebackground"] = self["btn_danger_bg"]
        return style

    def checkbutton_style(self, *, on: str = "app_bg") -> dict:
        return {
            "bg": self[on],
            "fg": self["text_primary"],
            "activebackground": self[on],
            "activeforeground": self["text_primary"],
            "selectcolor": self["surface_bg"],
            "highlightbackground": self[on],
        }

    def labelframe_style(self, *, on: str = "app_bg") -> dict:
        return {
            "bg": self[on],
            "fg": self["text_primary"],
            "highlightbackground": self["section_border"],
            "highlightcolor": self["section_border"],
        }

    def section_frame_style(self) -> dict:
        return {
            "bg": self["section_bg"],
            "highlightbackground": self["section_border"],
            "highlightthickness": 1,
        }

    # ------------------------------------------------------------------
    # ttk styling (combobox, etc.)
    # ------------------------------------------------------------------
    def configure_ttk(self, root: tk.Misc) -> None:
        """
        Apply the current palette to ttk widgets used in BlueVault.
        Call this once after creating a window that uses ttk widgets,
        and again whenever the theme changes.
        """
        try:
            style = ttk.Style(root)
        except tk.TclError:
            return

        # Combobox: the readonly state is what BlueVault uses for the
        # settings dropdowns.
        try:
            style.configure(
                "BlueVault.TCombobox",
                fieldbackground=self["input_bg"],
                background=self["surface_bg"],
                foreground=self["input_fg"],
                arrowcolor=self["text_primary"],
                bordercolor=self["input_border"],
                lightcolor=self["input_border"],
                darkcolor=self["input_border"],
                selectbackground=self["accent"],
                selectforeground=self["btn_primary_fg"],
                insertcolor=self["input_caret"],
            )
            style.map(
                "BlueVault.TCombobox",
                fieldbackground=[
                    ("readonly", self["input_bg"]),
                    ("disabled", self["input_bg"]),
                ],
                foreground=[
                    ("readonly", self["input_fg"]),
                    ("disabled", self["text_muted"]),
                ],
                selectbackground=[
                    ("readonly", self["input_bg"]),
                ],
                selectforeground=[
                    ("readonly", self["input_fg"]),
                ],
                background=[
                    ("readonly", self["surface_bg"]),
                ],
            )
        except tk.TclError:
            pass

        # The Combobox dropdown popup is a tk.Listbox, NOT a ttk widget,
        # so style.configure() does NOT colour it. The popup picks up
        # global tk option_db entries scoped under *TCombobox*Listbox.*.
        # Without these the dropdown text is invisible in dark mode
        # (white-on-white).
        try:
            root.option_add("*TCombobox*Listbox.background", self["input_bg"])
            root.option_add("*TCombobox*Listbox.foreground", self["input_fg"])
            root.option_add(
                "*TCombobox*Listbox.selectBackground", self["accent"]
            )
            root.option_add(
                "*TCombobox*Listbox.selectForeground", self["btn_primary_fg"]
            )
            root.option_add(
                "*TCombobox*Listbox.borderWidth", 0
            )
        except tk.TclError:
            pass

        # Scrollbar: tk.Scrollbar honours bg/troughcolor itself; this
        # block is here in case anyone uses ttk.Scrollbar later.
        try:
            style.configure(
                "BlueVault.Vertical.TScrollbar",
                background=self["surface_bg"],
                troughcolor=self["app_bg"],
                bordercolor=self["input_border"],
                arrowcolor=self["text_primary"],
            )
        except tk.TclError:
            pass


# -----------------------------------------------------------------------------
# Module-level singleton
# -----------------------------------------------------------------------------
# Importers should typically use ``from ui_controller import theme``.
theme = ThemeController()


# Convenience accessor (mirrors the singleton, useful for test injection).
def get_theme() -> ThemeController:
    return theme


# -----------------------------------------------------------------------------
# Public API
# -----------------------------------------------------------------------------
__all__ = [
    "LIGHT_THEME",
    "DARK_THEME",
    "THEMES",
    "DEFAULT_THEME_NAME",
    "ThemeController",
    "theme",
    "get_theme",
]


# Quick self-test
if __name__ == "__main__":
    print("Default theme:", theme.current_name)
    print("Sample colors:")
    for k in ("app_bg", "accent", "btn_primary_bg", "text_primary"):
        print(f"  {k:14s} {theme[k]}")
    theme.toggle()
    print("After toggle:", theme.current_name)
    for k in ("app_bg", "accent", "btn_primary_bg", "text_primary"):
        print(f"  {k:14s} {theme[k]}")
