import cv2
import numpy as np

def is_microscopic(image_path):
    try:
        img = cv2.imread(image_path)

        if img is None:
            return False, "Image not readable"

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Texture variation (microscopic images tend to have moderate variance)
        variance = np.var(gray)

        # Edge density (microscopic images often have dense fine structures)
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges) / edges.size

        # Heuristic thresholds (safe starting values)
        if 500 < variance < 5000 and edge_density > 0.03:
            return True, "Microscopic image detected"
        else:
            return False, "Image may not be microscopic"

    except Exception as e:
        return False, f"Error: {str(e)}"
