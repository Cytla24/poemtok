#!/usr/bin/env python3
"""
PoemTok Example
--------------
This script demonstrates how to use PoemTok with a sample PDF and video.
It creates a simple PDF with a poem and uses it to generate a TikTok-style video.
"""

import os
import tempfile
from fpdf import FPDF
from text_styler import TextStyler
import subprocess

def create_sample_pdf(output_path):
    """Create a sample PDF with a poem."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    
    # Add a title
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(200, 10, "Sample Poem", ln=True, align="C")
    pdf.ln(10)
    
    # Add the poem text
    pdf.set_font("Helvetica", size=12)
    poem = """someone must have snuck in to the
chambers of our hearts in the middle of
the night and switched out the puzzle
pieces that connected our souls in this
perfect piece because at dawn we wake
and discover that we are no longer
compatible"""
    
    for line in poem.split('\n'):
        pdf.cell(200, 10, line, ln=True, align="C")
    
    # Save the PDF
    pdf.output(output_path)
    print(f"Sample PDF created at: {output_path}")
    return output_path

def create_sample_video(output_path, duration=15):
    """Create a simple background video using ffmpeg."""
    # Create a solid color video
    command = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", "color=c=gray:s=1080x1920:d=15",
        "-vf", "format=yuv420p",
        output_path
    ]
    
    try:
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"Sample video created at: {output_path}")
        return output_path
    except subprocess.CalledProcessError as e:
        print(f"Error creating sample video: {e}")
        return None

def main():
    # Create temporary directory for samples
    temp_dir = tempfile.mkdtemp()
    
    # Create sample PDF
    pdf_path = os.path.join(temp_dir, "sample_poem.pdf")
    create_sample_pdf(pdf_path)
    
    # Create sample video
    video_path = os.path.join(temp_dir, "sample_background.mp4")
    create_sample_video(video_path)
    
    # Run PoemTok
    output_dir = os.path.join(os.getcwd(), "example_output")
    os.makedirs(output_dir, exist_ok=True)
    
    command = [
        "python", "poemtok.py",
        pdf_path,
        video_path,
        "--output", output_dir,
        "--duration", "10",
        "--minimalist"
    ]
    
    print("Running PoemTok with sample files...")
    subprocess.run(command)
    
    print(f"\nExample complete! Output videos are in: {output_dir}")
    print("You can now run PoemTok with your own PDF and video files.")

if __name__ == "__main__":
    main()
