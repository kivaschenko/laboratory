#!/usr/bin/env python3
"""
Test script for i18n functionality
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from pyramid.config import Configurator
from pyramid.i18n import get_localizer, TranslationStringFactory


# Test the translation setup
def test_i18n():
    print("Testing i18n setup...")

    # Test TranslationStringFactory
    _ = TranslationStringFactory("laboratory")

    # Test some translation strings
    test_strings = [
        "app.title",
        "navigation.home",
        "navigation.warehouse",
        "substances.catalog_title",
        "auth.login_failed",
    ]

    for locale in ["en", "uk"]:
        print(f"\n--- Testing locale: {locale} ---")

        # Create a minimal config for testing
        with Configurator() as config:
            config.add_translation_dirs("locale/")

            # Test if translation files exist
            locale_dir = f"locale/{locale}/LC_MESSAGES"
            po_file = f"{locale_dir}/laboratory.po"
            mo_file = f"{locale_dir}/laboratory.mo"

            print(f"PO file exists: {os.path.exists(po_file)}")
            print(f"MO file exists: {os.path.exists(mo_file)}")

            if os.path.exists(mo_file):
                print(f"MO file size: {os.path.getsize(mo_file)} bytes")

            # Test some translations
            for string_id in test_strings:
                trans_string = _(string_id)
                print(f"  {string_id}: {trans_string}")


if __name__ == "__main__":
    test_i18n()
