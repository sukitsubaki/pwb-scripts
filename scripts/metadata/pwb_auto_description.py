def suggest_categories(file_page, exif_data, location_name):
    """Suggest categories based on file information."""
    suggested_categories = set()
    
    # Add default categories for user's uploads
    suggested_categories.add(f"Files by {USERNAME}")
    
    # Add camera/equipment categories
    make = exif_data.get('Make', '').strip()
    model = exif_data.get('Model', '').strip()
    if make and model:
        # Clean up make/model
        make = make.replace(',', '').replace(';', '')
        model = model.replace(',', '').replace(';', '')
        
        # Add camera category
        suggested_categories.add(f"Photographs taken with {make} {model}")
    
    # Add year category based on file upload date or EXIF date
    year = None
    
    # Try EXIF date first
    if 'DateTimeOriginal' in exif_data:
        date_str = exif_data['DateTimeOriginal']
        try:
            # EXIF date format: '2023:01:25 15:30:45'
            year = date_str.split(':')[0]
        except:
            pass
    
    # Fall back to upload date if EXIF date not available
    if not year:
        try:
            revision = file_page.oldest_revision
            year = revision.timestamp.year
        except:
            pass
    
    if year:
        suggested_categories.add(f"Photographs taken in {year}")
    
    # Add location-based categories
    if location_name:
        location_parts = location_name.split(", ")
        
        # Country
        if len(location_parts) >= 1:
            country = location_parts[-1]
            suggested_categories.add(f"{country}")
        
        # Region/State
        if len(location_parts) >= 2:
            region = location_parts[-2]
            suggested_categories.add(f"{region}")
            
            # More specific location if available
            if len(location_parts) >= 3:
                place = location_parts[0]
                suggested_categories.add(f"{place}")
    
    # Normalize and filter categories
    normalized_categories = []
    for category in suggested_categories:
        # Skip empty categories
        if not category.strip():
            continue
            
        # Format as wiki link
        category = category.replace('_', ' ').strip()
        normalized_categories.append(f"[[Category:{category}]]")
    
    return "\n".join(normalized_categories)

def generate_description(file_page, exif_data=None, location_data=None):
    """Generate an improved description for a file."""
    # Get file URL
    try:
        file_url = file_page.get_file_url()
    except:
        print(f"Error: Could not get URL for {file_page.title()}")
        return None
    
    # Get EXIF data if not provided
    if not exif_data:
        exif_data = get_exif_data(file_url)
    
    # Get location data if not provided
    if not location_data:
        location_data = parse_location_from_exif(exif_data)
    
    # Get current description
    current_text = file_page.text
    
    # Extract existing information
    current_description = ""
    current_date = ""
    match = re.search(r'\|description=([^|]+)', current_text)
    if match:
        current_description = match.group(1).strip()
    
    match = re.search(r'\|date=([^|]+)', current_text)
    if match:
        current_date = match.group(1).strip()
    
    # Generate new description parts
    exif_description = format_exif_data(exif_data)
    
    # Combine descriptions
    if current_description and exif_description:
        description = f"{current_description}\n\n{exif_description}"
    elif exif_description:
        description = exif_description
    else:
        description = current_description or "No description available"
    
    # Get or generate date
    date = current_date
    if not date and 'DateTimeOriginal' in exif_data:
        date_str = exif_data['DateTimeOriginal']
        try:
            # Format: 2023:01:25 15:30:45
            date_parts = date_str.split(' ')[0].split(':')
            date = f"{date_parts[0]}-{date_parts[1]}-{date_parts[2]}"
        except:
            date = datetime.now().strftime("%Y-%m-%d")
    
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
    
    # Location information
    location_template = ""
    location_name = None
    if location_data:
        lat, lon = location_data
        location_template = format_location_template(lat, lon)
        location_name = get_location_name(lat, lon)
    
    # Suggest categories
    categories = suggest_categories(file_page, exif_data, location_name)
    
    # Fill the template
    new_description = INFORMATION_TEMPLATE.replace("$description", description)
    new_description = new_description.replace("$date", date)
    new_description = new_description.replace("$source", DEFAULT_SOURCE)
    new_description = new_description.replace("$author", DEFAULT_AUTHOR)
    new_description = new_description.replace("$permission", DEFAULT_PERMISSION)
    new_description = new_description.replace("$other_versions", "")
    new_description = new_description.replace("$location_template", location_template)
    new_description = new_description.replace("$license_template", DEFAULT_LICENSE)
    new_description = new_description.replace("$categories", categories)
    
    return new_description

def update_file_description(file_page, new_description, summary="Updated file description with improved information"):
    """Update a file's description."""
    try:
        file_page.text = new_description
        file_page.save(summary=summary)
        print(f"Successfully updated description for {file_page.title()}")
        return True
    except Exception as e:
        print(f"Error updating {file_page.title()}: {e}")
        return False

def process_file(file_title):
    """Process a single file by title."""
    # Ensure title has File: prefix
    if not file_title.startswith('File:'):
        file_title = f'File:{file_title}'
    
    # Get file page
    file_page = pywikibot.Page(site, file_title)
    
    if not file_page.exists():
        print(f"Error: File {file_title} does not exist")
        return False
    
    # Generate new description
    new_description = generate_description(file_page)
    
    if not new_description:
        print(f"Error generating description for {file_title}")
        return False
    
    # Show preview
    print("\nCurrent description:")
    print("-" * 40)
    print(file_page.text)
    print("\nProposed new description:")
    print("-" * 40)
    print(new_description)
    
    # Ask for confirmation
    if input("\nUpdate file description? (y/n): ").lower() == 'y':
        return update_file_description(file_page, new_description)
    else:
        print("Update cancelled")
        return False

def process_category(category_name):
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
        
        # Generate new description
        new_description = generate_description(file_page)
        
        if not new_description:
            print(f"Error generating description for {file_page.title()}")
            continue
        
        # Show preview
        print("\nCurrent description:")
        print("-" * 40)
        print(file_page.text[:500] + "..." if len(file_page.text) > 500 else file_page.text)
        print("\nProposed new description:")
        print("-" * 40)
        print(new_description[:500] + "..." if len(new_description) > 500 else new_description)
        
        # Ask for confirmation
        response = input("\nUpdate file description? (y/n/a/q - a=all remaining, q=quit): ").lower()
        
        if response == 'q':
            print("Operation cancelled")
            break
        elif response == 'a':
            # Update all remaining without prompting
            update_file_description(file_page, new_description)
            updated += 1
            
            for j, remaining_file in enumerate(files[i+1:]):
                print(f"\nProcessing file {i+j+2}/{len(files)}: {remaining_file.title()}")
                remaining_description = generate_description(remaining_file)
                
                if remaining_description:
                    if update_file_description(remaining_file, remaining_description):
                        updated += 1
            
            break
        elif response == 'y':
            if update_file_description(file_page, new_description):
                updated += 1
        else:
            print("Skipped")
    
    return updated

def interactive_mode():
    """Interactive mode for processing files."""
    print("=== PWB Auto Description Generator ===")
    
    while True:
        print("\nOptions:")
        print("1. Process single file")
        print("2. Process all files in a category")
        print("3. Exit")
        
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == '1':
            file_title = input("Enter file title (with or without 'File:' prefix): ").strip()
            process_file(file_title)
        
        elif choice == '2':
            category_name = input("Enter category name (with or without 'Category:' prefix): ").strip()
            updated = process_category(category_name)
            print(f"\nUpdated {updated} files")
        
        elif choice == '3':
            print("Exiting...")
            break
        
        else:
            print("Invalid choice")

def main():
    """Main function to handle command line arguments."""
    parser = argparse.ArgumentParser(description='Generate better descriptions for files on Wikimedia Commons')
    
    # Create mutually exclusive group for the modes
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--file', help='Process a single file')
    group.add_argument('--category', help='Process all files in a category')
    group.add_argument('--interactive', action='store_true', help='Run in interactive mode')
    
    args = parser.parse_args()
    
    if args.interactive:
        interactive_mode()
    elif args.file:
        process_file(args.file)
    elif args.category:
        updated = process_category(args.category)
        print(f"\nUpdated {updated} files")

if __name__ == "__main__":
    main()#!/usr/bin/python
# -*- coding: utf-8 -*-

import pywikibot
from pywikibot import pagegenerators
import os
import requests
from PIL import Image
from io import BytesIO
from PIL.ExifTags import TAGS, GPSTAGS
import re
import argparse
from datetime import datetime
import json

"""
pwb_auto_description.py - Generate better descriptions for image files

This script analyzes image files and creates improved descriptions based on:
- EXIF metadata (camera, lens, settings)
- Location data (coordinates to location names)
- Categorization suggestions
- Standardized templates

Usage:
    python pwb_auto_description.py --file "File:Example.jpg"
    python pwb_auto_description.py --category "Category:Your_uploads"
    python pwb_auto_description.py --interactive
"""

# Nominatim API endpoint for reverse geocoding
NOMINATIM_API = "https://nominatim.openstreetmap.org/reverse"

# Site configuration
site = pywikibot.Site('commons', 'commons')

# Your configuration - CHANGE THESE
USERNAME = "YOUR_USERNAME"
DEFAULT_SOURCE = "{{own}}"
DEFAULT_AUTHOR = f"{{{{Creator:{USERNAME}}}}}"
DEFAULT_PERMISSION = "{{self|cc-by-sa-4.0}}"
DEFAULT_LICENSE = "{{cc-by-sa-4.0}}"

# Templates
INFORMATION_TEMPLATE = """== {{int:filedesc}} ==
{{Information
|description={{en|1=$description}}
|date=$date
|source=$source
|author=$author
|permission=$permission
|other versions=$other_versions
}}
$location_template

== {{int:license-header}} ==
$license_template

$categories
"""

def format_location_template(lat, lon):
    """Format the location template with latitude and longitude."""
    if not lat or not lon:
        return ""
    
    # Convert decimal to degrees, minutes, seconds
    def decimal_to_dms(decimal):
        degrees = int(decimal)
        minutes = int((decimal - degrees) * 60)
        seconds = ((decimal - degrees) * 60 - minutes) * 60
        return degrees, minutes, seconds
    
    lat_deg, lat_min, lat_sec = decimal_to_dms(abs(lat))
    lat_dir = "N" if lat >= 0 else "S"
    
    lon_deg, lon_min, lon_sec = decimal_to_dms(abs(lon))
    lon_dir = "E" if lon >= 0 else "W"
    
    return f"{{{{Location|{lat_deg}|{lat_min}|{lat_sec:.1f}|{lat_dir}|{lon_deg}|{lon_min}|{lon_sec:.1f}|{lon_dir}}}}}"

def format_exif_data(exif_data):
    """Format EXIF data into a readable description."""
    if not exif_data:
        return ""
    
    description_parts = []
    
    # Camera make and model
    make = exif_data.get('Make', '').strip()
    model = exif_data.get('Model', '').strip()
    if make and model:
        # Avoid redundancy if make is included in model
        if make in model:
            description_parts.append(f"Camera: {model}")
        else:
            description_parts.append(f"Camera: {make} {model}")
    elif model:
        description_parts.append(f"Camera: {model}")
    
    # Lens info
    lens = exif_data.get('LensModel', exif_data.get('Lens', '')).strip()
    if lens:
        description_parts.append(f"Lens: {lens}")
    
    # Exposure settings
    exposure_info = []
    
    # Focal length
    if 'FocalLength' in exif_data:
        focal_length = exif_data['FocalLength']
        if isinstance(focal_length, tuple):
            focal_length = focal_length[0] / focal_length[1]
        exposure_info.append(f"{int(focal_length)}mm")
    
    # F-stop / aperture
    if 'FNumber' in exif_data:
        f_number = exif_data['FNumber']
        if isinstance(f_number, tuple):
            f_number = f_number[0] / f_number[1]
        exposure_info.append(f"f/{f_number:.1f}")
    
    # Shutter speed / exposure time
    if 'ExposureTime' in exif_data:
        exposure_time = exif_data['ExposureTime']
        if isinstance(exposure_time, tuple):
            exposure_time = exposure_time[0] / exposure_time[1]
        
        # Format exposure time nicely
        if exposure_time >= 1:
            exposure_str = f"{exposure_time:.1f}s"
        else:
            exposure_str = f"1/{int(1/exposure_time)}s"
        
        exposure_info.append(exposure_str)
    
    # ISO
    if 'ISOSpeedRatings' in exif_data:
        iso = exif_data['ISOSpeedRatings']
        exposure_info.append(f"ISO {iso}")
    
    if exposure_info:
        description_parts.append("Exposure: " + ", ".join(exposure_info))
    
    # Date taken
    if 'DateTimeOriginal' in exif_data:
        # Parse date in EXIF format: 'JJJJ:MM:DD HH:MM:SS'
        date_str = exif_data['DateTimeOriginal']
        try:
            # Replace ":" in date part with "-" for better formatting
            date_parts = date_str.split(' ')
            if len(date_parts) >= 1:
                date_parts[0] = date_parts[0].replace(':', '-')
                formatted_date = ' '.join(date_parts)
                description_parts.append(f"Date taken: {formatted_date}")
        except:
            pass
    
    return "\n".join(description_parts)

def get_exif_data(image_url):
    """Get EXIF data from image URL."""
    headers = {
        'User-Agent': f'{USERNAME}/1.0 (https://meta.wikimedia.org/wiki/User-Agent_policy)'
    }
    try:
        response = requests.get(image_url, headers=headers)
        img = Image.open(BytesIO(response.content))
        
        # Extract EXIF data
        exif_data = {}
        if hasattr(img, '_getexif') and img._getexif():
            for tag, value in img._getexif().items():
                tag_name = TAGS.get(tag, tag)
                exif_data[tag_name] = value
        
        return exif_data
    except Exception as e:
        print(f"Error getting EXIF data: {e}")
        return {}

def get_location_name(lat, lon):
    """Get location name from coordinates using Nominatim."""
    headers = {
        'User-Agent': f'{USERNAME}/1.0 (https://meta.wikimedia.org/wiki/User-Agent_policy)'
    }
    
    params = {
        'format': 'json',
        'lat': lat,
        'lon': lon,
        'zoom': 10,
        'addressdetails': 1
    }
    
    try:
        response = requests.get(NOMINATIM_API, headers=headers, params=params)
        data = json.loads(response.text)
        
        if 'address' in data:
            address = data['address']
            
            # Try to get city, town, or village
            locality = address.get('city', address.get('town', address.get('village', '')))
            
            # Get state/province and country
            state = address.get('state', address.get('county', ''))
            country = address.get('country', '')
            
            location_parts = [p for p in [locality, state, country] if p]
            return ', '.join(location_parts)
        
        return None
    
    except Exception as e:
        print(f"Error getting location name: {e}")
        return None

def parse_location_from_exif(exif_data):
    """Extract location from EXIF GPS data."""
    if 'GPSInfo' not in exif_data:
        return None
    
    try:
        gps_info = exif_data['GPSInfo']
        
        # Get latitude
        lat_ref = gps_info.get(GPSTAGS.get('GPSLatitudeRef'))
        lat = gps_info.get(GPSTAGS.get('GPSLatitude'))
        
        # Get longitude
        lon_ref = gps_info.get(GPSTAGS.get('GPSLongitudeRef'))
        lon = gps_info.get(GPSTAGS.get('GPSLongitude'))
        
        if not all([lat_ref, lat, lon_ref, lon]):
            return None
        
        # Convert to decimal degrees
        def convert_to_degrees(value):
            d, m, s = value
            return d + (m / 60.0) + (s / 3600.0)
        
        lat_deg = convert_to_degrees(lat)
        if lat_ref == 'S':
            lat_deg = -lat_deg
            
        lon_deg = convert_to_degrees(lon)
        if lon_ref == 'W':
            lon_deg = -lon_deg
            
        return lat_deg, lon_deg
        
    except Exception as e:
        print(f"Error parsing GPS data: {e}")
        return None