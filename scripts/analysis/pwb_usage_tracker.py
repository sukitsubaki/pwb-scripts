#!/usr/bin/python
# -*- coding: utf-8 -*-

import pywikibot
from pywikibot import pagegenerators
import re
import argparse
import time
from collections import defaultdict

"""
pwb_usage_tracker.py - Track where your files are used across Wikimedia projects

This script finds which Wikipedia articles, Wikimedia Commons galleries,
or other wiki pages are using your uploaded files.

Features:
- Tracks file usage across multiple Wikimedia wikis
- Generates usage reports by project or by file
- Shows which files are most/least used
- Identifies orphaned files (not used anywhere)

Usage:
    python pwb_usage_tracker.py --file "File:Example.jpg"
    python pwb_usage_tracker.py --category "Category:Your_uploads"
    python pwb_usage_tracker.py --user "YOUR_USERNAME"
    python pwb_usage_tracker.py --interactive
"""

# Site configuration
commons_site = pywikibot.Site('commons', 'commons')

# List of projects to check
WIKIMEDIA_PROJECTS = [
    'wikipedia', 'wikisource', 'wikibooks', 'wikinews', 
    'wikiquote', 'wikiversity', 'wikivoyage', 'wiktionary'
]

# Languages to check (add more as needed)
LANGUAGES = [
    'en', 'de', 'fr', 'es', 'it', 'ru', 'ja', 'zh',
    'pt', 'ar', 'fa', 'pl', 'nl', 'id', 'uk', 'he', 
    'sv', 'cs', 'ko', 'vi', 'hu', 'no', 'fi', 'da', 
    'ro', 'ca', 'hi', 'tr', 'sr', 'bg', 'ms', 'el'
]

def get_file_usage(file_page):
    """Get information on where a file is used."""
    usage = defaultdict(list)
    
    try:
        # File usage on Commons
        commons_usage = list(file_page.usingPages())
        if commons_usage:
            usage['commons'] = [(page.title(), 'commons') for page in commons_usage]
        
        # File usage on other wikis
        global_usage = file_page.globalusage()
        for wiki, pages in global_usage.items():
            # Extract project and language from wiki name
            parts = wiki.split('.')
            if len(parts) >= 2:
                project = parts[1].replace('wiki', '').replace('pedia', '')
                lang = parts[0]
                
                for page in pages:
                    usage[wiki].append((page.title, f"{lang}.{project}"))
        
        return usage
    
    except Exception as e:
        print(f"Error getting usage for {file_page.title()}: {e}")
        return usage

def format_usage_report(file_title, usage):
    """Format usage information as readable text."""
    total_usage = sum(len(pages) for pages in usage.values())
    
    report = f"=== Usage of {file_title} ===\n"
    report += f"Total usage: {total_usage} pages\n\n"
    
    if not total_usage:
        report += "This file is not used on any wiki pages (orphaned).\n"
        return report
    
    # Sort wikis by usage count (most used first)
    wikis_sorted = sorted(usage.items(), key=lambda x: len(x[1]), reverse=True)
    
    for wiki, pages in wikis_sorted:
        report += f"== {wiki} ({len(pages)} pages) ==\n"
        for title, _ in pages:
            report += f"* [[:{title}]]\n"
        report += "\n"
    
    return report

def process_file(file_title):
    """Process a single file by title."""
    # Ensure title has File: prefix
    if not file_title.startswith('File:'):
        file_title = f'File:{file_title}'
    
    # Get file page
    file_page = pywikibot.Page(commons_site, file_title)
    
    if not file_page.exists():
        print(f"Error: File {file_title} does not exist")
        return None
    
    print(f"Finding usage information for {file_title}...")
    usage = get_file_usage(file_page)
    
    # Create report
    report = format_usage_report(file_title, usage)
    print(report)
    
    return usage

def process_category(category_name, limit=None):
    """Process all files in a category."""
    # Ensure category has Category: prefix
    if not category_name.startswith('Category:'):
        category_name = f'Category:{category_name}'
    
    # Get category
    cat = pywikibot.Category(commons_site, category_name)
    
    if not cat.exists():
        print(f"Error: Category {category_name} does not exist")
        return None
    
    # Get files in category
    files = list(cat.articles(namespaces=6))  # Namespace 6 = File
    
    if not files:
        print(f"No files found in {category_name}")
        return None
    
    print(f"Found {len(files)} files in {category_name}")
    
    if limit and limit < len(files):
        print(f"Processing only the first {limit} files")
        files = files[:limit]
    
    # Process each file
    usage_data = {}
    orphaned_files = []
    total_usage_count = 0
    
    for i, file_page in enumerate(files):
        print(f"Processing file {i+1}/{len(files)}: {file_page.title()}")
        
        # Get usage data
        usage = get_file_usage(file_page)
        usage_data[file_page.title()] = usage
        
        # Count total usage
        file_usage_count = sum(len(pages) for pages in usage.values())
        total_usage_count += file_usage_count
        
        # Track orphaned files
        if file_usage_count == 0:
            orphaned_files.append(file_page.title())
        
        # Don't overload the server
        if i < len(files) - 1:
            time.sleep(1)
    
    # Create summary report
    summary_report = create_category_summary(usage_data, orphaned_files, total_usage_count)
    print(summary_report)
    
    return usage_data, summary_report

def process_user_uploads(username, limit=None):
    """Process uploads by a specific user."""
    # Get user
    user = pywikibot.User(commons_site, username)
    
    # Get user's uploads
    uploads = list(user.contributions(namespaces=6, total=5000))  # Namespace 6 = File
    
    if not uploads:
        print(f"No uploads found for user {username}")
        return None
    
    # Extract file pages
    files = []
    for _, page, _, _ in uploads:
        if page.namespace() == 6 and page not in files:
            files.append(page)
    
    print(f"Found {len(files)} uploads by {username}")
    
    if limit and limit < len(files):
        print(f"Processing only the first {limit} files")
        files = files[:limit]
    
    # Process each file
    usage_data = {}
    orphaned_files = []
    total_usage_count = 0
    
    for i, file_page in enumerate(files):
        print(f"Processing file {i+1}/{len(files)}: {file_page.title()}")
        
        # Get usage data
        usage = get_file_usage(file_page)
        usage_data[file_page.title()] = usage
        
        # Count total usage
        file_usage_count = sum(len(pages) for pages in usage.values())
        total_usage_count += file_usage_count
        
        # Track orphaned files
        if file_usage_count == 0:
            orphaned_files.append(file_page.title())
        
        # Don't overload the server
        if i < len(files) - 1:
            time.sleep(1)
    
    # Create summary report
    summary_report = create_user_summary(username, usage_data, orphaned_files, total_usage_count)
    print(summary_report)
    
    return usage_data, summary_report

def create_category_summary(usage_data, orphaned_files, total_usage_count):
    """Create a summary report for a category."""
    # Count files by project
    project_counts = defaultdict(int)
    for file_usage in usage_data.values():
        for project, pages in file_usage.items():
            project_counts[project] += len(pages)
    
    # Sort files by usage count
    file_usage_counts = []
    for file_title, file_usage in usage_data.items():
        count = sum(len(pages) for pages in file_usage.values())
        file_usage_counts.append((file_title, count))
    
    file_usage_counts.sort(key=lambda x: x[1], reverse=True)
    
    # Create report
    report = "= File Usage Summary =\n\n"
    report += f"Total files analyzed: {len(usage_data)}\n"
    report += f"Total file usages: {total_usage_count}\n"
    report += f"Average usages per file: {total_usage_count / len(usage_data):.2f}\n"
    report += f"Orphaned files (not used anywhere): {len(orphaned_files)} ({len(orphaned_files) / len(usage_data) * 100:.1f}%)\n\n"
    
    # Most used projects
    report += "== Usage by Project ==\n"
    for project, count in sorted(project_counts.items(), key=lambda x: x[1], reverse=True):
        report += f"* {project}: {count} usages\n"
    
    # Most used files
    report += "\n== Most Used Files ==\n"
    for i, (file_title, count) in enumerate(file_usage_counts[:10]):  # Top 10
        report += f"{i+1}. [[:{file_title}]] - {count} usages\n"
    
    # Orphaned files
    if orphaned_files:
        report += "\n== Orphaned Files ==\n"
        for file_title in orphaned_files[:20]:  # Limit to 20 to keep report manageable
            report += f"* [[:{file_title}]]\n"
        
        if len(orphaned_files) > 20:
            report += f"...and {len(orphaned_files) - 20} more\n"
    
    report += f"\nReport generated by pwb_usage_tracker.py on {time.strftime('%Y-%m-%d')}"
    
    return report

def create_user_summary(username, usage_data, orphaned_files, total_usage_count):
    """Create a summary report for a user's uploads."""
    # Same as category summary but with user-specific title
    report = create_category_summary(usage_data, orphaned_files, total_usage_count)
    report = f"= File Usage Summary for {username} =\n\n" + report.split("\n\n", 1)[1]
    
    return report

def save_report(report, title):
    """Save report to a wiki page."""
    try:
        page = pywikibot.Page(commons_site, title)
        page.text = report
        page.save(summary="pwb: Updated file usage report")
        print(f"Report saved to {title}")
        return True
    except Exception as e:
        print(f"Error saving report: {e}")
        return False

def interactive_mode():
    """Interactive mode for tracking file usage."""
    print("=== PWB File Usage Tracker ===")
    
    while True:
        print("\nOptions:")
        print("1. Track usage of a single file")
        print("2. Track usage of files in a category")
        print("3. Track usage of files uploaded by a user")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == '1':
            file_title = input("Enter file title (with or without 'File:' prefix): ").strip()
            process_file(file_title)
        
        elif choice == '2':
            category_name = input("Enter category name (with or without 'Category:' prefix): ").strip()
            limit_str = input("Limit number of files to process (leave empty for all): ").strip()
            limit = int(limit_str) if limit_str else None
            
            result = process_category(category_name, limit)
            if result:
                _, report = result
                save = input("Save report to a wiki page? (y/n): ").lower() == 'y'
                if save:
                    title = input("Enter page title (default: User:YOUR_USERNAME/pwb/Usage_Report): ").strip()
                    if not title:
                        title = "User:YOUR_USERNAME/pwb/Usage_Report"
                    save_report(report, title)
        
        elif choice == '3':
            username = input("Enter username: ").strip()
            limit_str = input("Limit number of files to process (leave empty for all): ").strip()
            limit = int(limit_str) if limit_str else None
            
            result = process_user_uploads(username, limit)
            if result:
                _, report = result
                save = input("Save report to a wiki page? (y/n): ").lower() == 'y'
                if save:
                    title = input("Enter page title (default: User:YOUR_USERNAME/pwb/Usage_Report): ").strip()
                    if not title:
                        title = "User:YOUR_USERNAME/pwb/Usage_Report"
                    save_report(report, title)
        
        elif choice == '4':
            print("Exiting...")
            break
        
        else:
            print("Invalid choice")

def main():
    """Main function to handle command line arguments."""
    parser = argparse.ArgumentParser(description='Track file usage across Wikimedia projects')
    
    # Create mutually exclusive group for the modes
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--file', help='Track usage of a single file')
    group.add_argument('--category', help='Track usage of files in a category')
    group.add_argument('--user', help='Track usage of files uploaded by a user')
    group.add_argument('--interactive', action='store_true', help='Run in interactive mode')
    
    # Additional arguments
    parser.add_argument('--limit', type=int, help='Limit number of files to process')
    parser.add_argument('--save', help='Save report to this wiki page')
    
    args = parser.parse_args()
    
    if args.interactive:
        interactive_mode()
    
    elif args.file:
        process_file(args.file)
    
    elif args.category:
        result = process_category(args.category, args.limit)
        if result and args.save:
            _, report = result
            save_report(report, args.save)
    
    elif args.user:
        result = process_user_uploads(args.user, args.limit)
        if result and args.save:
            _, report = result
            save_report(report, args.save)

if __name__ == "__main__":
    main()
