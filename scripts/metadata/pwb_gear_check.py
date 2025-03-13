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

# List for files with missing gear information
gear_files = []

# Regular expression to find specific gear structures
gear_pattern = re.compile(r'Gear/(CAMERA|LENS)')

# Process each file
def main():
    for file_page in file_generator:
        if not file_page.exists() or file_page.namespace() != 6:  # Namespace 6 = File namespace
            continue

        print(f"Checking file: {file_page.title()}")

        # Load the file's text
        text = file_page.text

        # Check for the presence of specific gear terms
        if gear_pattern.search(text):
            print(f"Gear found in: {file_page.title()}")
            gear_files.append(f"* [[:{file_page.title()}]]\n")
        else:
            print(f"No gear found in: {file_page.title()}")

    # If there are files with gear information, save to user page
    if gear_files:
        try:
            # Create content for the user page
            page_content = "The following files are missing camera/lens information:\n\n"
            page_content += ''.join(gear_files)

            # Update user page
            user_page = pywikibot.Page(site, 'User:YOUR_USERNAME/pwb/Equipment')
            user_page.text = page_content
            user_page.save(summary="Updated list of files without camera/lens information.")
            print(f"Page {user_page.title()} successfully updated.")
        except Exception as e:
            print(f"Error updating page {user_page.title()}: {e}")
    else:
        print("No files without camera/lens information found.")

    # Count the number of files in category "Category:YOUR_UPLOADS_CATEGORY"
    try:
        pwb_meta_category = pywikibot.Category(site, 'Category:YOUR_UPLOADS_CATEGORY')
        pwb_meta_files = list(pagegenerators.CategorizedPageGenerator(pwb_meta_category, recurse=False))
        meta_file_count = len(pwb_meta_files)
        print(f"Number of files in category 'YOUR_UPLOADS_CATEGORY': {meta_file_count}")
    except Exception as e:
        print(f"Error counting files in category 'YOUR_UPLOADS_CATEGORY': {e}")
        meta_file_count = "none"  # In case of error

    # Update the user page "User:YOUR_USERNAME/pwb" with the current number of files in the category "YOUR_UPLOADS_CATEGORY"
    try:
        # Load the page
        pwb_page = pywikibot.Page(site, 'User:YOUR_USERNAME/pwb')
        pwb_text = pwb_page.text

        # Count the number of files on the page "User:YOUR_USERNAME/pwb/Equipment"
        gear_file_count = len(gear_files)

        # Update text for gear files
        updated_text = re.sub(
            r"User:YOUR_USERNAME/pwb/Equipment \((\d+|none)\)",
            f"User:YOUR_USERNAME/pwb/Equipment ({gear_file_count})",
            updated_text
        )

        # Check if updates are necessary
        if pwb_text != updated_text:
            pwb_page.text = updated_text
            pwb_page.save(summary="pwb: Gear updated")
            print(f"Page {pwb_page.title()} successfully updated.")
        else:
            print(f"Page {pwb_page.title()} does not need updating.")
    except Exception as e:
        print(f"Error updating page {pwb_page.title()}: {e}")

if __name__ == "__main__":
    main()
