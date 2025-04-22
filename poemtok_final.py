#!/usr/bin/env python3
"""
PoemTok Final Version
-------------------
Creates TikTok-style videos with white text on a semi-transparent black background,
exactly like the processed_sc_video.mp4 but with customizable text size.
"""

import os
import sys
import argparse
import subprocess
import tempfile
from PIL import Image, ImageOps, ImageEnhance, ImageFilter

def process_image(image_path, output_path=None, bg_opacity=0.8, contrast=2.0):
    """
    Process an image to have white text on a semi-transparent black background.
    
    Args:
        image_path: Path to the input image
        output_path: Path to save the processed image (if None, uses a temp file)
        bg_opacity: Opacity of the background (0-1)
        contrast: Contrast enhancement factor
        
    Returns:
        Path to the processed image
    """
    print(f"Processing image to create white text on semi-transparent background...")
    
    # Open the image
    image = Image.open(image_path)
    
    # Convert to grayscale
    gray_image = image.convert("L")
    
    # Invert colors to make text white on black
    inverted = ImageOps.invert(gray_image)
    
    # Enhance contrast to make text stand out
    enhancer = ImageEnhance.Contrast(inverted)
    high_contrast = enhancer.enhance(contrast)
    
    # Create a new image with an alpha channel (RGBA)
    processed = Image.new("RGBA", high_contrast.size, (0, 0, 0, 0))
    
    # Calculate alpha value for background
    bg_alpha = int(255 * bg_opacity)
    
    # Process the image to create white text on semi-transparent black background
    for y in range(high_contrast.height):
        for x in range(high_contrast.width):
            pixel = high_contrast.getpixel((x, y))
            if pixel > 200:  # If the pixel is bright (text)
                processed.putpixel((x, y), (255, 255, 255, 255))  # White, fully opaque
            else:  # Background
                processed.putpixel((x, y), (0, 0, 0, bg_alpha))  # Black, semi-transparent
    
    # Save the processed image
    if output_path is None:
        temp_dir = tempfile.mkdtemp()
        output_path = os.path.join(temp_dir, f"processed_{os.path.basename(image_path)}")
    
    processed.save(output_path, "PNG")
    print(f"Saved processed image to {output_path}")
    
    return output_path

def create_video(image_path, video_path, output_path, duration=5, scale=0.7):
    """
    Create a video with the processed image overlay.
    
    Args:
        image_path: Path to the image
        video_path: Path to the background video
        output_path: Path to save the output video
        duration: Duration of the video in seconds
        scale: Scale factor for the image (0-1)
        
    Returns:
        Path to the created video
    """
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Process the image
    processed_image = process_image(image_path)
    
    print(f"Creating video with overlay...")
    
    # Use direct method which works reliably
    command = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", processed_image,
        "-filter_complex", (
            f"[1:v]scale=iw*{scale}:-1[scaled];"
            f"[0:v][scaled]overlay=(W-w)/2:(H-h)/2:enable='between(t,0,{duration})'"
        ),
        "-c:v", "libx264",
        "-c:a", "copy",
        "-t", str(duration),
        output_path
    ]
    
    try:
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"Created video: {output_path}")
        
        # Verify the video was created properly
        verify_command = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", output_path]
        verify_result = subprocess.run(verify_command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        duration_str = verify_result.stdout.decode('utf-8').strip()
        
        try:
            actual_duration = float(duration_str)
            print(f"Video duration: {actual_duration:.2f} seconds")
        except ValueError:
            print(f"Could not verify duration: {duration_str}")
        
        return output_path
    except subprocess.CalledProcessError as e:
        print(f"Error creating video: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Create TikTok videos with white text on semi-transparent black background")
    parser.add_argument("image_path", help="Path to the image file")
    parser.add_argument("video_path", help="Path to the background video")
    parser.add_argument("--output", "-o", default="output/final_video.mp4", help="Output video path")
    parser.add_argument("--duration", "-d", type=int, default=5, help="Duration of the video in seconds")
    parser.add_argument("--scale", "-s", type=float, default=0.7, help="Scale factor for the text size (0-1)")
    parser.add_argument("--bg-opacity", "-a", type=float, default=0.8, help="Opacity of the background (0-1)")
    parser.add_argument("--contrast", "-c", type=float, default=2.0, help="Contrast enhancement factor")
    
    args = parser.parse_args()
    
    # Create the video
    create_video(
        args.image_path,
        args.video_path,
        args.output,
        duration=args.duration,
        scale=args.scale
    )

if __name__ == "__main__":
    main()
