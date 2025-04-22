#!/usr/bin/env python3
"""
PoemTok Styled Version
----------------------
Creates TikTok-style videos from PDF books with stylized text overlay
that matches the minimalist mockup design.
"""

import os
import sys
import argparse
import tempfile
import shutil
import json
import subprocess
from pathlib import Path
from tqdm import tqdm
import PyPDF2

class PoemTokStyled:
    def __init__(self, output_dir="output", duration=5, font_size=32, 
                 text_color="white", box_color="black@0.8", box_width=0.8, box_height=0.7):
        """
        Initialize the PoemTok styled converter.
        
        Args:
            output_dir: Directory to save the generated videos
            duration: Duration of each video in seconds
            font_size: Font size for the text
            text_color: Color of the text
            box_color: Color of the background box (with alpha)
            box_width: Width of the box as a fraction of video width
            box_height: Height of the box as a fraction of video height
        """
        self.output_dir = output_dir
        self.duration = duration
        self.font_size = font_size
        self.text_color = text_color
        self.box_color = box_color
        self.box_width = box_width
        self.box_height = box_height
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
        Extract text from PDF pages.
        
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
                
                # Format the text for better display
                formatted_text = self._format_text(text)
                
                # Add to our list
                page_texts.append(formatted_text)
        
        print(f"Extracted text from {len(page_texts)} pages")
        return page_texts
    
    def _format_text(self, text, max_line_length=30):
        """
        Format text for better display in the video.
        
        Args:
            text: Text to format
            max_line_length: Maximum characters per line
            
        Returns:
            Formatted text
        """
        # Split into words
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            # If adding this word would exceed the max line length
            if len(current_line) + len(word) + 1 > max_line_length and current_line:
                lines.append(current_line)
                current_line = word
            else:
                if current_line:
                    current_line += " " + word
                else:
                    current_line = word
        
        # Add the last line
        if current_line:
            lines.append(current_line)
        
        # Join lines with newlines
        return "\\n".join(lines)
    
    def create_text_overlay(self, text, output_path):
        """
        Create a text file with the formatted text for ffmpeg.
        
        Args:
            text: Text to display
            output_path: Path to save the text file
            
        Returns:
            Path to the created text file
        """
        with open(output_path, 'w') as f:
            f.write(text)
        
        return output_path
    
    def create_video_with_styled_text(self, video_path, text, output_path):
        """
        Create a video with styled text overlay using ffmpeg.
        
        Args:
            video_path: Path to the background video
            text: Text to display
            output_path: Path to save the output video
            
        Returns:
            Path to the created video
        """
        # Create a text file with the content
        text_file = os.path.join(self.temp_dir, "text.txt")
        self.create_text_overlay(text, text_file)
        
        # Calculate box dimensions and position
        # These will be used in the ffmpeg filter to position the box and text
        
        # Prepare ffmpeg command with complex filter for styled text
        filter_complex = [
            # First, create a semi-transparent box
            f"color=c={self.box_color}:s=1080x1920:d={self.duration}[box];",
            # Then, add text on top of the box
            f"[box]drawtext=fontsize={self.font_size}:fontcolor={self.text_color}:textfile='{text_file}':"
            f"x=(w-text_w)/2:y=(h-text_h)/2:line_spacing=10[text_overlay];",
            # Crop the box to desired dimensions
            f"[text_overlay]crop=in_w*{self.box_width}:in_h*{self.box_height}:x=(in_w-out_w)/2:y=(in_h-out_h)/2[cropped_box];",
            # Overlay the cropped box on the video
            f"[0:v]trim=0:{self.duration},setpts=PTS-STARTPTS[bg];",
            f"[bg][cropped_box]overlay=(W-w)/2:(H-h)/2:shortest=1[out]"
        ]
        
        filter_str = "".join(filter_complex)
        
        command = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-filter_complex", filter_str,
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
                f"{pdf_name}_page_{i + start_page}_styled.mp4"
            )
            
            # Create the video
            result = self.create_video_with_styled_text(
                video_path,
                text,
                output_path
            )
            
            if result:
                output_videos.append(result)
        
        print(f"Created {len(output_videos)} videos in {self.output_dir}")
        return output_videos

def main():
    parser = argparse.ArgumentParser(description="Convert PDF books to TikTok videos with styled text")
    parser.add_argument("pdf_path", help="Path to the PDF file")
    parser.add_argument("video_path", help="Path to the background video")
    parser.add_argument("--output", "-o", default="output", help="Output directory")
    parser.add_argument("--start", "-s", type=int, default=1, help="First page to process (1-indexed)")
    parser.add_argument("--end", "-e", type=int, default=None, help="Last page to process (inclusive, 1-indexed)")
    parser.add_argument("--duration", "-d", type=int, default=5, help="Duration of each video in seconds")
    parser.add_argument("--font-size", type=int, default=32, help="Font size for text")
    parser.add_argument("--text-color", default="white", help="Text color")
    parser.add_argument("--box-color", default="black@0.8", help="Background box color (with alpha)")
    parser.add_argument("--box-width", type=float, default=0.8, help="Width of box as fraction of video width")
    parser.add_argument("--box-height", type=float, default=0.7, help="Height of box as fraction of video height")
    
    args = parser.parse_args()
    
    # Create PoemTok instance
    poemtok = PoemTokStyled(
        output_dir=args.output,
        duration=args.duration,
        font_size=args.font_size,
        text_color=args.text_color,
        box_color=args.box_color,
        box_width=args.box_width,
        box_height=args.box_height
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
