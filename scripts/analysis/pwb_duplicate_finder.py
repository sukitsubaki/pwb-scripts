#!/usr/bin/python
# -*- coding: utf-8 -*-

import pywikibot
from pywikibot import pagegenerators
import os
import requests
from io import BytesIO
from PIL import Image
import imagehash
import shutil
import tempfile

"""
pwb_duplicate_finder.py - Finds duplicate or similar images in your uploads

This script uses perceptual hashing to identify images that are visually similar,
helping to find potential duplicates in your uploads.

Requirements:
    pip install pillow imagehash numpy

Usage:
    python pwb_duplicate_finder.py
"""

# Site and category definition
site = pywikibot.Site('commons', 'commons')
category = pywikibot.Category(site, 'Category:YOUR_UPLOADS_CATEGORY')

# Similarity threshold (lower value = more sensitive)
# Values between 0-64, where 0 is identical and 64 is completely different
HASH_THRESHOLD = 8  

# Temp directory for downloaded images
TEMP_DIR = tempfile.mkdtemp()

def download_image(image_url, filename):
    """Download the image and save to temp location."""
    headers = {
        'User-Agent': 'YOUR_USERNAME/1.0 (https://meta.wikimedia.org/wiki/User-Agent_policy)'
    }
    try:
        response = requests.get(image_url, headers=headers, stream=True)
        if response.status_code == 200:
            file_path = os.path.join(TEMP_DIR, filename)
            with open(file_path, 'wb') as f:
                f.write(response.content)
            return file_path
        else:
            print(f"Error downloading image: Status Code {response.status_code}")
            return None
    except Exception as e:
        print(f"Error downloading image: {str(e)}")
        return None

def compute_image_hash(image_path):
    """Compute perceptual hash for the image."""
    try:
        img = Image.open(image_path)
        # Converting to grayscale for more stable hashing
        if img.mode != 'L':  # L means grayscale
            img = img.convert('L')
        # Using a combination of hash types for better accuracy
        phash = imagehash.phash(img)
        return phash
    except Exception as e:
        print(f"Error computing hash: {str(e)}")
        return None

def find_similar_images(files):
    """Find similar images using perceptual hashing."""
    print("Computing image hashes...")
    
    # Dictionary to store file info: {filename: [filepath, hash]}
    file_info = {}
    
    # Compute hashes for all images
    for i, file_page in enumerate(files):
        if not file_page.exists() or file_page.namespace() != 6:
            continue
        
        file_title = file_page.title()
        file_name = file_title.split(':', 1)[1]  # Remove 'File:' prefix
        
        print(f"Processing {i+1}/{len(files)}: {file_title}")
        
        # Download the image
        image_url = file_page.get_file_url()
        file_path = download_image(image_url, file_name)
        
        if file_path:
            # Compute hash
            img_hash = compute_image_hash(file_path)
            if img_hash:
                file_info[file_title] = [file_path, img_hash]
    
    # Find similar images
    print("\nSearching for similar images...")
    similar_pairs = []
    
    # Compare all combinations of images
    processed = set()
    for title1, (path1, hash1) in file_info.items():
        for title2, (path2, hash2) in file_info.items():
            if title1 != title2 and (title2, title1) not in processed:
                processed.add((title1, title2))
                
                # Calculate hash difference (0 = identical, high value = very different)
                hash_diff = hash1 - hash2
                
                if hash_diff <= HASH_THRESHOLD:
                    similar_pairs.append((title1, title2, hash_diff))
    
    # Sort by similarity (most similar first)
    similar_pairs.sort(key=lambda x: x[2])
    
    return similar_pairs, file_info

def create_report(similar_pairs, file_info):
    """Create a report of similar images."""
    total_files = len(file_info)
    
    report = f"""= Duplicate Image Detection Report =

== Summary ==
* Total files analyzed: {total_files}
* Similar image pairs found: {len(similar_pairs)}
* Similarity threshold: {HASH_THRESHOLD} (lower = more similar)

== Similar Image Pairs ==
The following pairs of images are visually similar and should be reviewed:

"""
    
    if not similar_pairs:
        report += "No similar image pairs were found."
    else:
        for i, (title1, title2, diff) in enumerate(similar_pairs):
            report += f"=== Pair {i+1} (Difference: {diff}) ===\n"
            report += f"* [[:{title1}]]\n"
            report += f"* [[:{title2}]]\n\n"
    
    report += f"\nReport generated by pwb_duplicate_finder.py on ~~~~~"
    
    return report

def main():
    try:
        print("Starting duplicate image finder...")
        
        # Get all files from the category
        print(f"Retrieving files from {category.title()}...")
        files = list(pagegenerators.CategorizedPageGenerator(category, recurse=True))
        print(f"Found {len(files)} files to process")
        
        # Find similar images
        similar_pairs, file_info = find_similar_images(files)
        
        # Create report
        report = create_report(similar_pairs, file_info)
        
        # Save report to user page
        try:
            user_page = pywikibot.Page(site, 'User:YOUR_USERNAME/pwb/Duplicate_Report')
            user_page.text = report
            user_page.save(summary="pwb: Updated duplicate image detection report")
            print(f"Report saved to {user_page.title()}")
        except Exception as e:
            print(f"Error saving report: {e}")
            print("Report content:")
            print(report)
    
    finally:
        # Clean up temporary files
        print("Cleaning up temporary files...")
        shutil.rmtree(TEMP_DIR, ignore_errors=True)
        print("Done!")

if __name__ == "__main__":
    main()
