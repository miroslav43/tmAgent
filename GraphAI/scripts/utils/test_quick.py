#!/usr/bin/env python3
"""
Quick Test Script - Test HCL analysis without API calls
Creates mock data to test the graph building functionality
"""

import json
import pandas as pd
import networkx as nx
from pathlib import Path

def create_mock_metadata():
    """Create mock metadata for testing"""
    mock_data = [
        {
            'hcl_nr': '466',
            'data_adoptarii': '2024-10-29',
            'data_publicarii': '2024-11-08T06:21:59.082929+00:00',
            'subject_matter': 'Valorificare masă lemnoasă din fond forestier',
            'hcl_references': ['208/2021'],
            'law_references': ['Ordonanța de Urgență nr. 57/2019', 'Hotărârea de Guvern nr. 715/2017'],
            'regulatory_references': ['Regulamentul de valorificare'],
            'relationship_indicators': ['având în vedere'],
            'entities_involved': ['Direcția Silvică Timiș', 'Primăria Municipiului Timișoara'],
            'relationship_type': 'referă'
        },
        {
            'hcl_nr': '456',
            'data_adoptarii': '2024-10-29',
            'data_publicarii': '2024-11-08T06:23:15.945888+00:00',
            'subject_matter': 'Operațiuni cadastrale teren municipiu',
            'hcl_references': ['208/2021'],
            'law_references': ['Legii nr. 7/1996', 'Ordonanța de Urgență nr. 57/2019'],
            'regulatory_references': ['Regulamentul de organizare'],
            'relationship_indicators': ['având în vedere'],
            'entities_involved': ['SC GIS-SURVEY SRL', 'OCPI Timiș'],
            'relationship_type': 'referă'
        },
        {
            'hcl_nr': '208',
            'data_adoptarii': '2021-06-15',
            'data_publicarii': '2021-06-20T10:00:00.000000+00:00',
            'subject_matter': 'Regulament organizare și funcționare Consiliul Local',
            'hcl_references': [],
            'law_references': ['Ordonanța de Urgență nr. 57/2019'],
            'regulatory_references': [],
            'relationship_indicators': [],
            'entities_involved': ['Consiliul Local Timișoara'],
            'relationship_type': 'referă'
        }
    ]
    
    # Convert lists to strings for CSV compatibility
    for item in mock_data:
        for key in ['hcl_references', 'law_references', 'regulatory_references', 
                   'relationship_indicators', 'entities_involved']:
            item[key] = str(item[key])
    
    return pd.DataFrame(mock_data)

def create_mock_relationships():
    """Create mock relationships for testing"""
    relationships_data = [
        {
            'source': '466',
            'target': '208',
            'relationship_type': 'referă',
            'reference_text': 'Hotărârea Consiliului Local nr. 208/2021',
            'year': '2021'
        },
        {
            'source': '456',
            'target': '208',
            'relationship_type': 'referă',
            'reference_text': 'Hotărârea Consiliului Local nr. 208/2021',
            'year': '2021'
        }
    ]
    
    return pd.DataFrame(relationships_data)

def test_graph_building():
    """Test the graph building functionality"""
    print("Testing graph building with mock data...")
    
    # Create mock data
    metadata_df = create_mock_metadata()
    relationships_df = create_mock_relationships()
    
    # Save mock data
    metadata_df.to_csv('hcl_metadata_test.csv', index=False, encoding='utf-8')
    relationships_df.to_csv('hcl_relationships_test.csv', index=False, encoding='utf-8')
    
    print(f"✓ Created test metadata with {len(metadata_df)} records")
    print(f"✓ Created test relationships with {len(relationships_df)} records")
    
    # Test graph building
    try:
        from hcl_graph_builder import HCLGraphBuilder
        
        builder = HCLGraphBuilder()
        
        # Load test data
        if builder.load_data('hcl_metadata_test.csv', 'hcl_relationships_test.csv'):
            print("✓ Test data loaded successfully")
            
            # Build graph
            builder.build_graph()
            print(f"✓ Graph built with {len(builder.graph.nodes)} nodes and {len(builder.graph.edges)} edges")
            
            # Analyze metrics
            metrics = builder.analyze_graph_metrics()
            print(f"✓ Graph metrics calculated")
            print(f"  - Density: {metrics['density']:.4f}")
            print(f"  - Components: {metrics['num_weakly_connected_components']}")
            
            # Test visualizations (without showing)
            print("✓ Graph building functionality works correctly!")
            return True
        else:
            print("✗ Failed to load test data")
            return False
            
    except Exception as e:
        print(f"✗ Error testing graph building: {e}")
        return False

def test_data_loading():
    """Test loading the actual HCL data"""
    print("Testing HCL data loading...")
    
    if not Path('hcl-1k.json').exists():
        print("⚠ hcl-1k.json not found - skipping data loading test")
        return True
    
    try:
        with open('hcl-1k.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        hcl_items = data['data']['hcl']
        print(f"✓ Loaded {len(hcl_items)} HCL items from JSON")
        
        # Test first item structure
        if hcl_items:
            first_item = hcl_items[0]
            required_fields = ['nr', 'dataAdoptarii', 'motivatie', 'articole']
            
            for field in required_fields:
                if field in first_item:
                    print(f"✓ Field '{field}' present")
                else:
                    print(f"⚠ Field '{field}' missing")
        
        return True
        
    except Exception as e:
        print(f"✗ Error loading HCL data: {e}")
        return False

def test_env_setup():
    """Test environment setup"""
    print("Testing environment setup...")
    
    # Check .env file
    if Path('.env').exists():
        print("✓ .env file exists")
        
        try:
            from dotenv import load_dotenv
            import os
            
            load_dotenv()
            gemini_key = os.getenv('GEMINI_KEY')
            
            if gemini_key and gemini_key != 'your_gemini_api_key_here':
                print("✓ GEMINI_KEY found in environment")
            else:
                print("⚠ GEMINI_KEY not configured or using template value")
                
        except Exception as e:
            print(f"⚠ Error checking environment: {e}")
    else:
        print("⚠ .env file not found")
    
    return True

def test_dependencies():
    """Test if all dependencies are available"""
    print("Testing dependencies...")
    
    required_packages = [
        ('pandas', 'Pandas'),
        ('networkx', 'NetworkX'),
        ('matplotlib', 'Matplotlib'),
        ('plotly', 'Plotly'),
        ('bs4', 'BeautifulSoup4'),
        ('dotenv', 'Python-dotenv')
    ]
    
    all_ok = True
    
    for package, name in required_packages:
        try:
            __import__(package)
            print(f"✓ {name} available")
        except ImportError:
            print(f"✗ {name} not available")
            all_ok = False
    
    # Test Gemini separately (optional for this test)
    try:
        import google.generativeai as genai
        print("✓ Google Generative AI available")
    except ImportError:
        print("⚠ Google Generative AI not available (needed for metadata extraction)")
    
    return all_ok

def cleanup_test_files():
    """Clean up test files"""
    test_files = ['hcl_metadata_test.csv', 'hcl_relationships_test.csv']
    
    for file in test_files:
        if Path(file).exists():
            Path(file).unlink()
            print(f"✓ Cleaned up {file}")

def main():
    """Run all tests"""
    print("HCL GRAPH ANALYSIS - QUICK TEST")
    print("="*40)
    print("Running quick tests to verify functionality...")
    print()
    
    tests = [
        ("Dependencies", test_dependencies),
        ("Environment Setup", test_env_setup),
        ("Data Loading", test_data_loading),
        ("Graph Building", test_graph_building)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"✗ Test '{test_name}' failed with error: {e}")
            results[test_name] = False
    
    # Clean up
    cleanup_test_files()
    
    # Summary
    print("\n" + "="*40)
    print("TEST SUMMARY")
    print("="*40)
    
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{test_name:<20} {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print(f"\n🎉 All tests passed! The system is ready to use.")
        print(f"Run 'python run_hcl_analysis.py' to start the full analysis.")
    else:
        print(f"\n⚠ Some tests failed. Please check the issues above.")
        print(f"Consider running 'python setup.py' to fix setup issues.")

if __name__ == "__main__":
    main() 