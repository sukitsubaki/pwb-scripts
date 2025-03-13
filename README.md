# pwb-scripts

A lightweight and minimalist collection of Pywikibot scripts for automating tasks on Wikimedia Commons. This toolkit helps with categorization, file management, metadata extraction, and various maintenance tasks.

## Overview

pwb-scripts is designed for Wikimedia Commons contributors who want to streamline their workflows. Whether you're managing thousands of files, maintaining complex category hierarchies, or ensuring your uploads meet quality standards, these scripts can help.

### Key Features

- **Category Management**: Rename, move, and repair category structures
- **File Processing**: Upload, rename, and modify files in batch
- **Metadata Extraction**: Utilize EXIF data for better categorization
- **Quality Control**: Find duplicates, validate licenses, check image quality
- **Statistics**: Generate insights about your contributions

## Installation

1. **Prerequisites**:
   - Python 3.6 or newer
   - Pywikibot installed and configured

2. **Clone this repository**:
   ```bash
   git clone https://github.com/sukitsubaki/pwb-scripts.git
   cd pwb-scripts
   ```

3. **Install dependencies**:
   ```bash
   pip install pillow requests matplotlib numpy opencv-python imagehash
   ```

4. **Configure scripts**:
   Edit the scripts you plan to use and update the configuration variables:
   - Replace `YOUR_USERNAME` with your Commons username
   - Update `YOUR_UPLOADS_CATEGORY` with your main uploads category
   - Customize other settings specific to your workflow

## Getting Started

Most scripts can be run directly from the command line:

```bash
python scripts/category/pwb_category_rename.py
python scripts/file/pwb_filename_check.py
python scripts/metadata/pwb_exif_categorize.py
```

Many scripts support an interactive mode:

```bash
python scripts/analysis/pwb_duplicate_finder.py --interactive
python scripts/category/pwb_category_suggest.py --interactive
```

## Scripts Collection

### Category Management
- **pwb_category_rename.py** - Bulk rename categories and update all references
- **pwb_category_suggest.py** - Suggest additional categories based on similar files
- **pwb_move_category.py** - Move categories while maintaining proper redirects
- **pwb_orphaned_categories.py** - Fix orphaned categories with appropriate redirects
- **pwb_repair_categories.py** - Find and fix various category hierarchy issues

### File Processing
- **pwb_batch_rename.py** - Batch rename files according to patterns
- **pwb_batch_downloader.py** - Download files from Commons based on categories or search
- **pwb_filename_check.py** - Validate filenames against standards
- **pwb_text_replace.py** - Find and replace text within file descriptions
- **pwb_upload.py** - Batch upload files with standardized descriptions

### Metadata Extraction
- **pwb_aspect_ratio.py** - Categorize files by aspect ratio
- **pwb_auto_description.py** - Generate improved file descriptions using EXIF data
- **pwb_exif_categorize.py** - Add appropriate categories based on EXIF data
- **pwb_gear_check.py** - Check for missing camera/lens information
- **pwb_geolocation.py** - Extract and add location data from GPS coordinates

### Analysis
- **pwb_duplicate_finder.py** - Find similar or duplicate images using perceptual hashing
- **pwb_license_validator.py** - Verify proper licensing information on files
- **pwb_quality_check.py** - Analyze image quality (resolution, noise, sharpness)
- **pwb_statistics.py** - Generate statistics about your uploads
- **pwb_usage_tracker.py** - Track where your files are being used across Wikimedia projects

## Workflow Examples

### Complete Upload Workflow

1. **Upload files**:
   ```bash
   python scripts/file/pwb_upload.py
   ```

2. **Extract EXIF data and add categories**:
   ```bash
   python scripts/metadata/pwb_exif_categorize.py --category "YOUR_USERNAME/pwb - new uploads"
   ```

3. **Add aspect ratio categories**:
   ```bash
   python scripts/metadata/pwb_aspect_ratio.py
   ```

4. **Add location data**:
   ```bash
   python scripts/metadata/pwb_geolocation.py
   ```

5. **Improve descriptions**:
   ```bash
   python scripts/metadata/pwb_auto_description.py --category "YOUR_USERNAME/pwb - new uploads"
   ```

6. **Check for duplicate images**:
   ```bash
   python scripts/analysis/pwb_duplicate_finder.py
   ```

### Maintenance Workflow

1. **Validate licenses**:
   ```bash
   python scripts/analysis/pwb_license_validator.py
   ```

2. **Find and fix category issues**:
   ```bash
   python scripts/category/pwb_repair_categories.py --interactive
   ```

3. **Generate usage statistics**:
   ```bash
   python scripts/analysis/pwb_statistics.py
   ```

4. **Check image quality**:
   ```bash
   python scripts/analysis/pwb_quality_check.py
   ```

## Documentation

For detailed information on using these scripts:

- Check the [Installation Guide](docs/installation.md) for setup instructions
- Read the [Configuration Guide](docs/configuration.md) for customization options
- See [Advanced Usage](docs/advanced_usage.md) for power-user techniques
- Browse the [examples](examples/) directory for practical workflows

## Tips for Success

- **Start small**: Test scripts on a small batch of files before running on your entire collection
- **Use interactive mode**: When available, interactive mode provides more control and feedback
- **Back up your data**: Always have a backup before making batch changes
- **Check report pages**: Most scripts generate detailed reports on your user pages
- **Customize scripts**: Modify the code to better fit your specific workflow needs

## Contributing

Contributions are welcome! Whether it's adding new scripts, improving existing ones, or fixing bugs, please feel free to contribute to this project.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
