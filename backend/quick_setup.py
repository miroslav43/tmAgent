#!/usr/bin/env python3
"""
🚀 QUICK SETUP SCRIPT
Romanian Public Administration Platform

Interactive setup for Gemini API key and environment configuration.
"""

import os
import webbrowser
from pathlib import Path

def main():
    print("🚀 ROMANIAN ADMIN PLATFORM - QUICK SETUP")
    print("=" * 50)
    print()
    
    # Check if .env exists
    env_path = Path(".env")
    if not env_path.exists():
        print("❌ .env file not found!")
        print("Run: python diagnose_auth_issues.py first")
        return
    
    # Read current .env
    with open(".env", "r") as f:
        env_content = f.read()
    
    # Check if API key is set
    if "your-gemini-api-key-here" in env_content:
        print("🔑 GEMINI API KEY SETUP NEEDED")
        print()
        print("You need a FREE Gemini API key to use OCR features.")
        print()
        
        # Ask if user wants to open browser
        response = input("Open Google AI Studio in browser to get API key? (y/n): ").lower()
        
        if response == 'y':
            print("🌐 Opening Google AI Studio...")
            webbrowser.open("https://ai.google.dev/gemini-api/docs/api-key")
            print()
            print("📋 STEPS:")
            print("1. Click 'Get a Gemini API key in Google AI Studio'")
            print("2. Sign in with Google account")
            print("3. Click 'Create API Key'")
            print("4. Copy the key (starts with 'AIza...')")
            print()
        
        # Get API key from user
        api_key = input("Paste your Gemini API key here: ").strip()
        
        if api_key and api_key.startswith("AIza"):
            # Update .env file
            updated_content = env_content.replace("your-gemini-api-key-here", api_key)
            
            with open(".env", "w") as f:
                f.write(updated_content)
            
            print("✅ API key saved successfully!")
            print()
            
            # Test the API key
            print("🧪 Testing API key...")
            try:
                from app.services.ocr_processor import LegalDocumentOCR
                ocr = LegalDocumentOCR()
                print("✅ API key works! OCR is ready.")
            except Exception as e:
                print(f"❌ API key test failed: {e}")
                return
            
            print()
            print("🎉 SETUP COMPLETE!")
            print()
            print("🚀 NEXT STEPS:")
            print("1. Start backend: python main.py")
            print("2. Start frontend: npm run dev (in frontend folder)")
            print("3. Register as OFFICIAL user")
            print("4. Test PDF upload at /auto-archive/upload")
            print()
            print("📁 Your uploaded documents will appear in /db-archive")
            
        else:
            print("❌ Invalid API key format. Should start with 'AIza'")
    else:
        print("✅ Gemini API key is already configured!")
        print()
        print("🧪 Testing configuration...")
        
        try:
            from app.services.ocr_processor import LegalDocumentOCR
            ocr = LegalDocumentOCR()
            print("✅ Everything looks good!")
            print()
            print("🚀 Ready to start:")
            print("1. python main.py")
            print("2. Test PDF upload!")
        except Exception as e:
            print(f"❌ Configuration issue: {e}")

if __name__ == "__main__":
    main() 