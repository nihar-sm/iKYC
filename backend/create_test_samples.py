from PIL import Image, ImageDraw, ImageFont
import os

def create_mock_aadhaar(filename: str):
    """Create a mock Aadhaar document for testing"""
    # Create image
    img = Image.new('RGB', (800, 500), color='white')
    draw = ImageDraw.Draw(img)
    
    # Try to use a font, fallback to default
    try:
        font = ImageFont.truetype("arial.ttf", 20)
        small_font = ImageFont.truetype("arial.ttf", 16)
    except:
        font = ImageFont.load_default()
        small_font = font
    
    # Add mock content
    draw.text((50, 50), "Government of India", fill='black', font=font)
    draw.text((50, 80), "Aadhaar", fill='blue', font=font)
    draw.text((50, 150), "1234 5678 9012", fill='black', font=font)
    draw.text((50, 200), "Name: JOHN DOE", fill='black', font=font)
    draw.text((50, 230), "DOB: 01/01/1990", fill='black', font=font)
    draw.text((50, 260), "Address: 123 Main Street", fill='black', font=small_font)
    draw.text((50, 280), "City, State - 123456", fill='black', font=small_font)
    
    # Save image
    os.makedirs("test_documents/aadhaar", exist_ok=True)
    img.save(f"test_documents/aadhaar/{filename}")
    print(f"Created mock Aadhaar: {filename}")

def create_mock_pan(filename: str):
    """Create a mock PAN document for testing"""
    img = Image.new('RGB', (600, 400), color='lightblue')
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("arial.ttf", 18)
    except:
        font = ImageFont.load_default()
    
    draw.text((50, 50), "Income Tax Department", fill='black', font=font)
    draw.text((50, 80), "Permanent Account Number Card", fill='black', font=font)
    draw.text((50, 150), "ABCDE1234F", fill='black', font=font)
    draw.text((50, 200), "JOHN DOE", fill='black', font=font)
    draw.text((50, 230), "01/01/1990", fill='black', font=font)
    
    os.makedirs("test_documents/pan", exist_ok=True)
    img.save(f"test_documents/pan/{filename}")
    print(f"Created mock PAN: {filename}")

if __name__ == "__main__":
    # Create sample documents
    create_mock_aadhaar("sample_aadhaar_1.png")
    create_mock_aadhaar("sample_aadhaar_2.png")
    create_mock_pan("sample_pan_1.png")
    create_mock_pan("sample_pan_2.png")
    
    print("✅ Test documents created successfully!")
