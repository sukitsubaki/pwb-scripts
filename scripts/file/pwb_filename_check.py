#!/usr/bin/python
# -*- coding: utf-8 -*-

import pywikibot
from pywikibot import pagegenerators
import re

# Site and category definition
site = pywikibot.Site('commons', 'commons')
category = pywikibot.Category(site, 'Category:YOUR_UPLOADS_CATEGORY')

# Generator to process files in the category
file_generator = pagegenerators.CategorizedPageGenerator(category, recurse=False)

# Lists for files matching different criteria
non_matching_files = []  # Files without "--" in filename
long_files = []  # Files with too long filename

# Process each file
def main():
    for file_page in file_generator:
        if not file_page.exists() or file_page.namespace() != 6:  # Namespace 6 = File namespace
            continue

        file_title = file_page.title()
        print(f"Checking file: {file_title}")

        # Check if the filename contains the characters "--"
        if "--" not in file_title:
            print(f"File does not contain '--': {file_title}")
            non_matching_files.append(f"* [[:{file_title}]]\n")
        else:
            print(f"File is OK (contains '--'): {file_title}")

        # Check if the filename is too long (more than 100 characters)
        if len(file_title) > 100:
            print(f"Filename too long: {file_title}")
            long_files.append(f"* [[:{file_title}]] ({len(file_title)} characters)\n")

    # Count files listed in the report
    file_count = len(non_matching_files) + len(long_files)
    file_count_str = str(file_count) if file_count > 0 else "none"

if __name__ == "__main__":
    main()
