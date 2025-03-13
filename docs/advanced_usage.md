# Advanced Usage Guide

This guide covers advanced usage scenarios and techniques for the pwb-scripts tools.

## Command-Line Integration

### Creating Command-Line Aliases

For frequent operations, create shell aliases (add to your `.bashrc` or `.zshrc`):

```bash
# Quick category check
alias pwb-cat="python /path/to/pwb-scripts/scripts/category/pwb_repair_categories.py --analyze"

# Quick file upload
alias pwb-upload="python /path/to/pwb-scripts/scripts/file/pwb_upload.py"
```

### Combining Scripts in Shell Scripts

Create shell scripts to chain multiple operations:

```bash
#!/bin/bash
# process_batch.sh - Process a batch of new uploads

# 1. Upload files
python /path/to/pwb_upload.py --directory "$1"

# 2. Check file quality
python /path/to/pwb_quality_check.py --category ""

# 3. Add EXIF-based categories
python /path/to/pwb_exif_categorize.py --category ""

# 4. Suggest additional categories
python /path/to/pwb_category_suggest.py --category "" --interactive
```

Usage: `./process_batch.sh /path/to/images`

## Automation with Cron Jobs

Schedule regular maintenance tasks using cron jobs:

```
# Run every day at 2:00 AM
0 2 * * * python /path/to/pwb_license_validator.py --category "YOUR_USERNAME/Files" --save "User:YOUR_USERNAME/pwb/License_Report"

# Run weekly on Sunday at 3:00 AM
0 3 * * 0 python /path/to/pwb_usage_tracker.py --user "YOUR_USERNAME" --save "User:YOUR_USERNAME/pwb/Usage_Report"
```

## Working with Large Categories

When working with large categories (1000+ files), consider these techniques:

### Batch Processing

Process files in smaller batches to avoid timeouts:

```python
def process_large_category(category_name, batch_size=100):
    """Process a large category in batches."""
    category = pywikibot.Category(site, category_name)
    file_generator = pagegenerators.CategorizedPageGenerator(category, namespaces=6)
    
    batch = []
    count = 0
    
    for file_page in file_generator:
        batch.append(file_page)
        count += 1
        
        if len(batch) >= batch_size:
            process_batch(batch)
            batch = []
            print(f"Processed {count} files so far...")
    
    # Process remaining files
    if batch:
        process_batch(batch)
    
    print(f"Finished processing {count} files.")
```

### Using Continuation

For very large categories, use continuation to resume operations:

```python
def process_with_continuation(category_name, start_title=None):
    """Process a category with continuation support."""
    category = pywikibot.Category(site, category_name)
    file_generator = pagegenerators.CategorizedPageGenerator(category, namespaces=6)
    
    # Skip to the start_title if provided
    if start_title:
        for file_page in file_generator:
            if file_page.title() == start_title:
                break
    
    # Process remaining files
    for file_page in file_generator:
        try:
            process_file(file_page)
            # Save the last processed title in case of errors
            with open('continuation.txt', 'w') as f:
                f.write(file_page.title())
        except Exception as e:
            print(f"Error processing {file_page.title()}: {e}")
            print(f"Resume from: {file_page.title()}")
            break
```

## Complex Category Management

### Creating Category Hierarchies

Build organized category hierarchies programmatically:

```python
def create_category_structure(base_name, types, locations, years):
    """Create a structured category hierarchy."""
    # Create base category
    base_category = pywikibot.Category(site, f"Category:{base_name}")
    if not base_category.exists():
        base_category.text = f"Category for images by {base_name}."
        base_category.save(summary="Creating base category")
    
    # Create subcategories by type
    for type_name in types:
        type_category = pywikibot.Category(site, f"Category:{base_name}/{type_name}")
        if not type_category.exists():
            type_category.text = f"{{{{subcat|{base_name}}}}}"
            type_category.save(summary=f"Creating type subcategory: {type_name}")
    
    # Create subcategories by location
    for location in locations:
        location_category = pywikibot.Category(site, f"Category:{base_name}/Location/{location}")
        if not location_category.exists():
            location_category.text = f"{{{{subcat|{base_name}}}}}"
            location_category.save(summary=f"Creating location subcategory: {location}")
    
    # Create subcategories by year
    for year in years:
        year_category = pywikibot.Category(site, f"Category:{base_name}/{year}")
        if not year_category.exists():
            year_category.text = f"{{{{subcat|{base_name}}}}}"
            year_category.save(summary=f"Creating year subcategory: {year}")
```

## Advanced File Analysis

### Deep Image Analysis

Perform more comprehensive image analysis by extending the quality check script:

```python
def analyze_image_composition(image_path):
    """Analyze image composition using OpenCV."""
    img = cv2.imread(image_path)
    
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Analyze rule of thirds points
    h, w = gray.shape
    third_h, third_w = h // 3, w // 3
    
    # Calculate energy at rule of thirds intersections
    intersection_points = [
        (third_w, third_h),
        (third_w * 2, third_h),
        (third_w, third_h * 2),
        (third_w * 2, third_h * 2)
    ]
    
    # Calculate energy around each intersection point
    energy_at_intersections = []
    for x, y in intersection_points:
        # Create a region of interest
        roi = gray[y-20:y+20, x-20:x+20]
        # Calculate energy (variance) in this region
        energy = np.var(roi)
        energy_at_intersections.append(energy)
    
    # Higher energy at intersections often indicates better composition
    return sum(energy_at_intersections) / len(energy_at_intersections)
```

## Custom Logging and Reporting

### Setting Up Detailed Logging

Implement detailed logging for better troubleshooting:

```python
import logging

def setup_logging(script_name):
    """Set up detailed logging for a script."""
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Set up logging
    log_file = f"logs/{script_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    # Configure logging
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Add console handler
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    logging.getLogger('').addHandler(console)
    
    return logging.getLogger('')
```

### Creating Advanced HTML Reports

Generate rich HTML reports instead of plain text:

```python
def create_html_report(data, title, filename):
    """Create an HTML report from data."""
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        tr:nth-child(even) {{ background-color: #f2f2f2; }}
        th {{ background-color: #4CAF50; color: white; }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <p>Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    <table>
        <tr>
            <th>File</th>
            <th>Status</th>
            <th>Details</th>
        </tr>
"""
    
    for item in data:
        html += f"""
        <tr>
            <td>{item['file']}</td>
            <td>{item['status']}</td>
            <td>{item['details']}</td>
        </tr>
"""
    
    html += """
    </table>
</body>
</html>
"""
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html)
```

## Integration with Other Tools

### Using with Flickr2Commons

If you use Flickr2Commons for uploads, integrate with pwb-scripts:

```python
def post_process_flickr_uploads(category):
    """Post-process images uploaded from Flickr."""
    # Find recently uploaded files in category
    recently_uploaded = get_files_from_category(category, limit=100)
    
    for file_page in recently_uploaded:
        # Check if it's a Flickr upload
        if "flickr" in file_page.text.lower():
            # Add missing EXIF categories
            add_exif_categories(file_page)
            
            # Check for quality issues
            check_quality(file_page)
            
            # Suggest additional categories
            suggest_categories(file_page)
```

### Integrating with Commons Batch Upload

Use pwb-scripts to enhance [Commons Batch Upload](https://commons.wikimedia.org/wiki/Commons:Upload_tools/CommonsBatchUpload):

```python
def enhance_batch_uploads(username, days=1):
    """Enhance recently batch uploaded files."""
    # Get recent uploads by user
    recent_uploads = get_recent_uploads(username, days)
    
    for file_page in recent_uploads:
        # Check for batch upload signature
        if "commonsbatchupload" in file_page.text.lower():
            # Improve file description
            enhance_description(file_page)
            
            # Add missing categories
            add_missing_categories(file_page)
```

## Performance Optimization

### Caching Results

Implement caching to avoid repeated API calls:

```python
import os
import pickle
import time

def cached_api_call(func, cache_file, max_age_hours=24):
    """Cache API call results to avoid repeated calls."""
    # Check if cache exists and is recent
    if os.path.exists(cache_file):
        cache_time = os.path.getmtime(cache_file)
        age_hours = (time.time() - cache_time) / 3600
        
        if age_hours < max_age_hours:
            # Load from cache
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
    
    # Call the function
    result = func()
    
    # Save to cache
    with open(cache_file, 'wb') as f:
        pickle.dump(result, f)
    
    return result
```

This advanced usage guide should help you get the most out of the pwb-scripts tools. Remember to test complex operations on a small scale before applying them to your entire collection.
