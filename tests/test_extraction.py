import unittest
from backend.extractor import extract_text, extract_from_pdf, extract_from_image
import os

class TestExtraction(unittest.TestCase):
    def test_unsupported_format(self):
        result = extract_text("test.txt")
        self.assertEqual(result, "Unsupported file format.")
        
    def test_pdf_extraction_no_file(self):
        # Should return text key with empty string
        result = extract_from_pdf("non_existent.pdf")
        self.assertEqual(result.get('text'), "")

    def test_image_extraction_no_file(self):
         result = extract_from_image("non_existent.png")
         self.assertEqual(result.get('text'), "")

if __name__ == '__main__':
    unittest.main()
