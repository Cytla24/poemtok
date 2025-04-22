#!/usr/bin/env python3
"""
PoemTok Direct Text Version
--------------------------
Creates TikTok-style videos from PDF books using direct text positioning
to better preserve the original text layout from the PDF.
"""

import os
import sys
import argparse
import tempfile
import shutil
import subprocess
import re
from pathlib import Path
from tqdm import tqdm
import PyPDF2

class PoemTokDirect:
    def __init__(self, output_dir="output", duration=5, font_size=24, 
                 text_color="white", box_color="black@0.7", box_width=0.6, box_height=0.4,
                 font="Arial"):
        """
        Initialize the PoemTok direct text converter.
        
        Args:
            output_dir: Directory to save the generated videos
            duration: Duration of each video in seconds
            font_size: Font size for the text
            text_color: Color of the text
            box_color: Color of the background box (with alpha)
            box_width: Width of box as fraction of video width
            box_height: Height of box as fraction of video height
            font: Font to use for text
        """
        self.output_dir = output_dir
        self.duration = duration
        self.font_size = font_size
        self.text_color = text_color
        self.box_color = box_color
        self.box_width = box_width
        self.box_height = box_height
        self.font = font
        self.temp_dir = tempfile.mkdtemp()
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
    
    def __del__(self):
        """Clean up temporary files when the object is destroyed."""
        try:
            shutil.rmtree(self.temp_dir)
        except:
            pass
    
    def extract_text_from_pdf(self, pdf_path, start_page=1, end_page=None):
        """
        Extract text from PDF pages with careful formatting preservation.
        
        Args:
            pdf_path: Path to the PDF file
            start_page: First page to process (1-indexed)
            end_page: Last page to process (inclusive, 1-indexed)
            
        Returns:
            List of extracted text for each page
        """
        print(f"Extracting text from {pdf_path}...")
        
        # Open the PDF file
        with open(pdf_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            total_pages = len(pdf_reader.pages)
            
            print(f"PDF has {total_pages} pages")
            
            # Adjust page range
            start_page = max(1, start_page)
            if end_page is None or end_page > total_pages:
                end_page = total_pages
            
            # Extract text from each page
            page_texts = []
            for i in tqdm(range(start_page - 1, end_page)):
                page = pdf_reader.pages[i]
                text = page.extract_text()
                
                # Clean up the text
                text = text.strip()
                
                # Add to our list
                page_texts.append(text)
        
        print(f"Extracted text from {len(page_texts)} pages")
        return page_texts
    
    def create_direct_text_filter(self, text):
        """
        Create an ffmpeg filter complex string for direct text positioning.
        
        Args:
            text: Text to display
            
        Returns:
            FFmpeg filter complex string
        """
        # Split text into lines
        lines = text.split('\n')
        
        # Calculate box dimensions
        box_w = int(1080 * self.box_width)
        box_h = int(1920 * self.box_height)
        box_x = int((1080 - box_w) / 2)
        box_y = int((1920 - box_h) / 2)
        
        # Create the box filter
        filter_complex = [
            f"drawbox=x={box_x}:y={box_y}:w={box_w}:h={box_h}:color={self.box_color}:t=fill"
        ]
        
        # Calculate line spacing and starting y position
        line_height = self.font_size * 1.5
        total_text_height = line_height * len(lines)
        start_y = box_y + (box_h - total_text_height) / 2
        
        # Add each line as a separate drawtext filter
        for i, line in enumerate(lines):
            if line.strip():  # Skip empty lines
                # Escape special characters
                escaped_line = line.replace("'", "'\\''").replace(':', '\\:').replace(',', '\\,')
                
                # Calculate y position for this line
                y_pos = start_y + i * line_height
                
                # Add drawtext filter
                filter_complex.append(
                    f"drawtext=text='{escaped_line}':fontsize={self.font_size}:"
                    f"fontcolor={self.text_color}:x=(w-text_w)/2:y={y_pos}:font={self.font}"
                )
        
        # Join all filters with commas
        return ','.join(filter_complex)
    
    def create_video_with_direct_text(self, video_path, text, output_path):
        """
        Create a video with direct text positioning using ffmpeg.
        
        Args:
            video_path: Path to the background video
            text: Text to display
            output_path: Path to save the output video
            
        Returns:
            Path to the created video
        """
        # Create the filter complex string
        filter_complex = self.create_direct_text_filter(text)
        
        # Create ffmpeg command
        command = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-vf", filter_complex,
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
        # Extract text from PDF pages
        page_texts = self.extract_text_from_pdf(pdf_path, start_page, end_page)
        
        # Create a video for each page
        output_videos = []
        
        print(f"Creating videos for pages {start_page} to {start_page + len(page_texts) - 1}...")
        for i, text in enumerate(tqdm(page_texts)):
            # Define output path
            pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
            output_path = os.path.join(
                self.output_dir,
                f"{pdf_name}_page_{i + start_page}_direct.mp4"
            )
            
            # Create the video
            result = self.create_video_with_direct_text(
                video_path,
                text,
                output_path
            )
            
            if result:
                output_videos.append(result)
        
        print(f"Created {len(output_videos)} videos in {self.output_dir}")
        return output_videos

def main():
    parser = argparse.ArgumentParser(description="Convert PDF books to TikTok videos with direct text positioning")
    parser.add_argument("pdf_path", help="Path to the PDF file")
    parser.add_argument("video_path", help="Path to the background video")
    parser.add_argument("--output", "-o", default="output", help="Output directory")
    parser.add_argument("--start", "-s", type=int, default=1, help="First page to process (1-indexed)")
    parser.add_argument("--end", "-e", type=int, default=None, help="Last page to process (inclusive, 1-indexed)")
    parser.add_argument("--duration", "-d", type=int, default=5, help="Duration of each video in seconds")
    parser.add_argument("--font-size", type=int, default=24, help="Font size for text")
    parser.add_argument("--text-color", default="white", help="Text color")
    parser.add_argument("--box-color", default="black@0.7", help="Background box color (with alpha)")
    parser.add_argument("--box-width", type=float, default=0.6, help="Width of box as fraction of video width")
    parser.add_argument("--box-height", type=float, default=0.4, help="Height of box as fraction of video height")
    parser.add_argument("--font", default="Arial", help="Font to use for text")
    
    args = parser.parse_args()
    
    # Create PoemTok instance
    poemtok = PoemTokDirect(
        output_dir=args.output,
        duration=args.duration,
        font_size=args.font_size,
        text_color=args.text_color,
        box_color=args.box_color,
        box_width=args.box_width,
        box_height=args.box_height,
        font=args.font
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
