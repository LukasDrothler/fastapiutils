import json
import os
from typing import Dict, Any, Optional


class I18n:
    """Internationalization helper class"""
    
    def __init__(self, locales_dir: Optional[str] = None, default_locale: str = "en"):
        self.default_locale = default_locale
        self._translations: Dict[str, Dict[str, Any]] = {}
        
        if locales_dir is None:
            # Use package's default locales directory
            current_dir = os.path.dirname(os.path.abspath(__file__))
            locales_dir = os.path.join(current_dir, 'locales')
        
        self.locales_dir = locales_dir
        self._load_translations()
    
    def _load_translations(self):
        """Load translation files from the locales directory"""
        if not os.path.exists(self.locales_dir):
            return
        
        for filename in os.listdir(self.locales_dir):
            if filename.endswith('.json'):
                locale = filename[:-5]  # Remove .json extension
                file_path = os.path.join(self.locales_dir, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        self._translations[locale] = json.load(f)
                except Exception as e:
                    print(f"Error loading translation file {filename}: {e}")
    
    def get_translation(self, key: str, locale: Optional[str] = None) -> str:
        """Get translation for a given key and locale"""
        if locale is None:
            locale = self.default_locale
        
        # If locale is not available, fallback to default locale
        if locale not in self._translations:
            locale = self.default_locale
        
        # If default locale is also not available, return the key
        if locale not in self._translations:
            return key
        
        # Navigate through nested keys (e.g., "auth.incorrect_credentials")
        translation = self._translations[locale]
        keys = key.split('.')
        
        try:
            for k in keys:
                translation = translation[k]
            return translation
        except (KeyError, TypeError):
            # If key not found, try fallback to default locale
            if locale != self.default_locale:
                return self.get_translation(key, self.default_locale)
            return key
    
    def t(self, key: str, locale: Optional[str] = None) -> str:
        """Shorthand for get_translation"""
        return self.get_translation(key, locale)


def extract_locale_from_header(accept_language: Optional[str]) -> str:
    """Extract locale from Accept-Language header"""
    if not accept_language:
        return "en"
    
    # Parse Accept-Language header (e.g., "en-US,en;q=0.9,de;q=0.8")
    # For simplicity, we'll just take the first language code
    languages = accept_language.split(',')
    if languages:
        # Get the first language and extract just the language code
        first_lang = languages[0].split(';')[0].strip()
        # Extract just the language part (e.g., "en" from "en-US")
        locale = first_lang.split('-')[0].lower()
        return locale
    
    return "en"
