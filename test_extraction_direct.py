import sys
sys.path.append('.')
from backend.extractor import extract_text_enhanced
import json

res = extract_text_enhanced('temp/test_image.png')
print(json.dumps(res, indent=2))
