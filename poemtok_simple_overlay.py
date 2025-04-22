#!/usr/bin/env python3
"""
PoemTok Simple Overlay
---------------------
A simplified version that directly overlays an image on a video without
complex image processing. This should be more reliable.
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

def create_video_with_overlay(image_path, video_path, output_path, 
                              duration=5, scale=0.7, opacity=0.9):
    """
    Create a video with a simple image overlay using ffmpeg.
    
    Args:
        image_path: Path to the image
        video_path: Path to the background video
        output_path: Path to save the output video
        duration: Duration of the video in seconds
        scale: Scale factor for the image (0-1)
        opacity: Opacity of the image overlay (0-1)
        
    Returns:
        Path to the created video
    """
    print(f"Creating video with simple overlay...")
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Use ffmpeg to overlay the image on the video
    command = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", image_path,
        "-filter_complex", (
            f"[0:v]trim=0:{duration},setpts=PTS-STARTPTS[bg];"
            f"[1:v]scale=iw*{scale}:-1,format=rgba,colorchannelmixer=aa={opacity}[overlay];"
            f"[bg][overlay]overlay=(W-w)/2:(H-h)/2:shortest=1[out]"
        ),
        "-map", "[out]",
        "-c:v", "libx264",
        "-preset", "fast",
        "-t", str(duration),
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

def main():
    parser = argparse.ArgumentParser(description="Create a video with a simple image overlay")
    parser.add_argument("image_path", help="Path to the image file")
    parser.add_argument("video_path", help="Path to the background video")
    parser.add_argument("--output", "-o", default="output/output.mp4", help="Output video path")
    parser.add_argument("--duration", "-d", type=int, default=5, help="Duration of the video in seconds")
    parser.add_argument("--scale", "-s", type=float, default=0.7, help="Scale factor for the image (0-1)")
    parser.add_argument("--opacity", "-a", type=float, default=0.9, help="Opacity of the image overlay (0-1)")
    
    args = parser.parse_args()
    
    # Create the video
    create_video_with_overlay(
        args.image_path,
        args.video_path,
        args.output,
        duration=args.duration,
        scale=args.scale,
        opacity=args.opacity
    )

if __name__ == "__main__":
    main()
