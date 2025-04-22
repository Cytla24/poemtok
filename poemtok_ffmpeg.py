#!/usr/bin/env python3
"""
PoemTok FFmpeg Version
----------------------
Creates TikTok-style videos from PDF books using ffmpeg for caption overlay.
This version focuses on extracting text and adding it as stylized captions
rather than preserving the PDF page layout.
"""

import os
import sys
import argparse
import tempfile
import shutil
import json
import random
import subprocess
from pathlib import Path
from tqdm import tqdm
import PyPDF2

class PoemTokFFmpeg:
    def __init__(self, output_dir="output", duration=5, font_size=24, font_color="white", 
                 bg_color="black@0.7", font_file=None):
        """
        Initialize the PoemTok converter using ffmpeg.
        
        Args:
            output_dir: Directory to save the generated videos
            duration: Duration of each video in seconds
            font_size: Font size for the captions
            font_color: Font color for the captions
            bg_color: Background color for the caption box (with alpha)
            font_file: Path to a font file (optional)
        """
        self.output_dir = output_dir
        self.duration = duration
        self.font_size = font_size
        self.font_color = font_color
        self.bg_color = bg_color
        self.font_file = font_file
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
    
    def create_subtitle_file(self, text, duration, output_path):
        """
        Create a subtitle file (SRT) for the video.
        
        Args:
            text: Text to display as captions
            duration: Duration of the video in seconds
            output_path: Path to save the subtitle file
            
        Returns:
            Path to the created subtitle file
        """
        # Format text for better display
        # Split into lines with max 40 chars per line
        formatted_lines = []
        words = text.split()
        current_line = ""
        
        for word in words:
            if len(current_line) + len(word) + 1 <= 40:
                if current_line:
                    current_line += " " + word
                else:
                    current_line = word
            else:
                formatted_lines.append(current_line)
                current_line = word
        
        if current_line:
            formatted_lines.append(current_line)
        
        # Join lines with line breaks
        formatted_text = "\\N".join(formatted_lines)
        
        # Create the subtitle content
        srt_content = f"1\n00:00:00,000 --> 00:{duration:02d}:00,000\n{formatted_text}\n"
        
        # Write to file
        with open(output_path, 'w') as f:
            f.write(srt_content)
        
        return output_path
    
    def create_video_with_captions(self, video_path, text, output_path):
        """
        Create a video with captions using ffmpeg.
        
        Args:
            video_path: Path to the background video
            text: Text to display as captions
            output_path: Path to save the output video
            
        Returns:
            Path to the created video
        """
        # Create a subtitle file
        subtitle_path = os.path.join(self.temp_dir, "subtitle.srt")
        self.create_subtitle_file(text, self.duration, subtitle_path)
        
        # Prepare ffmpeg command
        command = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-ss", "0",
            "-t", str(self.duration),
            "-vf", self._create_subtitle_filter(subtitle_path),
            "-c:v", "libx264",
            "-c:a", "aac",
            "-strict", "experimental",
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
    
    def _create_subtitle_filter(self, subtitle_path):
        """
        Create the ffmpeg filter string for adding subtitles.
        
        Args:
            subtitle_path: Path to the subtitle file
            
        Returns:
            FFmpeg filter string
        """
        # Base filter with subtitles
        filter_str = f"subtitles={subtitle_path}"
        
        # Add styling if font file is provided
        if self.font_file and os.path.exists(self.font_file):
            filter_str += f":force_style='FontName={self.font_file},FontSize={self.font_size},PrimaryColour={self.font_color},BackColour={self.bg_color},Alignment=10'"
        else:
            filter_str += f":force_style='FontSize={self.font_size},PrimaryColour={self.font_color},BackColour={self.bg_color},Alignment=10'"
        
        return filter_str
    
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
                f"{pdf_name}_page_{i + start_page}.mp4"
            )
            
            # Create the video
            result = self.create_video_with_captions(
                video_path,
                text,
                output_path
            )
            
            if result:
                output_videos.append(result)
        
        print(f"Created {len(output_videos)} videos in {self.output_dir}")
        return output_videos

def main():
    parser = argparse.ArgumentParser(description="Convert PDF books to TikTok videos with ffmpeg")
    parser.add_argument("pdf_path", help="Path to the PDF file")
    parser.add_argument("video_path", help="Path to the background video")
    parser.add_argument("--output", "-o", default="output", help="Output directory")
    parser.add_argument("--start", "-s", type=int, default=1, help="First page to process (1-indexed)")
    parser.add_argument("--end", "-e", type=int, default=None, help="Last page to process (inclusive, 1-indexed)")
    parser.add_argument("--duration", "-d", type=int, default=5, help="Duration of each video in seconds")
    parser.add_argument("--font-size", type=int, default=24, help="Font size for captions")
    parser.add_argument("--font-color", default="white", help="Font color for captions")
    parser.add_argument("--bg-color", default="black@0.7", help="Background color for caption box (with alpha)")
    parser.add_argument("--font", help="Path to a font file (optional)")
    
    args = parser.parse_args()
    
    # Create PoemTok instance
    poemtok = PoemTokFFmpeg(
        output_dir=args.output,
        duration=args.duration,
        font_size=args.font_size,
        font_color=args.font_color,
        bg_color=args.bg_color,
        font_file=args.font
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
