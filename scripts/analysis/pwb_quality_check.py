#!/usr/bin/python
# -*- coding: utf-8 -*-

import pywikibot
from pywikibot import pagegenerators
import os
import requests
from io import BytesIO
from PIL import Image, ImageStat
import numpy as np
import tempfile
import shutil
import cv2

"""
pwb_quality_check.py - Analyzes image quality metrics

This script checks various quality attributes of images including:
- Resolution (width and height)
- Aspect ratio (very unusual ratios might indicate issues)
- Noise levels
- Sharpness/blur detection
- Potential compression artifacts

Requirements:
    pip install pillow numpy opencv-python

Usage:
    python pwb_quality_check.py
"""

# Site and category definition
site = pywikibot.Site('commons', 'commons')
category = pywikibot.Category(site, 'Category:YOUR_UPLOADS_CATEGORY')

# Quality thresholds
MIN_RESOLUTION = 800  # Minimum width or height in pixels
MIN_FILE_SIZE = 50 * 1024  # Minimum file size in bytes (50 KB)
MAX_NOISE_LEVEL = 25  # Maximum acceptable noise level
MIN_SHARPNESS = 30  # Minimum sharpness value
UNUSUAL_ASPECT_RATIOS = [0.1, 10.0]  # Very narrow or wide images

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
            file_size = len(response.content)
            return file_path, file_size
        else:
            print(f"Error downloading image: Status Code {response.status_code}")
            return None, 0
    except Exception as e:
        print(f"Error downloading image: {str(e)}")
        return None, 0

def estimate_noise(image_path):
    """Estimate the noise level in an image."""
    try:
        # Read image with OpenCV
        img = cv2.imread(image_path)
        if img is None:
            return None
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Calculate standard deviation in small blocks
        h, w = gray.shape
        block_size = min(64, min(h//4, w//4))  # Adjust block size for small images
        if block_size < 8:
            block_size = 8
        
        noise_levels = []
        for y in range(0, h-block_size, block_size):
            for x in range(0, w-block_size, block_size):
                block = gray[y:y+block_size, x:x+block_size]
                # Check if the block is relatively uniform (not edges or textures)
                if np.std(block) < 15:  # Adjust threshold as needed
                    noise = np.std(cv2.Laplacian(block, cv2.CV_64F))
                    noise_levels.append(noise)
        
        # Return average noise or None if no suitable blocks found
        if noise_levels:
            return np.mean(noise_levels)
        return None
    except Exception as e:
        print(f"Error estimating noise: {str(e)}")
        return None

def measure_sharpness(image_path):
    """Measure image sharpness using Laplacian variance."""
    try:
        # Read image with OpenCV
        img = cv2.imread(image_path)
        if img is None:
            return 0
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Compute Laplacian and variance
        lap = cv2.Laplacian(gray, cv2.CV_64F)
        lap_var = lap.var()
        
        return lap_var
    except Exception as e:
        print(f"Error measuring sharpness: {str(e)}")
        return 0

def check_compression_artifacts(image_path):
    """Check for JPEG compression artifacts."""
    try:
        # Read image with OpenCV
        img = cv2.imread(image_path)
        if img is None:
            return False
        
        # Convert to YCrCb color space
        ycrcb = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
        
        # Extract chroma channels
        _, cr, cb = cv2.split(ycrcb)
        
        # Check for blockiness in chroma channels
        cr_edges = cv2.Canny(cr, 50, 150)
        cb_edges = cv2.Canny(cb, 50, 150)
        
        # Count edges and normalize by image size
        h, w = cr.shape
        edge_density = (np.sum(cr_edges) + np.sum(cb_edges)) / (h * w * 255)
        
        # Higher edge density suggests more artifacts
        return edge_density > 0.05  # Adjust threshold as needed
    except Exception as e:
        print(f"Error checking compression artifacts: {str(e)}")
        return False

def analyze_image_quality(file_page):
    """Analyze the quality of an image and return issues."""
    issues = []
    
    try:
        file_title = file_page.title()
        file_name = file_title.split(':', 1)[1]  # Remove 'File:' prefix
        
        # Get file info
        file_info = file_page.latest_file_info
        width = file_info.width
        height = file_info.height
        
        # Download the image
        image_url = file_page.get_file_url()
        file_path, file_size = download_image(image_url, file_name)
        
        if not file_path:
            return [f"Failed to download image for analysis"]
        
        # Check resolution
        if width < MIN_RESOLUTION or height < MIN_RESOLUTION:
            issues.append(f"Low resolution ({width}×{height} pixels)")
        
        # Check file size
        if file_size < MIN_FILE_SIZE:
            issues.append(f"Small file size ({file_size/1024:.1f} KB)")
        
        # Check aspect ratio
        aspect_ratio = width / height
        if aspect_ratio < UNUSUAL_ASPECT_RATIOS[0] or aspect_ratio > UNUSUAL_ASPECT_RATIOS[1]:
            issues.append(f"Unusual aspect ratio ({aspect_ratio:.2f})")
        
        # Check noise level
        noise_level = estimate_noise(file_path)
        if noise_level and noise_level > MAX_NOISE_LEVEL:
            issues.append(f"High noise level ({noise_level:.2f})")
        
        # Check sharpness
        sharpness = measure_sharpness(file_path)
        if sharpness < MIN_SHARPNESS:
            issues.append(f"Low sharpness/blurry ({sharpness:.2f})")
        
        # Check for compression artifacts
        if check_compression_artifacts(file_path):
            issues.append("Visible compression artifacts")
        
        return issues
    
    except Exception as e:
        return [f"Error analyzing image: {str(e)}"]

def main():
    try:
        print("Starting image quality checker...")
        
        # Get all files from the category
        print(f"Retrieving files from {category.title()}...")
        files = list(pagegenerators.CategorizedPageGenerator(category, recurse=True))
        print(f"Found {len(files)} files to process")
        
        # Dictionary to store quality issues: {file_title: [issues]}
        quality_issues = {}
        
        # Process each file
        for i, file_page in enumerate(files):
            if not file_page.exists() or file_page.namespace() != 6:
                continue
            
            file_title = file_page.title()
            print(f"Processing {i+1}/{len(files)}: {file_title}")
            
            # Analyze image quality
            issues = analyze_image_quality(file_page)
            
            if issues:
                quality_issues[file_title] = issues
                print(f"Issues found: {', '.join(issues)}")
            else:
                print("No quality issues detected")
        
        # Create report
        report = f"""= Image Quality Report =

== Summary ==
* Total files analyzed: {len(files)}
* Files with quality issues: {len(quality_issues)}

== Files with Quality Issues ==
The following files have potential quality issues:

"""
        
        if quality_issues:
            for title, issues in quality_issues.items():
                report += f"=== {title} ===\n"
                for issue in issues:
                    report += f"* {issue}\n"
                report += "\n"
        else:
            report += "No files with quality issues were found. Great job!"
        
        report += f"\nReport generated by pwb_quality_check.py on ~~~~~"
        
        # Save report to user page
        try:
            user_page = pywikibot.Page(site, 'User:YOUR_USERNAME/pwb/Quality_Report')
            user_page.text = report
            user_page.save(summary="pwb: Updated image quality report")
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
