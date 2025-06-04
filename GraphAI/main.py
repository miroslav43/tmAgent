#!/usr/bin/env python3
"""
HCL Analysis Pipeline - Main Entry Point
Orchestrates the complete analysis from text extraction to graph visualization
"""

import sys
import os
from pathlib import Path

# Try to load environment variables from config folder
try:
    from dotenv import load_dotenv
    load_dotenv('config/.env')
    print("✓ Environment variables loaded from config/.env")
except ImportError:
    print("⚠ python-dotenv not installed. Install with: pip install python-dotenv")
except Exception as e:
    print(f"⚠ Could not load .env file: {e}")

# Add scripts to Python path
script_base = Path(__file__).parent / "scripts"
sys.path.extend([
    str(script_base / "extraction"),
    str(script_base / "graph"),
    str(script_base / "analysis"),
    str(script_base / "utils")
])

def run_complete_pipeline():
    """Run the complete HCL analysis pipeline"""
    
    print("🚀 HCL ANALYSIS PIPELINE")
    print("=" * 50)
    
    # Step 1: Text Extraction
    print("\n📊 STEP 1: Text Extraction and Metadata Processing")
    print("-" * 30)
    
    try:
        from hcl_text_extractor import main as run_extraction
        print("Running text extraction...")
        run_extraction()
        print("✅ Text extraction completed!")
    except Exception as e:
        print(f"❌ Error in text extraction: {e}")
        return False
    
    # Step 2: Graph Building
    print("\n🕸️ STEP 2: Graph Construction and Visualization")
    print("-" * 30)
    
    try:
        from build_hcl_graph import main as run_graph_building
        print("Building HCL relationship graph...")
        run_graph_building()
        print("✅ Graph building completed!")
    except Exception as e:
        print(f"❌ Error in graph building: {e}")
        return False
    
    # Step 3: Analysis
    print("\n📈 STEP 3: Data Analysis and Statistics")
    print("-" * 30)
    
    try:
        from analyze_extracted_data import main as run_analysis
        print("Running data analysis...")
        run_analysis()
        print("✅ Analysis completed!")
    except Exception as e:
        print(f"❌ Error in analysis: {e}")
        print("Continuing anyway...")
    
    print("\n🎉 PIPELINE COMPLETED SUCCESSFULLY!")
    print("=" * 50)
    print("📁 Check the following folders for results:")
    print("  • results/visualizations/ - Graph visualizations")
    print("  • results/data_exports/ - Exported data files")
    print("  • datasets/ - Original data files")
    
    return True

def run_extraction_only():
    """Run only the text extraction step"""
    print("📊 Running HCL Text Extraction...")
    
    try:
        from hcl_text_extractor import main as run_extraction
        run_extraction()
        print("✅ Text extraction completed!")
        return True
    except Exception as e:
        print(f"❌ Error in text extraction: {e}")
        return False

def run_graph_only():
    """Run only the graph building step"""
    print("🕸️ Running HCL Graph Building...")
    
    try:
        from build_hcl_graph import main as run_graph_building
        run_graph_building()
        print("✅ Graph building completed!")
        return True
    except Exception as e:
        print(f"❌ Error in graph building: {e}")
        return False

def run_analysis_only():
    """Run only the analysis step"""
    print("📈 Running HCL Data Analysis...")
    
    try:
        from analyze_extracted_data import main as run_analysis
        run_analysis()
        print("✅ Analysis completed!")
        return True
    except Exception as e:
        print(f"❌ Error in analysis: {e}")
        return False

def setup_environment():
    """Setup the environment and install dependencies"""
    print("🔧 Setting up environment...")
    
    try:
        from setup import main as run_setup
        run_setup()
        print("✅ Environment setup completed!")
        return True
    except Exception as e:
        print(f"❌ Error in setup: {e}")
        return False

def show_help():
    """Show usage help"""
    print("HCL Analysis Pipeline - Usage")
    print("=" * 30)
    print("python main.py [command]")
    print()
    print("Commands:")
    print("  pipeline    - Run complete analysis pipeline (default)")
    print("  extraction  - Run only text extraction")
    print("  graph       - Run only graph building")
    print("  analysis    - Run only data analysis")
    print("  setup       - Setup environment and dependencies")
    print("  help        - Show this help message")
    print()
    print("Examples:")
    print("  python main.py                # Run complete pipeline")
    print("  python main.py extraction     # Extract text only")
    print("  python main.py graph          # Build graph only")

def main():
    """Main function"""
    
    # Get command from arguments
    command = sys.argv[1] if len(sys.argv) > 1 else "pipeline"
    
    # Execute based on command
    if command == "pipeline":
        success = run_complete_pipeline()
    elif command == "extraction":
        success = run_extraction_only()
    elif command == "graph":
        success = run_graph_only()
    elif command == "analysis":
        success = run_analysis_only()
    elif command == "setup":
        success = setup_environment()
    elif command == "help":
        show_help()
        success = True
    else:
        print(f"Unknown command: {command}")
        show_help()
        success = False
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 