import pywikibot

# Configuration of site and main category
site = pywikibot.Site('commons', 'commons')
category = pywikibot.Category(site, 'Category:YOUR_MAIN_CATEGORY')

# Replacement table: Old texts -> New texts
replacements = {
    'Old category name 1': 'New category name 1',
    'Old category name 2': 'New category name 2',
    'Old category name 3': 'New category name 3'
    # Add more replacements as needed
}

# Function that replaces texts in categories
def replace_text_in_page(page, replacements):
    text = page.text
    original_text = text  # Save text before changes

    # Iterate through the replacement table and make replacements
    for old_text, new_text in replacements.items():
        text = text.replace(old_text, new_text)

    # Check if the text has changed, and only then save
    if text != original_text:
        summary = "pwb: Category renamed"
        page.text = text
        try:
            page.save(summary=summary)
            print(f'Successfully updated: {page.title()}')
        except Exception as e:
            print(f'Error saving page {page.title()}: {e}')
    else:
        print(f'No changes needed for: {page.title()}')

# Process all files and pages in subcategories of the main category
def main():
    for subcategory in category.subcategories(recurse=True):
        print(f'Checking subcategory: {subcategory.title()}')

        # Check each page in the subcategory
        for page in subcategory.articles():
            print(f'Checking page: {page.title()}')
            replace_text_in_page(page, replacements)

if __name__ == "__main__":
    main()
