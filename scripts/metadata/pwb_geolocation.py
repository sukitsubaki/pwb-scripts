import pywikibot
from pywikibot import pagegenerators
import requests
from PIL import Image
from io import BytesIO
from PIL.ExifTags import TAGS, GPSTAGS
import re

def get_gps_data(exif_data):
    """Read GPS data from EXIF data."""
    # First check for GPSInfo
    if 'GPSInfo' in exif_data:
        gps_info = exif_data['GPSInfo']
        if gps_info and isinstance(gps_info, dict):  # Check if gps_info is a dictionary
            try:
                latitude = gps_info[GPSTAGS['GPSLatitude']]
                latitude_ref = gps_info[GPSTAGS['GPSLatitudeRef']]
                longitude = gps_info[GPSTAGS['GPSLongitude']]
                longitude_ref = gps_info[GPSTAGS['GPSLongitudeRef']]
                
                if latitude and longitude:
                    lat = convert_to_degrees(latitude)
                    lon = convert_to_degrees(longitude)

                    # Adjust for N/S and E/W
                    if latitude_ref == 'S':
                        lat = -lat
                    if longitude_ref == 'W':
                        lon = -lon
                    
                    print(f"GPS coordinates found (GPSInfo): lat={lat}, lon={lon}")
                    return lat, lon
                else:
                    print("GPS coordinates missing in GPSInfo.")
            except KeyError as e:
                print(f"Error accessing GPSInfo: Key {e} missing.")
    
    # If no GPSInfo, check tag 34853
    if 34853 in exif_data:
        gps_info = exif_data[34853]
        
        # Check structure of gps_info
        if len(gps_info) >= 6:
            try:
                latitude = gps_info[2]  # (51.0, 10.5864667, 0.0)
                latitude_ref = gps_info[1]  # 'N'
                longitude = gps_info[4]  # (6.0, 40.5995333, 0.0)
                longitude_ref = gps_info[3]  # 'E'
                
                if latitude and longitude:
                    lat = convert_to_degrees(latitude)
                    lon = convert_to_degrees(longitude)

                    # Adjust for N/S and E/W
                    if latitude_ref == 'S':
                        lat = -lat
                    if longitude_ref == 'W':
                        lon = -lon
                    
                    print(f"GPS coordinates found (Tag 34853): lat={lat}, lon={lon}")
                    return lat, lon
            except IndexError as e:
                print(f"Error accessing Tag 34853: Index {e} missing.")
        else:
            print("GPS data in Tag 34853 incomplete.")
    
    print("No GPSInfo or Tag 34853 found in EXIF data.")
    # Debugging: Output all EXIF data
    print(f"Complete EXIF data: {exif_data}")
    
    return None

def convert_to_degrees(value):
    """Convert GPS coordinates to decimal degrees."""
    degrees = float(value[0])
    minutes = float(value[1]) / 60.0
    seconds = float(value[2]) / 3600.0
    return degrees + minutes + seconds

def format_location_template(lat, lon):
    """Format the Location template with the given coordinates."""
    lat_deg = int(lat)
    lat_min = int(abs(lat * 60) % 60)
    lat_sec = (abs(lat * 3600) % 60)
    lat_ref = 'N' if lat >= 0 else 'S'
    
    lon_deg = int(abs(lon))
    lon_min = int(abs(lon * 60) % 60)
    lon_sec = (abs(lon * 3600) % 60)
    lon_ref = 'E' if lon >= 0 else 'W'
    
    return f"{{{{Location|{lat_deg}|{lat_min}|{lat_sec:.1f}|{lat_ref}|{lon_deg}|{lon_min}|{lon_sec:.1f}|{lon_ref}}}}}"

def add_location_template(file_page, lat, lon):
    """Add the Location template to the file, replace existing templates."""
    location_template = format_location_template(lat, lon)
    summary = f"pwb: Added location information"
    
    print(f"Adding the following location template: {location_template}")
    
    # Remove old location template
    old_template_pattern = re.compile(r'{{Location\|XXX\|XXX\|XXX\|[NS]\|XXX\|XXX\|XXX\|[EW]}}')
    if old_template_pattern.search(file_page.text):
        file_page.text = old_template_pattern.sub('', file_page.text)
        print("Old location template removed.")

    # Add the new location template
    if "</table>" in file_page.text:
        file_page.text = file_page.text.replace("</table>", f"</table>\n{location_template}")
    else:
        file_page.text += f"\n{location_template}"
    
    file_page.save(summary)
    pywikibot.log(f"Location template added: {file_page.title()}")
    print(f"Template for {file_page.title()} successfully added and saved.")

def get_exif_data(image_url):
    """Read EXIF data from an image URL."""
    headers = {
        'User-Agent': 'YOUR_USERNAME/1.0 (https://meta.wikimedia.org/wiki/User-Agent_policy)' 
    }
    try:
        response = requests.get(image_url, headers=headers)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content))
        exif_data = img._getexif() or {}
        if exif_data:
            print(f"EXIF data found for image: {image_url}")
        else:
            print(f"No EXIF data for image: {image_url}")
        return exif_data
    except Exception as e:
        pywikibot.error(f"Error reading EXIF data from {image_url}: {e}")
        print(f"Error retrieving EXIF data from {image_url}: {e}")
        return {}

def main():
    print("Starting main script.")
    site = pywikibot.Site('commons', 'commons')
    category = pywikibot.Category(site, 'Category:YOUR_UPLOADS_CATEGORY')

    # List for files without valid location information
    missing_location_files = []

    # Regular expression to find an incomplete Location template with "XXX" placeholders
    location_pattern = re.compile(r'Location\|XXX\|XXX\|XXX\|[NS]\|XXX\|XXX\|XXX\|[EW]')
    
    # Detect "Location withheld" template
    location_withheld_pattern = re.compile(r'{{Location withheld}}', re.IGNORECASE)

    # Generator for files in the category
    for file_page in pagegenerators.CategorizedPageGenerator(category, recurse=True):
        print(f"Processing file: {file_page.title()}")
        if file_page.isRedirectPage():
            file_page = file_page.getRedirectTarget()

        text = file_page.text

        # Skip files with the "Location withheld" template
        if location_withheld_pattern.search(text):
            print(f"File {file_page.title()} skipped because 'Location withheld' template is present.")
            continue

        # Check for the presence of a valid Location template
        has_location_template = "{{Location|" in text
        has_invalid_location_template = location_pattern.search(text)

        # If no valid Location template is present
        if not has_location_template or has_invalid_location_template:
            print(f"File {file_page.title()} has no or an incomplete Location template.")
            # Retrieve metadata
            image_url = file_page.get_file_url()
            exif_data = get_exif_data(image_url)

            if exif_data:
                gps_data = get_gps_data(exif_data)
                if gps_data:
                    lat, lon = gps_data
                    # Add the location template or replace the invalid template
                    add_location_template(file_page, lat, lon)
                else:
                    pywikibot.log(f"No GPS data found for {file_page.title()}")
                    print(f"No GPS data found for {file_page.title()}.")
                    missing_location_files.append(file_page.title())
            else:
                pywikibot.log(f"No EXIF data found for {file_page.title()}")
                print(f"No EXIF data found for {file_page.title()}.")
                missing_location_files.append(file_page.title())
        else:
            print(f"File {file_page.title()} already has a valid location template.")

if __name__ == "__main__":
    main()
