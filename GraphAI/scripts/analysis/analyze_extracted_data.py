#!/usr/bin/env python3
"""
Script pentru analiza datelor extrase din HCL-uri
Afișează statistici despre structura de date creată
"""

import json
from collections import Counter, defaultdict
from typing import Dict, List, Any

def load_extracted_data(file_path: str = 'results/data_exports/hcl_extracted_data.json') -> Dict[str, Dict[str, Any]]:
    """Încarcă datele extrase din JSON"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Eroare la încărcarea datelor: {e}")
        return {}

def analyze_hcl_connections(data: Dict[str, Dict[str, Any]]):
    """Analizează conexiunile între HCL-uri"""
    print("🔗 ANALIZA CONEXIUNILOR ÎNTRE HCL-URI")
    print("="*50)
    
    # Colectează toate conexiunile HCL
    all_connections = []
    relationship_types = Counter()
    
    for hcl_nr, hcl_data in data.items():
        hcl_legaturi = hcl_data.get('hcl_legaturi', [])
        for connection in hcl_legaturi:
            # Handle both tuple and list formats (JSON converts tuples to lists)
            if len(connection) >= 2:
                target_hcl = connection[0]
                rel_type = connection[1]
                all_connections.append((hcl_nr, str(target_hcl), rel_type))
                relationship_types[rel_type] += 1
    
    print(f"Total conexiuni HCL găsite: {len(all_connections)}")
    print(f"\nTipuri de relații între HCL-uri:")
    for rel_type, count in relationship_types.most_common():
        print(f"  {rel_type}: {count} conexiuni")
    
    # Găsește HCL-urile cele mai referențiate
    target_counts = Counter(target for _, target, _ in all_connections)
    print(f"\nHCL-urile cele mai referențiate:")
    for hcl_nr, count in target_counts.most_common(5):
        print(f"  HCL {hcl_nr}: referențiat de {count} alte HCL-uri")
    
    # Găsește HCL-urile care referențiază cel mai mult
    source_counts = Counter(source for source, _, _ in all_connections)
    print(f"\nHCL-urile care referențiază cel mai mult:")
    for hcl_nr, count in source_counts.most_common(5):
        print(f"  HCL {hcl_nr}: referențiază {count} alte HCL-uri")

def analyze_law_connections(data: Dict[str, Dict[str, Any]]):
    """Analizează conexiunile cu legile"""
    print("\n📜 ANALIZA CONEXIUNILOR CU LEGILE")
    print("="*50)
    
    # Colectează toate conexiunile cu legi
    all_law_connections = []
    law_relationship_types = Counter()
    
    for hcl_nr, hcl_data in data.items():
        legi_legaturi = hcl_data.get('legi_legaturi', [])
        for connection in legi_legaturi:
            # Handle both tuple and list formats (JSON converts tuples to lists)
            if len(connection) >= 2:
                law_nr = connection[0]
                rel_type = connection[1]
                all_law_connections.append((hcl_nr, law_nr, rel_type))
                law_relationship_types[rel_type] += 1
    
    print(f"Total conexiuni cu legi găsite: {len(all_law_connections)}")
    print(f"\nTipuri de relații cu legile:")
    for rel_type, count in law_relationship_types.most_common():
        print(f"  {rel_type}: {count} conexiuni")
    
    # Găsește legile cele mai referențiate
    law_counts = Counter(law for _, law, _ in all_law_connections)
    print(f"\nLegile cele mai referențiate:")
    for law_nr, count in law_counts.most_common(10):
        print(f"  Legea/OUG {law_nr}: referențiată de {count} HCL-uri")

def analyze_keywords(data: Dict[str, Dict[str, Any]]):
    """Analizează cuvintele cheie"""
    print("\n🔍 ANALIZA CUVINTELOR CHEIE")
    print("="*50)
    
    # Colectează toate cuvintele cheie
    all_keywords = []
    for hcl_nr, hcl_data in data.items():
        keywords = hcl_data.get('cuvinte_cheie', [])
        all_keywords.extend(keywords)
    
    keyword_counts = Counter(all_keywords)
    
    print(f"Total cuvinte cheie găsite: {len(all_keywords)}")
    print(f"Cuvinte cheie unice: {len(keyword_counts)}")
    print(f"\nCele mai frecvente cuvinte cheie:")
    for keyword, count in keyword_counts.most_common(15):
        print(f"  '{keyword}': {count} apariții")

def analyze_entities(data: Dict[str, Dict[str, Any]]):
    """Analizează entitățile principale"""
    print("\n🏢 ANALIZA ENTITĂȚILOR PRINCIPALE")
    print("="*50)
    
    # Colectează toate entitățile
    all_entities = []
    for hcl_nr, hcl_data in data.items():
        entities = hcl_data.get('entitati_principale', [])
        all_entities.extend(entities)
    
    entity_counts = Counter(all_entities)
    
    print(f"Total entități găsite: {len(all_entities)}")
    print(f"Entități unice: {len(entity_counts)}")
    print(f"\nCele mai frecvente entități:")
    for entity, count in entity_counts.most_common(10):
        print(f"  '{entity}': {count} apariții")

def analyze_text_statistics(data: Dict[str, Dict[str, Any]]):
    """Analizează statistici despre text"""
    print("\n📊 STATISTICI DESPRE TEXT")
    print("="*50)
    
    text_lengths = []
    for hcl_nr, hcl_data in data.items():
        text_length = hcl_data.get('text_length', 0)
        text_lengths.append(text_length)
    
    if text_lengths:
        avg_length = sum(text_lengths) / len(text_lengths)
        min_length = min(text_lengths)
        max_length = max(text_lengths)
        
        print(f"Lungime medie text: {avg_length:.0f} caractere")
        print(f"Lungime minimă text: {min_length} caractere")
        print(f"Lungime maximă text: {max_length} caractere")
        
        # Găsește HCL-urile cu cel mai mult/puțin text
        text_by_hcl = [(hcl_nr, data[hcl_nr].get('text_length', 0)) for hcl_nr in data.keys()]
        text_by_hcl.sort(key=lambda x: x[1], reverse=True)
        
        print(f"\nHCL-uri cu cel mai mult text:")
        for hcl_nr, length in text_by_hcl[:3]:
            nume = data[hcl_nr].get('nume', 'N/A')[:50]
            print(f"  HCL {hcl_nr}: {length} caractere - '{nume}...'")

def show_sample_hcl(data: Dict[str, Dict[str, Any]], hcl_nr: str):
    """Afișează un exemplu detaliat de HCL"""
    if hcl_nr not in data:
        print(f"HCL {hcl_nr} nu a fost găsit în date!")
        return
    
    hcl_data = data[hcl_nr]
    
    print(f"\n📄 EXEMPLU DETALIAT - HCL {hcl_nr}")
    print("="*50)
    
    print(f"Nume: {hcl_data.get('nume', 'N/A')}")
    print(f"Data adoptării: {hcl_data.get('data_adoptarii', 'N/A')}")
    print(f"Lungime text: {hcl_data.get('text_length', 0)} caractere")
    
    print(f"\nCuvinte cheie ({len(hcl_data.get('cuvinte_cheie', []))}):")
    for keyword in hcl_data.get('cuvinte_cheie', []):
        print(f"  • {keyword}")
    
    print(f"\nLegături HCL ({len(hcl_data.get('hcl_legaturi', []))}):")
    for connection in hcl_data.get('hcl_legaturi', []):
        # Handle both tuple and list formats (JSON converts tuples to lists)
        if len(connection) >= 2:
            target_hcl = connection[0]
            rel_type = connection[1]
            print(f"  • HCL {target_hcl} ({rel_type})")
    
    print(f"\nLegături cu legi ({len(hcl_data.get('legi_legaturi', []))}):")
    for connection in hcl_data.get('legi_legaturi', []):
        # Handle both tuple and list formats (JSON converts tuples to lists)
        if len(connection) >= 2:
            law_nr = connection[0]
            rel_type = connection[1]
            print(f"  • Legea/OUG {law_nr} ({rel_type})")
    
    print(f"\nEntități principale ({len(hcl_data.get('entitati_principale', []))}):")
    for entity in hcl_data.get('entitati_principale', []):
        print(f"  • {entity}")
    
    print(f"\nFișiere atașate ({len(hcl_data.get('fisiere_atasate', []))}):")
    for file in hcl_data.get('fisiere_atasate', []):
        if file:  # Skip empty strings
            print(f"  • {file}")

def main():
    """Funcția principală"""
    print("ANALIZA DATELOR EXTRASE DIN HCL-URI")
    print("="*60)
    
    # Încarcă datele
    data = load_extracted_data()
    
    if not data:
        print("Nu s-au putut încărca datele!")
        return
    
    print(f"📈 Numărul total de HCL-uri procesate: {len(data)}")
    print(f"📈 HCL-uri analizate: {', '.join(data.keys())}")
    
    # Analize generale
    analyze_hcl_connections(data)
    analyze_law_connections(data)
    analyze_keywords(data)
    analyze_entities(data)
    analyze_text_statistics(data)
    
    # Afișează câteva exemple
    hcl_examples = list(data.keys())[:2]  # Primele 2 HCL-uri
    for hcl_nr in hcl_examples:
        show_sample_hcl(data, hcl_nr)
    
    print(f"\n🎉 ANALIZA COMPLETĂ!")
    print(f"Datele sunt salvate în 'hcl_extracted_data.json'")
    print(f"Structura de date corespunde cerințelor:")
    print(f"  ✓ Key: numărul HCL-ului")
    print(f"  ✓ Value: dicționar cu nume, text, cuvinte_cheie, legături HCL, legături legi, etc.")

if __name__ == "__main__":
    main() 