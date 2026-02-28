import sys
import os
import base64
from PIL import Image, ImageDraw, ImageFont

# Create a test image with medical terms that might trigger safety filters
img = Image.new('RGB', (800, 600), color='white')
d = ImageDraw.Draw(img)

text = """
CT BRAIN (PLAIN)
TECHNIQUE: Serial axial sections.
Right periorbital swelling is noted.
No acute intra/extra axial bleed noted.
Sulcal and gyral pattern appears normal.
A high attenuation ring encircles the right eyeglobe - likely scleral buckle
IMPRESSION:
No acute intra / extra axial bleed
No fractures identified.
"""
d.text((10,10), text, fill=(0,0,0))
img.save('temp/test_image.png')

import os
from dotenv import load_dotenv
load_dotenv('.env')

# Now import the extractor
# Ensure we test the actual backend extraction
from backend.extractor import _extract_text_with_gemini_vision
print("Extracting...")
text = _extract_text_with_gemini_vision('temp/test_image.png')
print("Extracted Length:", len(text))
print("Extracted Text:", text)
