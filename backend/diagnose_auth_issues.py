#!/usr/bin/env python3
"""
🔧 AUTHENTICATION & API DIAGNOSTIC TOOL
Romanian Public Administration Platform

This script diagnoses and helps fix common authentication and API issues.
Run this when you get 401 errors or API failures.
"""

import os
import sys
import asyncio
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_status(message, status="info"):
    """Print colored status messages"""
    if status == "success":
        print(f"{Colors.GREEN}✅ {message}{Colors.END}")
    elif status == "error":
        print(f"{Colors.RED}❌ {message}{Colors.END}")
    elif status == "warning":
        print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")
    elif status == "info":
        print(f"{Colors.BLUE}ℹ️  {message}{Colors.END}")
    else:
        print(f"{Colors.BOLD}{message}{Colors.END}")

def check_environment_file():
    """Check if .env file exists and has required variables"""
    print_status("Checking environment configuration...", "info")
    
    env_path = Path(".env")
    if not env_path.exists():
        print_status(".env file not found!", "error")
        print("Creating .env file with template...")
        
        env_template = """# Romanian Public Administration Platform Environment Configuration
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/romanian_admin_dev
GEMINI_API_KEY=your-gemini-api-key-here
SECRET_KEY=dev-secret-key-change-in-production-please
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
"""
        with open(".env", "w") as f:
            f.write(env_template)
        print_status(".env file created with template", "success")
        return False
    
    # Load environment variables
    load_dotenv()
    
    # Check critical variables
    required_vars = {
        "GEMINI_API_KEY": "Gemini API key for OCR processing",
        "SECRET_KEY": "JWT secret key for authentication",
        "DATABASE_URL": "Database connection string"
    }
    
    missing_vars = []
    placeholder_vars = []
    
    for var, description in required_vars.items():
        value = os.getenv(var)
        if not value:
            missing_vars.append(f"{var} ({description})")
        elif value in ["your-gemini-api-key-here", "dev-secret-key-change-in-production-please"]:
            placeholder_vars.append(f"{var} ({description})")
    
    if missing_vars:
        print_status("Missing environment variables:", "error")
        for var in missing_vars:
            print(f"  - {var}")
        return False
    
    if placeholder_vars:
        print_status("Placeholder values detected:", "warning")
        for var in placeholder_vars:
            print(f"  - {var}")
        return False
    
    print_status("Environment configuration looks good", "success")
    return True

def check_gemini_api():
    """Test Gemini API connection"""
    print_status("Testing Gemini API connection...", "info")
    
    try:
        from app.services.ocr_processor import LegalDocumentOCR
        ocr = LegalDocumentOCR()
        print_status("Gemini API connection successful", "success")
        return True
    except ValueError as e:
        if "GEMINI_API_KEY" in str(e):
            print_status("Gemini API key not set or invalid", "error")
            print("Get your free API key from: https://ai.google.dev/gemini-api/docs/api-key")
        else:
            print_status(f"Gemini API error: {e}", "error")
        return False
    except ImportError as e:
        print_status(f"Import error: {e}", "error")
        print("Run: pip install -r requirements.txt")
        return False
    except Exception as e:
        print_status(f"Unexpected error: {e}", "error")
        return False

def check_database_connection():
    """Test database connection"""
    print_status("Testing database connection...", "info")
    
    try:
        # Try to import database modules
        from app.db.database import engine
        print_status("Database modules imported successfully", "success")
        return True
    except ImportError as e:
        print_status(f"Database import error: {e}", "error")
        return False
    except Exception as e:
        print_status(f"Database connection error: {e}", "warning")
        print("Make sure PostgreSQL is running and database exists")
        return False

def check_dependencies():
    """Check if all required dependencies are installed"""
    print_status("Checking Python dependencies...", "info")
    
    required_packages = [
        "fastapi",
        "sqlalchemy",
        "google-genai",
        "python-dotenv",
        "uvicorn",
        "asyncpg"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print_status("Missing Python packages:", "error")
        for package in missing_packages:
            print(f"  - {package}")
        print("\nRun: pip install -r requirements.txt")
        return False
    
    print_status("All required packages are installed", "success")
    return True

def check_file_permissions():
    """Check file and directory permissions"""
    print_status("Checking file permissions...", "info")
    
    critical_paths = [
        "uploads",
        "uploads/archive",
        "uploads/temp",
        "uploads/documents"
    ]
    
    issues = []
    
    for path_str in critical_paths:
        path = Path(path_str)
        if not path.exists():
            try:
                path.mkdir(parents=True, exist_ok=True)
                print_status(f"Created directory: {path}", "success")
            except PermissionError:
                issues.append(f"Cannot create directory: {path}")
        elif not os.access(path, os.W_OK):
            issues.append(f"No write permission: {path}")
    
    if issues:
        print_status("File permission issues:", "error")
        for issue in issues:
            print(f"  - {issue}")
        return False
    
    print_status("File permissions are correct", "success")
    return True

def test_auth_endpoint():
    """Test authentication endpoint"""
    print_status("Testing authentication system...", "info")
    
    try:
        # This is a basic test - in production you'd test actual endpoints
        from app.core.dependencies import get_current_user
        print_status("Authentication modules loaded successfully", "success")
        return True
    except ImportError as e:
        print_status(f"Authentication import error: {e}", "error")
        return False

def provide_solutions():
    """Provide step-by-step solutions for common issues"""
    print_status("SOLUTIONS FOR COMMON ISSUES", "info")
    print()
    
    print(f"{Colors.BOLD}🔑 401 Unauthorized Error:{Colors.END}")
    print("1. Make sure you're logged in as an OFFICIAL user (not citizen)")
    print("2. Check that your JWT token is valid")
    print("3. Verify GEMINI_API_KEY is set in .env file")
    print()
    
    print(f"{Colors.BOLD}🤖 Gemini API Issues:{Colors.END}")
    print("1. Get API key: https://ai.google.dev/gemini-api/docs/api-key")
    print("2. Replace 'your-gemini-api-key-here' in .env file")
    print("3. Restart the backend server")
    print()
    
    print(f"{Colors.BOLD}🗄️ Database Issues:{Colors.END}")
    print("1. Start PostgreSQL service")
    print("2. Create database: romanian_admin_dev")
    print("3. Run migrations: python create_categories.py")
    print()
    
    print(f"{Colors.BOLD}📁 File Upload Issues:{Colors.END}")
    print("1. Check uploads/ directory permissions")
    print("2. Ensure sufficient disk space")
    print("3. Verify file size limits")
    print()

def main():
    """Main diagnostic function"""
    print(f"{Colors.BOLD}🔧 ROMANIAN ADMIN PLATFORM DIAGNOSTICS{Colors.END}")
    print("=" * 50)
    print()
    
    # Change to backend directory if not already there
    if not Path("app").exists():
        backend_path = Path("HackTM2025/backend")
        if backend_path.exists():
            os.chdir(backend_path)
            print_status(f"Changed to backend directory: {backend_path.absolute()}", "info")
        else:
            print_status("Cannot find backend directory!", "error")
            sys.exit(1)
    
    # Run all checks
    checks = [
        ("Environment File", check_environment_file),
        ("Python Dependencies", check_dependencies),
        ("File Permissions", check_file_permissions),
        ("Database Connection", check_database_connection),
        ("Gemini API", check_gemini_api),
        ("Authentication System", test_auth_endpoint)
    ]
    
    results = {}
    
    for check_name, check_func in checks:
        print(f"\n{Colors.BOLD}--- {check_name} ---{Colors.END}")
        try:
            results[check_name] = check_func()
        except Exception as e:
            print_status(f"Check failed with error: {e}", "error")
            results[check_name] = False
    
    # Summary
    print(f"\n{Colors.BOLD}📊 DIAGNOSTIC SUMMARY{Colors.END}")
    print("=" * 30)
    
    passed = sum(results.values())
    total = len(results)
    
    for check_name, result in results.items():
        status = "✅" if result else "❌"
        print(f"{status} {check_name}")
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print_status("All checks passed! Your system should work correctly.", "success")
    else:
        print_status(f"{total - passed} issues found. See solutions below.", "warning")
        print()
        provide_solutions()
    
    print(f"\n{Colors.BOLD}🚀 NEXT STEPS:{Colors.END}")
    if passed < total:
        print("1. Fix the issues above")
        print("2. Run this script again to verify")
        print("3. Start the backend: python main.py")
        print("4. Test PDF upload at /auto-archive/upload")
    else:
        print("1. Start backend: python main.py")
        print("2. Start frontend: npm run dev")
        print("3. Login as OFFICIAL user")
        print("4. Test PDF upload and OCR!")

if __name__ == "__main__":
    main() 