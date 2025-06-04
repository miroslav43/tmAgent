#!/usr/bin/env python3
"""
HCL Analysis Pipeline - Main runner script
Executes the complete pipeline: metadata extraction → graph building → visualization
"""

import os
import sys
from pathlib import Path
import subprocess
import time

def check_dependencies():
    """Check if all required dependencies are installed"""
    print("Checking dependencies...")
    
    required_packages = [
        'google-generativeai',
        'pandas',
        'networkx',
        'matplotlib',
        'plotly',
        'beautifulsoup4',
        'python-dotenv'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"Missing packages: {', '.join(missing_packages)}")
        print("Installing missing packages...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing_packages)
        print("Dependencies installed successfully!")
    else:
        print("All dependencies are installed.")

def check_data_files():
    """Check if required data files exist"""
    print("Checking data files...")
    
    required_files = ['.env', 'hcl-1k.json']
    missing_files = []
    
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"Missing files: {', '.join(missing_files)}")
        return False
    
    print("All required files are present.")
    return True

def run_metadata_extraction():
    """Run the metadata extraction script"""
    print("\n" + "="*50)
    print("STEP 1: EXTRACTING METADATA FROM HCL DOCUMENTS")
    print("="*50)
    
    try:
        from hcl_metadata_extractor import main as extract_main
        extract_main()
        print("✓ Metadata extraction completed successfully!")
        return True
    except Exception as e:
        print(f"✗ Error in metadata extraction: {e}")
        return False

def run_graph_building():
    """Run the graph building and visualization script"""
    print("\n" + "="*50)
    print("STEP 2: BUILDING AND VISUALIZING HCL GRAPH")
    print("="*50)
    
    try:
        from hcl_graph_builder import main as graph_main
        graph_main()
        print("✓ Graph building and visualization completed successfully!")
        return True
    except Exception as e:
        print(f"✗ Error in graph building: {e}")
        return False

def display_results():
    """Display information about generated files"""
    print("\n" + "="*50)
    print("ANALYSIS COMPLETE - GENERATED FILES")
    print("="*50)
    
    output_files = [
        ('hcl_metadata.csv', 'Extracted metadata from HCL documents'),
        ('hcl_relationships.csv', 'Relationships between HCL documents'),
        ('hcl_graph_matplotlib.png', 'Static graph visualization'),
        ('hcl_graph_interactive.html', 'Interactive graph (open in browser)'),
        ('hcl_dashboard.html', 'Analysis dashboard (open in browser)'),
        ('hcl_graph.gexf', 'Graph in Gephi format'),
        ('hcl_graph.json', 'Graph in JSON format')
    ]
    
    print("\nGenerated files:")
    for filename, description in output_files:
        if Path(filename).exists():
            file_size = Path(filename).stat().st_size
            print(f"✓ {filename:<30} - {description} ({file_size:,} bytes)")
        else:
            print(f"✗ {filename:<30} - {description} (not found)")
    
    print(f"\nTo view the interactive results:")
    print(f"1. Open 'hcl_graph_interactive.html' in your web browser")
    print(f"2. Open 'hcl_dashboard.html' in your web browser")
    print(f"3. Use 'hcl_graph.gexf' with Gephi for advanced graph analysis")

def create_readme():
    """Create a README file with instructions"""
    readme_content = """# HCL Graph Analysis Results

This directory contains the results of analyzing HCL (Hotărâri ale Consiliului Local) documents.

## Generated Files

### Data Files
- `hcl_metadata.csv` - Extracted metadata from HCL documents
- `hcl_relationships.csv` - Relationships between HCL documents

### Visualizations
- `hcl_graph_matplotlib.png` - Static graph visualization
- `hcl_graph_interactive.html` - Interactive graph (open in web browser)
- `hcl_dashboard.html` - Comprehensive analysis dashboard (open in web browser)

### Graph Data Exports
- `hcl_graph.gexf` - Graph in Gephi format (for advanced analysis)
- `hcl_graph.json` - Graph in JSON format
- `hcl_graph.graphml` - Graph in GraphML format

## How to View Results

### Interactive Visualizations
1. **Interactive Graph**: Open `hcl_graph_interactive.html` in your web browser
   - Hover over nodes to see HCL details
   - Different edge colors represent different relationship types
   
2. **Analysis Dashboard**: Open `hcl_dashboard.html` in your web browser
   - View relationship type distributions
   - See node degree distributions
   - Explore centrality measures
   - Review graph statistics

### Static Visualization
- View `hcl_graph_matplotlib.png` for a static overview of the graph

### Advanced Analysis
- Import `hcl_graph.gexf` into [Gephi](https://gephi.org/) for advanced graph analysis
- Use the CSV files for custom analysis in Excel, R, or other tools

## Relationship Types

The analysis identifies the following relationship types between HCL documents:
- **modifică** (modifies) - Red edges
- **abrogă** (abrogates) - Teal edges  
- **completează** (complements) - Blue edges
- **referă** (references) - Green edges
- **înlocuiește** (replaces) - Yellow edges
- **suspendă** (suspends) - Gray edges

## Graph Metrics

The analysis calculates various graph metrics including:
- Node and edge counts
- Graph density
- Centrality measures (degree, betweenness, closeness)
- Connected components
- Most important nodes (by various measures)

## Scripts Used

- `hcl_metadata_extractor.py` - Extracts metadata using Gemini AI
- `hcl_graph_builder.py` - Builds and visualizes the graph
- `run_hcl_analysis.py` - Main pipeline runner

## Requirements

See `requirements.txt` for Python package dependencies.
"""
    
    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print("✓ README.md created with analysis instructions")

def main():
    """Main function to run the complete HCL analysis pipeline"""
    
    print("HCL GRAPH ANALYSIS PIPELINE")
    print("="*50)
    print("This script will:")
    print("1. Extract metadata from HCL documents using Gemini AI")
    print("2. Build a graph of HCL relationships")
    print("3. Create visualizations and analysis")
    print("="*50)
    
    # Check dependencies
    check_dependencies()
    
    # Check data files
    if not check_data_files():
        print("\n✗ Required data files are missing!")
        print("Please ensure you have:")
        print("- .env file with GEMINI_KEY")
        print("- hcl-1k.json file with HCL data")
        return
    
    start_time = time.time()
    
    # Step 1: Extract metadata
    if not run_metadata_extraction():
        print("\n✗ Pipeline failed at metadata extraction step!")
        return
    
    # Small delay between steps
    time.sleep(2)
    
    # Step 2: Build graph and create visualizations
    if not run_graph_building():
        print("\n✗ Pipeline failed at graph building step!")
        return
    
    # Create documentation
    create_readme()
    
    # Display results
    display_results()
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"\n🎉 PIPELINE COMPLETED SUCCESSFULLY!")
    print(f"Total execution time: {duration:.2f} seconds")
    print(f"\nNext steps:")
    print(f"1. Open the interactive HTML files in your browser")
    print(f"2. Explore the generated CSV files")
    print(f"3. Use Gephi for advanced graph analysis")

if __name__ == "__main__":
    main() 