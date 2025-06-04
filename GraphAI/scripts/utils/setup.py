#!/usr/bin/env python3
"""
Setup script for HCL Graph Analysis project
Installs dependencies and prepares the environment
"""

import subprocess
import sys
import os
from pathlib import Path

def install_requirements():
    """Install required packages from requirements.txt"""
    print("Installing Python dependencies...")
    
    try:
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'
        ])
        print("✓ All dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Error installing dependencies: {e}")
        return False
    except FileNotFoundError:
        print("✗ requirements.txt not found!")
        return False

def check_environment():
    """Check if the environment is properly set up"""
    print("Checking environment...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("✗ Python 3.8 or higher is required!")
        return False
    else:
        print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    
    # Check if .env file exists
    if not Path('.env').exists():
        print("⚠ .env file not found!")
        print("Creating template .env file...")
        create_env_template()
    else:
        print("✓ .env file found")
    
    # Check if data file exists
    if not Path('hcl-1k.json').exists():
        print("⚠ hcl-1k.json not found!")
        print("Please ensure you have the HCL data file in the project directory.")
    else:
        print("✓ hcl-1k.json data file found")
    
    return True

def create_env_template():
    """Create a template .env file"""
    env_template = """# Gemini API Configuration
GEMINI_KEY=your_gemini_api_key_here

# Optional: Other configuration
# MAX_HCL_ITEMS=10
# OUTPUT_DIR=./output
"""
    
    with open('.env', 'w') as f:
        f.write(env_template)
    
    print("✓ Template .env file created")
    print("  Please edit .env and add your actual Gemini API key!")

def create_directories():
    """Create necessary directories"""
    print("Creating directories...")
    
    directories = ['output', 'logs', 'data']
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✓ Directory '{directory}' ready")

def test_imports():
    """Test if all required packages can be imported"""
    print("Testing package imports...")
    
    required_packages = [
        ('google.generativeai', 'Google Generative AI'),
        ('pandas', 'Pandas'),
        ('networkx', 'NetworkX'),
        ('matplotlib', 'Matplotlib'),
        ('plotly', 'Plotly'),
        ('bs4', 'BeautifulSoup4'),
        ('dotenv', 'Python-dotenv')
    ]
    
    failed_imports = []
    
    for package, name in required_packages:
        try:
            __import__(package)
            print(f"✓ {name} imported successfully")
        except ImportError:
            print(f"✗ Failed to import {name}")
            failed_imports.append(name)
    
    if failed_imports:
        print(f"\nFailed imports: {', '.join(failed_imports)}")
        return False
    
    print("✓ All packages imported successfully!")
    return True

def display_next_steps():
    """Display next steps for the user"""
    print("\n" + "="*60)
    print("SETUP COMPLETE!")
    print("="*60)
    
    print("\nNext steps:")
    print("1. Edit the .env file and add your Gemini API key")
    print("2. Ensure hcl-1k.json is in the project directory")
    print("3. Run the analysis with: python run_hcl_analysis.py")
    
    print("\nProject structure:")
    print("├── .env                     # API keys and configuration")
    print("├── hcl-1k.json             # HCL data file")
    print("├── requirements.txt        # Python dependencies")
    print("├── setup.py               # This setup script")
    print("├── run_hcl_analysis.py    # Main analysis runner")
    print("├── hcl_metadata_extractor.py  # Metadata extraction")
    print("└── hcl_graph_builder.py   # Graph building and visualization")
    
    print("\nFor help:")
    print("- Check README.md (will be generated after first run)")
    print("- Review the script comments")
    print("- Ensure your Gemini API key is valid")

def main():
    """Main setup function"""
    print("HCL GRAPH ANALYSIS - SETUP")
    print("="*40)
    print("Setting up the environment for HCL graph analysis...")
    print()
    
    # Check environment
    if not check_environment():
        print("✗ Environment check failed!")
        return
    
    # Install requirements
    if not install_requirements():
        print("✗ Failed to install requirements!")
        return
    
    # Create directories
    create_directories()
    
    # Test imports
    if not test_imports():
        print("✗ Package import test failed!")
        print("Try running: pip install -r requirements.txt")
        return
    
    # Display next steps
    display_next_steps()

if __name__ == "__main__":
    main() 