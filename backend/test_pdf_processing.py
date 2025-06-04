#!/usr/bin/env python3
"""
Test PDF Processing with Fixed GEMINI API
"""

import os
import sys
import asyncio
import tempfile
from pathlib import Path
from dotenv import load_dotenv

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.services.ocr_processor import LegalDocumentOCR

# Load environment variables
load_dotenv()

async def test_pdf_processing():
    """Test PDF processing with a simple PDF file"""
    
    print("🔍 Testing PDF Processing with GEMINI API...")
    print("=" * 50)
    
    try:
        # Initialize OCR processor
        ocr_processor = LegalDocumentOCR()
        print("✅ OCR processor initialized")
        
        # Create a minimal test PDF content
        # This is a minimal valid PDF with some text
        minimal_pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
/Resources <<
/Font <<
/F1 5 0 R
>>
>>
>>
endobj

4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
72 720 Td
(Test Document) Tj
ET
endstream
endobj

5 0 obj
<<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
endobj

xref
0 6
0000000000 65535 f 
0000000010 00000 n 
0000000053 00000 n 
0000000125 00000 n 
0000000348 00000 n 
0000000443 00000 n 
trailer
<<
/Size 6
/Root 1 0 R
>>
startxref
540
%%EOF"""
        
        # Create temporary PDF file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(minimal_pdf_content)
            temp_pdf_path = temp_file.name
        
        print(f"📄 Created test PDF: {temp_pdf_path}")
        
        try:
            # Process the PDF
            print("🔄 Processing PDF with OCR...")
            result = await ocr_processor.process_pdf_file(temp_pdf_path, "Test Document")
            
            if result["success"]:
                print("✅ PDF processing successful!")
                print(f"   Transcribed text preview: {result['transcribed_text'][:100]}...")
                print(f"   Document ID: {result['document_id']}")
                print(f"   Processing time: {result['processing_time']:.2f}s")
                
                if result.get('metadata'):
                    metadata = result['metadata']
                    print(f"   Title: {metadata.get('title', 'N/A')}")
                    print(f"   Category: {metadata.get('category', 'N/A')}")
                    print(f"   Confidence: {metadata.get('confidence_score', 0.0)}")
                
                return True
            else:
                print(f"❌ PDF processing failed: {result.get('error', 'Unknown error')}")
                return False
                
        finally:
            # Clean up temporary file
            if os.path.exists(temp_pdf_path):
                os.unlink(temp_pdf_path)
                print(f"🗑️  Cleaned up test file")
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        return False

async def main():
    """Main test routine"""
    print("🚀 PDF Processing Test with GEMINI API")
    print("=" * 50)
    
    success = await test_pdf_processing()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 PDF processing test PASSED!")
        print("✨ Your system can successfully process PDF files with OCR.")
    else:
        print("❌ PDF processing test FAILED!")
        print("⚠️  Please check the error messages above.")
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 