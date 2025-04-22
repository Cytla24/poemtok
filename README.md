# PoemTok

PoemTok is a tool that converts PDF books into TikTok-style videos. Each page of the PDF becomes a separate video with the text displayed as white text on a semi-transparent black background, overlaid on a background video.

## Features

- **Automated PDF Processing**: Extract content from PDF pages while excluding headers and footers
- **High-Quality Screenshots**: Create clean screenshots of each page
- **Text Styling**: Convert text to white on semi-transparent black background
- **Video Creation**: Overlay processed text on background videos
- **Batch Processing**: Process multiple pages in one command
- **Customizable Appearance**: Adjust text size, background opacity, and more

## Installation

1. Clone this repository or download the source code
2. Install the required dependencies:

```bash
pip install -r requirements.txt
pip install PyMuPDF  # For PDF screenshot functionality
```

3. Make sure you have ffmpeg installed on your system:
   - Mac: `brew install ffmpeg`
   - Linux: `apt-get install ffmpeg`
   - Windows: Download from [ffmpeg.org](https://ffmpeg.org/download.html)

## Usage

### Process a PDF and Create Videos

```bash
# Process a range of pages (e.g., pages 10-20)
python pdf_to_screenshots.py book.pdf background_video.mp4 --start 10 --end 20

# Process the entire book
python pdf_to_screenshots.py book.pdf background_video.mp4

# Adjust margins to exclude more of the header/footer
python pdf_to_screenshots.py book.pdf background_video.mp4 --margin-top 0.15 --margin-bottom 0.15

# Create larger or smaller text
python pdf_to_screenshots.py book.pdf background_video.mp4 --scale 1.0  # Larger text
python pdf_to_screenshots.py book.pdf background_video.mp4 --scale 0.8  # Smaller text
```

### Create a Video from a Single Screenshot

```bash
python poemtok_final.py screenshot.png background_video.mp4 --output output/video.mp4 --scale 0.9
```

## Options

### PDF to Screenshots Options

- `--screenshots-dir`: Directory to save screenshots (default: "screenshots")
- `--output-dir`, `-o`: Directory to save videos (default: "output")
- `--start`, `-s`: First page to process (1-indexed)
- `--end`, `-e`: Last page to process (inclusive, 1-indexed)
- `--margin-top`: Top margin to exclude (fraction of page height, default: 0.1)
- `--margin-bottom`: Bottom margin to exclude (fraction of page height, default: 0.1)
- `--margin-left`: Left margin to exclude (fraction of page width, default: 0.1)
- `--margin-right`: Right margin to exclude (fraction of page width, default: 0.1)
- `--dpi`: DPI for the rendered images (default: 300)
- `--duration`, `-d`: Duration of each video in seconds (default: 5)
- `--scale`: Scale factor for the text size (0-1, default: 0.9)
- `--bg-opacity`: Opacity of the background (0-1, default: 0.8)
- `--screenshots-only`: Only create screenshots, not videos

### Single Video Options

- `--output`, `-o`: Output video path (default: "output/final_video.mp4")
- `--duration`, `-d`: Duration of the video in seconds (default: 5)
- `--scale`, `-s`: Scale factor for the text size (0-1, default: 0.7)
- `--bg-opacity`, `-a`: Opacity of the background (0-1, default: 0.8)
- `--contrast`, `-c`: Contrast enhancement factor (default: 2.0)

## Tips for Best Results

- Use a high-quality PDF with clear text
- Adjust the margins to exclude headers and footers
- For poetry or short text, 5-10 seconds duration is usually sufficient
- For pages with more text, consider increasing the duration
- Adjust the scale parameter to make text larger or smaller
- The default styling (white text on semi-transparent black) works well for most videos

## Requirements

- Python 3.8+
- PyMuPDF (for PDF processing)
- Pillow (for image processing)
- ffmpeg (for video creation)
- PyPDF2
- tqdm

## License

MIT
