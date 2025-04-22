#!/usr/bin/env python3
"""
PoemTok Simple Version
----------------------
Creates TikTok-style videos from PDF books with a minimalist design
that preserves the original text formatting from the PDF.
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

class PoemTokSimple:
    def __init__(self, output_dir="output", duration=5, font_size=32, 
                 text_color="white", box_color="black@0.7"):
        """
        Initialize the PoemTok simple converter.
        
        Args:
            output_dir: Directory to save the generated videos
            duration: Duration of each video in seconds
            font_size: Font size for the text
            text_color: Color of the text
            box_color: Color of the background box (with alpha)
        """
        self.output_dir = output_dir
        self.duration = duration
        self.font_size = font_size
        self.text_color = text_color
        self.box_color = box_color
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
                
                # Add to our list
                page_texts.append(text)
        
        print(f"Extracted text from {len(page_texts)} pages")
        return page_texts
    
    def create_text_file(self, text, output_path):
        """
        Create a text file for ffmpeg.
        
        Args:
            text: Text to display
            output_path: Path to save the text file
            
        Returns:
            Path to the created text file
        """
        # Replace newlines with escaped newlines for ffmpeg
        formatted_text = text.replace('\n', '\\n')
        
        with open(output_path, 'w') as f:
            f.write(formatted_text)
        
        return output_path
    
    def create_video_with_text(self, video_path, text, output_path):
        """
        Create a video with text overlay using ffmpeg.
        
        Args:
            video_path: Path to the background video
            text: Text to display
            output_path: Path to save the output video
            
        Returns:
            Path to the created video
        """
        # Create a text file with the content
        text_file = os.path.join(self.temp_dir, "text.txt")
        self.create_text_file(text, text_file)
        
        # Simple ffmpeg command that adds a small box with text
        command = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-vf", (
                f"drawbox=x=(iw-iw*0.7)/2:y=(ih-ih*0.4)/2:w=iw*0.7:h=ih*0.4:color={self.box_color}:t=fill,"
                f"drawtext=fontsize={self.font_size}:fontcolor={self.text_color}:textfile='{text_file}':"
                f"x=(w-text_w)/2:y=(h-text_h)/2:line_spacing=10"
            ),
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
                f"{pdf_name}_page_{i + start_page}_simple.mp4"
            )
            
            # Create the video
            result = self.create_video_with_text(
                video_path,
                text,
                output_path
            )
            
            if result:
                output_videos.append(result)
        
        print(f"Created {len(output_videos)} videos in {self.output_dir}")
        return output_videos

def main():
    parser = argparse.ArgumentParser(description="Convert PDF books to TikTok videos with simple styling")
    parser.add_argument("pdf_path", help="Path to the PDF file")
    parser.add_argument("video_path", help="Path to the background video")
    parser.add_argument("--output", "-o", default="output", help="Output directory")
    parser.add_argument("--start", "-s", type=int, default=1, help="First page to process (1-indexed)")
    parser.add_argument("--end", "-e", type=int, default=None, help="Last page to process (inclusive, 1-indexed)")
    parser.add_argument("--duration", "-d", type=int, default=5, help="Duration of each video in seconds")
    parser.add_argument("--font-size", type=int, default=32, help="Font size for text")
    parser.add_argument("--text-color", default="white", help="Text color")
    parser.add_argument("--box-color", default="black@0.7", help="Background box color (with alpha)")
    
    args = parser.parse_args()
    
    # Create PoemTok instance
    poemtok = PoemTokSimple(
        output_dir=args.output,
        duration=args.duration,
        font_size=args.font_size,
        text_color=args.text_color,
        box_color=args.box_color
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
