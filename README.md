# Beatport Auto Downloader

An automated tool for downloading tracks from your Beatport library. This tool uses dynamic selector management to stay resilient against Beatport website updates.

## Features

- Automated track downloading from Beatport library
- Support for both regular library and downloads page
- Dynamic selector management that adapts to website changes
- Works with both large and small screen layouts
- Detailed logging and error handling
- Selector testing utility to verify functionality

## Prerequisites

- Python 3.8 or higher
- Google Chrome browser
- A Beatport account with purchased tracks

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/beatport-auto.git
cd beatport-auto
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Running the Downloader

1. Start the downloader:
```bash
python main.py
```

2. The script will:
   - Open Chrome browser
   - Ask you to log in to Beatport (manual login required)
   - Start downloading tracks from your library
   - Save tracks to your specified download location

### Testing Selectors

To verify the scraper works with your Beatport account:

```bash
# Test regular library page
python test_selectors.py

# Test downloads page
python test_selectors.py --downloads
```

## Configuration

The scraper uses dynamic selectors stored in `selectors.json`. These are automatically managed and updated as needed.

## Troubleshooting

### Common Issues

1. **Chrome doesn't open**: Make sure you have Google Chrome installed and updated.
2. **Login issues**: The script requires manual login for security. Make sure you complete the login process when prompted.
3. **Download fails**: Check your internet connection and ensure you're logged in properly.

### Running the Tests

If you encounter issues, run the selector tests to verify everything is working:

```bash
python test_selectors.py --downloads
```

This will generate detailed logs and screenshots to help diagnose any problems.

## How It Works

The scraper uses a sophisticated SelectorsManager that:
1. Dynamically manages selectors for track containers, names, artists, and download buttons
2. Adapts to both large and small screen layouts
3. Includes fallback mechanisms when primary selectors fail
4. Learns from successful selections to improve reliability

## Contributing

Feel free to submit issues and pull requests.

## License

[Your chosen license]

## Security Note

This tool requires manual login to Beatport for security reasons. It will never ask for or store your Beatport credentials.
