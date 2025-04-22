#!/usr/bin/env python3
"""
PDF Screenshot Tool
------------------
Helps take screenshots of PDF pages to use with PoemTok.
"""

import os
import sys
import argparse
import PyPDF2
from PIL import Image
import matplotlib.pyplot as plt
import matplotlib.backends.backend_pdf
from pdf2image import convert_from_path

def save_pdf_pages_as_images(pdf_path, output_dir="screenshots", start_page=1, end_page=None, dpi=300):
    """
    Save PDF pages as image files.
    
    Args:
        pdf_path: Path to the PDF file
        output_dir: Directory to save the images
        start_page: First page to process (1-indexed)
        end_page: Last page to process (inclusive, 1-indexed)
        dpi: DPI for the rendered images
    
    Returns:
        List of paths to the created images
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Get total pages
    with open(pdf_path, 'rb') as f:
        pdf_reader = PyPDF2.PdfReader(f)
        total_pages = len(pdf_reader.pages)
    
    print(f"PDF has {total_pages} pages")
    
    # Adjust page range
    start_page = max(1, start_page)
    if end_page is None or end_page > total_pages:
        end_page = total_pages
    
    try:
        # Try using pdf2image (requires poppler)
        print(f"Converting pages {start_page} to {end_page} using pdf2image...")
        images = convert_from_path(
            pdf_path,
            dpi=dpi,
            first_page=start_page,
            last_page=end_page
        )
        
        # Save images
        image_paths = []
        pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
        for i, image in enumerate(images):
            page_num = i + start_page
            image_path = os.path.join(output_dir, f"{pdf_name}_page_{page_num}.png")
            image.save(image_path, "PNG")
            image_paths.append(image_path)
            print(f"Saved {image_path}")
        
        return image_paths
    
    except Exception as e:
        print(f"Error using pdf2image: {e}")
        print("Falling back to matplotlib...")
        
        # Fallback to matplotlib
        image_paths = []
        pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
        
        for page_num in range(start_page, end_page + 1):
            try:
                # Create a figure with the same size as the PDF page
                fig = plt.figure(figsize=(8.5, 11))
                
                # Read the PDF page
                pdf = matplotlib.backends.backend_pdf.PdfPages(pdf_path)
                page = pdf.pages[page_num - 1]
                
                # Add the page to the figure
                fig.figimage(page.get_images()[0].get_array())
                
                # Save the figure as an image
                image_path = os.path.join(output_dir, f"{pdf_name}_page_{page_num}.png")
                plt.savefig(image_path, format='png', dpi=dpi)
                plt.close(fig)
                
                image_paths.append(image_path)
                print(f"Saved {image_path}")
                
            except Exception as e:
                print(f"Error processing page {page_num}: {e}")
        
        return image_paths

def main():
    parser = argparse.ArgumentParser(description="Save PDF pages as images")
    parser.add_argument("pdf_path", help="Path to the PDF file")
    parser.add_argument("--output", "-o", default="screenshots", help="Output directory")
    parser.add_argument("--start", "-s", type=int, default=1, help="First page to process (1-indexed)")
    parser.add_argument("--end", "-e", type=int, default=None, help="Last page to process (inclusive, 1-indexed)")
    parser.add_argument("--dpi", type=int, default=300, help="DPI for the rendered images")
    
    args = parser.parse_args()
    
    # Save PDF pages as images
    save_pdf_pages_as_images(
        args.pdf_path,
        output_dir=args.output,
        start_page=args.start,
        end_page=args.end,
        dpi=args.dpi
    )

if __name__ == "__main__":
    main()
