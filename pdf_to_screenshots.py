#!/usr/bin/env python3
"""
PDF to Screenshots
-----------------
Automatically takes screenshots of PDF pages while excluding headers and footers.
"""

import os
import sys
import argparse
import tempfile
import fitz  # PyMuPDF
from PIL import Image
import numpy as np
from tqdm import tqdm

def extract_content_area(page, margin_top=0.1, margin_bottom=0.1, margin_left=0.1, margin_right=0.1):
    """
    Extract the content area of a page, excluding headers and footers.
    
    Args:
        page: PyMuPDF page object
        margin_top: Top margin to exclude (fraction of page height)
        margin_bottom: Bottom margin to exclude (fraction of page height)
        margin_left: Left margin to exclude (fraction of page width)
        margin_right: Right margin to exclude (fraction of page width)
        
    Returns:
        Tuple of (x0, y0, x1, y1) coordinates for the content area
    """
    # Get page dimensions
    page_rect = page.rect
    width, height = page_rect.width, page_rect.height
    
    # Calculate content area
    x0 = width * margin_left
    y0 = height * margin_top
    x1 = width * (1 - margin_right)
    y1 = height * (1 - margin_bottom)
    
    return (x0, y0, x1, y1)

def pdf_to_screenshots(pdf_path, output_dir="screenshots", start_page=1, end_page=None,
                      margin_top=0.1, margin_bottom=0.1, margin_left=0.1, margin_right=0.1,
                      dpi=300, bg_color=(255, 255, 255)):
    """
    Convert PDF pages to screenshots, excluding headers and footers.
    
    Args:
        pdf_path: Path to the PDF file
        output_dir: Directory to save the screenshots
        start_page: First page to process (1-indexed)
        end_page: Last page to process (inclusive, 1-indexed)
        margin_top: Top margin to exclude (fraction of page height)
        margin_bottom: Bottom margin to exclude (fraction of page height)
        margin_left: Left margin to exclude (fraction of page width)
        margin_right: Right margin to exclude (fraction of page width)
        dpi: DPI for the rendered images
        bg_color: Background color (RGB tuple)
        
    Returns:
        List of paths to the created screenshots
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Open the PDF
    pdf_document = fitz.open(pdf_path)
    total_pages = len(pdf_document)
    
    print(f"PDF has {total_pages} pages")
    
    # Adjust page range
    start_page = max(1, start_page)
    if end_page is None or end_page > total_pages:
        end_page = total_pages
    
    # Calculate zoom factor based on DPI
    zoom_factor = dpi / 72  # 72 DPI is the default PDF resolution
    
    # Process each page
    screenshot_paths = []
    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    
    for page_num in tqdm(range(start_page - 1, end_page), desc="Processing pages"):
        # Get the page
        page = pdf_document[page_num]
        
        # Extract content area
        content_rect = extract_content_area(
            page, 
            margin_top=margin_top,
            margin_bottom=margin_bottom,
            margin_left=margin_left,
            margin_right=margin_right
        )
        
        # Render the page to an image
        pix = page.get_pixmap(
            matrix=fitz.Matrix(zoom_factor, zoom_factor),
            clip=content_rect,
            alpha=False
        )
        
        # Convert to PIL Image
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        
        # Save the image
        output_path = os.path.join(output_dir, f"{pdf_name}_page_{page_num + 1}.png")
        img.save(output_path, "PNG")
        screenshot_paths.append(output_path)
        
        print(f"Saved screenshot: {output_path}")
    
    print(f"Created {len(screenshot_paths)} screenshots in {output_dir}")
    return screenshot_paths

def batch_process_to_videos(screenshot_paths, video_path, output_dir="output", 
                          duration=5, scale=0.9, bg_opacity=0.8):
    """
    Process multiple screenshots to create videos.
    
    Args:
        screenshot_paths: List of paths to screenshots
        video_path: Path to the background video
        output_dir: Directory to save the videos
        duration: Duration of each video in seconds
        scale: Scale factor for the text size (0-1)
        bg_opacity: Opacity of the background (0-1)
        
    Returns:
        List of paths to the created videos
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Process each screenshot
    video_paths = []
    
    for screenshot_path in tqdm(screenshot_paths, desc="Creating videos"):
        # Define output path
        base_name = os.path.splitext(os.path.basename(screenshot_path))[0]
        output_path = os.path.join(output_dir, f"{base_name}.mp4")
        
        # Create the video
        cmd = [
            "python", "poemtok_final.py",
            screenshot_path,
            video_path,
            "--output", output_path,
            "--duration", str(duration),
            "--scale", str(scale),
            "--bg-opacity", str(bg_opacity)
        ]
        
        # Run the command
        os.system(" ".join(cmd))
        
        video_paths.append(output_path)
    
    print(f"Created {len(video_paths)} videos in {output_dir}")
    return video_paths

def main():
    parser = argparse.ArgumentParser(description="Convert PDF pages to screenshots and videos")
    parser.add_argument("pdf_path", help="Path to the PDF file")
    parser.add_argument("video_path", help="Path to the background video")
    parser.add_argument("--screenshots-dir", default="screenshots", help="Directory to save screenshots")
    parser.add_argument("--output-dir", "-o", default="output", help="Directory to save videos")
    parser.add_argument("--start", "-s", type=int, default=1, help="First page to process (1-indexed)")
    parser.add_argument("--end", "-e", type=int, default=None, help="Last page to process (inclusive, 1-indexed)")
    parser.add_argument("--margin-top", type=float, default=0.1, help="Top margin to exclude (fraction of page height)")
    parser.add_argument("--margin-bottom", type=float, default=0.1, help="Bottom margin to exclude (fraction of page height)")
    parser.add_argument("--margin-left", type=float, default=0.1, help="Left margin to exclude (fraction of page width)")
    parser.add_argument("--margin-right", type=float, default=0.1, help="Right margin to exclude (fraction of page width)")
    parser.add_argument("--dpi", type=int, default=300, help="DPI for the rendered images")
    parser.add_argument("--duration", "-d", type=int, default=5, help="Duration of each video in seconds")
    parser.add_argument("--scale", type=float, default=0.9, help="Scale factor for the text size (0-1)")
    parser.add_argument("--bg-opacity", type=float, default=0.8, help="Opacity of the background (0-1)")
    parser.add_argument("--screenshots-only", action="store_true", help="Only create screenshots, not videos")
    
    args = parser.parse_args()
    
    # Create screenshots
    screenshot_paths = pdf_to_screenshots(
        args.pdf_path,
        output_dir=args.screenshots_dir,
        start_page=args.start,
        end_page=args.end,
        margin_top=args.margin_top,
        margin_bottom=args.margin_bottom,
        margin_left=args.margin_left,
        margin_right=args.margin_right,
        dpi=args.dpi
    )
    
    # Create videos if requested
    if not args.screenshots_only:
        batch_process_to_videos(
            screenshot_paths,
            args.video_path,
            output_dir=args.output_dir,
            duration=args.duration,
            scale=args.scale,
            bg_opacity=args.bg_opacity
        )

if __name__ == "__main__":
    main()
