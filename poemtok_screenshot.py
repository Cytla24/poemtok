#!/usr/bin/env python3
"""
PoemTok Screenshot Version
-------------------------
Creates TikTok-style videos from image screenshots of book pages.
This preserves the exact formatting and appearance of the original text.
"""

import os
import sys
import argparse
import tempfile
import shutil
import subprocess
from pathlib import Path
from tqdm import tqdm
from PIL import Image, ImageOps, ImageEnhance, ImageFilter

class PoemTokScreenshot:
    def __init__(self, output_dir="output", duration=5, 
                 box_width=0.7, box_height=0.8, 
                 bg_opacity=0.8, invert_colors=True,
                 enhance_contrast=1.5):
        """
        Initialize the PoemTok screenshot converter.
        
        Args:
            output_dir: Directory to save the generated videos
            duration: Duration of each video in seconds
            box_width: Width of the text box as a fraction of video width
            box_height: Height of the text box as a fraction of video height
            bg_opacity: Opacity of the background (0-1)
            invert_colors: Whether to invert colors (black text on white -> white text on black)
            enhance_contrast: Contrast enhancement factor
        """
        self.output_dir = output_dir
        self.duration = duration
        self.box_width = box_width
        self.box_height = box_height
        self.bg_opacity = bg_opacity
        self.invert_colors = invert_colors
        self.enhance_contrast = enhance_contrast
        self.temp_dir = tempfile.mkdtemp()
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
    
    def __del__(self):
        """Clean up temporary files when the object is destroyed."""
        try:
            shutil.rmtree(self.temp_dir)
        except:
            pass
    
    def process_image(self, image_path):
        """
        Process an image to create a clean text overlay.
        
        Args:
            image_path: Path to the image
            
        Returns:
            Path to the processed image
        """
        print(f"Processing image: {image_path}")
        
        # Open the image
        image = Image.open(image_path)
        
        # Convert to grayscale
        gray_image = image.convert("L")
        
        # Invert colors if needed (to make text white on black)
        if self.invert_colors:
            gray_image = ImageOps.invert(gray_image)
        
        # Enhance contrast
        if self.enhance_contrast > 1.0:
            enhancer = ImageEnhance.Contrast(gray_image)
            gray_image = enhancer.enhance(self.enhance_contrast)
        
        # Create a new image with an alpha channel (RGBA)
        processed = Image.new("RGBA", gray_image.size, (0, 0, 0, 0))
        
        # Calculate alpha value for background
        bg_alpha = int(255 * self.bg_opacity)
        
        # Process the image to create white text on semi-transparent black background
        for y in range(gray_image.height):
            for x in range(gray_image.width):
                pixel = gray_image.getpixel((x, y))
                if pixel > 200:  # If the pixel is bright (text)
                    processed.putpixel((x, y), (255, 255, 255, 255))  # White, fully opaque
                elif pixel > 100:  # Mid-tones
                    alpha = int(255 * (pixel / 255.0))
                    processed.putpixel((x, y), (255, 255, 255, alpha))
                else:  # Background (dark)
                    processed.putpixel((x, y), (0, 0, 0, bg_alpha))  # Black, semi-transparent
        
        # Save the processed image
        processed_path = os.path.join(self.temp_dir, f"processed_{os.path.basename(image_path)}")
        processed.save(processed_path, "PNG")
        
        return processed_path
    
    def create_video_with_image(self, video_path, image_path, output_path):
        """
        Create a video with an image overlay using ffmpeg.
        
        Args:
            video_path: Path to the background video
            image_path: Path to the image to overlay
            output_path: Path to save the output video
            
        Returns:
            Path to the created video
        """
        print(f"Creating video with image overlay...")
        
        # Get image dimensions
        with Image.open(image_path) as img:
            img_width, img_height = img.size
        
        # Calculate scaling to fit within desired box
        scale_factor = min(self.box_width, self.box_height)
        
        # Use ffmpeg to overlay the image on the video
        command = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", image_path,
            "-filter_complex", (
                f"[0:v]trim=0:{self.duration},setpts=PTS-STARTPTS[bg];"
                f"[1:v]scale=iw*{scale_factor}:-1[scaled];"
                f"[bg][scaled]overlay=(W-w)/2:(H-h)/2:shortest=1[out]"
            ),
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
    
    def process_images(self, image_paths, video_path):
        """
        Process multiple images and create videos for each.
        
        Args:
            image_paths: List of paths to images
            video_path: Path to the background video
            
        Returns:
            List of paths to the created videos
        """
        # Process each image
        processed_images = []
        for image_path in tqdm(image_paths, desc="Processing images"):
            processed = self.process_image(image_path)
            processed_images.append(processed)
        
        # Create a video for each processed image
        output_videos = []
        
        for i, image_path in enumerate(tqdm(processed_images, desc="Creating videos")):
            # Define output path
            base_name = os.path.splitext(os.path.basename(image_path))[0]
            output_path = os.path.join(
                self.output_dir,
                f"{base_name}_video.mp4"
            )
            
            # Create the video
            result = self.create_video_with_image(
                video_path,
                image_path,
                output_path
            )
            
            if result:
                output_videos.append(result)
        
        print(f"Created {len(output_videos)} videos in {self.output_dir}")
        return output_videos

def main():
    parser = argparse.ArgumentParser(description="Convert image screenshots to TikTok videos")
    parser.add_argument("images", nargs="+", help="Paths to image files")
    parser.add_argument("video_path", help="Path to the background video")
    parser.add_argument("--output", "-o", default="output", help="Output directory")
    parser.add_argument("--duration", "-d", type=int, default=5, help="Duration of each video in seconds")
    parser.add_argument("--box-width", type=float, default=0.7, help="Width of text box as fraction of video width")
    parser.add_argument("--box-height", type=float, default=0.8, help="Height of text box as fraction of video height")
    parser.add_argument("--bg-opacity", type=float, default=0.8, help="Opacity of the background (0-1)")
    parser.add_argument("--no-invert", action="store_true", help="Don't invert colors (keep original colors)")
    parser.add_argument("--contrast", type=float, default=1.5, help="Contrast enhancement factor")
    
    args = parser.parse_args()
    
    # Create PoemTok instance
    poemtok = PoemTokScreenshot(
        output_dir=args.output,
        duration=args.duration,
        box_width=args.box_width,
        box_height=args.box_height,
        bg_opacity=args.bg_opacity,
        invert_colors=not args.no_invert,
        enhance_contrast=args.contrast
    )
    
    # Process the images
    poemtok.process_images(args.images, args.video_path)

if __name__ == "__main__":
    main()
