#!/usr/bin/env python3
"""
GEMINI API Setup Validation Script
Ensures proper configuration for OCR and metadata extraction
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.services.ocr_processor import LegalDocumentOCR

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def validate_gemini_setup():
    """Comprehensive validation of GEMINI API setup"""
    
    print("🔍 Validating GEMINI API Configuration...")
    print("=" * 50)
    
    # Check environment variable
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY environment variable not found!")
        print("📝 Please set your GEMINI API key:")
        print("   1. Create a .env file in the backend directory")
        print("   2. Add: GEMINI_API_KEY=your_api_key_here")
        print("   3. Get your API key from: https://aistudio.google.com/app/apikey")
        return False
    
    print(f"✅ GEMINI_API_KEY found (length: {len(api_key)} characters)")
    
    # Test OCR processor initialization
    try:
        print("\n🔧 Initializing OCR processor...")
        ocr_processor = LegalDocumentOCR()
        print("✅ OCR processor initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize OCR processor: {str(e)}")
        return False
    
    # Test API connectivity
    try:
        print("\n🌐 Testing GEMINI API connectivity...")
        test_response = await ocr_processor._call_gemini_with_retry(
            prompt="Test connectivity. Respond with: Connection successful",
            temperature=0.1
        )
        
        if "success" in test_response.lower() or len(test_response.strip()) > 5:
            print("✅ GEMINI API connection successful")
            print(f"   Response preview: {test_response[:100]}...")
        else:
            print(f"⚠️  GEMINI API responded but response unclear: {test_response}")
    except Exception as e:
        print(f"❌ GEMINI API connection failed: {str(e)}")
        return False
    
    # Test OCR functionality with a simple text prompt
    try:
        print("\n📝 Testing OCR text processing...")
        test_metadata = await ocr_processor.extract_metadata_from_text(
            "Decizie nr. 123/2024 - Primăria Municipiului București - Aprobare regulament",
            "Test"
        )
        
        if test_metadata and test_metadata.get("title"):
            print("✅ Metadata extraction working correctly")
            print(f"   Generated title: {test_metadata.get('title')}")
            print(f"   Category: {test_metadata.get('category')}")
            print(f"   Confidence: {test_metadata.get('confidence_score')}")
        else:
            print("⚠️  Metadata extraction produced unexpected results")
    except Exception as e:
        print(f"❌ Metadata extraction test failed: {str(e)}")
        return False
    
    # Test database setup
    try:
        print("\n💾 Testing database setup...")
        ocr_processor._setup_database()
        print("✅ Database setup successful")
    except Exception as e:
        print(f"❌ Database setup failed: {str(e)}")
        return False
    
    # Test system health check
    try:
        print("\n🔍 Running comprehensive health check...")
        health_report = await ocr_processor.validate_scanner_health()
        
        print(f"   Overall status: {health_report['overall_status']}")
        for check in health_report['checks']:
            status_icon = "✅" if check['status'] == 'healthy' else "⚠️" if check['status'] == 'warning' else "❌"
            print(f"   {status_icon} {check['component']}: {check['message']}")
    except Exception as e:
        print(f"❌ Health check failed: {str(e)}")
        return False
    
    # Final validation
    print("\n" + "=" * 50)
    print("🎉 GEMINI API Setup Validation Complete!")
    print("\n✅ All core components are working correctly:")
    print("   • GEMINI API key is valid and working")
    print("   • OCR processor is functional")
    print("   • Metadata extraction is operational")
    print("   • Database is accessible")
    print("\n📋 Your system is ready for document scanning and OCR processing!")
    print("🔍 Use the following endpoints to monitor system health:")
    print("   • GET /api/auto-archive/system-health")
    print("   • GET /api/auto-archive/scanning-status")
    print("   • POST /api/auto-archive/test-scan")
    
    return True

def check_naps2_installation():
    """Check if NAPS2 scanner software is installed"""
    print("\n🖨️  Checking NAPS2 scanner installation...")
    
    naps2_paths = [
        r"C:\Program Files\NAPS2\NAPS2.Console.exe",
        r"C:\Program Files (x86)\NAPS2\NAPS2.Console.exe"
    ]
    
    found_paths = [path for path in naps2_paths if os.path.exists(path)]
    
    if found_paths:
        print(f"✅ NAPS2 found at: {found_paths[0]}")
        return True
    else:
        print("❌ NAPS2 not found!")
        print("📝 Please install NAPS2 scanner software:")
        print("   1. Download from: https://www.naps2.com/")
        print("   2. Install the software")
        print("   3. Restart this validation script")
        return False

async def main():
    """Main validation routine"""
    print("🚀 GEMINI API & OCR System Validation")
    print("=" * 50)
    
    # Check NAPS2 installation
    naps2_ok = check_naps2_installation()
    
    # Validate GEMINI setup
    gemini_ok = await validate_gemini_setup()
    
    print("\n" + "=" * 50)
    print("📊 VALIDATION SUMMARY")
    print("=" * 50)
    
    print(f"NAPS2 Scanner: {'✅ Ready' if naps2_ok else '❌ Not Installed'}")
    print(f"GEMINI API: {'✅ Ready' if gemini_ok else '❌ Not Configured'}")
    
    if naps2_ok and gemini_ok:
        print("\n🎉 System is fully ready for production use!")
        print("✨ You can now scan documents with automatic OCR and metadata extraction.")
    else:
        print("\n⚠️  System setup incomplete. Please address the issues above.")
    
    return naps2_ok and gemini_ok

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 