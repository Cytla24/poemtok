#!/usr/bin/env python3
"""
PoemTok Image-Based Version
---------------------------
Creates TikTok-style videos from PDF books by taking screenshots of each page,
processing the images to create a clean text overlay, and adding them to videos.
This preserves the exact formatting from the PDF.
"""

import os
import sys
import argparse
import tempfile
import shutil
import subprocess
from pathlib import Path
from tqdm import tqdm
import PyPDF2
from pdf2image import convert_from_path
from PIL import Image, ImageOps, ImageEnhance, ImageFilter

class PoemTokImage:
    def __init__(self, output_dir="output", duration=5, 
                 box_width=0.7, box_height=0.4, 
                 bg_opacity=0.7, invert=True):
        """
        Initialize the PoemTok image-based converter.
        
        Args:
            output_dir: Directory to save the generated videos
            duration: Duration of each video in seconds
            box_width: Width of the text box as a fraction of video width
            box_height: Height of the text box as a fraction of video height
            bg_opacity: Opacity of the background (0-1)
            invert: Whether to invert the colors (black text on white -> white text on black)
        """
        self.output_dir = output_dir
        self.duration = duration
        self.box_width = box_width
        self.box_height = box_height
        self.bg_opacity = bg_opacity
        self.invert = invert
        self.temp_dir = tempfile.mkdtemp()
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
    
    def __del__(self):
        """Clean up temporary files when the object is destroyed."""
        try:
            shutil.rmtree(self.temp_dir)
        except:
            pass
    
    def convert_pdf_to_images(self, pdf_path, start_page=1, end_page=None, dpi=300):
        """
        Convert PDF pages to images.
        
        Args:
            pdf_path: Path to the PDF file
            start_page: First page to process (1-indexed)
            end_page: Last page to process (inclusive, 1-indexed)
            dpi: DPI for the rendered images
            
        Returns:
            List of paths to the created images
        """
        print(f"Converting PDF pages to images...")
        
        # Get total pages
        with open(pdf_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            total_pages = len(pdf_reader.pages)
        
        print(f"PDF has {total_pages} pages")
        
        # Adjust page range
        start_page = max(1, start_page)
        if end_page is None or end_page > total_pages:
            end_page = total_pages
        
        # Convert pages to images
        images = convert_from_path(
            pdf_path,
            dpi=dpi,
            first_page=start_page,
            last_page=end_page
        )
        
        # Save images to temp directory
        image_paths = []
        for i, image in enumerate(tqdm(images)):
            image_path = os.path.join(self.temp_dir, f"page_{i + start_page}.png")
            image.save(image_path, "PNG")
            image_paths.append(image_path)
        
        print(f"Converted {len(image_paths)} pages to images")
        return image_paths
    
    def process_image(self, image_path):
        """
        Process an image to create a clean text overlay.
        
        Args:
            image_path: Path to the image
            
        Returns:
            Path to the processed image
        """
        # Open the image
        image = Image.open(image_path)
        
        # Crop to content area (remove margins)
        # This assumes white background with dark text
        # We'll find the bounding box of the text content
        
        # Convert to grayscale for easier processing
        gray_image = image.convert("L")
        
        # Invert if needed to make text white on black background
        if self.invert:
            gray_image = ImageOps.invert(gray_image)
        
        # Enhance contrast to make text stand out
        enhancer = ImageEnhance.Contrast(gray_image)
        high_contrast = enhancer.enhance(2.0)
        
        # Apply a slight blur to smooth edges
        smoothed = high_contrast.filter(ImageFilter.GaussianBlur(radius=0.5))
        
        # Create a semi-transparent background
        # We'll create a new image with an alpha channel
        processed = Image.new("RGBA", smoothed.size, (0, 0, 0, 0))
        
        # Calculate the alpha value for the background
        bg_alpha = int(255 * self.bg_opacity)
        
        # Paste the processed image onto the transparent background
        for y in range(smoothed.height):
            for x in range(smoothed.width):
                pixel = smoothed.getpixel((x, y))
                if pixel > 200:  # If the pixel is bright (text)
                    processed.putpixel((x, y), (255, 255, 255, 255))  # White, fully opaque
                else:  # Background
                    processed.putpixel((x, y), (0, 0, 0, bg_alpha))  # Black, semi-transparent
        
        # Save the processed image
        processed_path = os.path.join(self.temp_dir, f"processed_{os.path.basename(image_path)}")
        processed.save(processed_path, "PNG")
        
        return processed_path
    
    def create_video_with_image(self, video_path, image_path, output_path):
        """
        Create a video with an image overlay using ffmpeg.
        
        Args:
            video_path: Path to the background video
            image_path: Path to the image to overlay
            output_path: Path to save the output video
            
        Returns:
            Path to the created video
        """
        # Use ffmpeg to overlay the image on the video
        command = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", image_path,
            "-filter_complex", (
                f"[0:v]trim=0:{self.duration},setpts=PTS-STARTPTS[bg];"
                f"[1:v]scale=iw*{self.box_width}:-1[scaled];"
                f"[bg][scaled]overlay=(W-w)/2:(H-h)/2:shortest=1[out]"
            ),
            "-map", "[out]",
            "-c:v", "libx264",
            "-preset", "fast",
            "-t", str(self.duration),
            output_path
        ]
        
        # Run the command
        try:
            subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(f"Created video: {output_path}")
            return output_path
        except subprocess.CalledProcessError as e:
            print(f"Error creating video: {e}")
            return None
    
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
        # Convert PDF pages to images
        image_paths = self.convert_pdf_to_images(pdf_path, start_page, end_page)
        
        # Process each image
        print("Processing images...")
        processed_images = []
        for image_path in tqdm(image_paths):
            processed = self.process_image(image_path)
            processed_images.append(processed)
        
        # Create a video for each processed image
        output_videos = []
        
        print(f"Creating videos for pages {start_page} to {start_page + len(processed_images) - 1}...")
        for i, image_path in enumerate(tqdm(processed_images)):
            # Define output path
            pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
            output_path = os.path.join(
                self.output_dir,
                f"{pdf_name}_page_{i + start_page}_image.mp4"
            )
            
            # Create the video
            result = self.create_video_with_image(
                video_path,
                image_path,
                output_path
            )
            
            if result:
                output_videos.append(result)
        
        print(f"Created {len(output_videos)} videos in {self.output_dir}")
        return output_videos

def main():
    parser = argparse.ArgumentParser(description="Convert PDF books to TikTok videos using image processing")
    parser.add_argument("pdf_path", help="Path to the PDF file")
    parser.add_argument("video_path", help="Path to the background video")
    parser.add_argument("--output", "-o", default="output", help="Output directory")
    parser.add_argument("--start", "-s", type=int, default=1, help="First page to process (1-indexed)")
    parser.add_argument("--end", "-e", type=int, default=None, help="Last page to process (inclusive, 1-indexed)")
    parser.add_argument("--duration", "-d", type=int, default=5, help="Duration of each video in seconds")
    parser.add_argument("--box-width", type=float, default=0.7, help="Width of text box as fraction of video width")
    parser.add_argument("--box-height", type=float, default=0.4, help="Height of text box as fraction of video height")
    parser.add_argument("--bg-opacity", type=float, default=0.7, help="Opacity of the background (0-1)")
    parser.add_argument("--no-invert", action="store_true", help="Don't invert colors (keep black text on white)")
    
    args = parser.parse_args()
    
    # Create PoemTok instance
    poemtok = PoemTokImage(
        output_dir=args.output,
        duration=args.duration,
        box_width=args.box_width,
        box_height=args.box_height,
        bg_opacity=args.bg_opacity,
        invert=not args.no_invert
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
