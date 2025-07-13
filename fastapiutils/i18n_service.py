import json
import os
from typing import Dict, Any, Optional


def _deep_merge_dicts(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries, with override values taking precedence"""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge_dicts(result[key], value)
        else:
            result[key] = value
    return result


class I18nService:
    """Internationalization helper class"""
    
    def __init__(self, custom_locales_dir: Optional[str] = None, default_locale: str = "en"):
        self.default_locale = default_locale
        self._translations: Dict[str, Dict[str, Any]] = {}
        
        # Always load built-in locales first
        self._load_builtin_translations()
        
        # Then load custom locales if provided (these can override built-in ones)
        if custom_locales_dir is not None:
            self._load_custom_translations(custom_locales_dir)
    
    def _load_builtin_translations(self):
        """Load built-in translation files from the package's locales directory"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        builtin_locales_dir = os.path.join(current_dir, 'locales')
        
        if not os.path.exists(builtin_locales_dir):
            return
        
        for filename in os.listdir(builtin_locales_dir):
            if filename.endswith('.json'):
                locale = filename[:-5]  # Remove .json extension
                file_path = os.path.join(builtin_locales_dir, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        self._translations[locale] = json.load(f)
                except Exception as e:
                    print(f"Error loading built-in translation file {filename}: {e}")
    
    def _load_custom_translations(self, custom_locales_dir: str):
        """Load custom translation files that can override built-in translations"""
        if not os.path.exists(custom_locales_dir):
            print(f"Warning: Custom locales directory does not exist: {custom_locales_dir}")
            return
        
        for filename in os.listdir(custom_locales_dir):
            if filename.endswith('.json'):
                locale = filename[:-5]  # Remove .json extension
                file_path = os.path.join(custom_locales_dir, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        custom_translations = json.load(f)
                        
                    # If we already have translations for this locale, merge them
                    if locale in self._translations:
                        self._translations[locale] = _deep_merge_dicts(
                            self._translations[locale], 
                            custom_translations
                        )
                    else:
                        # New locale, just add it
                        self._translations[locale] = custom_translations
                        
                except Exception as e:
                    print(f"Error loading custom translation file {filename}: {e}")
    
    def get_translation(self, key: str, locale: Optional[str] = None, **kwargs) -> str:
        """Get translation for a given key and locale with parameter interpolation"""
        if locale is None:
            locale = self.default_locale
        
        # If locale is not available, fallback to default locale
        if locale not in self._translations:
            locale = self.default_locale
        
        # If default locale is also not available, return the key
        if locale not in self._translations:
            return key
        
        # Navigate through nested keys (e.g., "api.auth.credentials.incorrect_credentials")
        translation = self._translations[locale]
        keys = key.split('.')
        
        try:
            for k in keys:
                translation = translation[k]
            
            # Apply parameter interpolation if kwargs are provided
            if kwargs:
                return translation.format(**kwargs)
            return translation
            
        except (KeyError, TypeError):
            # If key not found, try fallback to default locale
            if locale != self.default_locale:
                return self.get_translation(key, self.default_locale, **kwargs)
            return key
        except (ValueError, KeyError) as e:
            # If string formatting fails, return the unformatted string
            print(f"Warning: Failed to format translation '{key}' with params {kwargs}: {e}")
            try:
                for k in keys:
                    translation = translation[k]
                return translation
            except (KeyError, TypeError):
                return key
    
    def t(self, key: str, locale: Optional[str] = None, **kwargs) -> str:
        """Shorthand for get_translation with parameter interpolation support"""
        return self.get_translation(key, locale, **kwargs)


    def extract_locale_from_header(self, accept_language: Optional[str]) -> str:
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
