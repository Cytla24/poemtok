# PoemTok

PoemTok is a tool that converts PDF books into TikTok-style videos, with each page of the book becoming a separate video. The text formatting from the PDF is preserved and overlaid on a background video of your choice.

## Features

- Convert each PDF page to a separate TikTok video
- Preserve text formatting from the original PDF
- Overlay text on a background video with a semi-transparent backdrop
- Customize video duration, resolution, and page range
- Batch process multiple pages at once

## Installation

1. Clone this repository or download the source code
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

3. Make sure you have ffmpeg installed on your system:
   - Mac: `brew install ffmpeg`
   - Linux: `apt-get install ffmpeg`
   - Windows: Download from [ffmpeg.org](https://ffmpeg.org/download.html)

## Usage

Basic usage:

```bash
python poemtok.py path/to/book.pdf path/to/background.mp4
```

Advanced options:

```bash
python poemtok.py path/to/book.pdf path/to/background.mp4 \
    --output output_directory \
    --start 1 \
    --end 10 \
    --duration 15 \
    --resolution 1080x1920
```

### Arguments

- `pdf_path`: Path to the PDF file (required)
- `video_path`: Path to the background video (required)
- `--output` or `-o`: Output directory for the generated videos (default: "output")
- `--start` or `-s`: First page to process, 1-indexed (default: 1)
- `--end` or `-e`: Last page to process, inclusive (default: all pages)
- `--duration` or `-d`: Duration of each video in seconds (default: 15)
- `--resolution` or `-r`: Output video resolution as width x height (default: 1080x1920)

## Example

Convert the first 5 pages of a poetry book with a 10-second duration:

```bash
python poemtok.py poetry_collection.pdf ambient_background.mp4 --start 1 --end 5 --duration 10
```

## Tips for Best Results

- Use a high-quality PDF with clear text
- Choose a background video that's not too distracting
- For poetry or short text, 10-15 seconds is usually sufficient
- For pages with more text, consider increasing the duration
- The default resolution (1080x1920) is optimized for TikTok's portrait mode

## Requirements

- Python 3.7+
- PyPDF2
- Pillow
- moviepy
- pdf2image
- numpy
- opencv-python
- pytesseract
- fpdf
- tqdm

## License

MIT
