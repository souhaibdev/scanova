import json
import os
import weakref

from PyQt6.QtCore import Qt, QObject, pyqtSignal

from utils.file_utils import load_json, save_json
from utils.storage import BASE_DIR

TRANSLATIONS_DIR = os.path.join(os.path.dirname(__file__), "translations")
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")


class TranslationManager(QObject):
    language_changed = pyqtSignal(str)
    _instance = None

    SUPPORTED_LANGUAGES = {
        "en": "English",
        "ar": "العربية",
    }

    def __init__(self):
        super().__init__()
        self._bindings: list[tuple[weakref.ReferenceType, str, str]] = []
        self._table_bindings: list[tuple[weakref.ReferenceType, list[str]]] = []
        self._combo_bindings: list[tuple[weakref.ReferenceType, list[tuple[str, str]]]] = []

        self._current_language = self._load_language()
        self._translations = self._load_translation_file(self._current_language)

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = TranslationManager()
        return cls._instance

    @property
    def current_language(self) -> str:
        return self._current_language

    @property
    def qt_layout_direction(self) -> Qt.LayoutDirection:
        return Qt.LayoutDirection.RightToLeft if self._current_language == "ar" else Qt.LayoutDirection.LeftToRight

    def _load_language(self) -> str:
        settings = load_json("settings.json")
        lang = settings.get("language", "en")
        if lang not in self.SUPPORTED_LANGUAGES:
            lang = "en"
        return lang

    def _load_translation_file(self, lang: str) -> dict:
        path = os.path.join(TRANSLATIONS_DIR, f"{lang}.json")
        if not os.path.exists(path):
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def t(self, key: str, **kwargs) -> str:
        text = self._translations.get(key)
        if text is None and self._current_language != "en":
            text = self._load_translation_file("en").get(key)
        if text is None:
            text = key
        try:
            return text.format(**kwargs)
        except Exception:
            return text

    def set_language(self, lang: str):
        if lang not in self.SUPPORTED_LANGUAGES:
            return
        if self._current_language == lang:
            return
        self._current_language = lang
        self._translations = self._load_translation_file(lang)
        self._save_settings()
        self.translate_all()
        self.language_changed.emit(lang)

    def _save_settings(self):
        save_json("settings.json", {"language": self._current_language})

    def bind_text(self, widget, key: str):
        self._bindings.append((weakref.ref(widget), key, "text"))
        widget.setText(self.t(key))

    def bind_placeholder(self, widget, key: str):
        self._bindings.append((weakref.ref(widget), key, "placeholder"))
        widget.setPlaceholderText(self.t(key))

    def bind_tooltip(self, widget, key: str):
        self._bindings.append((weakref.ref(widget), key, "tooltip"))
        widget.setToolTip(self.t(key))

    def bind_table_headers(self, table, keys: list[str]):
        self._table_bindings.append((weakref.ref(table), keys))
        table.setHorizontalHeaderLabels([self.t(key) for key in keys])

    def bind_combo_items(self, combo, items: list[tuple[str, str]]):
        self._combo_bindings.append((weakref.ref(combo), items))
        self._update_combo_items(combo, items)

    def _update_combo_items(self, combo, items: list[tuple[str, str]]):
        current_data = combo.currentData()
        combo.blockSignals(True)
        combo.clear()
        for key, data in items:
            combo.addItem(self.t(key), data)
        if current_data is not None:
            index = combo.findData(current_data)
            if index >= 0:
                combo.setCurrentIndex(index)
        combo.blockSignals(False)

    def translate_all(self):
        for ref, key, kind in self._bindings:
            widget = ref()
            if widget is None:
                continue
            if kind == "text":
                widget.setText(self.t(key))
            elif kind == "placeholder":
                widget.setPlaceholderText(self.t(key))
            elif kind == "tooltip":
                widget.setToolTip(self.t(key))

        for ref, keys in self._table_bindings:
            table = ref()
            if table is None:
                continue
            table.setHorizontalHeaderLabels([self.t(key) for key in keys])

        for ref, items in self._combo_bindings:
            combo = ref()
            if combo is None:
                continue
            self._update_combo_items(combo, items)

    def supported_languages(self) -> list[tuple[str, str]]:
        return list(self.SUPPORTED_LANGUAGES.items())
