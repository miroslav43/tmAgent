# 🚀 GEMINI API SETUP GUIDE

## Critical Issues & Solutions

You're getting `401 Unauthorized` errors because:
1. **Missing .env file** - Now created ✅
2. **Missing Gemini API key** - Follow steps below 🔧
3. **User authentication needed** - Login as official role

## Step 1: Get Your FREE Gemini API Key

### Option A: Quick Setup (Recommended)
1. **Go to Google AI Studio**: https://ai.google.dev/gemini-api/docs/api-key
2. **Click**: "Get a Gemini API key in Google AI Studio" 
3. **Sign in** with your Google account
4. **Click**: "Create API Key" 
5. **Copy** the generated key (starts with `AIza...`)

### Option B: Alternative Link  
- Direct link: https://aistudio.google.com/app/apikey

## Step 2: Configure Your .env File

1. **Open**: `HackTM2025/backend/.env` (already created)
2. **Replace**: `your-gemini-api-key-here` with your actual key

```bash
# Before (won't work):
GEMINI_API_KEY=your-gemini-api-key-here

# After (will work):
GEMINI_API_KEY=AIzaSyD...your-actual-key-here
```

## Step 3: Verify Setup

```bash
cd HackTM2025/backend
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('✅ Gemini API Key loaded:', 'Yes' if os.getenv('GEMINI_API_KEY') and os.getenv('GEMINI_API_KEY') != 'your-gemini-api-key-here' else 'No - Please set your API key')"
```

## Step 4: Test OCR Processing

```bash
python -c "
from app.services.ocr_processor import LegalDocumentOCR
try:
    ocr = LegalDocumentOCR()
    print('✅ OCR processor initialized successfully')
except ValueError as e:
    print('❌ Error:', e)
    print('Please set GEMINI_API_KEY in .env file')
"
```

## Step 5: User Authentication

**For PDF upload/scanning, you need to:**

1. **Start the backend**: `python main.py`
2. **Start the frontend**: `npm run dev` (in frontend folder)
3. **Register as OFFICIAL user** (not citizen)
4. **Login with official role**

Only **official** users can upload/scan documents.

## Step 6: Complete Environment Setup

Your `.env` should look like this:

```bash
# Romanian Public Administration Platform Environment Configuration
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/romanian_admin_dev
GEMINI_API_KEY=AIzaSyD...your-actual-key-here  # ← REPLACE THIS
SECRET_KEY=dev-secret-key-change-in-production-please
```

## Troubleshooting

### Error: "Could not validate credentials"
- **Cause**: User not logged in or wrong role
- **Solution**: Login as **official** user

### Error: "GEMINI_API_KEY environment variable must be set"
- **Cause**: API key not set or invalid
- **Solution**: Follow Step 2 above

### Error: "429 Too Many Requests"
- **Cause**: API rate limit exceeded
- **Solution**: Wait a few minutes and try again

### Error: "Files.upload() got an unexpected keyword argument 'path'"
- **Status**: ✅ FIXED (updated to use `file` parameter)

## Features After Setup

Once configured, you'll get:

### 🤖 Smart Features
- **Auto-OCR**: Extracts text from PDFs/images
- **Smart Categorization**: AI categorizes documents automatically  
- **Metadata Generation**: Extracts title, authority, description
- **Auto-Archive**: Documents added to appropriate categories

### 📁 Category Management
- **Auto-Creation**: Creates new categories if needed
- **Smart Matching**: Finds existing similar categories
- **Limit Protection**: Max 100 categories to prevent chaos

### 🔄 Real-time Updates
- **Auto-Refresh**: `/db-archive` page updates after upload
- **Progress Tracking**: Real-time upload/scan progress
- **Error Handling**: Graceful error recovery

## Quick Test

Upload a PDF document through `/auto-archive/upload` and watch:

1. **OCR Processing**: Text extracted with Gemini
2. **Metadata Generation**: AI analyzes content  
3. **Smart Categorization**: Finds or creates category
4. **Auto-Archive**: Document appears in `/db-archive`
5. **Page Refresh**: Archive automatically updates

## Need Help?

- **API Key Issues**: https://ai.google.dev/gemini-api/docs/api-key
- **Authentication**: Make sure you're logged in as **official** user
- **Rate Limits**: Gemini API has generous free limits
- **Database**: Ensure PostgreSQL is running

---

**🎯 Result**: After setup, your PDF uploads will work with full AI-powered OCR and smart categorization! 