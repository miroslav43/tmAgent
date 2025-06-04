#!/usr/bin/env python3
"""
Test script pentru verificarea extragerii cu regex
"""

import re
import sys
import os
from pathlib import Path

def test_hcl_regex_simple():
    """Test HCL regex extraction - simple version without API"""
    print("🔍 TESTING HCL REGEX EXTRACTION")
    print("=" * 50)
    
    def extract_hcl_references_regex(text: str):
        """Extract HCL references using regex - copied from main script"""
        
        # Diverse pattern-uri pentru identificarea HCL-urilor în text
        patterns = [
            # "Hotărârea Consiliului Local nr. 208/2021"
            (r'Hotărârea\s+Consiliului\s+Local\s+nr\.?\s*(\d+)[\/\-](\d{4})', 'referă'),
            # "HCL nr. 208/2021"
            (r'HCL\s+nr\.?\s*(\d+)[\/\-](\d{4})', 'referă'),
            # "hotărârea nr. 208/2021" (case insensitive)
            (r'hotărârea\s+nr\.?\s*(\d+)[\/\-](\d{4})', 'referă'),
            # "Hotărârea nr. 208/2021"
            (r'Hotărârea\s+nr\.?\s*(\d+)[\/\-](\d{4})', 'referă'),
            # "nr. 208/2021" (când contextul e clar că e HCL)
            (r'nr\.?\s*(\d+)[\/\-](\d{4})', 'referă'),
            # Pattern pentru modificări: "se modifică HCL nr. 123/2020"
            (r'(?:se\s+)?modifică.*?(?:HCL\s+)?nr\.?\s*(\d+)[\/\-](\d{4})', 'modifică'),
            # Pattern pentru abrogări: "se abrogă HCL nr. 123/2020"
            (r'(?:se\s+)?abrogă.*?(?:HCL\s+)?nr\.?\s*(\d+)[\/\-](\d{4})', 'abrogă'),
            # Pattern pentru completări: "se completează HCL nr. 123/2020"
            (r'(?:se\s+)?completează.*?(?:HCL\s+)?nr\.?\s*(\d+)[\/\-](\d{4})', 'completează'),
            # Pattern pentru înlocuiri: "se înlocuiește HCL nr. 123/2020"
            (r'(?:se\s+)?înlocuiește.*?(?:HCL\s+)?nr\.?\s*(\d+)[\/\-](\d{4})', 'înlocuiește'),
        ]
        
        references = []
        
        for pattern, default_rel_type in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                hcl_nr = match[0]
                year = match[1]
                
                # Validare că anul pare valid (între 2000-2030)
                try:
                    year_int = int(year)
                    if 2000 <= year_int <= 2030:
                        hcl_key = f"{hcl_nr}/{year}"
                        
                        # Determină tipul relației pe baza pattern-ului
                        if 'modifică' in pattern:
                            rel_type = 'modifică'
                        elif 'abrogă' in pattern:
                            rel_type = 'abrogă'
                        elif 'completează' in pattern:
                            rel_type = 'completează'
                        elif 'înlocuiește' in pattern:
                            rel_type = 'înlocuiește'
                        else:
                            rel_type = default_rel_type
                        
                        references.append((hcl_key, rel_type))
                except ValueError:
                    continue
        
        # Elimină duplicate și păstrează tipul de relație cel mai specific
        unique_refs = {}
        for hcl_key, rel_type in references:
            if hcl_key not in unique_refs:
                unique_refs[hcl_key] = rel_type
            else:
                # Preferă tipurile mai specifice (modifică, abrogă) față de referă
                if rel_type in ['modifică', 'abrogă', 'completează', 'înlocuiește'] and unique_refs[hcl_key] == 'referă':
                    unique_refs[hcl_key] = rel_type
        
        return list(unique_refs.items())
    
    # Test cases cu diferite formate
    test_texts = [
        "Prin Hotărârea Consiliului Local nr. 208/2021 s-a aprobat regulamentul.",
        "Se modifică HCL nr. 123/2020 în sensul că...",
        "Se abrogă hotărârea nr. 456/2019.",
        "În conformitate cu nr. 789/2018, se stabilește...",
        "Prin HCL 345/2022 se completează...",
        "Prin hotărârea nr. 450/07.12.2021 se stabilește...",  # Test cu dată completă
        "Se referă la HCL nr. 271/27.06.2023 pentru detalii."  # Alt test cu dată
    ]
    
    for i, text in enumerate(test_texts, 1):
        print(f"\nTest {i}: {text[:60]}...")
        results = extract_hcl_references_regex(text)
        print(f"Results type: {type(results)}")
        print(f"Results: {results}")
        
        # Verificăm structura fiecărui element
        for j, result in enumerate(results):
            print(f"  Element {j}: {result} (length: {len(result)})")
    
    return True

def test_year_extraction():
    """Test year extraction from dates"""
    print("\n\n📅 TESTING YEAR EXTRACTION")
    print("=" * 50)
    
    test_dates = [
        "2024-10-29",
        "07.12.2021",
        "27.06.2023",
        "2023-02-02",
        "31.03.2020",
        "2022-08-30"
    ]
    
    for date_str in test_dates:
        year_match = re.search(r'(\d{4})', date_str)
        year = year_match.group(1) if year_match else "unknown"
        print(f"Date: {date_str} → Year: {year}")

def main():
    """Main test function"""
    print("🧪 REGEX EXTRACTION TESTS")
    print("=" * 60)
    
    # Run tests
    test_hcl_regex_simple()
    test_year_extraction()
    
    print(f"\n✅ All tests completed!")

if __name__ == "__main__":
    main() 