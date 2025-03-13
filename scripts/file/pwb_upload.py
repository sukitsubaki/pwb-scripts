#!/usr/bin/python
# -*- coding: utf-8 -*-

import pywikibot
import os
import argparse
from datetime import datetime

"""
pwb_upload.py - Batch upload files to Wikimedia Commons

This script provides a flexible tool for uploading multiple files 
to Wikimedia Commons with customizable descriptions and metadata.

Features:
- Batch upload from a directory
- Customizable file description template
- Support for different file types
- Interactive and command-line modes
- Upload tracking and reporting

Usage:
    python pwb_upload.py --directory "/path/to/images"
    python pwb_upload.py --interactive
"""

# Site configuration
site = pywikibot.Site('commons', 'commons')

# Default file description template
DEFAULT_DESCRIPTION = """== {{int:filedesc}} ==
{{Information
|Description=
|Source={{own}}
|Date={{date|YYYY-MM-DD}}
|Author=[[User:YOUR_USERNAME|YOUR_USERNAME]]
|Permission=
|Other_versions=
}}

== {{int:license-header}} ==
{{self|cc-by-sa-4.0}}

[[Category:Files by YOUR_USERNAME]]
"""

def generate_file_description(filename, custom_description=None):
    """
    Generate file description using template and filename details.
    
    Args:
        filename (str): Name of the file being uploaded
        custom_description (str, optional): Custom description template
    
    Returns:
        str: Formatted file description
    """
    # Use custom description or default
    description = custom_description or DEFAULT_DESCRIPTION
    
    # Replace placeholders
    description = description.replace('{{date|YYYY-MM-DD}}', datetime.now().strftime('%Y-%m-%d'))
    
    return description

def upload_file(file_path, site, description=None):
    """
    Upload a single file to Wikimedia Commons.
    
    Args:
        file_path (str): Path to the file to upload
        site (pywikibot.Site): Wikimedia Commons site instance
        description (str, optional): File description
    
    Returns:
        dict: Upload result information
    """
    try:
        # Validate file exists
        if not os.path.exists(file_path):
            return {
                'filename': os.path.basename(file_path),
                'success': False,
                'error': 'File does not exist'
            }
        
        # Prepare file for upload
        filename = os.path.basename(file_path)
        commons_filename = filename  # You might want to modify this for consistent naming
        
        # Create FilePage
        file_page = pywikibot.FilePage(site, f'File:{commons_filename}')
        
        # Check if file already exists
        if file_page.exists():
            return {
                'filename': commons_filename,
                'success': False,
                'error': 'File already exists on Commons'
            }
        
        # Generate description if not provided
        upload_description = description or generate_file_description(filename)
        
        # Perform upload
        try:
            site.upload(
                filepage=file_page,
                source_filename=file_path,
                comment="Batch upload",
                text=upload_description,
                ignore_warnings=False
            )
            
            return {
                'filename': commons_filename,
                'success': True,
                'path': file_path
            }
        
        except Exception as upload_error:
            return {
                'filename': commons_filename,
                'success': False,
                'error': str(upload_error)
            }
    
    except Exception as e:
        return {
            'filename': os.path.basename(file_path),
            'success': False,
            'error': str(e)
        }

def process_directory(directory, file_types=None, description=None):
    """
    Process and upload files from a directory.
    
    Args:
        directory (str): Path to directory with files to upload
        file_types (list, optional): Allowed file extensions
        description (str, optional): Custom file description
    
    Returns:
        list: List of upload results
    """
    # Validate directory
    if not os.path.isdir(directory):
        print(f"Error: {directory} is not a valid directory")
        return []
    
    # Default file types if not specified
    if file_types is None:
        file_types = ['jpg', 'jpeg', 'png', 'gif', 'svg', 'tif', 'tiff']
    
    # Normalize file types to lowercase
    file_types = [ft.lower().lstrip('.') for ft in file_types]
    
    # Collect files to upload
    files_to_upload = []
    for filename in os.listdir(directory):
        # Check file extension
        file_ext = os.path.splitext(filename)[1].lower().lstrip('.')
        if file_ext in file_types:
            files_to_upload.append(os.path.join(directory, filename))
    
    # Upload files
    upload_results = []
    for file_path in files_to_upload:
        result = upload_file(file_path, site, description)
        upload_results.append(result)
    
    # Generate report
    report = create_report(upload_results)
    save_report(report)
    
    return upload_results

def create_report(upload_results):
    """
    Create a report of upload operations.
    
    Args:
        upload_results (list): List of upload operation results
    
    Returns:
        str: Formatted report in wiki markup
    """
    report = """= Batch Upload Report =

== Summary ==
* Total files processed: {}
* Successful uploads: {}
* Failed uploads: {}

== Upload Details ==
""".format(
        len(upload_results),
        sum(1 for r in upload_results if r['success']),
        sum(1 for r in upload_results if not r['success'])
    )
    
    # Successful uploads
    report += "\n=== Successful Uploads ===\n"
    successful_uploads = [r for r in upload_results if r['success']]
    if successful_uploads:
        for result in successful_uploads:
            report += f"* [[File:{result['filename']}]]\n"
    else:
        report += "No files uploaded successfully.\n"
    
    # Failed uploads
    report += "\n=== Failed Uploads ===\n"
    failed_uploads = [r for r in upload_results if not r['success']]
    if failed_uploads:
        for result in failed_uploads:
            report += f"* {result['filename']}: {result.get('error', 'Unknown error')}\n"
    else:
        report += "No upload failures.\n"
    
    report += f"\nReport generated by pwb_upload.py on ~~~~~"
    
    return report

def save_report(report):
    """
    Save the report to a user page.
    
    Args:
        report (str): Report content to save
    """
    try:
        user_page = pywikibot.Page(site, 'User:YOUR_USERNAME/pwb/Upload_Report')
        user_page.text = report
        user_page.save(summary="pwb: Updated batch upload report")
        print(f"Report saved to {user_page.title()}")
    except Exception as e:
        print(f"Error saving report: {e}")
        print("Report content:")
        print(report)

def interactive_mode():
    """Interactive mode for batch uploading."""
    print("=== PWB Batch Upload Tool ===")
    
    while True:
        print("\nOptions:")
        print("1. Upload files from a directory")
        print("2. Exit")
        
        choice = input("\nEnter your choice (1-2): ").strip()
        
        if choice == '1':
            # Get directory path
            directory = input("Enter directory path to upload from: ").strip()
            
            # Optional file type filtering
            filter_types = input("Filter by file types? (y/n): ").lower() == 'y'
            file_types = None
            if filter_types:
                file_types = input("Enter file types (comma-separated, e.g., jpg,png): ").strip().split(',')
            
            # Optional custom description
            use_custom_desc = input("Use custom file description? (y/n): ").lower() == 'y'
            description = None
            if use_custom_desc:
                print("Enter custom description template (use wiki markup):")
                description = input("Description: ").strip()
            
            # Confirm upload
            print("\nUpload configuration:")
            print(f"Directory: {directory}")
            print(f"File types: {file_types or 'All'}")
            
            confirm = input("\nProceed with upload? (y/n): ").lower()
            
            if confirm == 'y':
                # Perform upload
                results = process_directory(directory, file_types, description)
                
                # Display summary
                successful = sum(1 for r in results if r['success'])
                print(f"\nUploaded {successful} out of {len(results)} files")
        
        elif choice == '2':
            print("Exiting...")
            break
        
        else:
            print("Invalid choice")

def main():
    """
    Main function to handle command-line arguments and script execution.
    """
    parser = argparse.ArgumentParser(description='Batch upload files to Wikimedia Commons')
    
    # Create mutually exclusive group for the modes
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--directory', help='Directory containing files to upload')
    group.add_argument('--interactive', action='store_true', help='Run in interactive mode')
    
    # Additional arguments
    parser.add_argument('--types', nargs='+', 
                        help='File types to upload (e.g., jpg png)')
    parser.add_argument('--description', 
                        help='Custom file description template')
    
    args = parser.parse_args()
    
    # Validate login
    try:
        site.login()
    except Exception as e:
        print(f"Login failed: {e}")
        return
    
    if args.interactive:
        interactive_mode()
    elif args.directory:
        # Process directory upload
        results = process_directory(
            args.directory, 
            args.types, 
            args.description
        )
        
        # Display summary
        successful = sum(1 for r in results if r['success'])
        print(f"Uploaded {successful} out of {len(results)} files")

if __name__ == "__main__":
    main()