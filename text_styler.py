#!/usr/bin/env python3
"""
Text Styler for PoemTok
-----------------------
This module provides functionality to style text overlays for PoemTok videos,
allowing customization of fonts, colors, and text positioning.
"""

import os
import sys
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import cv2

class TextStyler:
    def __init__(self, resolution=(1080, 1920)):
        """
        Initialize the text styler.
        
        Args:
            resolution: Output video resolution (width, height)
        """
        self.resolution = resolution
        self.default_font = None
        self.default_font_size = 36
        self.default_color = (255, 255, 255, 255)  # White with full opacity
        self.default_bg_color = (0, 0, 0, 160)     # Black with 160/255 opacity
        self.default_padding = 40
        
        # Try to load a nice default font
        try:
            # Try to find a suitable font on the system
            font_paths = [
                # macOS fonts
                "/System/Library/Fonts/Supplemental/Didot.ttc",
                "/Library/Fonts/Georgia.ttf",
                "/System/Library/Fonts/Supplemental/Baskerville.ttc",
                # Linux fonts
                "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
                # Windows fonts
                "C:\\Windows\\Fonts\\georgia.ttf",
                "C:\\Windows\\Fonts\\times.ttf",
            ]
            
            for path in font_paths:
                if os.path.exists(path):
                    self.default_font = path
                    break
        except:
            pass
    
    def create_styled_overlay(self, text, style=None):
        """
        Create a styled text overlay.
        
        Args:
            text: Text to display
            style: Dictionary with styling options:
                - font_path: Path to font file
                - font_size: Font size
                - text_color: Text color as (R, G, B, A)
                - bg_color: Background color as (R, G, B, A)
                - padding: Padding around text
                - position: Position of text block ('center', 'top', 'bottom')
                - alignment: Text alignment ('left', 'center', 'right')
                
        Returns:
            PIL Image with styled text overlay
        """
        # Create a transparent image
        overlay = Image.new('RGBA', self.resolution, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Apply default style if none provided
        if style is None:
            style = {}
        
        # Get styling options
        font_path = style.get('font_path', self.default_font)
        font_size = style.get('font_size', self.default_font_size)
        text_color = style.get('text_color', self.default_color)
        bg_color = style.get('bg_color', self.default_bg_color)
        padding = style.get('padding', self.default_padding)
        position = style.get('position', 'center')
        alignment = style.get('alignment', 'center')
        
        # Load font
        try:
            if font_path:
                font = ImageFont.truetype(font_path, font_size)
            else:
                font = ImageFont.load_default()
        except:
            font = ImageFont.load_default()
        
        # Calculate text size
        lines = text.strip().split('\n')
        line_sizes = [draw.textsize(line, font=font) for line in lines]
        text_width = max(size[0] for size in line_sizes)
        text_height = sum(size[1] for size in line_sizes)
        
        # Calculate text position
        if position == 'top':
            pos_y = padding
        elif position == 'bottom':
            pos_y = self.resolution[1] - text_height - padding
        else:  # center
            pos_y = (self.resolution[1] - text_height) // 2
        
        # Draw background
        bg_width = text_width + padding * 2
        bg_height = text_height + padding * 2
        bg_x = (self.resolution[0] - bg_width) // 2
        
        draw.rectangle(
            [bg_x, pos_y - padding, bg_x + bg_width, pos_y + text_height + padding],
            fill=bg_color
        )
        
        # Draw text
        current_y = pos_y
        for i, line in enumerate(lines):
            line_width, line_height = line_sizes[i]
            
            if alignment == 'left':
                line_x = bg_x + padding
            elif alignment == 'right':
                line_x = bg_x + bg_width - padding - line_width
            else:  # center
                line_x = bg_x + (bg_width - line_width) // 2
            
            draw.text((line_x, current_y), line, font=font, fill=text_color)
            current_y += line_height
        
        return overlay
    
    def create_minimalist_overlay(self, text, style=None):
        """
        Create a minimalist text overlay similar to the mockup.
        
        Args:
            text: Text to display
            style: Dictionary with styling options (see create_styled_overlay)
                
        Returns:
            PIL Image with styled text overlay
        """
        # Default minimalist style
        minimalist_style = {
            'font_size': 48,
            'text_color': (255, 255, 255, 255),  # White
            'bg_color': (0, 0, 0, 200),          # Dark background
            'padding': 60,
            'position': 'center',
            'alignment': 'center'
        }
        
        # Update with provided style
        if style:
            minimalist_style.update(style)
        
        return self.create_styled_overlay(text, minimalist_style)
    
    def extract_text_from_pdf_page(self, page_image):
        """
        Attempt to extract text from a PDF page image.
        Requires pytesseract to be installed.
        
        Args:
            page_image: PIL Image of a PDF page
            
        Returns:
            Extracted text as string
        """
        try:
            import pytesseract
            return pytesseract.image_to_string(page_image)
        except:
            return "Text extraction failed. Please install pytesseract."
    
    def apply_overlay_to_image(self, background_image, text_overlay):
        """
        Apply a text overlay to a background image.
        
        Args:
            background_image: PIL Image of the background
            text_overlay: PIL Image of the text overlay
            
        Returns:
            PIL Image with overlay applied
        """
        # Resize background to match resolution if needed
        if background_image.size != self.resolution:
            background_image = background_image.resize(self.resolution, Image.LANCZOS)
        
        # Composite the images
        result = Image.alpha_composite(
            background_image.convert('RGBA'),
            text_overlay
        )
        
        return result

# Example usage
if __name__ == "__main__":
    # Create a sample overlay
    styler = TextStyler()
    
    sample_text = """someone must have snuck in to the
chambers of our hearts in the middle of
the night and switched out the puzzle
pieces that connected our souls in this
perfect piece because at dawn we wake
and discover that we are no longer
compatible"""
    
    overlay = styler.create_minimalist_overlay(sample_text)
    
    # Save the overlay
    overlay.save("sample_overlay.png")
    print("Sample overlay saved as sample_overlay.png")
