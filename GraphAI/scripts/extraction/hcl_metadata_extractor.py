#!/usr/bin/env python3
"""
HCL Metadata Extractor - Extracts metadata and references from HCL documents using Gemini API
"""

import json
import os
import pandas as pd
import re
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import google.generativeai as genai
from typing import Dict, List, Tuple, Any
import time

# Load environment variables
load_dotenv()

class HCLMetadataExtractor:
    def __init__(self):
        """Initialize the metadata extractor with Gemini API"""
        self.api_key = os.getenv('GEMINI_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_KEY not found in environment variables")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
    def clean_html_text(self, html_text: str) -> str:
        """Clean HTML tags from text"""
        if not html_text:
            return ""
        soup = BeautifulSoup(html_text, 'html.parser')
        return soup.get_text(separator=' ', strip=True)
    
    def load_hcl_data(self, file_path: str) -> List[Dict[str, Any]]:
        """Load HCL data from JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data['data']['hcl']
        except Exception as e:
            print(f"Error loading HCL data: {e}")
            return []
    
    def extract_metadata_with_gemini(self, hcl_item: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata from HCL using Gemini API"""
        
        # Prepare the text for analysis
        motivatie_text = self.clean_html_text(hcl_item.get('motivatie', ''))
        articole_text = self.clean_html_text(hcl_item.get('articole', ''))
        
        full_text = f"""
        MOTIVATIE: {motivatie_text}
        
        ARTICOLE: {articole_text}
        """
        
        prompt = f"""
        Analizează următorul text dintr-o Hotărâre a Consiliului Local (HCL) și extrage următoarele informații în format JSON:

        1. "hcl_references": o listă cu toate referințele la alte HCL-uri (de exemplu: "Hotărârea Consiliului Local nr. 208/2021", "HCL nr. 123/2020", etc.)
        2. "law_references": o listă cu toate referințele la legi, ordonanțe, ordine (de exemplu: "Ordonanța de Urgență nr. 57/2019", "Legii nr. 7/1996", etc.)
        3. "regulatory_references": o listă cu alte referințe la regulamente, hotărâri de guvern, etc.
        4. "relationship_indicators": o listă cu indicatori care sugerează tipul de relație cu alte acte (caută cuvinte precum: "modifică", "abrogă", "completează", "înlocuiește", "suspendă")
        5. "subject_matter": o descriere scurtă a subiectului principal al HCL-ului
        6. "entities_involved": o listă cu entitățile/instituțiile menționate în text

        Text HCL:
        {full_text}

        Răspunde DOAR cu un JSON valid, fără text suplimentar:
        """
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Extract JSON from response (in case there's extra text)
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_text = response_text[json_start:json_end]
                metadata = json.loads(json_text)
            else:
                # Fallback parsing
                metadata = json.loads(response_text)
            
            return metadata
            
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON response for HCL {hcl_item.get('nr', 'unknown')}: {e}")
            print(f"Response was: {response.text}")
            return self._create_empty_metadata()
        except Exception as e:
            print(f"Error calling Gemini API for HCL {hcl_item.get('nr', 'unknown')}: {e}")
            return self._create_empty_metadata()
    
    def _create_empty_metadata(self) -> Dict[str, Any]:
        """Create empty metadata structure"""
        return {
            "hcl_references": [],
            "law_references": [],
            "regulatory_references": [],
            "relationship_indicators": [],
            "subject_matter": "",
            "entities_involved": []
        }
    
    def extract_hcl_references_regex(self, text: str) -> List[str]:
        """Extract HCL references using regex as backup"""
        patterns = [
            r'Hotărârea Consiliului Local nr\.\s*(\d+[\/\-]\d{4})',
            r'HCL nr\.\s*(\d+[\/\-]\d{4})',
            r'hotărârea nr\.\s*(\d+[\/\-]\d{4})',
            r'Hotărârea nr\.\s*(\d+[\/\-]\d{4})'
        ]
        
        references = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            references.extend(matches)
        
        return list(set(references))  # Remove duplicates
    
    def determine_relationship_type(self, metadata: Dict[str, Any], text: str) -> str:
        """Determine the relationship type based on indicators"""
        indicators = metadata.get('relationship_indicators', [])
        text_lower = text.lower()
        
        # Check for specific relationship indicators
        if any('modifică' in ind.lower() or 'modific' in text_lower for ind in indicators):
            return 'modifică'
        elif any('abrogă' in ind.lower() or 'abrog' in text_lower for ind in indicators):
            return 'abrogă'
        elif any('completează' in ind.lower() or 'complet' in text_lower for ind in indicators):
            return 'completează'
        else:
            return 'referă'  # Default relationship type
    
    def process_hcl_batch(self, hcl_list: List[Dict[str, Any]], max_items: int = 10) -> pd.DataFrame:
        """Process a batch of HCL items and extract metadata"""
        
        results = []
        
        for i, hcl_item in enumerate(hcl_list[:max_items]):
            print(f"Processing HCL {i+1}/{min(max_items, len(hcl_list))}: nr. {hcl_item.get('nr', 'unknown')}")
            
            # Extract metadata using Gemini
            metadata = self.extract_metadata_with_gemini(hcl_item)
            
            # Prepare full text for relationship analysis
            full_text = self.clean_html_text(hcl_item.get('motivatie', '')) + " " + \
                       self.clean_html_text(hcl_item.get('articole', ''))
            
            # Extract basic info
            result = {
                'hcl_nr': hcl_item.get('nr', ''),
                'data_adoptarii': hcl_item.get('dataAdoptarii', ''),
                'data_publicarii': hcl_item.get('dataPublicarii', ''),
                'subject_matter': metadata.get('subject_matter', ''),
                'hcl_references': metadata.get('hcl_references', []),
                'law_references': metadata.get('law_references', []),
                'regulatory_references': metadata.get('regulatory_references', []),
                'relationship_indicators': metadata.get('relationship_indicators', []),
                'entities_involved': metadata.get('entities_involved', []),
                'relationship_type': self.determine_relationship_type(metadata, full_text),
                'full_text': full_text[:1000] + "..." if len(full_text) > 1000 else full_text  # Truncate for storage
            }
            
            results.append(result)
            
            # Add a small delay to respect API limits
            time.sleep(1)
        
        return pd.DataFrame(results)
    
    def save_metadata_to_csv(self, df: pd.DataFrame, output_file: str = 'hcl_metadata.csv'):
        """Save metadata DataFrame to CSV"""
        df.to_csv(output_file, index=False, encoding='utf-8')
        print(f"Metadata saved to {output_file}")
    
    def create_relationships_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create a relationships DataFrame for graph construction"""
        relationships = []
        
        for index, row in df.iterrows():
            source_hcl = row['hcl_nr']
            hcl_refs = row['hcl_references']
            relationship_type = row['relationship_type']
            
            # Extract HCL numbers from references
            for ref in hcl_refs:
                # Try to extract HCL number from reference text
                hcl_numbers = re.findall(r'(\d+)[\/\-](\d{4})', str(ref))
                for hcl_num, year in hcl_numbers:
                    target_hcl = f"{hcl_num}"
                    
                    relationships.append({
                        'source': source_hcl,
                        'target': target_hcl,
                        'relationship_type': relationship_type,
                        'reference_text': str(ref),
                        'year': year
                    })
        
        return pd.DataFrame(relationships)

def main():
    """Main function to execute the metadata extraction"""
    
    print("Starting HCL Metadata Extraction...")
    
    # Initialize extractor
    extractor = HCLMetadataExtractor()
    
    # Load HCL data
    hcl_data = extractor.load_hcl_data('hcl-1k.json')
    
    if not hcl_data:
        print("No HCL data found!")
        return
    
    print(f"Loaded {len(hcl_data)} HCL items")
    
    # Process first 10 HCL items
    print("Processing first 20 HCL items...")
    metadata_df = extractor.process_hcl_batch(hcl_data, max_items=20)
    
    # Save metadata
    extractor.save_metadata_to_csv(metadata_df, 'hcl_metadata.csv')
    
    # Create relationships DataFrame
    relationships_df = extractor.create_relationships_dataframe(metadata_df)
    
    # Save relationships
    relationships_df.to_csv('hcl_relationships.csv', index=False, encoding='utf-8')
    print(f"Relationships saved to hcl_relationships.csv")
    
    # Display summary
    print(f"\nSummary:")
    print(f"- Processed {len(metadata_df)} HCL items")
    print(f"- Found {len(relationships_df)} relationships")
    print(f"- Unique relationship types: {relationships_df['relationship_type'].unique()}")
    
    # Display sample data
    print(f"\nSample metadata:")
    print(metadata_df[['hcl_nr', 'subject_matter', 'relationship_type']].head())
    
    print(f"\nSample relationships:")
    print(relationships_df.head())

if __name__ == "__main__":
    main() 