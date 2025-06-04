#!/usr/bin/env python3
"""
HCL Text Extractor - Specialized extractor for creating organized HCL data structure
Creates a dictionary with HCL number as key and detailed information as value
"""

import json
import os
import re
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import google.generativeai as genai
from typing import Dict, List, Tuple, Any
import time

# Load environment variables
load_dotenv()

class HCLTextExtractor:
    def __init__(self):
        """Initialize the text extractor with Gemini API"""
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
    
    def load_hcl_data(self, file_path: str = 'datasets/hcl-1k.json') -> List[Dict[str, Any]]:
        """Load HCL data from JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data['data']['hcl']
        except Exception as e:
            print(f"Error loading HCL data: {e}")
            return []
    
    def extract_hcl_references_regex(self, text: str) -> List[Tuple[str, str]]:
        """Extract HCL references using regex - more reliable than AI"""
        import re
        
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
    
    def extract_law_references_regex(self, text: str) -> List[Tuple[str, str]]:
        """Extract law references using regex"""
        import re
        
        patterns = [
            # "Legea nr. 50/1991"
            (r'Legea\s+nr\.?\s*(\d+)[\/\-](\d{4})', 'referă'),
            # "Ordonanța de Urgență nr. 123/2020" sau "OUG nr. 123/2020"
            (r'(?:Ordonanța\s+de\s+Urgență|OUG)(?:\s+a\s+Guvernului)?\s+nr\.?\s*(\d+)[\/\-](\d{4})', 'referă'),
            # "Hotărârea de Guvern nr. 123/2020" sau "HG nr. 123/2020"
            (r'(?:Hotărârea\s+de\s+Guvern|HG)\s+nr\.?\s*(\d+)[\/\-](\d{4})', 'referă'),
            # "Ordonanța Guvernului nr. 123/2020"
            (r'Ordonanța\s+Guvernului\s+nr\.?\s*(\d+)[\/\-](\d{4})', 'referă'),
        ]
        
        references = []
        
        for pattern, rel_type in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                law_nr = match[0]
                year = match[1]
                
                # Validare anul
                try:
                    year_int = int(year)
                    if 1950 <= year_int <= 2030:  # Range mai larg pentru legi
                        law_key = f"nr. {law_nr}/{year}"
                        references.append((law_key, rel_type))
                except ValueError:
                    continue
        
        # Elimină duplicate
        return list(set(references))
    
    def extract_detailed_info_with_gemini(self, hcl_item: Dict[str, Any]) -> Dict[str, Any]:
        """Extract detailed information from HCL using Gemini API - without HCL references"""
        
        # Prepare the text for analysis
        motivatie_text = self.clean_html_text(hcl_item.get('motivatie', ''))
        articole_text = self.clean_html_text(hcl_item.get('articole', ''))
        
        full_text = f"MOTIVATIE: {motivatie_text}\n\nARTICOLE: {articole_text}"
        
        prompt = f"""
        Analizează următorul text dintr-o Hotărâre a Consiliului Local (HCL) și extrage următoarele informații în format JSON:

        1. "nume": un titlu scurt și descriptiv pentru acest HCL (maxim 100 caractere)
        2. "cuvinte_cheie": o listă cu 5-10 cuvinte/fraze cheie care caracterizează cel mai bine acest HCL
        3. "entitati_principale": o listă cu 3-5 entități/instituții principale menționate în text
        4. "data_info": orice informații despre date relevante din text (altele decât data adoptării)

        NU include "hcl_legaturi" și "legi_legaturi" - acestea vor fi extrase separat prin script.

        Text HCL:
        {full_text}

        Răspunde DOAR cu un JSON valid, fără text suplimentar:
        """
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Extract JSON from response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_text = response_text[json_start:json_end]
                metadata = json.loads(json_text)
            else:
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
            "nume": "",
            "cuvinte_cheie": [],
            "entitati_principale": [],
            "data_info": []
        }
    
    def process_hcl_item(self, hcl_item: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Process a single HCL item and return (hcl_nr_with_year, data_dict)"""
        
        hcl_nr = hcl_item.get('nr', '')
        data_adoptarii = hcl_item.get('dataAdoptarii', '')
        
        # Extract year from adoption date using regex - more reliable
        year = "unknown"
        if data_adoptarii:
            try:
                # Extract only the year (4 digits) from date string
                import re
                year_match = re.search(r'(\d{4})', data_adoptarii)
                if year_match:
                    year = year_match.group(1)
            except:
                year = "unknown"
        
        # Create HCL key with year format
        hcl_key = f"{hcl_nr}/{year}"
        
        print(f"Processing HCL nr. {hcl_key}")
        
        # Get basic information
        data_publicarii = hcl_item.get('dataPublicarii', '')
        
        # Clean and combine text
        motivatie_text = self.clean_html_text(hcl_item.get('motivatie', ''))
        articole_text = self.clean_html_text(hcl_item.get('articole', ''))
        full_text = f"MOTIVATIE:\n{motivatie_text}\n\nARTICOLE:\n{articole_text}"
        
        # Extract detailed info using Gemini (without HCL/law references)
        gemini_data = self.extract_detailed_info_with_gemini(hcl_item)
        
        # Extract HCL references using regex (more reliable)
        print(f"  Extracting HCL references using regex...")
        hcl_refs_regex = self.extract_hcl_references_regex(full_text)
        print(f"  Found {len(hcl_refs_regex)} HCL references: {hcl_refs_regex}")
        
        # Extract law references using regex
        print(f"  Extracting law references using regex...")
        law_refs_regex = self.extract_law_references_regex(full_text)
        print(f"  Found {len(law_refs_regex)} law references: {law_refs_regex}")
        
        # Create the final data structure
        hcl_data = {
            'nume': gemini_data.get('nume', f"HCL {hcl_key}"),
            'text': full_text,
            'data_adoptarii': data_adoptarii,
            'data_publicarii': data_publicarii,
            'cuvinte_cheie': gemini_data.get('cuvinte_cheie', []),
            'hcl_legaturi': hcl_refs_regex,  # Use regex results
            'legi_legaturi': law_refs_regex,  # Use regex results
            'entitati_principale': gemini_data.get('entitati_principale', []),
            'data_info': gemini_data.get('data_info', []),
            'fisiere_atasate': [f.get('file', {}).get('filenameDownload', '') 
                               for f in hcl_item.get('fisiereAtasate', [])],
            'text_length': len(full_text),
            'num_hcl_legaturi': len(hcl_refs_regex),
            'num_legi_legaturi': len(law_refs_regex)
        }
        
        return hcl_key, hcl_data
    
    def extract_hcl_batch(self, hcl_list: List[Dict[str, Any]], max_items: int = 100) -> Dict[str, Dict[str, Any]]:
        """Extract information from a batch of HCL items"""
        
        extracted_data = {}
        
        for i, hcl_item in enumerate(hcl_list[:max_items]):
            try:
                hcl_key, hcl_data = self.process_hcl_item(hcl_item)
                extracted_data[hcl_key] = hcl_data
                
                # Add a small delay to respect API limits
                time.sleep(1)
                
            except Exception as e:
                hcl_key = hcl_item.get('nr', f'unknown_{i}')
                print(f"Error processing HCL {hcl_key}: {e}")
                continue
        
        return extracted_data
    
    def save_extracted_data(self, data: Dict[str, Dict[str, Any]], output_file: str = 'results/data_exports/hcl_extracted_data.json'):
        """Save extracted data to JSON file"""
        try:
            # Create output directory if it doesn't exist
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"Extracted data saved to {output_file}")
            return True
        except Exception as e:
            print(f"Error saving data: {e}")
            return False
    
    def print_summary(self, data: Dict[str, Dict[str, Any]]):
        """Print a summary of the extracted data"""
        print(f"\n" + "="*50)
        print("EXTRACTION SUMMARY")
        print("="*50)
        
        print(f"Total HCL items processed: {len(data)}")
        
        # Count statistics
        total_hcl_connections = sum(item['num_hcl_legaturi'] for item in data.values())
        total_law_connections = sum(item['num_legi_legaturi'] for item in data.values())
        
        print(f"Total HCL connections found: {total_hcl_connections}")
        print(f"Total law connections found: {total_law_connections}")
        
        # Show sample data
        print(f"\nSample extracted items:")
        for i, (hcl_key, hcl_data) in enumerate(list(data.items())[:3]):
            print(f"\nHCL {hcl_key}:")
            print(f"  Nume: {hcl_data['nume'][:80]}...")
            print(f"  Cuvinte cheie: {hcl_data['cuvinte_cheie'][:5]}")
            print(f"  HCL legături ({len(hcl_data['hcl_legaturi'])}): {hcl_data['hcl_legaturi'][:3]}")
            print(f"  Legi legături ({len(hcl_data['legi_legaturi'])}): {hcl_data['legi_legaturi'][:3]}")
            print(f"  Text length: {hcl_data['text_length']} characters")
    
    def load_hcl_total_data(self, file_path: str = 'datasets/hcl_total.json') -> List[Dict[str, Any]]:
        """Load HCL data from total JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Check if data is directly a list or has nested structure
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict) and 'data' in data and 'hcl' in data['data']:
                    return data['data']['hcl']
                else:
                    print(f"Unexpected data structure in {file_path}")
                    return []
        except Exception as e:
            print(f"Error loading HCL total data: {e}")
            return []

    def find_referenced_hcls(self, extracted_data: Dict[str, Dict[str, Any]], all_hcl_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find all HCL documents referenced in the extracted data from hcl_total.json"""
        
        # Load the complete HCL data from hcl_total.json
        print("Loading complete HCL data from datasets/hcl_total.json...")
        hcl_total_data = self.load_hcl_total_data('datasets/hcl_total.json')
        
        if not hcl_total_data:
            print("Could not load hcl_total.json, using provided data instead")
            hcl_total_data = all_hcl_data
        else:
            print(f"Loaded {len(hcl_total_data)} HCL items from hcl_total.json")
        
        # Collect all referenced HCL numbers
        referenced_hcl_numbers = set()
        
        for hcl_key, hcl_data in extracted_data.items():
            hcl_legaturi = hcl_data.get('hcl_legaturi', [])
            for connection in hcl_legaturi:
                if len(connection) == 2:
                    referenced_hcl_nr = connection[0]  # Format: "208/2021"
                    referenced_hcl_numbers.add(referenced_hcl_nr)
        
        print(f"Found {len(referenced_hcl_numbers)} referenced HCL numbers: {list(referenced_hcl_numbers)}")
        
        # Find these HCLs in the hcl_total.json data
        found_hcls = []
        
        for referenced_hcl_nr in referenced_hcl_numbers:
            # Parse the referenced HCL number and year
            try:
                if '/' in referenced_hcl_nr:
                    hcl_nr, target_year = referenced_hcl_nr.split('/')
                else:
                    hcl_nr = referenced_hcl_nr
                    target_year = None
                
                print(f"Searching for HCL nr={hcl_nr}, year={target_year}")
                
                # Search for this HCL in the total data
                for hcl_item in hcl_total_data:
                    item_nr = str(hcl_item.get('nr', ''))
                    item_date = hcl_item.get('dataAdoptarii', '')
                    
                    # Extract year from the item's adoption date
                    item_year = None
                    if item_date:
                        import re
                        year_match = re.search(r'(\d{4})', item_date)
                        if year_match:
                            item_year = year_match.group(1)
                    
                    # Match by HCL number and year
                    if item_nr == hcl_nr:
                        if target_year is None or item_year == target_year:
                            found_hcls.append(hcl_item)
                            print(f"✓ Found referenced HCL {item_nr}/{item_year} (date: {item_date})")
                            break
                else:
                    print(f"✗ Could not find referenced HCL {referenced_hcl_nr}")
                    
            except Exception as e:
                print(f"Error parsing referenced HCL {referenced_hcl_nr}: {e}")
        
        print(f"Successfully found {len(found_hcls)} referenced HCL documents to process")
        return found_hcls
    
    def process_referenced_hcls(self, extracted_data: Dict[str, Dict[str, Any]], all_hcl_data: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Process all HCL documents referenced in the initially extracted data"""
        
        print(f"\n" + "="*50)
        print("PROCESSING REFERENCED HCL DOCUMENTS")
        print("="*50)
        
        # Find referenced HCLs
        referenced_hcls = self.find_referenced_hcls(extracted_data, all_hcl_data)
        
        if not referenced_hcls:
            print("No referenced HCLs found to process.")
            return extracted_data
        
        # Process the referenced HCLs
        print(f"\nProcessing {len(referenced_hcls)} referenced HCL documents...")
        
        for i, hcl_item in enumerate(referenced_hcls):
            try:
                hcl_key, hcl_data = self.process_hcl_item(hcl_item)
                
                # Only add if not already processed
                if hcl_key not in extracted_data:
                    extracted_data[hcl_key] = hcl_data
                    print(f"✓ Added referenced HCL {hcl_key}")
                else:
                    print(f"⚠ HCL {hcl_key} already processed, skipping")
                
                # Add a small delay to respect API limits
                time.sleep(1)
                
            except Exception as e:
                hcl_nr = hcl_item.get('nr', f'unknown_ref_{i}')
                print(f"Error processing referenced HCL {hcl_nr}: {e}")
                continue
        
        return extracted_data

def main():
    """Main function to execute the text extraction"""
    
    print("HCL TEXT EXTRACTION - SPECIALIZED EXTRACTOR")
    print("="*50)
    print("Creating organized data structure for HCL analysis...")
    print()
    
    # Initialize extractor
    extractor = HCLTextExtractor()
    
    # Load HCL data
    hcl_data = extractor.load_hcl_data()
    
    if not hcl_data:
        print("No HCL data found!")
        return
    
    print(f"Loaded {len(hcl_data)} HCL items")
    print("Processing first 20 HCL items...")
    
    # Extract data from initial 10 HCLs
    extracted_data = extractor.extract_hcl_batch(hcl_data, max_items=20)
    
    print(f"✓ Initial extraction completed with {len(extracted_data)} HCL items")
    
    # Now process all referenced HCLs from the initial extraction
    extracted_data = extractor.process_referenced_hcls(extracted_data, hcl_data)
    
    # Save to JSON
    if extractor.save_extracted_data(extracted_data, 'results/data_exports/hcl_extracted_data.json'):
        print("✓ Complete data extraction saved successfully!")
    
    # Print final summary
    extractor.print_summary(extracted_data)
    
    print(f"\n🎉 COMPLETE EXTRACTION FINISHED!")
    print(f"Total HCL items processed: {len(extracted_data)}")
    print(f"Check 'results/data_exports/hcl_extracted_data.json' for the complete results.")
    print(f"Structure: Dictionary with keys in format 'nr/year' (e.g., '471/2024')")

if __name__ == "__main__":
    main() 