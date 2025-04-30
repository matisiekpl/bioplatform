import cv2
import os
import tempfile
from PIL import Image
import numpy as np

def detect_cells_from_image(image_file):
    """
    Analyzes an image to count the number of cells
    
    Args:
        image_file: Django ImageField file object
    
    Returns:
        int: The number of detected cells
    """
    # Create a temporary file to work with OpenCV
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
        temp_path = temp_file.name
        # Save the uploaded image to temp file
        with Image.open(image_file) as img:
            img.save(temp_path)
        
        # Process image with OpenCV
        img = cv2.imread(temp_path)
        if img is None:
            os.unlink(temp_path)
            return 0
            
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply thresholding
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Count cells based on contours
        cell_count = 0
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
                        cell_count += 1
                except Exception:
                    continue
        
        # Clean up the temporary file
        os.unlink(temp_path)
        
        return cell_count 