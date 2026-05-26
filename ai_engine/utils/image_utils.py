"""
Image processing utilities for document analysis
"""

import cv2
import numpy as np
from PIL import Image
import base64
import io
from typing import Dict, Tuple, Optional

class ImageProcessor:
    """Image processing utilities for document images"""
    
    @staticmethod
    def preprocess_document_image(image_data: bytes) -> Dict:
        """
        Preprocess document image for better OCR results
        
        Args:
            image_data: Raw image bytes
            
        Returns:
            Dict: Processed image data and quality metrics
        """
        try:
            # Convert bytes to PIL Image
            pil_image = Image.open(io.BytesIO(image_data))
            
            # Convert to RGB if needed
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')
            
            # Convert to OpenCV format
            cv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            
            # Image quality analysis
            quality_metrics = ImageProcessor._analyze_image_quality(cv_image)
            
            # Apply preprocessing based on quality
            processed_image = ImageProcessor._enhance_image(cv_image, quality_metrics)
            
            # Convert back to bytes
            _, buffer = cv2.imencode('.jpg', processed_image)
            processed_bytes = buffer.tobytes()
            
            return {
                'success': True,
                'processed_image': processed_bytes,
                'original_size': pil_image.size,
                'quality_metrics': quality_metrics,
                'preprocessing_applied': True
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Image preprocessing failed: {str(e)}",
                'preprocessing_applied': False
            }
    
    @staticmethod
    def _analyze_image_quality(image: np.ndarray) -> Dict:
        """Analyze image quality metrics"""
        
        # Convert to grayscale for analysis
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Calculate blur metric (Laplacian variance)
        blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        # Calculate brightness
        brightness = np.mean(gray)
        
        # Calculate contrast
        contrast = gray.std()
        
        # Determine overall quality
        quality_score = 1.0
        issues = []
        
        if blur_score < 100:
            quality_score -= 0.3
            issues.append('blurry')
        
        if brightness < 50 or brightness > 200:
            quality_score -= 0.2
            issues.append('poor_lighting')
        
        if contrast < 30:
            quality_score -= 0.2
            issues.append('low_contrast')
        
        return {
            'quality_score': max(0.0, quality_score),
            'blur_score': blur_score,
            'brightness': brightness,
            'contrast': contrast,
            'issues': issues,
            'is_acceptable': quality_score > 0.5
        }
    
    @staticmethod
    def _enhance_image(image: np.ndarray, quality_metrics: Dict) -> np.ndarray:
        """Apply image enhancements based on quality analysis"""
        
        enhanced = image.copy()
        
        # Enhance contrast if needed
        if quality_metrics['contrast'] < 30:
            enhanced = cv2.convertScaleAbs(enhanced, alpha=1.2, beta=10)
        
        # Adjust brightness if needed
        if quality_metrics['brightness'] < 50:
            enhanced = cv2.convertScaleAbs(enhanced, alpha=1.0, beta=30)
        elif quality_metrics['brightness'] > 200:
            enhanced = cv2.convertScaleAbs(enhanced, alpha=1.0, beta=-30)
        
        # Apply denoising if blurry
        if quality_metrics['blur_score'] < 100:
            enhanced = cv2.fastNlMeansDenoisingColored(enhanced)
        
        return enhanced
    
    @staticmethod
    def extract_document_regions(image_data: bytes) -> Dict:
        """Extract key regions from document image"""
        
        try:
            # Convert to OpenCV format
            pil_image = Image.open(io.BytesIO(image_data))
            cv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            
            # Convert to grayscale
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            
            # Apply edge detection
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)
            
            # Find contours
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Extract regions
            regions = []
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                if w > 50 and h > 20:  # Filter small regions
                    region = {
                        'x': x, 'y': y, 'width': w, 'height': h,
                        'area': w * h
                    }
                    regions.append(region)
            
            # Sort by area (largest first)
            regions.sort(key=lambda r: r['area'], reverse=True)
            
            return {
                'success': True,
                'regions': regions[:10],  # Top 10 regions
                'total_regions': len(regions)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Region extraction failed: {str(e)}"
            }
    
    @staticmethod
    def detect_tampering_signs(image_data: bytes) -> Dict:
        """Detect potential tampering in document image"""
        
        try:
            # Convert to OpenCV format
            pil_image = Image.open(io.BytesIO(image_data))
            cv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            
            tampering_indicators = {
                'inconsistent_lighting': False,
                'irregular_edges': False,
                'compression_artifacts': False,
                'copy_paste_signs': False
            }
            
            # Check for inconsistent lighting
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            lighting_variance = np.var(gray)
            if lighting_variance > 5000:
                tampering_indicators['inconsistent_lighting'] = True
            
            # Check for irregular edges
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.sum(edges > 0) / (edges.shape[0] * edges.shape[1])
            if edge_density > 0.15:
                tampering_indicators['irregular_edges'] = True
            
            # Calculate tampering score
            tampering_score = sum(tampering_indicators.values()) / len(tampering_indicators)
            
            return {
                'success': True,
                'tampering_score': tampering_score,
                'indicators': tampering_indicators,
                'is_likely_tampered': tampering_score > 0.3
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Tampering detection failed: {str(e)}"
            }
