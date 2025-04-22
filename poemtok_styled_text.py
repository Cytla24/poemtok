#!/usr/bin/env python3
"""
PoemTok Styled Text
------------------
Creates TikTok-style videos from screenshots with white text on a 
semi-transparent black background.
"""

import os
import sys
import argparse
import subprocess
import tempfile
from PIL import Image, ImageOps, ImageEnhance, ImageFilter

def process_image_to_white_text(image_path, output_path=None, 
                               bg_opacity=0.7, contrast=2.0, threshold=180):
    """
    Process an image to have white text on a semi-transparent black background.
    
    Args:
        image_path: Path to the input image
        output_path: Path to save the processed image (if None, uses a temp file)
        bg_opacity: Opacity of the background (0-1)
        contrast: Contrast enhancement factor
        threshold: Threshold for text detection (0-255)
        
    Returns:
        Path to the processed image
    """
    print(f"Processing image to create white text on semi-transparent background...")
    
    # Open the image
    image = Image.open(image_path)
    
    # Convert to grayscale
    gray_image = image.convert("L")
    
    # Enhance contrast to make text stand out
    enhancer = ImageEnhance.Contrast(gray_image)
    high_contrast = enhancer.enhance(contrast)
    
    # Create a new image with an alpha channel (RGBA)
    processed = Image.new("RGBA", high_contrast.size, (0, 0, 0, 0))
    
    # Calculate alpha value for background
    bg_alpha = int(255 * bg_opacity)
    
    # Process the image to create white text on semi-transparent black background
    for y in range(high_contrast.height):
        for x in range(high_contrast.width):
            pixel = high_contrast.getpixel((x, y))
            if pixel > threshold:  # If the pixel is bright (text)
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

def create_video_with_styled_text(image_path, video_path, output_path, 
                                 duration=5, scale=0.6, bg_opacity=0.7, 
                                 contrast=2.0, threshold=180):
    """
    Create a video with styled text overlay (white text on semi-transparent black).
    
    Args:
        image_path: Path to the image
        video_path: Path to the background video
        output_path: Path to save the output video
        duration: Duration of the video in seconds
        scale: Scale factor for the image (0-1)
        bg_opacity: Opacity of the background (0-1)
        contrast: Contrast enhancement factor
        threshold: Threshold for text detection (0-255)
        
    Returns:
        Path to the created video
    """
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Process the image to have white text on semi-transparent black background
    processed_image = process_image_to_white_text(
        image_path, 
        bg_opacity=bg_opacity,
        contrast=contrast,
        threshold=threshold
    )
    
    # Create the video using ffmpeg
    print(f"Creating video with styled text overlay...")
    
    command = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", processed_image,
        "-filter_complex", (
            f"[0:v]trim=0:{duration},setpts=PTS-STARTPTS[bg];"
            f"[1:v]scale=iw*{scale}:-1[scaled];"
            f"[bg][scaled]overlay=(W-w)/2:(H-h)/2:shortest=1[out]"
        ),
        "-map", "[out]",
        "-map", "0:a?",  # Include audio if available
        "-c:v", "libx264",
        "-c:a", "aac",   # Audio codec
        "-shortest",     # End when shortest input ends
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
            # Try alternative method if needed
            return create_video_direct(processed_image, video_path, output_path, duration, scale)
        
        return output_path
    except subprocess.CalledProcessError as e:
        print(f"Error creating video: {e}")
        # Try alternative method
        return create_video_direct(processed_image, video_path, output_path, duration, scale)

def create_video_direct(image_path, video_path, output_path, duration=5, scale=0.6):
    """
    Direct method to create a video with an image overlay.
    
    Args:
        image_path: Path to the image
        video_path: Path to the background video
        output_path: Path to save the output video
        duration: Duration of the video in seconds
        scale: Scale factor for the image (0-1)
        
    Returns:
        Path to the created video
    """
    print(f"Using direct method...")
    
    # Simple overlay without complex filters
    command = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", image_path,
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
        print(f"Created video using direct method: {output_path}")
        return output_path
    except subprocess.CalledProcessError as e:
        print(f"Error with direct method: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Create videos with styled text (white on semi-transparent black)")
    parser.add_argument("image_path", help="Path to the image file")
    parser.add_argument("video_path", help="Path to the background video")
    parser.add_argument("--output", "-o", default="output/styled_text.mp4", help="Output video path")
    parser.add_argument("--duration", "-d", type=int, default=5, help="Duration of the video in seconds")
    parser.add_argument("--scale", "-s", type=float, default=0.6, help="Scale factor for the image (0-1)")
    parser.add_argument("--bg-opacity", "-a", type=float, default=0.7, help="Opacity of the background (0-1)")
    parser.add_argument("--contrast", "-c", type=float, default=2.0, help="Contrast enhancement factor")
    parser.add_argument("--threshold", "-t", type=int, default=180, help="Threshold for text detection (0-255)")
    
    args = parser.parse_args()
    
    # Create the video with styled text
    create_video_with_styled_text(
        args.image_path,
        args.video_path,
        args.output,
        duration=args.duration,
        scale=args.scale,
        bg_opacity=args.bg_opacity,
        contrast=args.contrast,
        threshold=args.threshold
    )

if __name__ == "__main__":
    main()
