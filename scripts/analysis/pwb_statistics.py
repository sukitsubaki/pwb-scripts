#!/usr/bin/python
# -*- coding: utf-8 -*-

import pywikibot
from pywikibot import pagegenerators
import re
from datetime import datetime
from collections import Counter, defaultdict
import matplotlib.pyplot as plt
import os
from PIL import Image
from io import BytesIO
import requests
import json

"""
pwb_statistics.py - Generate statistics about your uploads

This script analyzes your uploads and generates various statistics:
- Upload counts by month/year
- Most used categories
- Camera-lens combinations
- Aspect ratios
- Geographic distribution
- File sizes and resolutions

Requirements:
    pip install pillow matplotlib requests

Usage:
    python pwb_statistics.py
"""

# Site and category configuration
site = pywikibot.Site('commons', 'commons')
username = 'YOUR_USERNAME'  # Replace with your username
category = pywikibot.Category(site, f'Category:Files by {username}')  # Adjust as needed

# Output paths
OUTPUT_DIR = './statistics'
os.makedirs(OUTPUT_DIR, exist_ok=True)

def extract_date_from_filename(filename):
    """Extract date from filename if it contains a date pattern."""
    # Common date patterns: YYYY-MM-DD, YYYYMMDD, etc.
    date_patterns = [
        r'(\d{4})-(\d{2})-(\d{2})',  # YYYY-MM-DD
        r'(\d{4})(\d{2})(\d{2})',     # YYYYMMDD
        r'(\d{2})-(\d{2})-(\d{4})',   # DD-MM-YYYY
        r'(\d{2})(\d{2})(\d{4})'      # DDMMYYYY
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, filename)
        if match:
            groups = match.groups()
            if len(groups[0]) == 4:  # YYYY-MM-DD format
                year, month, day = groups
            else:  # DD-MM-YYYY format
                day, month, year = groups
            
            try:
                return datetime(int(year), int(month), int(day))
            except ValueError:
                continue
    
    return None

def extract_date_from_text(text):
    """Extract date from file description or information template."""
    # Look for date in information template
    date_match = re.search(r'\|Date=([^\|\}]+)', text)
    if date_match:
        date_str = date_match.group(1).strip()
        
        # Try different date formats
        date_formats = [
            '%Y-%m-%d',          # 2023-01-25
            '%d %B %Y',          # 25 January 2023
            '%B %d, %Y',         # January 25, 2023
            '%Y/%m/%d',          # 2023/01/25
            '%d/%m/%Y',          # 25/01/2023
            '%Y %m %d',          # 2023 01 25
            '%d.%m.%Y',          # 25.01.2023
            '%Y'                 # 2023
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
    
    return None

def extract_camera_lens_info(text):
    """Extract camera and lens information from file description."""
    camera = None
    lens = None
    
    # Look for camera information
    camera_patterns = [
        r'Camera:\s*([^,\|\}\n]+)',
        r'camera used[:\s]+([^,\|\}\n]+)',
        r'taken with[:\s]+([^,\|\}\n]+)',
        r'shot with[:\s]+([^,\|\}\n]+)'
    ]
    
    for pattern in camera_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            camera = match.group(1).strip()
            break
    
    # Look for lens information
    lens_patterns = [
        r'Lens:\s*([^,\|\}\n]+)',
        r'lens used[:\s]+([^,\|\}\n]+)',
        r'([0-9]+[-\s]*[0-9]*\s*mm\s*f\/[0-9\.]+)',  # Pattern like "24-70mm f/2.8"
        r'([0-9]+\s*mm\s*f\/[0-9\.]+)'               # Pattern like "50mm f/1.4"
    ]
    
    for pattern in lens_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            lens = match.group(1).strip()
            break
    
    return camera, lens

def extract_categories(text):
    """Extract all categories from file description."""
    category_pattern = r'\[\[Category:([^\]]+)\]\]'
    return re.findall(category_pattern, text)

def extract_location(text):
    """Extract location information from file description."""
    # Look for Location template
    location_match = re.search(r'{{Location\s*\|([^}]+)}}', text)
    if location_match:
        try:
            params = location_match.group(1).split('|')
            if len(params) >= 8:
                lat_deg, lat_min, lat_sec, lat_dir = params[0:4]
                lon_deg, lon_min, lon_sec, lon_dir = params[4:8]
                
                # Calculate decimal coordinates
                lat = int(lat_deg) + float(lat_min)/60 + float(lat_sec)/3600
                lon = int(lon_deg) + float(lon_min)/60 + float(lon_sec)/3600
                
                if lat_dir.upper() == 'S':
                    lat = -lat
                if lon_dir.upper() == 'W':
                    lon = -lon
                
                return lat, lon
        except (ValueError, IndexError):
            pass
    
    # Look for coordinates in other formats
    coord_match = re.search(r'{{Coord\|([^}]+)}}', text)
    if coord_match:
        coords = coord_match.group(1).split('|')
        try:
            if len(coords) >= 2:
                lat = float(coords[0])
                lon = float(coords[1])
                return lat, lon
        except ValueError:
            pass
    
    return None

def extract_resolution_and_size(file_page):
    """Get resolution and file size information."""
    try:
        file_info = file_page.latest_file_info
        width = file_info.width
        height = file_info.height
        size = file_info.size  # in bytes
        return width, height, size
    except:
        return None, None, None

def get_reverse_geocode(lat, lon):
    """Get location name from coordinates using Nominatim API."""
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}&zoom=10"
        headers = {
            'User-Agent': 'YOUR_USERNAME Wikipedia Bot/1.0'
        }
        response = requests.get(url, headers=headers)
        data = json.loads(response.text)
        
        # Extract country and state/city
        address = data.get('address', {})
        country = address.get('country', 'Unknown')
        state = address.get('state', address.get('county', address.get('city', 'Unknown')))
        
        return f"{state}, {country}"
    except:
        return "Unknown"

def download_and_get_aspect_ratio(file_page):
    """Download image and calculate aspect ratio."""
    try:
        # Get resolution from file info
        width, height, _ = extract_resolution_and_size(file_page)
        if width and height:
            return width / height
        
        # If that fails, download image and check
        image_url = file_page.get_file_url()
        response = requests.get(image_url)
        img = Image.open(BytesIO(response.content))
        width, height = img.size
        return width / height
    except:
        return None

def format_aspect_ratio(ratio):
    """Format aspect ratio as a string like 16:9, 4:3, etc."""
    if not ratio:
        return "Unknown"
    
    # Common aspect ratios and their names
    common_ratios = {
        1.0: "1:1",
        1.33: "4:3",
        1.5: "3:2",
        1.78: "16:9",
        1.85: "1.85:1",
        2.35: "2.35:1",
        0.67: "2:3",
        0.75: "3:4",
        0.56: "9:16"
    }
    
    # Find closest common ratio
    for r, name in common_ratios.items():
        if abs(ratio - r) < 0.05:
            return name
    
    # If not common, return numerical value
    return f"{ratio:.2f}:1"

def generate_statistics():
    """Generate statistics about uploads."""
    print("Generating statistics about your uploads...")
    
    # Get all files by the user
    user = pywikibot.User(site, username)
    files = list(user.contributions(total=5000, namespace=6))  # Namespace 6 is File
    
    if not files:
        print(f"No files found for user {username}")
        return
    
    print(f"Found {len(files)} files to analyze")
    
    # Data structures for statistics
    upload_dates = []
    categories_count = Counter()
    camera_lens_combos = Counter()
    aspect_ratios = Counter()
    locations = defaultdict(int)
    resolutions = []
    file_sizes = []
    
    # Counts for charts
    uploads_by_month = defaultdict(int)
    uploads_by_year = defaultdict(int)
    
    # Process each file
    for i, (timestamp, page, _, _) in enumerate(files):
        if i % 10 == 0:
            print(f"Processing file {i+1}/{len(files)}: {page.title()}")
        
        try:
            if not page.exists() or page.namespace() != 6:  # Only process files
                continue
            
            # 1. Get upload date
            upload_date = timestamp
            upload_dates.append(upload_date)
            uploads_by_month[upload_date.strftime('%Y-%m')] += 1
            uploads_by_year[upload_date.year] += 1
            
            # 2. Get text content
            text = page.text
            
            # 3. Extract categories
            for category in extract_categories(text):
                categories_count[category] += 1
            
            # 4. Extract camera and lens info
            camera, lens = extract_camera_lens_info(text)
            if camera and lens:
                camera_lens_combos[f"{camera} + {lens}"] += 1
            elif camera:
                camera_lens_combos[camera] += 1
            
            # 5. Extract aspect ratio
            aspect_ratio = download_and_get_aspect_ratio(page)
            if aspect_ratio:
                ratio_name = format_aspect_ratio(aspect_ratio)
                aspect_ratios[ratio_name] += 1
            
            # 6. Extract location
            location_coords = extract_location(text)
            if location_coords:
                lat, lon = location_coords
                location_name = get_reverse_geocode(lat, lon)
                locations[location_name] += 1
            
            # 7. Extract resolution and file size
            width, height, size = extract_resolution_and_size(page)
            if width and height:
                resolutions.append((width, height))
            if size:
                file_sizes.append(size)
        
        except Exception as e:
            print(f"Error processing {page.title()}: {e}")
    
    # Generate plots and report
    generate_plots(uploads_by_month, uploads_by_year, categories_count, 
                  camera_lens_combos, aspect_ratios, locations, 
                  resolutions, file_sizes)
    
    generate_report(uploads_by_month, uploads_by_year, categories_count, 
                   camera_lens_combos, aspect_ratios, locations, 
                   resolutions, file_sizes)

def generate_plots(uploads_by_month, uploads_by_year, categories_count, 
                  camera_lens_combos, aspect_ratios, locations, 
                  resolutions, file_sizes):
    """Generate plots from the collected statistics."""
    
    # 1. Upload trend by month
    plt.figure(figsize=(12, 6))
    months = sorted(uploads_by_month.keys())
    counts = [uploads_by_month[m] for m in months]
    plt.bar(months, counts)
    plt.xticks(rotation=90)
    plt.title(f'Uploads by Month - {username}')
    plt.xlabel('Month')
    plt.ylabel('Number of uploads')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'uploads_by_month.png'))
    plt.close()
    
    # 2. Upload trend by year
    plt.figure(figsize=(10, 6))
    years = sorted(uploads_by_year.keys())
    counts = [uploads_by_year[y] for y in years]
    plt.bar(years, counts)
    plt.title(f'Uploads by Year - {username}')
    plt.xlabel('Year')
    plt.ylabel('Number of uploads')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'uploads_by_year.png'))
    plt.close()
    
    # 3. Top categories pie chart
    plt.figure(figsize=(10, 8))
    top_categories = dict(categories_count.most_common(10))
    plt.pie(top_categories.values(), labels=top_categories.keys(), autopct='%1.1f%%')
    plt.title(f'Top 10 Categories - {username}')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'top_categories.png'))
    plt.close()
    
    # 4. Camera-lens combinations bar chart
    plt.figure(figsize=(12, 6))
    top_combos = dict(camera_lens_combos.most_common(10))
    plt.barh(list(top_combos.keys()), list(top_combos.values()))
    plt.title(f'Top 10 Camera-Lens Combinations - {username}')
    plt.xlabel('Number of uploads')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'camera_lens_combos.png'))
    plt.close()
    
    # 5. Aspect ratios pie chart
    plt.figure(figsize=(10, 8))
    plt.pie(aspect_ratios.values(), labels=aspect_ratios.keys(), autopct='%1.1f%%')
    plt.title(f'Aspect Ratios Distribution - {username}')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'aspect_ratios.png'))
    plt.close()
    
    # 6. File sizes histogram
    if file_sizes:
        plt.figure(figsize=(10, 6))
        sizes_mb = [s / (1024 * 1024) for s in file_sizes]  # Convert to MB
        plt.hist(sizes_mb, bins=20)
        plt.title(f'File Size Distribution - {username}')
        plt.xlabel('Size (MB)')
        plt.ylabel('Number of files')
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUT_DIR, 'file_sizes.png'))
        plt.close()
    
    # 7. Resolutions scatter plot
    if resolutions:
        plt.figure(figsize=(10, 6))
        widths = [r[0] for r in resolutions]
        heights = [r[1] for r in resolutions]
        plt.scatter(widths, heights, alpha=0.5)
        plt.title(f'Image Resolutions - {username}')
        plt.xlabel('Width (pixels)')
        plt.ylabel('Height (pixels)')
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUT_DIR, 'resolutions.png'))
        plt.close()

def generate_report(uploads_by_month, uploads_by_year, categories_count, 
                   camera_lens_combos, aspect_ratios, locations, 
                   resolutions, file_sizes):
    """Generate a report with the statistics."""
    
    # Calculate some additional statistics
    total_uploads = sum(uploads_by_month.values())
    
    # For file sizes
    if file_sizes:
        avg_size_mb = sum(file_sizes) / len(file_sizes) / (1024 * 1024)  # Average size in MB
        max_size_mb = max(file_sizes) / (1024 * 1024)  # Max size in MB
    else:
        avg_size_mb = 0
        max_size_mb = 0
    
    # For resolutions
    if resolutions:
        avg_width = sum(r[0] for r in resolutions) / len(resolutions)
        avg_height = sum(r[1] for r in resolutions) / len(resolutions)
        max_res = max(resolutions, key=lambda r: r[0] * r[1])
    else:
        avg_width = 0
        avg_height = 0
        max_res = (0, 0)
    
    # Generate wiki markup report
    report = f"""= Upload Statistics for {username} =

== Summary ==
* Total uploads: {total_uploads}
* First upload: {min(uploads_by_month.keys()) if uploads_by_month else 'Unknown'}
* Latest upload: {max(uploads_by_month.keys()) if uploads_by_month else 'Unknown'}
* Average file size: {avg_size_mb:.2f} MB
* Average resolution: {avg_width:.0f} × {avg_height:.0f} pixels
* Most uploads in a month: {max(uploads_by_month.values()) if uploads_by_month else 0}
* Most uploads in a year: {max(uploads_by_year.values()) if uploads_by_year else 0}

== Top Categories ==
{chr(10).join(['* ' + cat + ': ' + str(count) for cat, count in categories_count.most_common(20)])}

== Top Camera-Lens Combinations ==
{chr(10).join(['* ' + combo + ': ' + str(count) for combo, count in camera_lens_combos.most_common(10)])}

== Aspect Ratio Distribution ==
{chr(10).join(['* ' + ratio + ': ' + str(count) for ratio, count in aspect_ratios.most_common()])}

== Top Locations ==
{chr(10).join(['* ' + loc + ': ' + str(count) for loc, count in sorted(locations.items(), key=lambda x: x[1], reverse=True)[:10]])}

== File Size Statistics ==
* Average file size: {avg_size_mb:.2f} MB
* Maximum file size: {max_size_mb:.2f} MB
* Files larger than 5 MB: {sum(1 for s in file_sizes if s > 5 * 1024 * 1024)}
* Files smaller than 1 MB: {sum(1 for s in file_sizes if s < 1024 * 1024)}

== Resolution Statistics ==
* Average resolution: {avg_width:.0f} × {avg_height:.0f} pixels
* Maximum resolution: {max_res[0]} × {max_res[1]} pixels
* Files with 4K+ resolution: {sum(1 for r in resolutions if r[0] >= 3840 or r[1] >= 2160)}
* Files with HD resolution: {sum(1 for r in resolutions if 1920 <= r[0] < 3840 or 1080 <= r[1] < 2160)}

Report generated by pwb_statistics.py on ~~~~~
"""
    
    # Save report to a file
    with open(os.path.join(OUTPUT_DIR, 'statistics_report.txt'), 'w', encoding='utf-8') as f:
        f.write(report)
    
    # Save report to user page
    try:
        user_page = pywikibot.Page(site, f'User:{username}/pwb/Statistics')
        user_page.text = report
        user_page.save(summary="pwb: Updated upload statistics")
        print(f"Report saved to {user_page.title()}")
    except Exception as e:
        print(f"Error saving report to wiki: {e}")
        print("Report saved locally instead.")

def main():
    """Main function."""
    print(f"Generating statistics for user {username}...")
    generate_statistics()
    print(f"Done! Statistics saved to {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
