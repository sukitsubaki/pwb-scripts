#!/usr/bin/python
# -*- coding: utf-8 -*-

import pywikibot
from pywikibot import pagegenerators
import re
import csv
import os
import sys
from datetime import datetime

"""
pwb_batch_rename.py - Batch rename files on Wikimedia Commons

This script allows you to rename multiple files according to defined patterns
or using a CSV file with old and new filenames.

Usage:
    1. Using patterns:
        python pwb_batch_rename.py --pattern "Old pattern" "New pattern"
        
    2. Using a CSV file:
        python pwb_batch_rename.py --csv filename.csv
        
    3. Interactive mode:
        python pwb_batch_rename.py --interactive
"""

import argparse

# Initialize site
site = pywikibot.Site('commons', 'commons')

def rename_file(old_name, new_name, reason):
    """Rename a file from old_name to new_name with given reason."""
    try:
        # Ensure filenames have "File:" prefix
        if not old_name.startswith('File:'):
            old_name = f'File:{old_name}'
        if not new_name.startswith('File:'):
            new_name = f'File:{new_name}'
        
        # Create page objects
        old_page = pywikibot.Page(site, old_name)
        
        # Check if old file exists
        if not old_page.exists():
            print(f"Error: {old_name} does not exist")
            return False
        
        # Check if new file already exists
        new_page = pywikibot.Page(site, new_name)
        if new_page.exists():
            print(f"Error: {new_name} already exists")
            return False
        
        # Move the page
        old_page.move(new_name, reason=reason, noredirect=False)
        print(f"Successfully renamed {old_name} to {new_name}")
        return True
    
    except pywikibot.exceptions.Error as e:
        print(f"Error renaming {old_name} to {new_name}: {e}")
        return False

def rename_by_pattern(category, old_pattern, new_pattern, reason):
    """Rename files in category using search and replace patterns."""
    # Get all files in the category
    files = pagegenerators.CategorizedPageGenerator(
        pywikibot.Category(site, category), recurse=False
    )
    
    renamed_count = 0
    error_count = 0
    
    # Compile regex pattern
    regex = re.compile(old_pattern)
    
    for file_page in files:
        if file_page.namespace() != 6:  # Only process files
            continue
        
        old_name = file_page.title()
        file_name = old_name.split(':', 1)[1]  # Remove "File:" prefix for pattern matching
        
        # Check if pattern matches
        if regex.search(file_name):
            # Create new filename
            new_file_name = regex.sub(new_pattern, file_name)
            new_name = f"File:{new_file_name}"
            
            print(f"Renaming {old_name} to {new_name}")
            
            # Confirm with user
            if input("Proceed with this rename? (y/n): ").lower() != 'y':
                print("Skipping this file")
                continue
            
            # Perform rename
            if rename_file(old_name, new_name, reason):
                renamed_count += 1
            else:
                error_count += 1
    
    return renamed_count, error_count

def rename_from_csv(csv_file, reason):
    """Rename files according to a CSV file with old and new filenames."""
    if not os.path.exists(csv_file):
        print(f"Error: CSV file {csv_file} not found")
        return 0, 0
    
    renamed_count = 0
    error_count = 0
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        csv_reader = csv.reader(f)
        for row in csv_reader:
            if len(row) < 2:
                print(f"Warning: Skipping invalid row in CSV: {row}")
                continue
            
            old_name, new_name = row[0], row[1]
            
            print(f"Renaming {old_name} to {new_name}")
            
            # Perform rename
            if rename_file(old_name, new_name, reason):
                renamed_count += 1
            else:
                error_count += 1
            
    return renamed_count, error_count

def interactive_mode():
    """Interactive mode for batch renaming files."""
    print("=== PWB Batch File Renamer - Interactive Mode ===")
    
    # Get the category
    category_name = input("Enter the category name to process (without 'Category:' prefix): ").strip()
    category = f"Category:{category_name}"
    
    # Check if category exists
    cat_page = pywikibot.Category(site, category)
    if not cat_page.exists():
        print(f"Error: Category {category} does not exist")
        return 0, 0
    
    # Get rename options
    print("\nRename options:")
    print("1. Search and replace in filenames")
    print("2. Add prefix to filenames")
    print("3. Add suffix to filenames")
    print("4. Custom regex pattern")
    
    option = input("Select an option (1-4): ").strip()
    
    # Prepare reason for move
    reason = input("\nEnter reason for rename: ").strip()
    if not reason:
        reason = "pwb: Batch file rename"
    
    # Process based on selected option
    if option == "1":
        search_text = input("Enter text to search for: ")
        replace_text = input("Enter replacement text: ")
        old_pattern = re.escape(search_text)
        new_pattern = replace_text
    
    elif option == "2":
        prefix = input("Enter prefix to add: ")
        old_pattern = r"^(.+)$"
        new_pattern = f"{prefix}\\1"
    
    elif option == "3":
        suffix = input("Enter suffix to add (before extension): ")
        old_pattern = r"^(.+)(\..+)$"
        new_pattern = f"\\1{suffix}\\2"
    
    elif option == "4":
        old_pattern = input("Enter regex search pattern: ")
        new_pattern = input("Enter regex replacement pattern: ")
    
    else:
        print("Invalid option selected")
        return 0, 0
    
    # Confirm
    print("\nReview your settings:")
    print(f"Category: {category}")
    print(f"Search pattern: {old_pattern}")
    print(f"Replace pattern: {new_pattern}")
    print(f"Reason: {reason}")
    
    if input("\nProceed with batch rename? (y/n): ").lower() != 'y':
        print("Operation cancelled")
        return 0, 0
    
    # Perform renames
    return rename_by_pattern(category, old_pattern, new_pattern, reason)

def create_report(renamed_count, error_count):
    """Create a report of the renaming operation."""
    total = renamed_count + error_count
    
    report = f"""= File Rename Operation Report =

== Summary ==
* Operation date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
* Total files processed: {total}
* Successfully renamed: {renamed_count}
* Errors encountered: {error_count}

"""
    
    if renamed_count > 0:
        success_rate = (renamed_count / total) * 100 if total > 0 else 0
        report += f"Operation completed with {success_rate:.1f}% success rate.\n"
    
    report += f"\nReport generated by pwb_batch_rename.py"
    
    # Save report to user page
    try:
        user_page = pywikibot.Page(site, 'User:YOUR_USERNAME/pwb/Rename_Report')
        user_page.text = report
        user_page.save(summary="pwb: File rename operation report")
        print(f"Report saved to {user_page.title()}")
    except Exception as e:
        print(f"Error saving report: {e}")
        print("Report content:")
        print(report)