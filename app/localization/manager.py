import json
from pathlib import Path
from typing import Dict, Any, Optional
from loguru import logger


class LocalizationManager:
    """Manages multi-language translations with fallback support."""

    def __init__(self, locales_dir: Optional[Path] = None, default_lang: str = "en"):
        self.default_lang = default_lang
        self.locales_dir = locales_dir or Path(__file__).parent / "locales"
        self._translations: Dict[str, Dict[str, Any]] = {}
        self.load_translations()

    def load_translations(self) -> None:
        """Load all JSON translation files from locales directory."""
        if not self.locales_dir.exists():
            logger.warning(f"Locales directory does not exist: {self.locales_dir}")
            return

        for json_path in self.locales_dir.glob("*.json"):
            lang_code = json_path.stem.lower()
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    self._translations[lang_code] = json.load(f)
                logger.debug(f"Loaded locale: {lang_code}")
            except Exception as e:
                logger.error(f"Failed to load locale {json_path}: {e}")

    def get(self, key: str, lang: str = "en", **kwargs) -> str:
        """
        Get translation string by dot-separated key, with fallback to default_lang.
        Supports formatting kwargs, e.g. t('book.details', title='Python 101').
        """
        lang = (lang or self.default_lang).lower()
        text = self._resolve_key(lang, key)

        if text is None and lang != self.default_lang:
            text = self._resolve_key(self.default_lang, key)

        if text is None:
            # Fallback to key itself if missing completely
            return key

        if kwargs:
            try:
                return text.format(**kwargs)
            except KeyError as e:
                logger.warning(f"Missing placeholder {e} in key '{key}' for lang '{lang}'")
                return text
            except Exception:
                return text

        return text

    def _resolve_key(self, lang: str, key: str) -> Optional[str]:
        """Traverse nested dictionary by dot notation."""
        data = self._translations.get(lang)
        if not data:
            return None

        parts = key.split(".")
        current = data
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None

        return str(current) if not isinstance(current, (dict, list)) else None

    @property
    def available_languages(self) -> list[str]:
        """Return list of loaded language codes."""
        return list(self._translations.keys())


# Singleton instance
i18n = LocalizationManager()
