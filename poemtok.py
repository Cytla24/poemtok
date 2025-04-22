#!/usr/bin/env python3
"""
PoemTok: Convert PDF Books to TikTok Videos
-------------------------------------------
This script takes a PDF book and a background video, then creates
TikTok-style videos with each page of the book overlaid on the video
while preserving the original text formatting.
"""

# Set environment variable to disable parallelism which can cause hanging
import os
os.environ["OMP_NUM_THREADS"] = "1"

import os
import sys
import argparse
import tempfile
from pathlib import Path
import shutil
from tqdm import tqdm
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# Handle Pillow version compatibility
if not hasattr(Image, 'ANTIALIAS'):
    # In newer versions of Pillow, ANTIALIAS was renamed to LANCZOS
    Image.ANTIALIAS = Image.LANCZOS
from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip, TextClip, ColorClip
import PyPDF2
import io

# Import the text styler
from text_styler import TextStyler

# Try to import pytesseract, but don't fail if it's not available
try:
    import pytesseract
    HAS_PYTESSERACT = True
except ImportError:
    HAS_PYTESSERACT = False
    print("Warning: pytesseract not installed. OCR functionality will be disabled.")

class PoemTok:
    def __init__(self, output_dir="output", resolution=(1080, 1920), duration=15, style=None):
        """
        Initialize the PoemTok converter.
        
        Args:
            output_dir: Directory to save the generated videos
            resolution: Output video resolution (width, height) - TikTok portrait format
            duration: Duration of each video in seconds
            style: Dictionary with text styling options
        """
        self.output_dir = output_dir
        self.resolution = resolution
        self.duration = duration
        self.temp_dir = tempfile.mkdtemp()
        self.style = style or {}
        
        # Initialize text styler
        self.text_styler = TextStyler(resolution=resolution)
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
    def __del__(self):
        """Clean up temporary files when the object is destroyed."""
        try:
            shutil.rmtree(self.temp_dir)
        except:
            pass
    
    def extract_pdf_pages(self, pdf_path):
        """
        Extract pages from a PDF file using PyPDF2 and render to images.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            List of page images
        """
        print(f"Extracting pages from {pdf_path}...")
        
        # Open the PDF file
        with open(pdf_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            total_pages = len(pdf_reader.pages)
            
            print(f"PDF has {total_pages} pages")
            pages = []
            
            # Process each page
            for i in tqdm(range(total_pages)):
                # Get the page text
                page = pdf_reader.pages[i]
                text = page.extract_text()
                
                # Create a blank image with RGBA mode for transparency support
                img = Image.new('RGBA', (1000, 1400), color=(255, 255, 255, 255))
                draw = ImageDraw.Draw(img)
                
                # Use a default font
                try:
                    font = ImageFont.truetype("Arial", 20)
                except:
                    font = ImageFont.load_default()
                
                # Draw the text on the image
                draw.text((50, 50), text, fill=(0, 0, 0), font=font)
                
                # Add the image to our list
                pages.append(img)
        
        print(f"Extracted {len(pages)} pages from PDF")
        return pages
    
    def prepare_background_video(self, video_path):
        """
        Prepare the background video by ensuring it's the right resolution and duration.
        
        Args:
            video_path: Path to the background video
            
        Returns:
            VideoFileClip object
        """
        print(f"Preparing background video from {video_path}...")
        
        # Load the video
        video = VideoFileClip(video_path)
        
        # Resize to TikTok dimensions (center crop)
        if video.w / video.h > self.resolution[0] / self.resolution[1]:
            # Video is wider than TikTok aspect ratio
            new_width = int(video.h * self.resolution[0] / self.resolution[1])
            x1 = int((video.w - new_width) / 2)
            video = video.crop(x1=x1, y1=0, x2=x1+new_width, y2=video.h)
        else:
            # Video is taller than TikTok aspect ratio
            new_height = int(video.w * self.resolution[1] / self.resolution[0])
            y1 = int((video.h - new_height) / 2)
            video = video.crop(x1=0, y1=y1, x2=video.w, y2=y1+new_height)
        
        # Resize to target resolution
        video = video.resize(self.resolution)
        
        print(f"Video prepared: {video.w}x{video.h}, {video.duration}s")
        return video
    
    def create_text_overlay(self, page_image):
        """
        Create a text overlay from a PDF page image.
        
        Args:
            page_image: PIL Image of a PDF page
            
        Returns:
            PIL Image with transparent background and text
        """
        # Method 1: Extract text using OCR and create styled overlay (if pytesseract is available)
        if HAS_PYTESSERACT:
            try:
                # Extract text from the page image
                text = pytesseract.image_to_string(page_image)
                
                # If text extraction succeeded, create a styled overlay
                if text and len(text.strip()) > 0:
                    # Use the text styler to create a minimalist overlay
                    overlay = self.text_styler.create_minimalist_overlay(text, self.style)
                    return overlay
            except Exception as e:
                print(f"OCR text extraction failed: {e}. Falling back to image-based overlay.")
        else:
            print("OCR not available. Using image-based overlay.")
        
        # Method 2 (Fallback): Use the page image directly
        # Create a transparent image
        overlay = Image.new('RGBA', self.resolution, (0, 0, 0, 0))
        
        # Resize the page image to fit within the video frame
        # while preserving aspect ratio
        page_w, page_h = page_image.size
        scale = min(
            self.resolution[0] * 0.8 / page_w,
            self.resolution[1] * 0.8 / page_h
        )
        
        new_size = (int(page_w * scale), int(page_h * scale))
        
        # Convert the page image to RGBA mode if it's not already
        if page_image.mode != 'RGBA':
            page_image = page_image.convert('RGBA')
            
        resized_page = page_image.resize(new_size, Image.LANCZOS)
        
        # Calculate position to center the text
        pos_x = (self.resolution[0] - new_size[0]) // 2
        pos_y = (self.resolution[1] - new_size[1]) // 2
        
        # Create a semi-transparent background for text
        draw = ImageDraw.Draw(overlay)
        padding = 60  # Increased padding to match mockup
        draw.rectangle(
            [
                pos_x - padding, 
                pos_y - padding, 
                pos_x + new_size[0] + padding, 
                pos_y + new_size[1] + padding
            ],
            fill=(0, 0, 0, 200)  # Darker background to match mockup
        )
        
        # Paste the resized page onto the overlay without using a mask
        overlay.paste(resized_page, (pos_x, pos_y))
        
        return overlay
    
    def create_video(self, background_video, page_image, output_path):
        """
        Create a TikTok video with the page overlaid on the background video.
        
        Args:
            background_video: VideoFileClip of the background
            page_image: PIL Image of the PDF page
            output_path: Path to save the output video
            
        Returns:
            Path to the created video
        """
        # Create text overlay
        overlay = self.create_text_overlay(page_image)
        
        # Save overlay to a temporary file
        overlay_path = os.path.join(self.temp_dir, "overlay.png")
        overlay.save(overlay_path)
        
        # Create a clip from the overlay image
        overlay_clip = ImageClip(overlay_path).set_duration(self.duration)
        
        # If background video is shorter than desired duration, loop it
        if background_video.duration < self.duration:
            n_loops = int(np.ceil(self.duration / background_video.duration))
            background_video = background_video.loop(n=n_loops).subclip(0, self.duration)
        else:
            # Use a random section of the video if it's longer than needed
            import random
            max_start = max(0, background_video.duration - self.duration)
            start_time = random.uniform(0, max_start)
            background_video = background_video.subclip(start_time, start_time + self.duration)
        
        # Composite the clips
        final_clip = CompositeVideoClip([
            background_video,
            overlay_clip
        ])
        
        # Write the output video
        final_clip.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            fps=30,
            preset="ultrafast",  # For faster processing, change to "medium" for final output
            threads=4
        )
        
        # Clean up
        final_clip.close()
        background_video.close()
        if os.path.exists(overlay_path):
            os.remove(overlay_path)
        
        return output_path
    
    def process(self, pdf_path, video_path, start_page=1, end_page=None):
        """
        Process a PDF and create TikTok videos for each page.
        
        Args:
            pdf_path: Path to the PDF file
            video_path: Path to the background video
            start_page: First page to process (1-indexed)
            end_page: Last page to process (inclusive, 1-indexed)
            
        Returns:
            List of paths to the created videos
        """
        # Extract PDF pages
        pages = self.extract_pdf_pages(pdf_path)
        
        # Adjust page range
        start_page = max(1, start_page)
        if end_page is None or end_page > len(pages):
            end_page = len(pages)
        
        # Prepare background video
        background_video = self.prepare_background_video(video_path)
        
        # Create a video for each page
        output_videos = []
        
        print(f"Creating videos for pages {start_page} to {end_page}...")
        for i in tqdm(range(start_page - 1, end_page)):
            page = pages[i]
            
            # Define output path
            pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
            output_path = os.path.join(
                self.output_dir,
                f"{pdf_name}_page_{i+1}.mp4"
            )
            
            # Create the video
            self.create_video(
                background_video.copy(),
                page,
                output_path
            )
            
            output_videos.append(output_path)
        
        print(f"Created {len(output_videos)} videos in {self.output_dir}")
        return output_videos

def main():
    parser = argparse.ArgumentParser(description="Convert PDF books to TikTok videos")
    parser.add_argument("pdf_path", help="Path to the PDF file")
    parser.add_argument("video_path", help="Path to the background video")
    parser.add_argument("--output", "-o", default="output", help="Output directory")
    parser.add_argument("--start", "-s", type=int, default=1, help="First page to process (1-indexed)")
    parser.add_argument("--end", "-e", type=int, default=None, help="Last page to process (inclusive, 1-indexed)")
    parser.add_argument("--duration", "-d", type=int, default=15, help="Duration of each video in seconds")
    parser.add_argument("--resolution", "-r", default="1080x1920", 
                        help="Output video resolution (width x height)")
    parser.add_argument("--font-size", type=int, default=48, help="Font size for text overlay")
    parser.add_argument("--font", help="Path to font file for text overlay")
    parser.add_argument("--minimalist", "-m", action="store_true", 
                        help="Use minimalist style similar to the mockup")
    
    args = parser.parse_args()
    
    # Parse resolution
    try:
        width, height = map(int, args.resolution.split("x"))
        resolution = (width, height)
    except:
        print(f"Invalid resolution format: {args.resolution}. Using default 1080x1920.")
        resolution = (1080, 1920)
    
    # Set up text style
    style = {
        'font_size': args.font_size,
        'position': 'center',
        'alignment': 'center',
    }
    
    if args.font:
        style['font_path'] = args.font
    
    if args.minimalist:
        style['bg_color'] = (0, 0, 0, 200)  # Darker background
        style['text_color'] = (255, 255, 255, 255)  # White text
        style['padding'] = 60  # Larger padding
    
    # Create PoemTok instance
    poemtok = PoemTok(
        output_dir=args.output,
        resolution=resolution,
        duration=args.duration,
        style=style
    )
    
    # Process the PDF
    poemtok.process(
        args.pdf_path,
        args.video_path,
        start_page=args.start,
        end_page=args.end
    )

if __name__ == "__main__":
    main()
