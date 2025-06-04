#!/usr/bin/env python3
"""
Test script for Response Style functionality
Tests both detailed and compact response styles
"""

import os
import sys
import json
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir))

from tools.concatenate_web_searches_into_final_response import concatenate_web_searches_into_final_response

def test_response_styles():
    """Test both detailed and compact response styles"""
    
    print("=" * 80)
    print("TESTING RESPONSE STYLE FUNCTIONALITY")
    print("=" * 80)
    
    # Test data
    test_question = "Cum îmi reînnoiesc cartea de identitate în Timișoara?"
    test_reformulated = "Care sunt pașii pentru reînnoirea cărții de identitate în Timișoara, documentele necesare, taxele și locațiile unde se poate face procedura?"
    test_regular_search = "Pentru reînnoirea cărții de identitate în Timișoara, trebuie să faceți programare online..."
    test_trusted_search = {
        "success": True,
        "selected_domains": ["depabd.mai.gov.ro", "evpers.primariatm.ro"],
        "search_results": "Reînnoirea cărții de identitate se face prin programare online la ghișeele DEPABD..."
    }
    
    # Test configuration for RAG
    test_rag_config = {
        "use_rag_context": False,  # Disable for testing to avoid file dependencies
        "rag_domains": ["dfmt.ro", "timpark.ro"],
        "rag_context_path": "rag_context"
    }
    
    # Test 1: Detailed Response Style
    print("\n🔍 TEST 1: DETAILED RESPONSE STYLE")
    print("-" * 60)
    
    detailed_response = concatenate_web_searches_into_final_response(
        original_question=test_question,
        reformulated_query=test_reformulated,
        regular_web_search_results=test_regular_search,
        trusted_sites_search_results=test_trusted_search,
        temperature=0.1,
        max_tokens=15000,
        model="gemini-2.5-flash-preview-04-17",
        rag_config=test_rag_config,
        response_style="detailed",
        save_to_file=False  # Don't save test files
    )
    
    if detailed_response:
        print(f"✅ Detailed response generated successfully!")
        print(f"   📊 Length: {len(detailed_response)} characters")
        print(f"   📝 Preview: {detailed_response[:200]}...")
    else:
        print("❌ Failed to generate detailed response")
    
    print("\n" + "=" * 60)
    
    # Test 2: Compact Response Style
    print("\n🔍 TEST 2: COMPACT RESPONSE STYLE")
    print("-" * 60)
    
    compact_response = concatenate_web_searches_into_final_response(
        original_question=test_question,
        reformulated_query=test_reformulated,
        regular_web_search_results=test_regular_search,
        trusted_sites_search_results=test_trusted_search,
        temperature=0.1,
        max_tokens=15000,
        model="gemini-2.5-flash-preview-04-17",
        rag_config=test_rag_config,
        response_style="compact",
        save_to_file=False  # Don't save test files
    )
    
    if compact_response:
        print(f"✅ Compact response generated successfully!")
        print(f"   📊 Length: {len(compact_response)} characters")
        print(f"   📝 Preview: {compact_response[:200]}...")
    else:
        print("❌ Failed to generate compact response")
    
    print("\n" + "=" * 60)
    
    # Compare results
    if detailed_response and compact_response:
        print("\n📊 COMPARISON RESULTS:")
        print(f"   📏 Detailed response length: {len(detailed_response)} characters")
        print(f"   📏 Compact response length: {len(compact_response)} characters")
        
        length_diff = len(detailed_response) - len(compact_response)
        percentage_diff = (length_diff / len(detailed_response)) * 100 if len(detailed_response) > 0 else 0
        
        print(f"   📊 Length difference: {length_diff} characters ({percentage_diff:.1f}%)")
        
        if len(compact_response) < len(detailed_response):
            print("   ✅ Compact response is shorter than detailed response ✅")
        else:
            print("   ⚠️ Compact response is not shorter than detailed response")
    
    print("\n" + "=" * 80)
    print("✨ RESPONSE STYLE TESTING COMPLETED!")
    print("=" * 80)

def test_config_integration():
    """Test integration with agent configuration"""
    print("\n🔧 TESTING CONFIGURATION INTEGRATION")
    print("-" * 60)
    
    # Load current agent config
    config_path = Path(__file__).parent / "agent_config.json"
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        final_config = config.get("final_response_generation", {})
        response_style = final_config.get("response_style", "detailed")
        
        print(f"   📄 Current config file: {config_path}")
        print(f"   🎨 Current response style: {response_style}")
        print(f"   🤖 Model: {final_config.get('model', 'N/A')}")
        print(f"   🌡️ Temperature: {final_config.get('temperature', 'N/A')}")
        print(f"   🔢 Max tokens: {final_config.get('max_tokens', 'N/A')}")
        
        if response_style in ["detailed", "compact"]:
            print(f"   ✅ Response style is valid")
        else:
            print(f"   ⚠️ Response style '{response_style}' is not recognized")
        
    except Exception as e:
        print(f"   ❌ Error loading config: {e}")

if __name__ == "__main__":
    try:
        test_config_integration()
        test_response_styles()
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}") 