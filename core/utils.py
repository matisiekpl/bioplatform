import cv2
import os
import tempfile
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
from django.conf import settings

def extract_cells(image_file):
    """
    Analyzes an image to detect cells and returns count and processed images
    
    Args:
        image_file: Django ImageField file object
    
    Returns:
        tuple: (cell_count, original_img_path, contours_img_path)
    """
    # Create temporary files to work with OpenCV
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
        temp_path = temp_file.name
        # Save the uploaded image to temp file
        with Image.open(image_file) as img:
            img.save(temp_path)
        
        # Process image with OpenCV
        img = cv2.imread(temp_path)
        if img is None:
            os.unlink(temp_path)
            return 0, None, None
            
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply thresholding
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Draw contours on the original image
        img_contours = img.copy()
        cv2.drawContours(img_contours, contours, -1, (0, 255, 0), 2)
        
        # Find centroids and count cells
        centroids = []
        for contour in contours:
            M = cv2.moments(contour)
            if M["m00"] != 0:
                cX = int(M["m10"] / M["m00"])
                cY = int(M["m01"] / M["m00"])
                
                try:
                    # Check for cell-like properties in surrounding pixels
                    if (cY-10 >= 0 and cX-10 >= 0 and 
                        cY+10 < thresh.shape[0] and cX+10 < thresh.shape[1] and
                        thresh[cY-10, cX-10] > 0 and thresh[cY+10, cX+10] > 0 and 
                        thresh[cY-10, cX+10] > 0 and thresh[cY+10, cX-10] > 0):
                        centroids.append((cX, cY))
                        cv2.circle(img_contours, (cX, cY), 10, (255, 0, 0), -1)
                except Exception:
                    continue
        
        # Save the processed images to media directory
        media_dir = os.path.join(settings.MEDIA_ROOT, 'analysis')
        os.makedirs(media_dir, exist_ok=True)
        
        # Generate unique filenames based on timestamp
        import time
        timestamp = int(time.time())
        
        # Save original image with contours
        contours_filename = f'contours_{timestamp}.png'
        contours_path = os.path.join(media_dir, contours_filename)
        cv2.imwrite(contours_path, cv2.cvtColor(img_contours, cv2.COLOR_BGR2RGB))
        
        # Save original image 
        original_filename = f'original_{timestamp}.png'
        original_path = os.path.join(media_dir, original_filename)
        cv2.imwrite(original_path, cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        
        # Clean up the temporary file
        os.unlink(temp_path)
        
        # Return the count of cells and paths to images (relative to MEDIA_URL)
        return (
            len(centroids), 
            f'analysis/{original_filename}',
            f'analysis/{contours_filename}'
        )
