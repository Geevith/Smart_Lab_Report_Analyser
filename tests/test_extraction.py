import unittest
from backend.extractor import extract_text, extract_from_pdf, extract_from_image
import os

class TestExtraction(unittest.TestCase):
    def test_unsupported_format(self):
        result = extract_text("test.txt")
        self.assertEqual(result, "Unsupported file format.")
        
    def test_pdf_extraction_no_file(self):
        # Should return empty string and print error (captured if we want, but simple check is enough)
        result = extract_from_pdf("non_existent.pdf")
        self.assertEqual(result, "")

    def test_image_extraction_no_file(self):
         result = extract_from_image("non_existent.png")
         self.assertEqual(result, "")

if __name__ == '__main__':
    unittest.main()
