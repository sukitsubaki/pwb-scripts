# Configuration Guide

This document explains how to configure the pwb-scripts tools for your specific needs.

## Global Configuration

Most scripts share common configuration settings that you'll need to adjust before using them:

### User-Specific Settings

In most scripts, you'll need to update the following variables near the top:

```python
# Change these settings
USERNAME = "YOUR_USERNAME"  # Your Wikimedia Commons username
```

### Category Settings

Many scripts work with categories. You'll need to specify the categories relevant to your uploads:

```python
# Category settings
category = pywikibot.Category(site, 'Category:YOUR_UPLOADS_CATEGORY')
```

Replace `YOUR_UPLOADS_CATEGORY` with the main category containing your uploads.

## Script-Specific Configuration

### Category Management Scripts

#### pwb_category_rename.py

Edit the `replacements` dictionary to define your category renaming scheme:

```python
replacements = {
    'Old text': 'New text'
    # Add more replacements as needed
}
```

#### pwb_repair_categories.py

The script works with default settings, but you may want to customize the analysis depth:

```python
# Adjust the maximum depth for category hierarchy analysis
MAX_DEPTH = 3  # Default value
```

### File Processing Scripts

#### pwb_batch_rename.py

Configure file naming patterns if using batch mode:

```python
# Adjust these patterns for your naming convention
OLD_PATTERN = r"^(.+)$"
NEW_PATTERN = f"PREFIX_\\1"  # Adds a prefix to all filenames
```

#### pwb_upload.py

Customize the file description template:

```python
FILE_DESCRIPTION = """== {{int:filedesc}} ==
{{Information
|Description=
|Source=
|Date=
|Author=
|Permission=
|Other_versions=
}}

== {{int:license-header}} ==

[[Category:YOUR_CATEGORY_STRUCTURE]]
"""
```

### Metadata Scripts

#### pwb_exif_categorize.py

Customize EXIF data processing:

```python
# Excluded expressions (gear-related templates that should be ignored)
excluded_expressions = []

# Terms that should cause a file to be skipped
skip_expressions = []
```

#### pwb_auto_description.py

Configure your default templates:

```python
# Your configuration
DEFAULT_SOURCE = "{{own}}"
DEFAULT_AUTHOR = f"{{{{Creator:{USERNAME}}}}}"
DEFAULT_PERMISSION = "{{self|cc-by-sa-4.0}}"
DEFAULT_LICENSE = "{{cc-by-sa-4.0}}"
```

### Analysis Scripts

#### pwb_quality_check.py

Adjust quality thresholds:

```python
# Quality thresholds
MIN_RESOLUTION = 800  # Minimum width or height in pixels
MIN_FILE_SIZE = 50 * 1024  # Minimum file size in bytes (50 KB)
MAX_NOISE_LEVEL = 25  # Maximum acceptable noise level
MIN_SHARPNESS = 30  # Minimum sharpness value
```

#### pwb_duplicate_finder.py

Configure similarity threshold:

```python
# Similarity threshold (lower value = more sensitive)
# Values between 0-64, where 0 is identical and 64 is completely different
HASH_THRESHOLD = 8  # Adjust based on your needs
```

## Advanced Configuration

### User-Agent

When making HTTP requests to Wikimedia servers, it's important to provide a proper User-Agent:

```python
headers = {
    'User-Agent': f'{USERNAME}/1.0 (https://meta.wikimedia.org/wiki/User-Agent_policy)'
}
```

### Rate Limiting

To avoid overloading the Wikimedia servers, most scripts include rate limiting. You can adjust this:

```python
# Adjust sleep time between requests (in seconds)
if i < len(files) - 1:
    time.sleep(1)  # Increase this value if you're getting rate limited
```

### Concurrent Processing

Some scripts use concurrent processing for efficiency. Adjust the number of threads:

```python
# Number of concurrent threads
DEFAULT_THREADS = 4  # Increase for faster processing, but may hit rate limits
```

## User Pages Configuration

Many scripts create or update user pages with reports. Configure these page titles:

```python
# Page where reports will be saved
user_page = pywikibot.Page(site, 'User:YOUR_USERNAME/pwb/Report_Name')
```

Replace `YOUR_USERNAME` and `Report_Name` as appropriate.

## Testing Your Configuration

After making configuration changes, it's recommended to test each script with `--help` or in interactive mode before running it on your actual files:

```
python script_name.py --interactive
```

This allows you to verify that your configuration is correct before making any changes to your files on Wikimedia Commons.
