import pytest
from app.localization.manager import LocalizationManager


def test_all_languages_loaded():
    """Verify all 8 requested languages are present and loaded."""
    manager = LocalizationManager()
    expected_languages = {"en", "ru", "uz", "tr", "ar", "de", "fr", "es"}
    loaded = set(manager.available_languages)
    for lang in expected_languages:
        assert lang in loaded, f"Language '{lang}' is missing from loaded locales!"


def test_localization_key_resolutions():
    """Test string translation across languages."""
    manager = LocalizationManager()

    # English
    en_search = manager.get("menu.search", lang="en")
    assert "Search" in en_search

    # Russian
    ru_search = manager.get("menu.search", lang="ru")
    assert "Найти" in ru_search or "Поиск" in ru_search

    # Uzbek
    uz_search = manager.get("menu.search", lang="uz")
    assert "qidirish" in uz_search.lower()

    # Turkish
    tr_search = manager.get("menu.search", lang="tr")
    assert "Ara" in tr_search

    # Arabic
    ar_search = manager.get("menu.search", lang="ar")
    assert "البحث" in ar_search

    # German
    de_search = manager.get("menu.search", lang="de")
    assert "suchen" in de_search.lower()

    # French
    fr_search = manager.get("menu.search", lang="fr")
    assert "Rechercher" in fr_search

    # Spanish
    es_search = manager.get("menu.search", lang="es")
    assert "Buscar" in es_search


def test_placeholder_formatting():
    """Test variable injection into localized strings."""
    manager = LocalizationManager()
    text = manager.get("welcome", lang="en", name="Alice")
    assert "Alice" in text


def test_fallback_behavior():
    """Missing key in specific language should fall back to English or key itself."""
    manager = LocalizationManager()
    # Non-existent language falls back to English
    fallback_text = manager.get("menu.search", lang="non_existent_lang")
    assert "Search" in fallback_text

    # Completely non-existent key returns key name
    missing = manager.get("non.existent.key.xyz", lang="en")
    assert missing == "non.existent.key.xyz"
