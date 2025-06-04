# HCL Analysis Pipeline

Un sistem complet pentru analiza și vizualizarea relațiilor între Hotărârile Consiliului Local (HCL) din Timișoara.

## 🏗️ Structura Proiectului

```
TestGraph/
├── main.py                     # Script principal pentru rularea pipeline-ului
├── README.md                   # Această documentație
│
├── 📁 config/                  # Configurări și setări
│   ├── .env                    # Chei API (Gemini)
│   └── requirements.txt        # Dependințe Python
│
├── 📁 datasets/                # Date originale
│   ├── hcl-1k.json            # Date HCL pentru procesare (1000 items)
│   └── hcl_total.json         # Baza de date completă HCL
│
├── 📁 scripts/                 # Toate scripturile organizate pe categorii
│   ├── 📂 extraction/          # Extracția de text și metadate
│   │   ├── hcl_text_extractor.py      # Script principal pentru extracție
│   │   └── hcl_metadata_extractor.py  # Script auxiliar pentru metadate
│   │
│   ├── 📂 graph/               # Construirea și vizualizarea grafurilor
│   │   ├── build_hcl_graph.py         # Script principal pentru graf
│   │   └── hcl_graph_builder.py       # Script auxiliar pentru graf
│   │
│   ├── 📂 analysis/            # Analiza datelor
│   │   └── analyze_extracted_data.py  # Analiză și statistici
│   │
│   └── 📂 utils/               # Utilitare și setup
│       ├── run_hcl_analysis.py        # Runner pentru pipeline complet
│       ├── setup.py                   # Instalare dependințe
│       └── test_quick.py              # Teste rapide
│
├── 📁 results/                 # Rezultatele generate
│   ├── 📂 visualizations/      # Grafice și vizualizări
│   │   ├── hcl_graph_analysis.png     # Analiză statică (matplotlib)
│   │   ├── hcl_graph_interactive.html # Graf interactiv (plotly)
│   │   └── hcl_graph_matplotlib.png   # Vizualizare suplimentară
│   │
│   └── 📂 data_exports/        # Date exportate
│       ├── hcl_extracted_data.json    # Date extrase structurate
│       ├── hcl_graph.json             # Graf în format JSON
│       ├── hcl_graph.gexf             # Graf pentru Gephi
│       └── hcl_adjacency_matrix.csv   # Matricea de adiacență
│
├── 📁 data/                    # Folder auxiliar pentru date temporare
├── 📁 logs/                    # Folder pentru log-uri
└── 📁 output/                  # Folder pentru output temporar
```

## 🚀 Utilizare Rapidă

### 0. Verificare Setup
```bash
# Verifică dacă totul este configurat corect
python verify_setup.py
```

### 1. Configurare Inițială
```bash
# Instalează dependințele
python main.py setup

# Sau manual:
pip install -r config/requirements.txt
```

### 2. Configurare Chei API
Editează `config/.env` și adaugă cheia Gemini:
```
GEMINI_KEY=your_api_key_here
```

### 3. Rulare Pipeline Complet
```bash
# Rulează tot: extracție → graf → analiză
python main.py pipeline
```

### 4. Rulare Modulară
```bash
# Doar extracția de text
python main.py extraction

# Doar construirea grafului  
python main.py graph

# Doar analiza
python main.py analysis

# Help pentru comenzi
python main.py help
```

## 📊 Ce Face Pipeline-ul

### 1. **Extracția de Text** (`scripts/extraction/hcl_text_extractor.py`)
- Procesează primele 100 HCL-uri din `datasets/hcl-1k.json`
- Folosește Gemini AI pentru extragerea metadatelor
- Identifică HCL-urile referențiate și le caută în `datasets/hcl_total.json`
- Generează `results/data_exports/hcl_extracted_data.json`

**Structura datelor extrase:**
```json
{
  "471/2024": {
    "nume": "Titlul HCL",
    "text": "Textul complet din HCL",
    "cuvinte_cheie": ["cuvânt1", "cuvânt2"],
    "hcl_legaturi": [["208/2021", "modifică"]],
    "legi_legaturi": [["Legea nr. 50/1991", "referă"]],
    "entitati_principale": ["Consiliul Local"],
    "data_adoptarii": "2024-10-29",
    "data_publicarii": "2024-11-08",
    "text_length": 1500,
    "num_hcl_legaturi": 3,
    "num_legi_legaturi": 2
  }
}
```

### 2. **Construirea Grafului** (`scripts/graph/build_hcl_graph.py`)
- Creează un graf orientat cu HCL-urile ca noduri
- Relațiile între HCL-uri devin muchii cu tipuri:
  - `modifică` (roșu)
  - `abrogă` (teal)
  - `completează` (albastru)
  - `referă` (verde)
  - `înlocuiește` (galben)
  - `revocă` (gri)

**Ieșiri generate:**
- `results/visualizations/hcl_graph_analysis.png` - Analiză statică
- `results/visualizations/hcl_graph_interactive.html` - Graf interactiv
- `results/data_exports/hcl_graph.json` - Date graf în JSON
- `results/data_exports/hcl_graph.gexf` - Format Gephi
- `results/data_exports/hcl_adjacency_matrix.csv` - Matricea de adiacență

### 3. **Analiza Datelor** (`scripts/analysis/analyze_extracted_data.py`)
- Statistici despre conexiuni și relații
- Identificarea HCL-urilor centrale
- Analiza tipurilor de relații
- Distribuția gradelor în graf

## 🔧 Cerințe Tehnice

### Python Packages (vezi `config/requirements.txt`)
```
google-generativeai==0.3.2
pandas==2.1.4
networkx==3.2.1
matplotlib==3.8.2
plotly==5.17.0
beautifulsoup4==4.12.2
python-dotenv==1.0.0
seaborn==0.13.0
numpy==1.25.2
```

### Chei API (în `config/.env`)
- **Gemini AI**: Pentru procesarea textului și extragerea metadatelor

## 📈 Rezultate Tipice

Un run complet procesează ~100 HCL-uri și generează:
- **Graf cu ~150+ noduri și ~200+ muchii**
- **Densitate graf: ~0.01-0.05**
- **Tipuri relații**: referă (majoritatea), modifică, completează, etc.
- **HCL cel mai referențiat**: de obicei regulamente fundamentale

## 🛠️ Dezvoltare și Extensii

### Adăugarea de noi funcționalități:
1. **Extracție**: Modifică `scripts/extraction/hcl_text_extractor.py`
2. **Vizualizare**: Extinde `scripts/graph/build_hcl_graph.py`
3. **Analiză**: Adaugă în `scripts/analysis/`

### Scripturi Auxiliare:
- `scripts/utils/test_quick.py` - Teste rapide fără API
- `scripts/utils/setup.py` - Instalare automată dependințe
- `scripts/utils/run_hcl_analysis.py` - Runner alternativ

### Testing:
```bash
python scripts/utils/test_quick.py
```

## 📁 Fișiere Importante

### Configurare:
- `config/.env` - Chei API
- `config/requirements.txt` - Dependințe Python

### Date:
- `datasets/hcl-1k.json` - Dataset principal pentru procesare
- `datasets/hcl_total.json` - Baza de date completă pentru referințe

### Rezultate:
- `results/data_exports/hcl_extracted_data.json` - Date procesate
- `results/visualizations/hcl_graph_interactive.html` - Graf interactiv
- `results/visualizations/hcl_graph_analysis.png` - Analiză vizuală

## 🚦 Workflow Tipic

1. **Setup inițial**: `python main.py setup`
2. **Configurare .env**: Adaugă cheia Gemini în `config/.env`
3. **Extracție**: `python main.py extraction` (procesează HCL-uri + referințe)
4. **Construire graf**: `python main.py graph` (creează vizualizări)
5. **Analiză**: `python main.py analysis` (statistici detaliate)

Sau simplu: `python main.py pipeline` pentru tot.

## 📝 Licență și Contact

Proiect dezvoltat pentru analiza documentelor administrative locale.
Pentru întrebări și sugestii, consultați documentația din fiecare script individual.
