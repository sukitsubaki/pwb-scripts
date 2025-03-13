def save_metadata(files_metadata, output_dir):
    """Save metadata of downloaded files to a CSV file."""
    import csv
    
    if not files_metadata:
        return
    
    csv_path = os.path.join(output_dir, "download_metadata.csv")
    
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=files_metadata[0].keys())
        writer.writeheader()
        writer.writerows(files_metadata)
    
    print(f"Metadata saved to {csv_path}")

def get_files_from_category(category_name, file_types=None, limit=None):
    """Get files from a category."""
    # Ensure category has Category: prefix
    if not category_name.startswith('Category:'):
        category_name = f'Category:{category_name}'
    
    # Get category
    cat = pywikibot.Category(site, category_name)
    
    if not cat.exists():
        print(f"Error: Category {category_name} does not exist")
        return []
    
    # Get files in category
    files = []
    for file_page in pagegenerators.CategorizedPageGenerator(cat, namespaces=6):  # Namespace 6 = File
        # Check file extension if specified
        if file_types:
            file_ext = os.path.splitext(file_page.title())[1].lower().lstrip('.')
            if file_ext not in file_types:
                continue
        
        files.append(file_page)
        
        # Check limit
        if limit and len(files) >= limit:
            break
    
    return files

def get_files_from_user(username, file_types=None, limit=None):
    """Get files uploaded by a user."""
    # Get user
    user = pywikibot.User(site, username)
    
    # Get user's uploads
    uploads = list(user.contributions(namespaces=6, total=5000))  # Namespace 6 = File
    
    if not uploads:
        print(f"No uploads found for user {username}")
        return []
    
    # Extract file pages
    files = []
    for _, page, _, _ in uploads:
        # Check if it's a file and not already in the list
        if page.namespace() == 6 and page not in files:
            # Check file extension if specified
            if file_types:
                file_ext = os.path.splitext(page.title())[1].lower().lstrip('.')
                if file_ext not in file_types:
                    continue
            
            files.append(page)
            
            # Check limit
            if limit and len(files) >= limit:
                break
    
    return files

def get_files_from_search(search_term, file_types=None, limit=None):
    """Get files from search results."""
    # Search for files
    files = []
    search_gen = pagegenerators.SearchPageGenerator(search_term, namespaces=[6], total=5000)
    
    for page in search_gen:
        # Check file extension if specified
        if file_types:
            file_ext = os.path.splitext(page.title())[1].lower().lstrip('.')
            if file_ext not in file_types:
                continue
        
        files.append(page)
        
        # Check limit
        if limit and len(files) >= limit:
            break
    
    return files

def get_files_from_text_file(file_path, file_types=None):
    """Get files from a text file containing file titles."""
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found")
        return []
    
    files = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            # Clean up the line
            file_title = line.strip()
            
            # Ensure title has File: prefix
            if not file_title.startswith('File:'):
                file_title = f'File:{file_title}'
            
            # Check file extension if specified
            if file_types:
                file_ext = os.path.splitext(file_title)[1].lower().lstrip('.')
                if file_ext not in file_types:
                    continue
            
            # Get file page
            file_page = pywikibot.Page(site, file_title)
            
            if file_page.exists() and file_page.namespace() == 6:
                files.append(file_page)
    
    return files

def download_files(files, output_dir, threads=DEFAULT_THREADS, preserve_filename=True, max_size=None):
    """Download multiple files using thread pool."""
    if not files:
        print("No files to download")
        return
    
    print(f"Downloading {len(files)} files to {output_dir} using {threads} threads")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    metadata = []
    
    # Use ThreadPoolExecutor for concurrent downloads
    with ThreadPoolExecutor(max_workers=threads) as executor:
        # Submit download tasks
        future_to_file = {
            executor.submit(download_file, file_page, output_dir, preserve_filename, max_size): file_page
            for file_page in files
        }
        
        # Process results as they complete
        for future in future_to_file:
            result = future.result()
            if result:
                metadata.append(result)
    
    print(f"Download complete. {len(metadata)} files downloaded.")
    
    # Save metadata
    save_metadata(metadata, output_dir)
    
    return metadata

def interactive_mode():
    """Interactive mode for downloading files."""
    print("=== PWB Batch Downloader ===")
    
    while True:
        print("\nOptions:")
        print("1. Download files from a category")
        print("2. Download files uploaded by a user")
        print("3. Download files from search results")
        print("4. Download files listed in a text file")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == '1':
            category_name = input("Enter category name (with or without 'Category:' prefix): ").strip()
            files = get_files_from_category(
                category_name,
                file_types=input("Enter file types to download (comma-separated, empty for all): ").strip().split(',') if input("Filter by file type? (y/n): ").lower() == 'y' else None,
                limit=int(input("Limit number of files (empty for no limit): ") or 0) or None
            )
        
        elif choice == '2':
            username = input("Enter username: ").strip()
            files = get_files_from_user(
                username,
                file_types=input("Enter file types to download (comma-separated, empty for all): ").strip().split(',') if input("Filter by file type? (y/n): ").lower() == 'y' else None,
                limit=int(input("Limit number of files (empty for no limit): ") or 0) or None
            )
        
        elif choice == '3':
            search_term = input("Enter search term: ").strip()
            files = get_files_from_search(
                search_term,
                file_types=input("Enter file types to download (comma-separated, empty for all): ").strip().split(',') if input("Filter by file type? (y/n): ").lower() == 'y' else None,
                limit=int(input("Limit number of files (empty for no limit): ") or 0) or None
            )
        
        elif choice == '4':
            file_path = input("Enter path to text file: ").strip()
            files = get_files_from_text_file(
                file_path,
                file_types=input("Enter file types to download (comma-separated, empty for all): ").strip().split(',') if input("Filter by file type? (y/n): ").lower() == 'y' else None
            )
        
        elif choice == '5':
            print("Exiting...")
            break
        
        else:
            print("Invalid choice")
            continue
        
        if not files:
            print("No files found to download")
            continue
        
        print(f"Found {len(files)} files")
        
        # Get download settings
        output_dir = input(f"Enter output directory (default: {DEFAULT_OUTPUT_DIR}): ").strip() or DEFAULT_OUTPUT_DIR
        threads = int(input(f"Enter number of download threads (default: {DEFAULT_THREADS}): ").strip() or DEFAULT_THREADS)
        preserve_filename = input("Preserve original filenames? (y/n, default: y): ").strip().lower() != 'n'
        max_size = int(input("Maximum file size in MB (empty for no limit): ").strip() or 0) or None
        
        # Confirm download
        if input(f"Download {len(files)} files to {output_dir}? (y/n): ").lower() != 'y':
            print("Download cancelled")
            continue
        
        # Download files
        download_files(files, output_dir, threads, preserve_filename, max_size)

def main():
    """Main function to handle command line arguments."""
    parser = argparse.ArgumentParser(description='Download files from Wikimedia Commons')
    
    # Create mutually exclusive group for the source
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument('--category', help='Download files from a category')
    source_group.add_argument('--user', help='Download files uploaded by a user')
    source_group.add_argument('--search', help='Download files from search results')
    source_group.add_argument('--file', help='Download files listed in a text file')
    source_group.add_argument('--interactive', action='store_true', help='Run in interactive mode')
    
    # Additional arguments
    parser.add_argument('--output', default=DEFAULT_OUTPUT_DIR, help=f'Output directory (default: {DEFAULT_OUTPUT_DIR})')
    parser.add_argument('--threads', type=int, default=DEFAULT_THREADS, help=f'Number of download threads (default: {DEFAULT_THREADS})')
    parser.add_argument('--limit', type=int, help='Limit number of files to download')
    parser.add_argument('--types', nargs='+', help='File types to download (e.g., jpg png)')
    parser.add_argument('--max-size', type=int, help='Maximum file size in MB')
    parser.add_argument('--rename', action='store_true', help='Rename files instead of preserving original filenames')
    
    args = parser.parse_args()
    
    if args.interactive:
        interactive_mode()
        return
    
    # Get files based on source
    files = []
    file_types = args.types if not args.types else [t.lower().lstrip('.') for t in args.types]
    
    if args.category:
        files = get_files_from_category(args.category, file_types, args.limit)
    elif args.user:
        files = get_files_from_user(args.user, file_types, args.limit)
    elif args.search:
        files = get_files_from_search(args.search, file_types, args.limit)
    elif args.file:
        files = get_files_from_text_file(args.file, file_types)
    
    if not files:
        print("No files found to download")
        return
    
    # Download files
    download_files(
        files,
        args.output,
        args.threads,
        not args.rename,  # preserve_filename = not args.rename
        args.max_size
    )

if __name__ == "__main__":
    main()#!/usr/bin/python
# -*- coding: utf-8 -*-

import pywikibot
from pywikibot import pagegenerators
import os
import requests
import argparse
import re
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

"""
pwb_batch_downloader.py - Download files from Wikimedia Commons

This script allows you to download multiple files from Wikimedia Commons based on:
- Category membership
- User uploads
- File titles from a text file
- Search results

Features:
- Concurrent downloads to speed up the process
- Preserves original filenames or formats them based on preferences
- Can filter by file type, size, upload date, etc.
- Saves file metadata in a CSV file

Usage:
    python pwb_batch_downloader.py --category "Category:Your_category" --output "./downloads"
    python pwb_batch_downloader.py --user "Username" --output "./downloads"
    python pwb_batch_downloader.py --file "filelist.txt" --output "./downloads"
    python pwb_batch_downloader.py --search "search term" --output "./downloads"
"""

# Site configuration
site = pywikibot.Site('commons', 'commons')

# Default settings
DEFAULT_OUTPUT_DIR = "./downloads"
DEFAULT_MAX_FILES = 100
DEFAULT_THREADS = 4
DEFAULT_FILE_TYPES = ["jpg", "jpeg", "png", "gif", "svg", "tif", "tiff"]

def sanitize_filename(filename):
    """Remove invalid characters from filename."""
    # Remove namespace prefix if present
    if ':' in filename:
        filename = filename.split(':', 1)[1]
    
    # Replace problematic characters
    invalid_chars = r'[<>:"/\\|?*]'
    filename = re.sub(invalid_chars, '_', filename)
    
    return filename

def download_file(file_page, output_dir, preserve_filename=True, max_size=None):
    """Download a single file."""
    try:
        # Get file URL for the original file
        file_url = file_page.get_file_url()
        
        # Get file info
        file_info = file_page.latest_file_info
        file_size = file_info.size if hasattr(file_info, 'size') else 0
        
        # Check file size
        if max_size and file_size > max_size * 1024 * 1024:  # Convert MB to bytes
            print(f"Skipping {file_page.title()} - size {file_size / (1024 * 1024):.1f} MB exceeds limit of {max_size} MB")
            return None
        
        # Determine filename
        if preserve_filename:
            filename = sanitize_filename(file_page.title())
        else:
            # Use upload date and file ID to create filename
            revision = file_page.latest_revision
            timestamp = revision.timestamp.strftime('%Y%m%d')
            file_id = hash(file_page.title()) % 10000  # Simple hash for unique ID
            ext = os.path.splitext(file_page.title())[1].lower()
            if not ext:
                ext = '.jpg'  # Default extension
            filename = f"commons_{timestamp}_{file_id}{ext}"
        
        # Ensure the output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Full path to save the file
        filepath = os.path.join(output_dir, filename)
        
        # Download the file
        headers = {
            'User-Agent': 'pwb_batch_downloader/1.0 (https://meta.wikimedia.org/wiki/User-Agent_policy)'
        }
        response = requests.get(file_url, headers=headers, stream=True)
        
        if response.status_code == 200:
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"Downloaded: {file_page.title()} -> {filepath}")
            return {
                'title': file_page.title(),
                'url': file_url,
                'size': file_size,
                'local_path': filepath,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        else:
            print(f"Failed to download {file_page.title()}: HTTP {response.status_code}")
            return None
    
    except Exception as e:
        print(f"Error downloading {file_page.title()}: {e}")
        return None