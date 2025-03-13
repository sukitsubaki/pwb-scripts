import pywikibot
from pywikibot import pagegenerators
import requests
from PIL import Image
from io import BytesIO
from PIL.ExifTags import TAGS

# List of typical shutter speeds and their fractions
KNOWN_SHUTTER_SPEEDS = {
    1/32000: "1/32000", 1/16000: "1/16000", 1/12800: "1/12800", 1/10000: "1/10000", 1/8000: "1/8000",
    1/6400: "1/6400", 1/5000: "1/5000", 1/4000: "1/4000", 1/3200: "1/3200", 1/2500: "1/2500", 
    1/2000: "1/2000", 1/1600: "1/1600", 1/1250: "1/1250", 1/1000: "1/1000", 1/800: "1/800", 
    1/640: "1/640", 1/500: "1/500", 1/400: "1/400", 1/320: "1/320", 1/250: "1/250", 
    1/200: "1/200", 1/160: "1/160", 1/125: "1/125", 1/100: "1/100", 1/80: "1/80", 1/60: "1/60", 
    1/50: "1/50", 1/40: "1/40", 1/30: "1/30", 1/25: "1/25", 1/20: "1/20", 1/15: "1/15", 
    1/13: "1/13", 1/10: "1/10", 1/8: "1/8", 1/6: "1/6", 1/5: "1/5", 1/4: "1/4", 1/3: "1/3", 
    2/5: "2/5", 1/2: "1/2", 3/5: "3/5", 4/5: "4/5", 1: "1", 13/10: "1.3", 16/10: "1.6", 
    25/10: "2.5", 32/10: "3.2", 2: "2", 4: "4", 8: "8", 15: "15", 30: "30"
}

def format_exposure_time(exposure_time):
    """Convert exposure time to known photographic times."""
    for known_time, label in KNOWN_SHUTTER_SPEEDS.items():
        if abs(exposure_time - known_time) < 0.0000005:  # Tolerance for floating-point deviations
            return label
    if exposure_time > 4:
        return f"{int(exposure_time)}"
    else:
        return f"{exposure_time:.1f}"

def get_exif_data(image_url):
    """Read Exif data from an image URL."""
    headers = {
        'User-Agent': 'YOUR_USERNAME/1.0 (https://meta.wikimedia.org/wiki/User-Agent_policy)' 
    }
    try:
        response = requests.get(image_url, headers=headers)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content))
        exif_data = img._getexif() or {}
        data = {}
        for tag, value in exif_data.items():
            tag_name = TAGS.get(tag, tag)
            if tag_name in ['FocalLength', 'ExposureTime', 'ISOSpeedRatings', 'FNumber']:
                data[tag_name] = value
        return data
    except Exception as e:
        pywikibot.error(f"Error reading EXIF data from {image_url}: {e}")
        return {}

# List of known aperture values (F-numbers)
KNOWN_F_NUMBERS = [
    1.2, 1.4, 1.6, 1.8, 2, 2.2, 2.5, 2.8, 3.2, 3.5, 4, 4.5, 5.0, 5.6, 6.3, 
    7.1, 8, 9, 10, 11, 13, 14, 16, 18, 20, 22, 25, 29, 32
]

def find_closest_f_number(f_number):
    """Find the closest known F-number."""
    return min(KNOWN_F_NUMBERS, key=lambda x: abs(x - f_number))

def format_exif_value(tag, value):
    """Format EXIF values for categories."""
    if tag == 'FocalLength':
        if isinstance(value, tuple):
            focal_length = value[0] / value[1]
            return f"{int(focal_length)}"
        else:
            return str(int(value))
    elif tag == 'FNumber':
        if isinstance(value, tuple):
            f_number = value[0] / value[1]  # Convert fraction to decimal
        else:
            f_number = value
        
        # Find the closest known F-number
        closest_f_number = find_closest_f_number(f_number)

        # Check if the resulting number is an integer
        if closest_f_number.is_integer():
            return f"{int(closest_f_number)}"
        else:
            return f"{closest_f_number:.1f}"  # Keep 1 decimal place if needed
    elif tag == 'ISOSpeedRatings':
        return str(value)
    elif tag == 'ExposureTime':
        if isinstance(value, tuple):
            exposure_time = value[0] / value[1]
        else:
            exposure_time = value
        return format_exposure_time(exposure_time)

def add_maintenance_category(file_page):
    """Add the category 'Category:YOUR_USERNAME/pwb - maintenance'."""
    maintenance_category = "[[Category:YOUR_USERNAME/pwb - maintenance]]"
    
    if maintenance_category not in file_page.text:
        file_page.text += "\n" + maintenance_category
        file_page.save("pwb: Added maintenance category for missing EXIF data")
        pywikibot.log(f"Maintenance category added: {file_page.title()}")

def create_category(site, category_title, content):
    """Create a new category if it doesn't exist yet."""
    category_page = pywikibot.Category(site, category_title)
    
    if not category_page.exists():
        category_page.text = content
        category_page.save(f"pwb: Category created")
        pywikibot.log(f"Category created: {category_title}")
    else:
        pywikibot.log(f"Category already exists: {category_title}")
        
def main():
    site = pywikibot.Site('commons', 'commons')
    category = pywikibot.Category(site, 'Category:YOUR_PHOTO_CATEGORY')

    # List of expressions that should not be in the text to add focal length categories
    excluded_expressions = [
        # Add more as needed based on your equipment
    ]

    # List of terms to skip file processing
    skip_expressions = [""] # Add more as needed based on your equipment

    for file_page in pagegenerators.CategorizedPageGenerator(category):
        if file_page.isRedirectPage():
            file_page = file_page.getRedirectTarget()

        # Check if the file should be skipped
        if any(expr in file_page.text for expr in skip_expressions):
            pywikibot.log(f"Skipped: {file_page.title()} due to: {', '.join([expr for expr in skip_expressions if expr in file_page.text])}")
            continue

        image_url = file_page.get_file_url()

        exif_data = get_exif_data(image_url)

        if exif_data:
            categories_to_add = []

            for tag in ['FocalLength', 'FNumber', 'ISOSpeedRatings', 'ExposureTime']:
                if tag in exif_data:
                    formatted_value = format_exif_value(tag, exif_data[tag])
                    
                    if tag == 'FocalLength':
                        if not any(expr in file_page.text for expr in excluded_expressions):
                            categories_to_add.append(f"[[Category:Lens focal length {formatted_value} mm]]")
                            
                    elif tag == 'FNumber':
                        # Categories for aperture
                        categories_to_add.append(f"[[Category:F-number f/{formatted_value}]]")
                        
                    elif tag == 'ISOSpeedRatings':
                        # Categories for ISO values
                        categories_to_add.append(f"[[Category:ISO speed rating {formatted_value}]]")
    
                    elif tag == 'ExposureTime':
                        # Categories for exposure times
                        categories_to_add.append(f"[[Category:Exposure time {formatted_value} sec]]")
        
                        # Determine numeric exposure time for categorization
                        if isinstance(exif_data[tag], tuple):
                            numerical_exposure_time = exif_data[tag][0] / exif_data[tag][1]
                        else:
                            numerical_exposure_time = exif_data[tag]
    
            # Search the file's wikitext to check if categories are already present
            current_text = file_page.text
            new_categories = [cat for cat in categories_to_add if cat not in current_text]
    
            if new_categories:
                # Add new categories that are not yet in the wikitext
                file_page.text += "\n" + "\n".join(new_categories)
                file_page.save("pwb: Added EXIF-based categories")
                pywikibot.log(f"Added: {new_categories} to {file_page.title()}")
        else:
            # If no EXIF data found, add the maintenance category
            add_maintenance_category(file_page)

if __name__ == "__main__":
    main()
