#!/usr/bin/env python3
"""
PoemTok Advanced Version
-----------------------
Creates TikTok-style videos from PDF books using advanced ffmpeg text formatting
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

class PoemTokAdvanced:
    def __init__(self, output_dir="output", duration=5, font_size=24, 
                 text_color="white", box_color="black@0.7", box_width=0.6, box_height=0.4):
        """
        Initialize the PoemTok advanced converter.
        
        Args:
            output_dir: Directory to save the generated videos
            duration: Duration of each video in seconds
            font_size: Font size for the text
            text_color: Color of the text
            box_color: Color of the background box (with alpha)
            box_width: Width of box as fraction of video width
            box_height: Height of box as fraction of video height
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
    
    def create_advanced_subtitle(self, text, output_path):
        """
        Create an ASS subtitle file with advanced formatting.
        
        Args:
            text: Text to display
            output_path: Path to save the subtitle file
            
        Returns:
            Path to the created subtitle file
        """
        # ASS subtitle format header
        header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,{fontsize},&H00FFFFFF,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,0,0,2,10,10,10,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        header = header.format(fontsize=self.font_size)
        
        # Process text to preserve formatting
        lines = text.split('\n')
        
        # Create events for each line
        events = []
        for i, line in enumerate(lines):
            if line.strip():  # Skip empty lines
                # Escape special characters
                line = line.replace('\\', '\\\\').replace('{', '\\{').replace('}', '\\}')
                
                # Add the line as an event
                event = f"Dialogue: 0,0:00:00.00,0:{self.duration:02d}:00.00,Default,,0,0,0,,{line}"
                events.append(event)
        
        # Write the subtitle file
        with open(output_path, 'w') as f:
            f.write(header)
            f.write('\n'.join(events))
        
        return output_path
    
    def create_video_with_advanced_text(self, video_path, text, output_path):
        """
        Create a video with advanced text formatting using ffmpeg.
        
        Args:
            video_path: Path to the background video
            text: Text to display
            output_path: Path to save the output video
            
        Returns:
            Path to the created video
        """
        # Create an ASS subtitle file
        subtitle_path = os.path.join(self.temp_dir, "subtitle.ass")
        self.create_advanced_subtitle(text, subtitle_path)
        
        # Calculate box dimensions
        box_w = int(1080 * self.box_width)
        box_h = int(1920 * self.box_height)
        box_x = int((1080 - box_w) / 2)
        box_y = int((1920 - box_h) / 2)
        
        # Create ffmpeg command with complex filter
        command = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-vf", (
                f"drawbox=x={box_x}:y={box_y}:w={box_w}:h={box_h}:color={self.box_color}:t=fill,"
                f"subtitles='{subtitle_path}':force_style='Alignment=2,MarginV={box_h//4}'"
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
                f"{pdf_name}_page_{i + start_page}_advanced.mp4"
            )
            
            # Create the video
            result = self.create_video_with_advanced_text(
                video_path,
                text,
                output_path
            )
            
            if result:
                output_videos.append(result)
        
        print(f"Created {len(output_videos)} videos in {self.output_dir}")
        return output_videos

def main():
    parser = argparse.ArgumentParser(description="Convert PDF books to TikTok videos with advanced text formatting")
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
    
    args = parser.parse_args()
    
    # Create PoemTok instance
    poemtok = PoemTokAdvanced(
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
