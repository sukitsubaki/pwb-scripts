import os
import tempfile
import requests
from PIL import Image
import pywikibot
from pywikibot import pagegenerators
from io import BytesIO

def download_image(image_url):
    """Download the image and return the local file path."""
    headers = {
        'User-Agent': 'YourUsername/1.0 (https://meta.wikimedia.org/wiki/User-Agent_policy)'
    }
    response = requests.get(image_url, headers=headers, stream=True)
    if response.status_code == 200:
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
        with open(temp_file.name, 'wb') as f:
            f.write(response.content)
        return temp_file.name
    else:
        raise Exception(f"Error downloading image: Status Code {response.status_code}")

def get_image_dimensions(image_path):
    """Get the dimensions of the image using PIL."""
    with Image.open(image_path) as img:
        return img.size  # (width, height)

def find_closest_aspect_ratio(aspect_ratio, tolerance=0.05):
    """Find the closest aspect ratio within a given tolerance."""
    predefined_aspect_ratios = {
        2.0: "2:1",
        0.5: "1:2",
        1.0: "1:1",
        1.5: "3:2",
        0.67: "2:3",
        1.33: "4:3",
        0.75: "3:4",
        1.25: "5:4",
        0.8: "4:5",
        1.4: "7:5",
        0.71: "5:7",
        1.78: "16:9",
        0.56: "9:16",
        2.33: "21:9",
        0.43: "9:21"
    }
    
    closest_ratio = None
    smallest_difference = float('inf')
    
    for ratio, label in predefined_aspect_ratios.items():
        difference = abs(aspect_ratio - ratio)
        if difference < smallest_difference and difference <= tolerance:
            smallest_difference = difference
            closest_ratio = ratio
    
    return closest_ratio

def main():
    site = pywikibot.Site('commons', 'commons')
    category = pywikibot.Category(site, 'Category:YOUR_PHOTO_CATEGORY')

    # Mapping of aspect ratios to their categories
    aspect_ratio_categories = {
        2.0: [
            "[[Category:Photographs with aspect ratio of 2:1]]"
        ],
        0.5: [
            "[[Category:Photographs with aspect ratio of 1:2]]"
        ],
        1.0: [
            "[[Category:Photographs with aspect ratio of 1:1]]"
        ],
        1.5: [
            "[[Category:Photographs with aspect ratio of 3:2]]"
        ],
        0.67: [
            "[[Category:Photographs with aspect ratio of 2:3]]"
        ],
        1.33: [
            "[[Category:Photographs with aspect ratio of 4:3]]"
        ],
        0.75: [
            "[[Category:Photographs with aspect ratio of 3:4]]"
        ],
        1.25: [
            "[[Category:Photographs with aspect ratio of 5:4]]"
        ],
        0.8: [
            "[[Category:Photographs with aspect ratio of 4:5]]"
        ],
        1.4: [
            "[[Category:Photographs with aspect ratio of 7:5]]"
        ],
        0.71: [
            "[[Category:Photographs with aspect ratio of 5:7]]"
        ],
        1.78: [
            "[[Category:Photographs with aspect ratio of 16:9]]"
        ],
        0.56: [
            "[[Category:Photographs with aspect ratio of 9:16]]"
        ],
        2.33: [
            "[[Category:Photographs with aspect ratio of 21:9]]"
        ],
        0.43: [
            "[[Category:Photographs with aspect ratio of 9:21]]"
        ]
    }

    # Category for unknown aspect ratios
    unknown_aspect_ratio_category = "[[Category:YOUR_USERNAME/pwb - maintenance]]"

    # Mapping for text form of aspect ratios
    aspect_ratio_labels = {
        2.0: "2:1",
        0.5: "1:2",
        1.0: "1:1",
        1.5: "3:2",
        0.67: "2:3",
        1.33: "4:3",
        0.75: "3:4",
        1.25: "5:4",
        0.8: "4:5",
        1.4: "7:5",
        0.71: "5:7",
        1.78: "16:9",
        0.56: "9:16",
        2.33: "21:9",
        0.43: "9:21"
    }

    for file_page in pagegenerators.CategorizedPageGenerator(category):
        if file_page.isRedirectPage():
            file_page = file_page.getRedirectTarget()

        ts = file_page.latest_revision.timestamp

        try:
            if not file_page.exists():
                raise ValueError(f"File {file_page.title()} does not exist.")

            file_info = file_page.get_file_info(ts)
            if not file_info:
                raise ValueError(f"No image information for {file_page.title()}.")

            width = file_info.get('width', 0)
            height = file_info.get('height', 0)

            if width <= 0 or height <= 0:
                raise ValueError(f"Invalid dimensions for {file_page.title()}: Width {width}, Height {height}")

            aspect_ratio = width / height
            closest_ratio = find_closest_aspect_ratio(aspect_ratio)

            if closest_ratio is None:
                categories_to_add = [unknown_aspect_ratio_category]
                aspect_ratio_str = "unknown"
            else:
                categories_to_add = aspect_ratio_categories.get(closest_ratio, [unknown_aspect_ratio_category])
                aspect_ratio_str = aspect_ratio_labels.get(closest_ratio, "unknown")

            current_text = file_page.text
            new_categories = [cat for cat in categories_to_add if cat not in current_text]

            if closest_ratio and unknown_aspect_ratio_category in current_text:
                current_text = current_text.replace(unknown_aspect_ratio_category, "")

            if new_categories:
                file_page.text = current_text + "\n" + "\n".join(new_categories)
                summary = f"pwb: Added aspect ratio – {aspect_ratio_str}"
                file_page.save(summary)
                pywikibot.log(f"Added: {new_categories} to {file_page.title()}")

        except (pywikibot.exceptions.PageRelatedError, ValueError) as e:
            pywikibot.error(f"Error for {file_page.title()}: {e}. Trying to download the image locally and check the resolution.")

            image_url = file_page.get_file_url()
            try:
                temp_image_path = download_image(image_url)
                width, height = get_image_dimensions(temp_image_path)
                aspect_ratio = width / height
                closest_ratio = find_closest_aspect_ratio(aspect_ratio)

                if closest_ratio is None:
                    categories_to_add = [unknown_aspect_ratio_category]
                    aspect_ratio_str = "unknown"
                else:
                    categories_to_add = aspect_ratio_categories.get(closest_ratio, [unknown_aspect_ratio_category])
                    aspect_ratio_str = aspect_ratio_labels.get(closest_ratio, "unknown")

                current_text = file_page.text
                new_categories = [cat for cat in categories_to_add if cat not in current_text]

                if closest_ratio and unknown_aspect_ratio_category in current_text:
                    current_text = current_text.replace(unknown_aspect_ratio_category, "")

                if new_categories:
                    file_page.text = current_text + "\n" + "\n".join(new_categories)
                    summary = f"pwb: Added aspect ratio – {aspect_ratio_str}"
                    file_page.save(summary)
                    pywikibot.log(f"Added: {new_categories} to {file_page.title()}")

            except Exception as download_error:
                pywikibot.error(f"Error downloading the image: {download_error}")

            finally:
                if 'temp_image_path' in locals() and os.path.exists(temp_image_path):
                    os.remove(temp_image_path)

if __name__ == "__main__":
    main()
