#!/usr/bin/python
# -*- coding: utf-8 -*-

import pywikibot
from pywikibot import pagegenerators
import re
from collections import Counter, defaultdict
import argparse

"""
pwb_category_suggest.py - Suggests categories for files

This script analyzes existing categories on similar images and suggests
additional relevant categories that might be appropriate for your files.

Features:
- Finds related files based on filename patterns or existing categories
- Analyzes category patterns across similar files
- Suggests additional categories based on frequency and relevance
- Can be run in batch mode or interactive mode

Usage:
    python pwb_category_suggest.py --file "File:Example.jpg"
    python pwb_category_suggest.py --category "Category:Your_uploads"
    python pwb_category_suggest.py --interactive
"""

# Site configuration
site = pywikibot.Site('commons', 'commons')

def extract_categories(text):
    """Extract all categories from file description."""
    category_pattern = r'\[\[Category:([^\]|]+)(?:\|[^\]]+)?\]\]'
    return [cat.strip() for cat in re.findall(category_pattern, text, re.IGNORECASE)]

def get_file_categories(file_page):
    """Get all categories for a file."""
    if not file_page.exists():
        return []
    
    return extract_categories(file_page.text)

def find_similar_files(file_page, max_files=50):
    """Find similar files based on filename patterns."""
    similar_files = []
    
    # Get the base file name without File: prefix
    file_name = file_page.title(with_ns=False)
    
    # Extract meaningful parts of the filename (e.g., location, subject)
    name_parts = re.split(r'[-_,\s.]', file_name)
    name_parts = [part for part in name_parts if len(part) > 3]  # Filter out short parts
    
    # Get existing categories for the file
    file_categories = get_file_categories(file_page)
    
    # Find similar files based on filename patterns
    for part in name_parts:
        if len(part) < 4:
            continue
            
        # Search for files with similar name parts
        search_term = f"insource:/{part}/i"
        search_gen = pagegenerators.SearchPageGenerator(search_term, namespaces=[6], total=20)
        
        for similar_page in search_gen:
            if similar_page.title() != file_page.title() and similar_page not in similar_files:
                similar_files.append(similar_page)
                
                # Limit the number of similar files
                if len(similar_files) >= max_files // 2:
                    break
    
    # Also find files in the same categories (if not enough found by filename)
    if file_categories and len(similar_files) < max_files:
        for category_name in file_categories:
            try:
                category = pywikibot.Category(site, f"Category:{category_name}")
                if not category.exists():
                    continue
                    
                # Get files in this category
                category_files = list(category.articles(namespaces=[6]))
                
                # Add unique files
                for cat_file in category_files:
                    if cat_file.title() != file_page.title() and cat_file not in similar_files:
                        similar_files.append(cat_file)
                        
                        # Break if we have enough files
                        if len(similar_files) >= max_files:
                            break
                
                if len(similar_files) >= max_files:
                    break
            except Exception as e:
                print(f"Error processing category {category_name}: {e}")
    
    return similar_files

def suggest_categories(file_page, similar_files=None, min_occurrence=2):
    """Suggest categories based on similar files."""
    if not similar_files:
        similar_files = find_similar_files(file_page)
    
    if not similar_files:
        print(f"No similar files found for {file_page.title()}")
        return []
    
    # Get current categories of the file
    current_categories = set(get_file_categories(file_page))
    
    # Collect categories from similar files
    all_categories = []
    for similar_file in similar_files:
        similar_cats = get_file_categories(similar_file)
        all_categories.extend(similar_cats)
    
    # Count occurrences of each category
    category_counts = Counter(all_categories)
    
    # Filter out categories that are already on the file
    # or don't appear with minimum frequency
    suggested_categories = []
    for category, count in category_counts.items():
        if category not in current_categories and count >= min_occurrence:
            suggested_categories.append((category, count))
    
    # Sort by frequency (most common first)
    suggested_categories.sort(key=lambda x: x[1], reverse=True)
    
    return suggested_categories

def process_file(file_title, add_categories=False):
    """Process a single file by title."""
    # Ensure title has File: prefix
    if not file_title.startswith('File:'):
        file_title = f'File:{file_title}'
    
    # Get file page
    file_page = pywikibot.Page(site, file_title)
    
    if not file_page.exists():
        print(f"Error: File {file_title} does not exist")
        return False
    
    print(f"Finding similar files to {file_title}...")
    similar_files = find_similar_files(file_page)
    print(f"Found {len(similar_files)} similar files")
    
    # Get category suggestions
    suggestions = suggest_categories(file_page, similar_files)
    
    if not suggestions:
        print("No category suggestions found")
        return False
    
    # Display suggestions
    print("\nSuggested categories:")
    for i, (category, count) in enumerate(suggestions):
        print(f"{i+1}. {category} (found in {count} similar files)")
    
    if add_categories:
        selected = input("\nEnter numbers of categories to add (comma-separated) or 'all' for all: ")
        
        categories_to_add = []
        if selected.lower() == 'all':
            categories_to_add = [cat for cat, _ in suggestions]
        else:
            try:
                indices = [int(idx.strip()) - 1 for idx in selected.split(',') if idx.strip()]
                for idx in indices:
                    if 0 <= idx < len(suggestions):
                        categories_to_add.append(suggestions[idx][0])
            except ValueError:
                print("Invalid input")
                return False
        
        if categories_to_add:
            # Add selected categories to the file
            text = file_page.text
            new_text = text
            for category in categories_to_add:
                category_tag = f"[[Category:{category}]]"
                if category_tag not in new_text:
                    new_text += f"\n{category_tag}"
            
            # Save changes
            if new_text != text:
                file_page.text = new_text
                file_page.save(summary="pwb: Added suggested categories")
                print(f"Added {len(categories_to_add)} categories to {file_title}")
                return True
    
    return False

def process_category(category_name, add_categories=False, min_occurrence=2):
    """Process all files in a category."""
    # Ensure category has Category: prefix
    if not category_name.startswith('Category:'):
        category_name = f'Category:{category_name}'
    
    # Get category
    cat = pywikibot.Category(site, category_name)
    
    if not cat.exists():
        print(f"Error: Category {category_name} does not exist")
        return 0
    
    # Get files in category
    files = list(cat.articles(namespaces=6))  # Namespace 6 = File
    
    if not files:
        print(f"No files found in {category_name}")
        return 0
    
    print(f"Found {len(files)} files in {category_name}")
    
    updated = 0
    for i, file_page in enumerate(files):
        print(f"\nProcessing file {i+1}/{len(files)}: {file_page.title()}")
        
        # Find similar files
        similar_files = find_similar_files(file_page)
        print(f"Found {len(similar_files)} similar files")
        
        # Get category suggestions
        suggestions = suggest_categories(file_page, similar_files, min_occurrence)
        
        if not suggestions:
            print("No category suggestions found")
            continue
        
        # Display suggestions
        print("\nSuggested categories:")
        for j, (category, count) in enumerate(suggestions):
            print(f"{j+1}. {category} (found in {count} similar files)")
        
        if add_categories:
            selected = input("\nEnter numbers of categories to add (comma-separated), 'all', 'skip', or 'quit': ")
            
            if selected.lower() == 'quit':
                print("Operation cancelled")
                break
                
            if selected.lower() == 'skip':
                print("Skipped this file")
                continue
            
            categories_to_add = []
            if selected.lower() == 'all':
                categories_to_add = [cat for cat, _ in suggestions]
            else:
                try:
                    indices = [int(idx.strip()) - 1 for idx in selected.split(',') if idx.strip()]
                    for idx in indices:
                        if 0 <= idx < len(suggestions):
                            categories_to_add.append(suggestions[idx][0])
                except ValueError:
                    print("Invalid input, skipping this file")
                    continue
            
            if categories_to_add:
                # Add selected categories to the file
                text = file_page.text
                new_text = text
                for category in categories_to_add:
                    category_tag = f"[[Category:{category}]]"
                    if category_tag not in new_text:
                        new_text += f"\n{category_tag}"
                
                # Save changes
                if new_text != text:
                    file_page.text = new_text
                    file_page.save(summary="pwb: Added suggested categories")
                    print(f"Added {len(categories_to_add)} categories to {file_page.title()}")
                    updated += 1
    
    return updated

def interactive_mode():
    """Interactive mode for suggesting categories."""
    print("=== PWB Category Suggestion Tool ===")
    
    while True:
        print("\nOptions:")
        print("1. Process single file")
        print("2. Process all files in a category")
        print("3. Exit")
        
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == '1':
            file_title = input("Enter file title (with or without 'File:' prefix): ").strip()
            add_cats = input("Add categories to file? (y/n): ").lower() == 'y'
            process_file(file_title, add_cats)
        
        elif choice == '2':
            category_name = input("Enter category name (with or without 'Category:' prefix): ").strip()
            add_cats = input("Add categories to files? (y/n): ").lower() == 'y'
            min_occurrence = int(input("Minimum occurrence threshold (default 2): ") or 2)
            updated = process_category(category_name, add_cats, min_occurrence)
            print(f"\nUpdated {updated} files")
        
        elif choice == '3':
            print("Exiting...")
            break
        
        else:
            print("Invalid choice")

def main():
    """Main function to handle command line arguments."""
    parser = argparse.ArgumentParser(description='Suggest categories for files on Wikimedia Commons')
    
    # Create mutually exclusive group for the modes
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--file', help='Process a single file')
    group.add_argument('--category', help='Process all files in a category')
    group.add_argument('--interactive', action='store_true', help='Run in interactive mode')
    
    # Additional arguments
    parser.add_argument('--add', action='store_true', help='Add suggested categories to files')
    parser.add_argument('--min', type=int, default=2, help='Minimum occurrence threshold (default: 2)')
    
    args = parser.parse_args()
    
    if args.interactive:
        interactive_mode()
    elif args.file:
        process_file(args.file, args.add)
    elif args.category:
        updated = process_category(args.category, args.add, args.min)
        print(f"\nUpdated {updated} files")

if __name__ == "__main__":
    main()