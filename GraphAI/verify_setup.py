#!/usr/bin/env python3
"""
Verification Script - Checks if all paths and configurations are correct
"""

import os
import sys
from pathlib import Path
import json

def check_file_exists(file_path: str, description: str) -> bool:
    """Check if a file exists and report result"""
    exists = os.path.exists(file_path)
    status = "✓" if exists else "✗"
    print(f"{status} {description}: {file_path}")
    return exists

def check_directory_exists(dir_path: str, description: str) -> bool:
    """Check if a directory exists and report result"""
    exists = os.path.isdir(dir_path)
    status = "✓" if exists else "✗"
    print(f"{status} {description}: {dir_path}")
    return exists

def check_json_file(file_path: str, description: str) -> bool:
    """Check if a JSON file exists and is valid"""
    if not os.path.exists(file_path):
        print(f"✗ {description}: {file_path} (file not found)")
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            json.load(f)
        print(f"✓ {description}: {file_path}")
        return True
    except json.JSONDecodeError as e:
        print(f"✗ {description}: {file_path} (invalid JSON: {e})")
        return False
    except Exception as e:
        print(f"✗ {description}: {file_path} (error: {e})")
        return False

def verify_setup():
    """Verify the complete setup"""
    print("🔍 HCL ANALYSIS PIPELINE - SETUP VERIFICATION")
    print("=" * 60)
    
    all_good = True
    
    # Check main files
    print("\n📄 Main Files:")
    all_good &= check_file_exists("main.py", "Main script")
    all_good &= check_file_exists("README.md", "Documentation")
    
    # Check config files
    print("\n⚙️ Configuration:")
    all_good &= check_directory_exists("config", "Config directory")
    all_good &= check_file_exists("config/.env", "Environment file")
    all_good &= check_file_exists("config/requirements.txt", "Requirements file")
    
    # Check datasets
    print("\n📊 Datasets:")
    all_good &= check_directory_exists("datasets", "Datasets directory")
    all_good &= check_json_file("datasets/hcl-1k.json", "HCL dataset")
    all_good &= check_json_file("datasets/hcl_total.json", "HCL total dataset")
    
    # Check scripts
    print("\n📜 Scripts:")
    all_good &= check_directory_exists("scripts", "Scripts directory")
    all_good &= check_directory_exists("scripts/extraction", "Extraction scripts")
    all_good &= check_directory_exists("scripts/graph", "Graph scripts")
    all_good &= check_directory_exists("scripts/analysis", "Analysis scripts")
    all_good &= check_directory_exists("scripts/utils", "Utility scripts")
    
    all_good &= check_file_exists("scripts/extraction/hcl_text_extractor.py", "Text extractor")
    all_good &= check_file_exists("scripts/extraction/hcl_metadata_extractor.py", "Metadata extractor")
    all_good &= check_file_exists("scripts/graph/build_hcl_graph.py", "Graph builder")
    all_good &= check_file_exists("scripts/graph/hcl_graph_builder.py", "Graph builder aux")
    all_good &= check_file_exists("scripts/analysis/analyze_extracted_data.py", "Data analyzer")
    all_good &= check_file_exists("scripts/utils/setup.py", "Setup script")
    all_good &= check_file_exists("scripts/utils/test_quick.py", "Quick test")
    all_good &= check_file_exists("scripts/utils/run_hcl_analysis.py", "Analysis runner")
    
    # Check results directories
    print("\n📁 Results Directories:")
    all_good &= check_directory_exists("results", "Results directory")
    all_good &= check_directory_exists("results/visualizations", "Visualizations directory")
    all_good &= check_directory_exists("results/data_exports", "Data exports directory")
    
    # Check auxiliary directories
    print("\n📂 Auxiliary Directories:")
    check_directory_exists("data", "Data directory")
    check_directory_exists("logs", "Logs directory")
    check_directory_exists("output", "Output directory")
    
    # Check environment variables
    print("\n🔑 Environment Variables:")
    try:
        from dotenv import load_dotenv
        load_dotenv('config/.env')
        
        gemini_key = os.getenv('GEMINI_KEY')
        if gemini_key:
            print(f"✓ GEMINI_KEY is set (length: {len(gemini_key)} chars)")
        else:
            print("✗ GEMINI_KEY is not set in .env file")
            all_good = False
            
    except ImportError:
        print("✗ python-dotenv not installed")
        all_good = False
    except Exception as e:
        print(f"✗ Error loading environment: {e}")
        all_good = False
    
    # Check if results exist
    print("\n📈 Generated Results (optional):")
    check_json_file("results/data_exports/hcl_extracted_data.json", "Extracted data")
    check_file_exists("results/visualizations/hcl_graph_interactive.html", "Interactive graph")
    check_file_exists("results/visualizations/hcl_graph_analysis.png", "Graph analysis")
    
    # Summary
    print("\n" + "=" * 60)
    if all_good:
        print("🎉 SETUP VERIFICATION PASSED!")
        print("All essential files and configurations are in place.")
        print("You can run: python main.py pipeline")
    else:
        print("❌ SETUP VERIFICATION FAILED!")
        print("Some essential files or configurations are missing.")
        print("Please check the issues above and fix them.")
    
    print("=" * 60)
    return all_good

if __name__ == "__main__":
    verify_setup() 