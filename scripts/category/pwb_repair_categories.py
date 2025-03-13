#!/usr/bin/python
# -*- coding: utf-8 -*-

import pywikibot
from pywikibot import pagegenerators
import re
import argparse
from collections import defaultdict

"""
pwb_repair_categories.py - Find and repair category issues

This script helps fix several common category issues:
- Missing parent categories
- Broken category hierarchies
- Duplicate or redundant categories
- Orphaned categories
- Misplaced categories

Features:
- Analyzes category structure
- Suggests category improvements
- Can automatically fix common issues
- Creates a report of issues found

Usage:
    python pwb_repair_categories.py --user "YOUR_USERNAME"
    python pwb_repair_categories.py --category "Category:Your_uploads"
    python pwb_repair_categories.py --analyze "Category:Your_category"
    python pwb_repair_categories.py --interactive
"""

# Site configuration
site = pywikibot.Site('commons', 'commons')

def extract_categories(text):
    """Extract all categories from wiki text."""
    category_pattern = r'\[\[Category:([^\]|]+)(?:\|[^\]]+)?\]\]'
    return [cat.strip() for cat in re.findall(category_pattern, text, re.IGNORECASE)]

def get_parent_categories(category_page):
    """Get parent categories of a category."""
    try:
        # Extract categories from the category page text
        return extract_categories(category_page.text)
    except Exception as e:
        print(f"Error getting parent categories for {category_page.title()}: {e}")
        return []

def get_subcategories(category_page):
    """Get subcategories of a category."""
    try:
        return list(category_page.subcategories())
    except Exception as e:
        print(f"Error getting subcategories for {category_page.title()}: {e}")
        return []

def analyze_category_hierarchy(category_name, max_depth=3):
    """Analyze a category hierarchy for issues."""
    # Ensure category has Category: prefix
    if not category_name.startswith('Category:'):
        category_name = f'Category:{category_name}'
    
    # Get category
    category = pywikibot.Category(site, category_name)
    
    if not category.exists():
        print(f"Error: Category {category_name} does not exist")
        return None
    
    # Results dictionary
    results = {
        'orphaned_categories': [],
        'missing_parent_categories': [],
        'broken_hierarchies': [],
        'duplicate_categories': [],
        'empty_categories': []
    }
    
    # Keep track of processed categories to avoid loops
    processed = set()
    
    # Categories to process with their depth
    to_process = [(category, 0)]
    
    while to_process:
        current_category, depth = to_process.pop(0)
        
        if current_category.title() in processed:
            continue
        
        processed.add(current_category.title())
        
        # Check if category is empty
        has_articles = False
        has_subcategories = False
        
        try:
            # Check for articles
            for _ in current_category.articles(recurse=False):
                has_articles = True
                break
            
            # Check for subcategories
            subcategories = list(current_category.subcategories())
            has_subcategories = len(subcategories) > 0
            
            if not has_articles and not has_subcategories:
                results['empty_categories'].append(current_category.title())
        except Exception as e:
            print(f"Error checking if {current_category.title()} is empty: {e}")
        
        # Get parent categories
        parent_categories = get_parent_categories(current_category)
        
        # Check for orphaned categories (no parent categories)
        if not parent_categories:
            results['orphaned_categories'].append(current_category.title())
        
        # Check for parent categories that don't exist
        for parent in parent_categories:
            parent_page = pywikibot.Category(site, f"Category:{parent}")
            if not parent_page.exists():
                results['missing_parent_categories'].append((current_category.title(), parent))
        
        # Add subcategories to process if not at max depth
        if depth < max_depth:
            subcategories = get_subcategories(current_category)
            for subcat in subcategories:
                to_process.append((subcat, depth + 1))
    
    # Check for duplicate categories in files
    files = list(category.articles(namespaces=6))  # Namespace 6 = File
    
    # Dictionary to track categories by file
    file_categories = defaultdict(list)
    
    for file_page in files:
        categories = extract_categories(file_page.text)
        file_categories[file_page.title()] = categories
    
    # Find files with duplicate categories
    for file_title, categories in file_categories.items():
        seen = set()
        duplicates = []
        
        for cat in categories:
            if cat in seen:
                duplicates.append(cat)
            seen.add(cat)
        
        if duplicates:
            results['duplicate_categories'].append((file_title, duplicates))
    
    return results

def suggest_parent_categories(category_name):
    """Suggest potential parent categories based on name and content."""
    # Ensure category has Category: prefix
    if not category_name.startswith('Category:'):
        category_name = f'Category:{category_name}'
    
    # Get category
    category = pywikibot.Category(site, category_name)
    
    if not category.exists():
        print(f"Error: Category {category_name} does not exist")
        return []
    
    suggestions = []
    
    # Extract meaningful parts from the category name
    name_parts = category.title(with_ns=False).split(' ')
    
    # Search for similar categories
    for part in name_parts:
        if len(part) < 4:
            continue
        
        try:
            search_results = list(pagegenerators.SearchPageGenerator(
                f"incategory:Categories {part}", namespaces=[14], total=10  # Namespace 14 = Category
            ))
            
            for result in search_results:
                if result.title() != category.title():
                    suggestions.append(result.title())
        except Exception as e:
            print(f"Error searching for similar categories: {e}")
    
    return suggestions

def fix_duplicate_categories(file_title, duplicates):
    """Remove duplicate categories from a file."""
    try:
        file_page = pywikibot.Page(site, file_title)
        if not file_page.exists():
            return False
        
        text = file_page.text
        new_text = text
        
        # Remove duplicate category tags
        for duplicate in duplicates:
            # Find all occurrences of this category
            pattern = re.compile(r'\[\[Category:' + re.escape(duplicate) + r'(?:\|[^\]]+)?\]\]')
            matches = list(pattern.finditer(new_text))
            
            # Keep the first occurrence, remove the rest
            if len(matches) > 1:
                for match in reversed(matches[1:]):  # Process in reverse to avoid position issues
                    new_text = new_text[:match.start()] + new_text[match.end():]
        
        if new_text != text:
            file_page.text = new_text
            file_page.save(summary="pwb: Removed duplicate categories")
            return True
    
    except Exception as e:
        print(f"Error fixing duplicate categories for {file_title}: {e}")
    
    return False

def fix_orphaned_category(category_title, suggested_parents):
    """Add parent categories to an orphaned category."""
    try:
        category_page = pywikibot.Category(site, category_title)
        if not category_page.exists():
            return False
        
        # Get text
        text = category_page.text
        
        # If no suggestions, can't fix
        if not suggested_parents:
            return False
        
        # Ask user to select parent categories
        print(f"\nOrphaned category: {category_title}")
        print("Suggested parent categories:")
        
        for i, parent in enumerate(suggested_parents):
            print(f"{i+1}. {parent}")
        
        selected = input("\nEnter numbers of categories to add (comma-separated), or 'skip': ")
        
        if selected.lower() == 'skip':
            return False
        
        try:
            selected_indices = [int(idx.strip()) - 1 for idx in selected.split(',') if idx.strip()]
            selected_parents = [suggested_parents[idx] for idx in selected_indices if 0 <= idx < len(suggested_parents)]
        except ValueError:
            print("Invalid input")
            return False
        
        # Add selected parent categories
        for parent in selected_parents:
            # Remove Category: prefix if present
            if parent.startswith('Category:'):
                parent = parent[len('Category:'):]
                
            category_tag = f"[[Category:{parent}]]"
            if category_tag not in text:
                text += f"\n{category_tag}"
        
        # Save changes
        category_page.text = text
        category_page.save(summary="pwb: Added parent categories to orphaned category")
        return True
    
    except Exception as e:
        print(f"Error fixing orphaned category {category_title}: {e}")
    
    return False

def process_category(category_name, fix_issues=False):
    """Process a category, find and optionally fix issues."""
    print(f"Analyzing category: {category_name}")
    
    # Analyze category hierarchy
    results = analyze_category_hierarchy(category_name)
    
    if not results:
        return
    
    # Display results
    print("\n=== Category Analysis Results ===\n")
    
    print(f"Orphaned categories: {len(results['orphaned_categories'])}")
    print(f"Missing parent categories: {len(results['missing_parent_categories'])}")
    print(f"Empty categories: {len(results['empty_categories'])}")
    print(f"Files with duplicate categories: {len(results['duplicate_categories'])}")
    
    # Fix issues if requested
    if fix_issues:
        fixed_count = 0
        
        # Fix duplicate categories
        if results['duplicate_categories']:
            print("\nFixing duplicate categories...")
            for file_title, duplicates in results['duplicate_categories']:
                print(f"Fixing {file_title}...")
                if fix_duplicate_categories(file_title, duplicates):
                    fixed_count += 1
            print(f"Fixed {fixed_count} files with duplicate categories")
        
        # Fix orphaned categories
        if results['orphaned_categories']:
            orphan_fixed = 0
            print("\nFixing orphaned categories...")
            
            for category_title in results['orphaned_categories']:
                # Skip maintenance categories or user categories
                if 'maintenance' in category_title.lower() or '/pwb' in category_title:
                    continue
                
                # Get suggested parent categories
                suggestions = suggest_parent_categories(category_title)
                
                if suggestions:
                    if fix_orphaned_category(category_title, suggestions):
                        orphan_fixed += 1
            
            print(f"Fixed {orphan_fixed} orphaned categories")
    
    # Create detailed report
    report = "= Category Structure Analysis Report =\n\n"
    report += f"Analysis of category: {category_name}\n\n"
    
    # Orphaned categories
    report += "== Orphaned Categories ==\n"
    if results['orphaned_categories']:
        for category in results['orphaned_categories']:
            report += f"* [[:{category}]]\n"
    else:
        report += "No orphaned categories found.\n"
    
    # Missing parent categories
    report += "\n== Missing Parent Categories ==\n"
    if results['missing_parent_categories']:
        for category, missing_parent in results['missing_parent_categories']:
            report += f"* [[:{category}]] links to non-existent category: {missing_parent}\n"
    else:
        report += "No missing parent categories found.\n"
    
    # Empty categories
    report += "\n== Empty Categories ==\n"
    if results['empty_categories']:
        for category in results['empty_categories']:
            report += f"* [[:{category}]] has no articles or subcategories\n"
    else:
        report += "No empty categories found.\n"
    
    # Duplicate categories
    report += "\n== Files with Duplicate Categories ==\n"
    if results['duplicate_categories']:
        for file_title, duplicates in results['duplicate_categories']:
            report += f"* [[:{file_title}]] has duplicate categories: {', '.join(duplicates)}\n"
    else:
        report += "No files with duplicate categories found.\n"
    
    print("\nAnalysis complete! Detailed report:")
    print(report)
    
    # Offer to save report
    if input("\nSave report to wiki page? (y/n): ").lower() == 'y':
        page_title = input("Enter page title (default: User:YOUR_USERNAME/pwb/Category_Report): ").strip()
        if not page_title:
            page_title = "User:YOUR_USERNAME/pwb/Category_Report"
        
        try:
            page = pywikibot.Page(site, page_title)
            page.text = report
            page.save(summary="pwb: Updated category structure analysis report")
            print(f"Report saved to {page_title}")
        except Exception as e:
            print(f"Error saving report: {e}")

def process_files_in_category(category_name, fix_issues=False):
    """Process all files in a category, checking for category issues."""
    # Ensure category has Category: prefix
    if not category_name.startswith('Category:'):
        category_name = f'Category:{category_name}'
    
    # Get category
    category = pywikibot.Category(site, category_name)
    
    if not category.exists():
        print(f"Error: Category {category_name} does not exist")
        return
    
    # Get files in category
    files = list(category.articles(namespaces=6))  # Namespace 6 = File
    
    if not files:
        print(f"No files found in {category_name}")
        return
    
    print(f"Found {len(files)} files in {category_name}")
    
    # Track issues
    issues = {
        'duplicate_categories': [],
        'missing_categories': []
    }
    
    # Process each file
    for i, file_page in enumerate(files):
        if i % 10 == 0:
            print(f"Processing file {i+1}/{len(files)}: {file_page.title()}")
        
        # Extract categories
        categories = extract_categories(file_page.text)
        
        # Check for duplicate categories
        seen = set()
        duplicates = []
        
        for cat in categories:
            if cat in seen:
                duplicates.append(cat)
            seen.add(cat)
        
        if duplicates:
            issues['duplicate_categories'].append((file_page.title(), duplicates))
    
    # Display results
    print("\n=== Category Issues in Files ===\n")
    
    print(f"Files with duplicate categories: {len(issues['duplicate_categories'])}")
    
    # Fix duplicate categories if requested
    if fix_issues and issues['duplicate_categories']:
        fixed_count = 0
        print("\nFixing duplicate categories...")
        
        for file_title, duplicates in issues['duplicate_categories']:
            print(f"Fixing {file_title}...")
            if fix_duplicate_categories(file_title, duplicates):
                fixed_count += 1
        
        print(f"Fixed {fixed_count} files with duplicate categories")
    
    # Create report
    report = f"= Category Issues in {category_name} =\n\n"
    
    # Duplicate categories
    report += "== Files with Duplicate Categories ==\n"
    if issues['duplicate_categories']:
        for file_title, duplicates in issues['duplicate_categories']:
            report += f"* [[:{file_title}]] has duplicate categories: {', '.join(duplicates)}\n"
    else:
        report += "No files with duplicate categories found.\n"
    
    print("\nAnalysis complete! Detailed report:")
    print(report)
    
    # Offer to save report
    if input("\nSave report to wiki page? (y/n): ").lower() == 'y':
        page_title = input("Enter page title (default: User:YOUR_USERNAME/pwb/Category_Issues): ").strip()
        if not page_title:
            page_title = "User:YOUR_USERNAME/pwb/Category_Issues"
        
        try:
            page = pywikibot.Page(site, page_title)
            page.text = report
            page.save(summary="pwb: Updated category issues report")
            print(f"Report saved to {page_title}")
        except Exception as e:
            print(f"Error saving report: {e}")

def process_user_categories(username, fix_issues=False):
    """Process categories created by a specific user."""
    # Get user
    user = pywikibot.User(site, username)
    
    # Get user's contributions in category namespace
    contributions = user.contributions(namespaces=14)  # Namespace 14 = Category
    
    # Extract unique categories
    categories = set()
    for timestamp, page, _, _ in contributions:
        if page.exists() and page.namespace() == 14:  # Category namespace
            categories.add(page.title())
    
    if not categories:
        print(f"No categories found created by {username}")
        return
    
    print(f"Found {len(categories)} categories created by {username}")
    
    # Analyze each category
    results = {
        'orphaned_categories': [],
        'missing_parent_categories': [],
        'empty_categories': []
    }
    
    for i, category_title in enumerate(categories):
        if i % 10 == 0:
            print(f"Analyzing category {i+1}/{len(categories)}: {category_title}")
        
        category = pywikibot.Category(site, category_title)
        
        # Check if category is orphaned (no parent categories)
        parent_categories = get_parent_categories(category)
        if not parent_categories:
            results['orphaned_categories'].append(category_title)
        
        # Check for missing parent categories
        for parent in parent_categories:
            parent_page = pywikibot.Category(site, f"Category:{parent}")
            if not parent_page.exists():
                results['missing_parent_categories'].append((category_title, parent))
        
        # Check if category is empty
        has_articles = False
        has_subcategories = False
        
        try:
            # Check for articles
            for _ in category.articles(recurse=False):
                has_articles = True
                break
            
            # Check for subcategories
            for _ in category.subcategories():
                has_subcategories = True
                break
            
            if not has_articles and not has_subcategories:
                results['empty_categories'].append(category_title)
        except Exception as e:
            print(f"Error checking if {category_title} is empty: {e}")
    
    # Display results
    print("\n=== Category Analysis Results ===\n")
    
    print(f"Orphaned categories: {len(results['orphaned_categories'])}")
    print(f"Missing parent categories: {len(results['missing_parent_categories'])}")
    print(f"Empty categories: {len(results['empty_categories'])}")
    
    # Fix issues if requested
    if fix_issues:
        # Fix orphaned categories
        if results['orphaned_categories']:
            orphan_fixed = 0
            print("\nFixing orphaned categories...")
            
            for category_title in results['orphaned_categories']:
                # Skip maintenance categories or user categories
                if 'maintenance' in category_title.lower() or '/pwb' in category_title:
                    continue
                
                # Get suggested parent categories
                suggestions = suggest_parent_categories(category_title)
                
                if suggestions:
                    if fix_orphaned_category(category_title, suggestions):
                        orphan_fixed += 1
            
            print(f"Fixed {orphan_fixed} orphaned categories")
    
    # Create detailed report
    report = f"= Category Analysis for User:{username} =\n\n"
    
    # Orphaned categories
    report += "== Orphaned Categories ==\n"
    if results['orphaned_categories']:
        for category in results['orphaned_categories']:
            report += f"* [[:{category}]]\n"
    else:
        report += "No orphaned categories found.\n"
    
    # Missing parent categories
    report += "\n== Missing Parent Categories ==\n"
    if results['missing_parent_categories']:
        for category, missing_parent in results['missing_parent_categories']:
            report += f"* [[:{category}]] links to non-existent category: {missing_parent}\n"
    else:
        report += "No missing parent categories found.\n"
    
    # Empty categories
    report += "\n== Empty Categories ==\n"
    if results['empty_categories']:
        for category in results['empty_categories']:
            report += f"* [[:{category}]] has no articles or subcategories\n"
    else:
        report += "No empty categories found.\n"
    
    print("\nAnalysis complete! Detailed report:")
    print(report)
    
    # Offer to save report
    if input("\nSave report to wiki page? (y/n): ").lower() == 'y':
        page_title = input(f"Enter page title (default: User:{username}/pwb/Category_Report): ").strip()
        if not page_title:
            page_title = f"User:{username}/pwb/Category_Report"
        
        try:
            page = pywikibot.Page(site, page_title)
            page.text = report
            page.save(summary="pwb: Updated category analysis report")
            print(f"Report saved to {page_title}")
        except Exception as e:
            print(f"Error saving report: {e}")

def interactive_mode():
    """Interactive mode for repairing categories."""
    print("=== PWB Category Repair Tool ===")
    
    while True:
        print("\nOptions:")
        print("1. Analyze category structure")
        print("2. Check files in a category for category issues")
        print("3. Analyze categories created by a user")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == '1':
            category_name = input("Enter category name to analyze (with or without 'Category:' prefix): ").strip()
            fix = input("Fix issues automatically? (y/n): ").lower() == 'y'
            process_category(category_name, fix)
        
        elif choice == '2':
            category_name = input("Enter category name (with or without 'Category:' prefix): ").strip()
            fix = input("Fix issues automatically? (y/n): ").lower() == 'y'
            process_files_in_category(category_name, fix)
        
        elif choice == '3':
            username = input("Enter username: ").strip()
            fix = input("Fix issues automatically? (y/n): ").lower() == 'y'
            process_user_categories(username, fix)
        
        elif choice == '4':
            print("Exiting...")
            break
        
        else:
            print("Invalid choice")

def main():
    """Main function to handle command line arguments."""
    parser = argparse.ArgumentParser(description='Find and repair category issues on Wikimedia Commons')
    
    # Create mutually exclusive group for the modes
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--analyze', help='Analyze a specific category structure')
    group.add_argument('--category', help='Check files in a category for category issues')
    group.add_argument('--user', help='Analyze categories created by a user')
    group.add_argument('--interactive', action='store_true', help='Run in interactive mode')
    
    # Additional arguments
    parser.add_argument('--fix', action='store_true', help='Fix issues automatically')
    
    args = parser.parse_args()
    
    if args.interactive:
        interactive_mode()
    elif args.analyze:
        process_category(args.analyze, args.fix)
    elif args.category:
        process_files_in_category(args.category, args.fix)
    elif args.user:
        process_user_categories(args.user, args.fix)

if __name__ == "__main__":
    main()
    files = list(category.