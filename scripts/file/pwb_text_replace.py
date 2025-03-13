#!/usr/bin/python
# -*- coding: utf-8 -*-

import pywikibot
from pywikibot import pagegenerators

# Site and category definition
site = pywikibot.Site('commons', 'commons')
category = pywikibot.Category(site, 'YOUR_PHOTO_CATEGORY/ID')

# Generator to process files in the category
file_generator = pagegenerators.CategorizedPageGenerator(category, recurse=False)

# Text to be replaced
text_to_replace = [
    ''
]

# Process each file
def main():
    for file_page in file_generator:
        if not file_page.exists() or file_page.namespace() != 6:  # Namespace 6 = File namespace
            continue

        print(f"Processing file: {file_page.title()}")

        # Load file text
        text = file_page.text
        original_text = text

        # Check and remove text
        for text_to_replace in text_to_replace:
            if text_to_replace in text:
                print(f"Removing '{text_to_replace}' from {file_page.title()}")
                text = text.replace(text_to_replace, '')

        # If changes were made, save the file
        if text != original_text:
            file_page.text = text
            try:
                file_page.save(summary="pwb: Removed text")
                print(f"Changes for {file_page.title()} successfully saved.")
            except Exception as e:
                print(f"Error saving changes: {e}")
        else:
            print(f"No changes required for {file_page.title()}.")

if __name__ == "__main__":
    main()
