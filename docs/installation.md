# Installation Guide

This guide will help you set up the pwb-scripts tools on your system.

## Prerequisites

Before installing pwb-scripts, you'll need:

1. **Python 3.6 or newer** - The scripts are designed to work with Python 3.6+
2. **Pywikibot** - The foundation library for interacting with Wikimedia sites
3. **Additional Python libraries** - Some scripts require additional libraries

## Step 1: Install Python

If you don't have Python installed:

- **Windows**: Download and install from [python.org](https://www.python.org/downloads/)
- **macOS**: Use [Homebrew](https://brew.sh/) with `brew install python` or download from python.org
- **Linux**: Most distributions include Python. Install with your package manager:
  ```
  # Ubuntu/Debian
  sudo apt update
  sudo apt install python3 python3-pip
  
  # Fedora
  sudo dnf install python3 python3-pip
  ```

Verify your installation by running:
```
python --version
# or 
python3 --version
```

## Step 2: Install Pywikibot

1. Clone the Pywikibot repository:
   ```
   git clone https://gerrit.wikimedia.org/r/pywikibot/core.git pywikibot
   ```

2. Navigate to the pywikibot directory:
   ```
   cd pywikibot
   ```

3. Install Pywikibot:
   ```
   pip install -e .
   ```

4. Generate a user-config.py file:
   ```
   python pwb.py generate_user_files
   ```
   Follow the prompts to set up your configuration.

## Step 3: Install Additional Libraries

Many of the pwb-scripts require additional Python libraries. Install them with pip:

```
pip install pillow requests matplotlib numpy opencv-python imagehash
```

## Step 4: Clone the pwb-scripts Repository

1. Clone this repository:
   ```
   git clone https://github.com/sukitsubaki/pwb-scripts.git
   ```

2. Navigate to the pwb-scripts directory:
   ```
   cd pwb-scripts
   ```

## Step 5: Configuration

Before using the scripts, you need to configure them for your specific needs:

1. Edit each script you plan to use and update the following variables near the top:
   - `USERNAME`: Your Wikimedia Commons username
   - Any other configuration variables specific to that script

2. Ensure your Pywikibot is properly configured with your account credentials.

## Verification

Test your installation by running a simple script:

```
python scripts/file/pwb_filename_check.py --help
```

You should see the help message for the script.

## Troubleshooting

### Common Issues

1. **ModuleNotFoundError**: If you see errors about missing modules, install them with pip:
   ```
   pip install <module_name>
   ```

2. **Authentication Issues**: Make sure your Pywikibot user-config.py file is correctly set up.

3. **Permission Denied**: Ensure you have the necessary permissions to write to directories.

### Getting Help

If you encounter any issues:

1. Check the error messages for clues
2. Consult the [Pywikibot documentation](https://www.mediawiki.org/wiki/Manual:Pywikibot)
3. Open an issue on the GitHub repository
