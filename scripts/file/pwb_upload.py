import pywikibot
from pywikibot import pagegenerators
import os

# Terminal query for the path
DIRECTORY = input("Please enter the path to the directory with JPG files: ").strip()

# Check directory
if os.path.exists(DIRECTORY):
    print(f"The directory {DIRECTORY} exists and will be used.")
else:
    print(f"The directory {DIRECTORY} was not found.")
    exit(1)  # Exit the script if the directory is not found

# Default file description (you can customize this)
FILE_DESCRIPTION = """"""

# Default summary for the upload
UPLOAD_SUMMARY = "pwb: File uploaded"

def main():
    site = pywikibot.Site('commons', 'commons')  # Wikimedia Commons site
    site.login()  # Make sure you're logged in

    # Process all files in the directory
    for file_name in os.listdir(DIRECTORY):
        if file_name.lower().endswith(".jpg"):  # Only select JPG files
            file_path = os.path.join(DIRECTORY, file_name)  # Path to file

            # Check if the file exists
            if not os.path.exists(file_path):
                pywikibot.error(f"File not found: {file_path}")
                continue

            # Set the file title on Commons
            commons_file_title = f"File:{file_name}"  # Filename with "File:" prefix

            # Upload file
            try:
                # Create a FilePage for the file
                file_page = pywikibot.FilePage(site, commons_file_title)

                if file_page.exists():
                    pywikibot.log(f"File already exists: {commons_file_title}")
                else:
                    # Upload file
                    pywikibot.log(f"Uploading file: {file_path}")
                    site.upload(
                        filepage=file_page,  # The FilePage representing the file
                        source_filename=file_path,  # Path to local file
                        comment=UPLOAD_SUMMARY,  # Summary line for the upload
                        text=FILE_DESCRIPTION,  # Description of the file
                        ignore_warnings=True  # Ignore warnings, e.g., if file already exists
                    )
                    pywikibot.log(f"Successfully uploaded: {commons_file_title}")
            except Exception as e:
                pywikibot.error(f"Error uploading file {file_name}: {str(e)}")

if __name__ == "__main__":
    main()
