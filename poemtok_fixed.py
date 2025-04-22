#!/usr/bin/env python3
"""
PoemTok Fixed Version
-------------------
A fixed version that properly handles video duration and audio.
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

def create_video_with_overlay(image_path, video_path, output_path, 
                              duration=5, scale=0.7, opacity=0.9):
    """
    Create a video with an image overlay using ffmpeg.
    
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
    print(f"Creating video with overlay...")
    
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
            f"[bg][overlay]overlay=(W-w)/2:(H-h)/2:shortest=1[outv]"
        ),
        "-map", "[outv]",
        "-map", "0:a?",  # Include audio if available
        "-c:v", "libx264",
        "-c:a", "aac",   # Audio codec
        "-shortest",     # End when shortest input ends
        "-t", str(duration),
        output_path
    ]
    
    # Run the command
    try:
        result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"Created video: {output_path}")
        
        # Verify the video was created properly
        verify_command = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", output_path]
        verify_result = subprocess.run(verify_command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        duration_str = verify_result.stdout.decode('utf-8').strip()
        
        try:
            actual_duration = float(duration_str)
            print(f"Video duration: {actual_duration:.2f} seconds")
            
            if actual_duration < 0.1:
                print("WARNING: Video appears to have no duration. Trying alternative method...")
                return create_video_alternative(image_path, video_path, output_path, duration, scale, opacity)
            
        except ValueError:
            print(f"Could not verify duration: {duration_str}")
            return create_video_alternative(image_path, video_path, output_path, duration, scale, opacity)
        
        return output_path
    except subprocess.CalledProcessError as e:
        print(f"Error creating video: {e}")
        print("Trying alternative method...")
        return create_video_alternative(image_path, video_path, output_path, duration, scale, opacity)

def create_video_alternative(image_path, video_path, output_path, 
                            duration=5, scale=0.7, opacity=0.9):
    """
    Alternative method to create a video with an image overlay.
    
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
    print(f"Using alternative method...")
    
    # First, create a video from the image
    temp_image_video = output_path + ".temp_image.mp4"
    image_command = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", image_path,
        "-c:v", "libx264",
        "-t", str(duration),
        "-pix_fmt", "yuv420p",
        "-vf", f"scale=iw*{scale}:-1",
        temp_image_video
    ]
    
    # Then, overlay it on the background video
    overlay_command = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", temp_image_video,
        "-filter_complex", (
            f"[0:v]trim=0:{duration},setpts=PTS-STARTPTS[bg];"
            f"[1:v]format=rgba,colorchannelmixer=aa={opacity}[overlay];"
            f"[bg][overlay]overlay=(W-w)/2:(H-h)/2:shortest=1[outv]"
        ),
        "-map", "[outv]",
        "-map", "0:a?",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-shortest",
        "-t", str(duration),
        output_path
    ]
    
    try:
        # Create the image video
        subprocess.run(image_command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Overlay it on the background video
        subprocess.run(overlay_command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Clean up temporary file
        if os.path.exists(temp_image_video):
            os.remove(temp_image_video)
        
        print(f"Created video using alternative method: {output_path}")
        return output_path
    except subprocess.CalledProcessError as e:
        print(f"Error with alternative method: {e}")
        
        # Try one more method - direct copy with overlay
        return create_video_direct(image_path, video_path, output_path, duration, scale, opacity)

def create_video_direct(image_path, video_path, output_path, 
                       duration=5, scale=0.7, opacity=0.9):
    """
    Direct method to create a video with an image overlay.
    
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
    parser = argparse.ArgumentParser(description="Create a video with an image overlay")
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
