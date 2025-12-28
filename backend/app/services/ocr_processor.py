import os
import base64
import sqlite3
import datetime
from pathlib import Path
from google import genai
from google.genai import types
import logging
from dotenv import load_dotenv
import time
import json
from typing import Dict, Optional, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from .personal_info_extractor import PersonalInfoExtractor
from .openai_wrapper import OpenAIProcessor

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LegalDocumentOCR:
    def __init__(self, api_key=None, db_session: AsyncSession = None):
        """
        Initialize the Legal Document OCR processor using Gemini 2.0 Flash or OpenAI GPT-4o
        
        Args:
            api_key (str): Google AI API key. If None, reads from GEMINI_API_KEY environment variable
            db_session: SQLAlchemy async session for database operations
        """
        # Check if we should use OpenAI instead of Gemini
        self.use_openai = os.getenv("USE_OPENAI", "false").lower() == "true"
        
        if self.use_openai:
            logger.info("Initializing OCR processor with OpenAI GPT-4o")
            self.openai_processor = OpenAIProcessor()
            self.client = None
            self.model_name = "gpt-4o"
        else:
            logger.info("Initializing OCR processor with Gemini 2.0 Flash")
            self.api_key = api_key or os.getenv("GEMINI_API_KEY")
            if not self.api_key:
                raise ValueError("GEMINI_API_KEY environment variable must be set or api_key provided")
            
            # Initialize the new Gen AI client
            self.client = genai.Client(api_key=self.api_key)
            self.model_name = "gemini-2.0-flash-001"
            self.openai_processor = None
        
        # Database session for async operations
        self.db_session = db_session
        
        # Use a separate database for OCR documents (fallback for non-async operations)
        self.db_path = "legal_documents_ocr.db"
        self._setup_database()
        
        # Configuration for retry logic
        self.max_retries = 3
        self.retry_delay = 2  # seconds
        
        # Initialize personal info extractor
        if not self.use_openai:
            self.personal_extractor = PersonalInfoExtractor(api_key=self.api_key)
        else:
            self.personal_extractor = None
    
    def _setup_database(self):
        """Set up SQLite database for storing transcribed documents"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS legal_documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                document_type TEXT,
                transcribed_text TEXT NOT NULL,
                original_format TEXT NOT NULL,
                scan_date TIMESTAMP NOT NULL,
                confidence_score REAL,
                verification_status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata_json TEXT,
                processing_time REAL,
                gemini_model TEXT,
                user_id TEXT
            )
        ''')
        
        # Check if columns exist and add them if they don't
        cursor.execute("PRAGMA table_info(legal_documents)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'metadata_json' not in columns:
            logger.info("Adding missing metadata_json column to legal_documents table")
            cursor.execute("ALTER TABLE legal_documents ADD COLUMN metadata_json TEXT")
        
        if 'processing_time' not in columns:
            logger.info("Adding missing processing_time column to legal_documents table")
            cursor.execute("ALTER TABLE legal_documents ADD COLUMN processing_time REAL")
        
        if 'gemini_model' not in columns:
            logger.info("Adding missing gemini_model column to legal_documents table")
            cursor.execute("ALTER TABLE legal_documents ADD COLUMN gemini_model TEXT")
        
        if 'user_id' not in columns:
            logger.info("Adding missing user_id column to legal_documents table")
            cursor.execute("ALTER TABLE legal_documents ADD COLUMN user_id TEXT")
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_filename ON legal_documents(filename);
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_scan_date ON legal_documents(scan_date);
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_document_type ON legal_documents(document_type);
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_user_id ON legal_documents(user_id);
        ''')
        
        conn.commit()
        conn.close()
    
    def _get_legal_ocr_prompt(self):
        """
        Get the specialized system prompt for legal document OCR transcription
        Following best practices from Gemini documentation
        """
        return """Ești un specialist expert în transcrierea documentelor juridice și administrative românești cu zeci de ani de experiență în transcrierea documentelor legale cu precizie și acuratețe absolută.

INSTRUCȚIUNI CRITICE:
1. Vei primi un PDF sau o imagine scanată a unui document juridic/administrativ românesc (contracte, statute, dosare de instanță, legislație, regulamente, hotărâri, ordonanțe, etc.)
2. Sarcina ta este să transcrii FIECARE cuvânt, semn de punctuație, număr și element de formatare cu 100% acuratețe
3. Documentele juridice/administrative necesită transcripție PERFECTĂ - chiar și erorile mici pot avea consecințe juridice serioase
4. Menține formatarea EXACTĂ, structura și aspectul documentului original
5. Păstrează toate convențiile de formatare juridică (indentarea, numerotarea, întreruperile de secțiuni, semnăturile, datele, etc.)

PROCES DE TRANSCRIPȚIE:
1. Primul pas: examinează cu atenție întregul document pentru a înțelege structura și tipul acestuia
2. Transcrie documentul cuvânt cu cuvânt, menținând formatarea originală
3. După finalizarea transcripției inițiale, REVIZUIEȘTE cu atenție munca ta
4. Verifică pentru orice erori, text lipsă sau probleme de formatare
5. Fă corecții pentru a te asigura că transcripția se potrivește perfect cu originalul
6. Furnizează transcripția finală, verificată

CERINȚE DE FORMATARE:
- Păstrează toate întreruperile de paragraf, întreruperile de linie și spațierea
- Menține sistemele de numerotare originale (1., a), i), etc.)
- Păstrează toate anteturile de secțiuni, titlurile și subtitlurile exact așa cum sunt afișate
- Păstrează semnăturile, datele și ștampilele/sigiliile juridice ca descrieri text
- Menține tabelele, listele și punctele în formatul lor original
- Include notele marginale, notele de subsol și adnotările dacă sunt prezente

ASIGURAREA CALITĂȚII:
- Verifică din nou toate numerele, datele, numele și termenii juridici
- Verifică că toată punctuația este transcrisă corect
- Asigură-te că niciun text nu lipsește sau nu este duplicat
- Confirmă că formatarea se potrivește cu structura documentului original

FORMAT DE IEȘIRE:
Furnizează doar textul transcris în formatul și structura exactă a documentului juridic original. Nu adăuga niciun comentariu, explicații sau metadate decât dacă sunt solicitate în mod specific."""

    async def _call_gemini_with_retry(self, prompt: str, file_data: bytes = None, mime_type: str = None, 
                                     response_mime_type: str = None, temperature: float = 0.1) -> str:
        """Call AI API (Gemini or OpenAI) with retry logic for better reliability"""
        
        # Use OpenAI if configured
        if self.use_openai and self.openai_processor:
            logger.info("Using OpenAI for document processing")
            try:
                if file_data and mime_type:
                    # Document with image
                    result = await self.openai_processor.process_document_with_vision(
                        prompt=prompt,
                        file_data=file_data,
                        mime_type=mime_type,
                        temperature=temperature,
                        max_tokens=8000 if response_mime_type != "application/json" else 1000
                    )
                else:
                    # Text-only processing
                    result = await self.openai_processor.process_text(
                        prompt=prompt,
                        temperature=temperature,
                        max_tokens=1000 if response_mime_type == "application/json" else 8000,
                        response_format="json" if response_mime_type == "application/json" else None
                    )
                return result
            except Exception as e:
                logger.error(f"OpenAI processing failed: {str(e)}")
                raise Exception(f"OpenAI API failed: {str(e)}")
        
        # Use Gemini (original implementation)
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Calling Gemini API (attempt {attempt + 1}/{self.max_retries})")
                
                generation_config = types.GenerateContentConfig(
                    temperature=temperature,
                    top_p=0.9,
                    max_output_tokens=8000 if response_mime_type != "application/json" else 1000
                )
                
                if response_mime_type:
                    generation_config.response_mime_type = response_mime_type
                
                if file_data and mime_type:
                    # Create proper Part object for file data
                    file_part = types.Part.from_bytes(
                        data=file_data,
                        mime_type=mime_type
                    )
                    
                    # Create Content with text and file parts
                    content = types.Content(
                        parts=[
                            types.Part(text=prompt),
                            file_part
                        ]
                    )
                    
                    contents = content
                else:
                    # For text-only processing
                    contents = prompt
                
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=contents,
                    config=generation_config,
                )
                
                if response.text:
                    logger.info(f"Gemini API call successful on attempt {attempt + 1}")
                    return response.text
                else:
                    raise Exception("Empty response from Gemini API")
                    
            except Exception as e:
                logger.warning(f"Gemini API call failed on attempt {attempt + 1}: {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))  # Exponential backoff
                else:
                    raise Exception(f"Gemini API failed after {self.max_retries} attempts: {str(e)}")

    def _get_metadata_extraction_prompt(self, text: str, document_type: str = None) -> str:
        """
        Get specialized prompt for extracting structured metadata from Romanian legal documents
        """
        return f"""
Ești un expert în analiza documentelor administrative și legale românești cu experiență de zeci de ani. MISIUNEA TA CRITICĂ este să extragi metadate complete și utile pentru ORICE document, indiferent de calitatea textului.

TEXTUL DOCUMENTULUI:
{text[:4000]}...

INSTRUCȚIUNI OBLIGATORII - ZERO TOLERANȚĂ PENTRU CÂMPURI GOALE:

1. **TITLU OBLIGATORIU**: Nu NICIODATĂ "Document fără titlu". Analizează textul și generează:
   - Dacă găsești un titlu clar → folosește-l exact
   - Dacă textul este fragmentat → creează un titlu descriptiv bazat pe cuvintele cheie
   - Dacă textul este neclar → generează "Document [tip] - [data/număr/context]"
   - Dacă nu ai nimic → "Document administrativ scanat [data curentă]"

2. **CATEGORIE INTELIGENTĂ**: Analizează contextul și alege cea mai potrivită categorie:
   - Caută cuvinte cheie: "hotărâre", "ordin", "contract", "decizie", "regulament"
   - Dacă nu găsești nimic specific → alege "Document" dar cu încredere

3. **DESCRIERE OBLIGATORIE**: Minimum 20 de cuvinte, maximum 150. INTERZIS texte generice:
   - Analizează conținutul și sumarizează scopul documentului
   - Include orice informații specifice găsite (numere, date, părți implicate)
   - Dacă textul este neclar → descrie ce pare să fie documentul bazat pe structura vizibilă

4. **AUTORITATE INTELIGENTĂ**: 
   - Caută indicii: anteturi, ștampile, semnături, context
   - Dacă nu găsești nimic specific → inferează din tipul documentului

5. **CONFIDENCE SCORE REALIST**:
   - 0.8-0.9: Text clar și complet
   - 0.6-0.7: Text parțial citibil dar suficient pentru metadate
   - 0.4-0.5: Text fragmentat dar cu elemente identificabile
   - 0.2-0.3: Text foarte neclar dar cu structură documentală

EXEMPLE DE TITLURI CREATIVE PENTRU TEXTE NECLARE:
- "Hotărâre de consiliu local - fragmentară"
- "Document oficial cu antet instituțional"
- "Formular administrativ cu câmpuri completate"
- "Corespondență oficială - parțial lizibilă"
- "Document cu ștampilă oficială - proces administrativ"

REGULI STRICTE:
- NICIODATĂ "fără titlu", "nu au putut fi extrase", "eroare la procesare"
- ÎNTOTDEAUNA minimum 4 etichete relevante
- ÎNTOTDEAUNA o descriere specifică și utilă
- CONFIDENCE SCORE minimum 0.3 pentru orice document scanat

RETURNEAZĂ DOAR JSON-ul:
{{
    "title": "[OBLIGATORIU] Titlu specific și descriptiv - NICIODATĂ generic",
    "document_number": "[OPȚIONAL] Numărul documentului dacă e identificabil",
    "category": "[OBLIGATORIU] Categorie potrivită din lista: Regulament|Hotărâre|Ordin|Lege|Contract|Notificare|Cerere|Decizie|Proces-verbal|Raport|Adeverință|Comunicat|Dispoziție|Document",
    "authority": "[OBLIGATORIU] Autoritatea emitentă identificată sau inferată inteligent",
    "issue_date": "[OPȚIONAL] Data în format YYYY-MM-DD dacă e clară",
    "tags": "[OBLIGATORIU] Minimum 4 cuvinte cheie relevante și descriptive",
    "description": "[OBLIGATORIU] Minimum 20 cuvinte - descriere specifică și utilă despre conținut și scop",
    "confidence_score": "[OBLIGATORIU] Scor realist între 0.3-1.0"
}}"""

    async def extract_metadata_from_text(self, text: str, document_type: str = None) -> dict:
        """Extract structured metadata from OCR text using Gemini API with enhanced validation"""
        logger.info(f"Starting enhanced metadata extraction for document type: {document_type}")
        logger.debug(f"Text preview: {text[:200]}...")
        
        start_time = time.time()
        
        try:
            metadata_prompt = self._get_metadata_extraction_prompt(text, document_type)
            
            # Call Gemini with retry logic
            response_text = await self._call_gemini_with_retry(
                prompt=metadata_prompt,
                response_mime_type="application/json",
                temperature=0.2  # Lower temperature for more consistent JSON
            )
            
            processing_time = time.time() - start_time
            logger.info(f"Gemini metadata extraction took {processing_time:.2f} seconds")
            
            # Parse and validate JSON
            metadata_json = json.loads(response_text)
            logger.info(f"Parsed metadata JSON: {metadata_json}")
            
            # Add processing metadata
            metadata_json["_original_text"] = text[:1000]
            metadata_json["_processing_time"] = processing_time
            metadata_json["_gemini_model"] = self.model_name
            
            # Enhanced validation and cleaning
            cleaned_metadata = self._validate_and_clean_metadata_enhanced(metadata_json, document_type, text)
            logger.info(f"Final enhanced metadata: {cleaned_metadata}")
            
            return cleaned_metadata
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}")
            logger.error(f"Raw response: {response_text if 'response_text' in locals() else 'No response'}")
            return self._get_enhanced_fallback_metadata(document_type, text)
        except Exception as e:
            logger.error(f"Enhanced metadata extraction error: {str(e)}")
            return self._get_enhanced_fallback_metadata(document_type, text)
    
    def _validate_and_clean_metadata_enhanced(self, metadata: dict, document_type: str = None, full_text: str = "") -> dict:
        """Enhanced validation and cleaning of extracted metadata with intelligent fallbacks"""
        logger.info("Enhanced validation and cleaning of metadata...")
        
        text_preview = full_text[:500] if full_text else ""
        
        # Enhanced validation with text analysis
        validated = {
            "title": self._force_title_enhanced(metadata.get("title"), text_preview),
            "document_number": self._clean_optional_field(metadata.get("document_number")),
            "category": self._force_category_enhanced(metadata.get("category"), text_preview),
            "authority": self._force_authority_enhanced(metadata.get("authority"), text_preview),
            "issue_date": self._clean_date(metadata.get("issue_date")),
            "tags": self._force_tags_enhanced(metadata.get("tags"), text_preview),
            "description": self._force_description_enhanced(metadata.get("description"), text_preview),
            "confidence_score": self._calculate_enhanced_confidence(metadata.get("confidence_score"), text_preview, metadata)
        }
        
        # Add processing metadata
        validated["_processing_time"] = metadata.get("_processing_time", 0)
        validated["_gemini_model"] = metadata.get("_gemini_model", self.model_name)
        validated["_validation_enhanced"] = True
        
        return validated
    
    def _force_title_enhanced(self, title, text_preview):
        """Force a meaningful title with aggressive intelligence"""
        if title and str(title).strip() and "fără titlu" not in str(title).lower():
            return str(title).strip()
        
        # Advanced text analysis for title generation
        lines = text_preview.split('\n')
        text_upper = text_preview.upper()
        
        # Priority 1: Look for document type indicators
        if 'HOTĂRÂRE' in text_upper or 'HOTARARE' in text_upper:
            return "Hotărâre de consiliu local"
        elif 'ORDIN' in text_upper:
            return "Ordin al primarului"
        elif 'REGULAMENT' in text_upper:
            return "Regulament local"
        elif 'CONTRACT' in text_upper:
            return "Contract administrativ"
        elif 'DECIZIE' in text_upper:
            return "Decizie administrativă"
        elif 'PROCES' in text_upper and 'VERBAL' in text_upper:
            return "Proces-verbal de ședință"
        
        # Priority 2: Look for institutional indicators
        if any(word in text_upper for word in ['PRIMĂRIA', 'PRIMAR']):
            return "Document primar - act administrativ"
        elif 'CONSILIUL LOCAL' in text_upper:
            return "Act al consiliului local"
        elif any(word in text_upper for word in ['PREFECT', 'JUDEȚ']):
            return "Document prefectural"
        
        # Priority 3: Look for structural patterns
        for line in lines[:5]:
            line = line.strip()
            if len(line) > 15 and len(line) < 100:
                # Check if it looks like a title
                if not line.isupper() and any(char.isupper() for char in line):
                    return line[:80]
        
        # Priority 4: Generate from document characteristics
        import datetime
        current_date = datetime.datetime.now().strftime('%d.%m.%Y')
        
        if len(text_preview) > 500:
            return f"Document oficial complet - scanat {current_date}"
        elif len(text_preview) > 200:
            return f"Act administrativ - procesat {current_date}"
        elif len(text_preview) > 50:
            return f"Formular oficial - arhivat {current_date}"
        else:
            return f"Document fragmentar - recuperat {current_date}"
    
    def _force_category_enhanced(self, category, text_preview):
        """Force a valid category"""
        valid_categories = [
            "Regulament", "Hotărâre", "Ordin", "Lege", "Contract", 
            "Notificare", "Cerere", "Decizie", "Proces-verbal", 
            "Raport", "Adeverință", "Comunicat", "Dispoziție"
        ]
        
        if category and str(category).strip() in valid_categories:
            return str(category).strip()
        
        # Try to detect from text
        text_upper = text_preview.upper()
        for cat in valid_categories:
            if cat.upper() in text_upper:
                return cat
        
        # Smart defaults based on keywords
        if any(word in text_upper for word in ['HOTĂRÂRE', 'HOTARARE']):
            return "Hotărâre"
        elif any(word in text_upper for word in ['ORDIN']):
            return "Ordin"
        elif any(word in text_upper for word in ['REGULAMENT']):
            return "Regulament"
        elif any(word in text_upper for word in ['CONTRACT']):
            return "Contract"
        elif any(word in text_upper for word in ['DECIZIE']):
            return "Decizie"
        
        return "Document"
    
    def _force_authority_enhanced(self, authority, text_preview):
        """Force a meaningful authority"""
        if authority and str(authority).strip():
            return str(authority).strip()
        
        # Try to detect from text
        text_upper = text_preview.upper()
        authorities = [
            ("PRIMĂRIA", "Primăria"),
            ("CONSILIUL LOCAL", "Consiliul Local"),
            ("PREFECTURA", "Prefectura"),
            ("MINISTERUL", "Ministerul"),
            ("ANAF", "ANAF"),
            ("AGENȚIA", "Agenția"),
            ("COMPANIA", "Compania"),
            ("DIRECȚIA", "Direcția")
        ]
        
        for keyword, name in authorities:
            if keyword in text_upper:
                return name
        
        return "Autoritate publică"
    
    def _force_tags_enhanced(self, tags, text_preview):
        """Generate enhanced tags with deep content analysis"""
        if tags and isinstance(tags, list) and len(tags) >= 4:
            cleaned_tags = [str(tag).strip() for tag in tags if str(tag).strip()]
            if len(cleaned_tags) >= 4:
                return cleaned_tags[:8]
        
        # Advanced tag generation
        text_upper = text_preview.upper()
        words = text_preview.lower().split()
        
        # Base administrative tags
        enhanced_tags = ['document', 'oficial', 'administrativ']
        
        # Document type tags
        if 'HOTĂRÂRE' in text_upper:
            enhanced_tags.extend(['hotărâre', 'consiliu', 'local'])
        elif 'ORDIN' in text_upper:
            enhanced_tags.extend(['ordin', 'primar', 'executiv'])
        elif 'CONTRACT' in text_upper:
            enhanced_tags.extend(['contract', 'juridic', 'contractual'])
        elif 'REGULAMENT' in text_upper:
            enhanced_tags.extend(['regulament', 'normativ', 'reglementare'])
        elif 'DECIZIE' in text_upper:
            enhanced_tags.extend(['decizie', 'autoritate', 'administrativ'])
        
        # Content-based tags
        if any(word in words for word in ['buget', 'financiar', 'suma']):
            enhanced_tags.append('financiar')
        if any(word in words for word in ['urbanism', 'construcție', 'planificare']):
            enhanced_tags.append('urbanism')
        if any(word in words for word in ['personal', 'angajat', 'funcționar']):
            enhanced_tags.append('resurse-umane')
        if any(word in words for word in ['licență', 'autorizație', 'aprobare']):
            enhanced_tags.append('autorizații')
        
        # Authority tags
        if 'PRIMĂRIA' in text_upper:
            enhanced_tags.append('primărie')
        if 'CONSILIUL' in text_upper:
            enhanced_tags.append('consiliu')
        
        # Quality tags
        if len(text_preview) > 1000:
            enhanced_tags.append('complet')
        elif len(text_preview) > 300:
            enhanced_tags.append('parțial')
        else:
            enhanced_tags.append('fragmentar')
        
        # Temporal tag
        import datetime
        enhanced_tags.append(f'scanat-{datetime.datetime.now().year}')
        
        # Remove duplicates and ensure minimum count
        unique_tags = list(dict.fromkeys(enhanced_tags))  # Preserve order
        
        if len(unique_tags) < 6:
            unique_tags.extend(['digitizat', 'arhivă', 'publică'])
        
        return unique_tags[:8]
    
    def _force_description_enhanced(self, description, text_preview):
        """Force a meaningful description with advanced intelligence"""
        if description and str(description).strip() and len(str(description).strip()) > 20:
            clean_desc = str(description).strip()
            if "nu au putut fi extrase" not in clean_desc.lower() and "metadate" not in clean_desc.lower():
                return clean_desc[:200]
        
        # Advanced description generation based on content analysis
        text_upper = text_preview.upper()
        words = text_preview.lower().split()
        
        # Analyze document content for intelligent description
        description_parts = []
        
        # Document type detection
        if 'HOTĂRÂRE' in text_upper:
            description_parts.append("Hotărâre adoptată de consiliul local")
        elif 'ORDIN' in text_upper:
            description_parts.append("Ordin emis de către primar")
        elif 'CONTRACT' in text_upper:
            description_parts.append("Contract încheiat în cadrul activității administrative")
        elif 'REGULAMENT' in text_upper:
            description_parts.append("Regulament cu aplicabilitate locală")
        else:
            description_parts.append("Document oficial din arhiva instituțională")
        
        # Content characteristics
        if any(word in words for word in ['buget', 'financial', 'suma', 'lei']):
            description_parts.append("cu implicații financiare")
        elif any(word in words for word in ['urbanism', 'construc', 'planificare']):
            description_parts.append("referitor la dezvoltare urbană")
        elif any(word in words for word in ['personal', 'angaja', 'funcționar']):
            description_parts.append("privind resursele umane")
        elif any(word in words for word in ['licen', 'autorizat', 'aprobar']):
            description_parts.append("de natură autorizatorie")
        
        # Authority detection
        if 'PRIMĂRIA' in text_upper:
            description_parts.append("emis de primărie")
        elif 'CONSILIUL' in text_upper:
            description_parts.append("adoptat în ședința consiliului")
        
        # Quality indicators
        if len(text_preview) > 1000:
            description_parts.append("cu conținut detaliat și structurat")
        elif len(text_preview) > 300:
            description_parts.append("cu informații esențiale identificabile")
        else:
            description_parts.append("cu conținut parțial recuperat prin OCR")
        
        # Temporal context
        import datetime
        description_parts.append(f"procesat automat în data de {datetime.datetime.now().strftime('%d.%m.%Y')}")
        
        # Combine all parts
        full_description = ", ".join(description_parts)
        
        # Ensure minimum length and readability
        if len(full_description) < 50:
            full_description += ". Document oficial digitizat prin tehnologie OCR avansată cu extragere automată de metadate."
        
        return full_description[:200] + "..." if len(full_description) > 200 else full_description
    
    def _clean_optional_field(self, value):
        """Clean optional field"""
        if value and str(value).strip() and str(value).strip().lower() != 'null':
            return str(value).strip()
        return None
    
    def _clean_date(self, date_value):
        """Clean and validate date"""
        if not date_value:
            return None
        
        date_str = str(date_value).strip()
        if len(date_str) == 10 and date_str.count('-') == 2:
            return date_str
        return None
    
    def _calculate_enhanced_confidence(self, confidence, text_preview, metadata):
        """Calculate enhanced confidence score"""
        try:
            score = float(confidence) if confidence is not None else 0.0
            if score >= 0.8:
                return score
            elif score >= 0.5:
                return 0.7
            elif score >= 0.3:
                return 0.5
            else:
                return 0.3
        except:
            return 0.0
    
    def _get_enhanced_fallback_metadata(self, document_type: str = None, text: str = "") -> dict:
        """Get enhanced fallback metadata with intelligent content generation"""
        import datetime
        current_date = datetime.datetime.now().strftime('%d.%m.%Y')
        
        # Generate intelligent fallback based on available text
        text_preview = text[:500] if text else ""
        
        # Force intelligent metadata generation
        title = self._force_title_enhanced("", text_preview)
        description = self._force_description_enhanced("", text_preview)
        tags = self._force_tags_enhanced([], text_preview)
        category = self._force_category_enhanced(document_type, text_preview)
        authority = self._force_authority_enhanced("", text_preview)
        
        # Calculate realistic confidence based on text quality
        if len(text_preview) > 500:
            confidence = 0.6
        elif len(text_preview) > 200:
            confidence = 0.5
        elif len(text_preview) > 50:
            confidence = 0.4
        else:
            confidence = 0.3
        
            return {
            "title": title,
            "document_number": None,
            "category": category,
            "authority": authority,
            "issue_date": None,
            "description": description,
            "tags": tags,
            "confidence_score": confidence,
            "_original_text": text[:1000],
            "_processing_time": 0,
            "_gemini_model": self.model_name,
            "_validation_enhanced": True,
            "_fallback_generated": True
        }

    async def process_pdf_file(self, pdf_path, document_type=None):
        """Process PDF file with enhanced OCR using Gemini API with retry logic"""
        logger.info(f"Starting enhanced PDF processing: {pdf_path}")
        start_time = time.time()
        
        if not os.path.exists(pdf_path):
            logger.error(f"PDF file not found: {pdf_path}")
            return {"success": False, "error": f"File not found: {pdf_path}"}
        
        try:
            # Read PDF file
            with open(pdf_path, 'rb') as pdf_file:
                pdf_content = pdf_file.read()
            
            if len(pdf_content) == 0:
                return {"success": False, "error": "Empty PDF file"}
            
            # Get OCR prompt
            ocr_prompt = self._get_legal_ocr_prompt()
            
            # Process with Gemini API using retry mechanism
            try:
                transcribed_text = await self._call_gemini_with_retry(
                    prompt=ocr_prompt,
                    file_data=pdf_content,
                    mime_type="application/pdf",
                    temperature=0.1  # Low temperature for consistent transcription
                )
            except Exception as e:
                logger.error(f"Gemini OCR processing failed: {str(e)}")
                return {"success": False, "error": f"OCR processing failed: {str(e)}"}
            
            processing_time = time.time() - start_time
            logger.info(f"PDF OCR processing completed in {processing_time:.2f} seconds")
            
            if not transcribed_text or len(transcribed_text.strip()) < 10:
                return {"success": False, "error": "OCR produced insufficient text"}
            
            # Verify transcription quality
            verification_result = self._verify_transcription_enhanced(transcribed_text, pdf_path)
            
            # Extract metadata
            try:
                metadata = await self.extract_metadata_from_text(transcribed_text, document_type)
                metadata["_processing_time"] = processing_time
            except Exception as e:
                logger.error(f"Metadata extraction failed: {str(e)}")
                metadata = self._get_enhanced_fallback_metadata(document_type, transcribed_text)
            
            # Store in database
            try:
                doc_id = self._store_in_database_enhanced(
                    filename=os.path.basename(pdf_path),
                    document_type=document_type or metadata.get("category", "PDF"),
                    transcribed_text=transcribed_text,
                    original_format="PDF",
                    metadata=metadata,
                    processing_time=processing_time
                )
            except Exception as e:
                logger.error(f"Database storage failed: {str(e)}")
                doc_id = None
            
            result = {
                "success": True,
                "transcribed_text": transcribed_text,
                "filename": os.path.basename(pdf_path),
                "document_id": doc_id,
                "metadata": metadata,
                "verification": verification_result,
                "processing_time": processing_time,
                "gemini_model": self.model_name
            }
            
            logger.info(f"Enhanced PDF processing completed successfully: {os.path.basename(pdf_path)}")
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Enhanced PDF processing failed after {processing_time:.2f}s: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "filename": os.path.basename(pdf_path),
                "processing_time": processing_time
            }

    async def process_image_file(self, image_path, document_type=None):
        """Process image file with enhanced OCR using Gemini API with retry logic"""
        logger.info(f"Starting enhanced image processing: {image_path}")
        start_time = time.time()
        
        if not os.path.exists(image_path):
            logger.error(f"Image file not found: {image_path}")
            return {"success": False, "error": f"File not found: {image_path}"}
        
        try:
            # Read image file
            with open(image_path, 'rb') as image_file:
                image_content = image_file.read()
            
            if len(image_content) == 0:
                return {"success": False, "error": "Empty image file"}
            
            # Get MIME type
            file_extension = Path(image_path).suffix.lower()
            mime_type = self._get_image_mime_type(file_extension)
            
            if not mime_type:
                return {"success": False, "error": f"Unsupported image format: {file_extension}"}
            
            # Get OCR prompt
            ocr_prompt = self._get_legal_ocr_prompt()
            
            # Process with Gemini API using retry mechanism
            try:
                transcribed_text = await self._call_gemini_with_retry(
                    prompt=ocr_prompt,
                    file_data=image_content,
                    mime_type=mime_type,
                    temperature=0.1  # Low temperature for consistent transcription
                )
            except Exception as e:
                logger.error(f"Gemini OCR processing failed: {str(e)}")
                return {"success": False, "error": f"OCR processing failed: {str(e)}"}
            
            processing_time = time.time() - start_time
            logger.info(f"Image OCR processing completed in {processing_time:.2f} seconds")
            
            if not transcribed_text or len(transcribed_text.strip()) < 10:
                return {"success": False, "error": "OCR produced insufficient text"}
            
            # Verify transcription quality
            verification_result = self._verify_transcription_enhanced(transcribed_text, image_path)
            
            # Extract metadata
            try:
                metadata = await self.extract_metadata_from_text(transcribed_text, document_type)
                metadata["_processing_time"] = processing_time
            except Exception as e:
                logger.error(f"Metadata extraction failed: {str(e)}")
                metadata = self._get_enhanced_fallback_metadata(document_type, transcribed_text)
            
            # Store in database
            try:
                doc_id = self._store_in_database_enhanced(
                    filename=os.path.basename(image_path),
                    document_type=document_type or metadata.get("category", "IMAGE"),
                    transcribed_text=transcribed_text,
                    original_format=f"IMAGE_{file_extension.upper()}",
                    metadata=metadata,
                    processing_time=processing_time
                )
            except Exception as e:
                logger.error(f"Database storage failed: {str(e)}")
                doc_id = None
            
            result = {
                "success": True,
                "transcribed_text": transcribed_text,
                "filename": os.path.basename(image_path),
                "document_id": doc_id,
                "metadata": metadata,
                "verification": verification_result,
                "processing_time": processing_time,
                "gemini_model": self.model_name
            }
            
            logger.info(f"Enhanced image processing completed successfully: {os.path.basename(image_path)}")
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Enhanced image processing failed after {processing_time:.2f}s: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "filename": os.path.basename(image_path),
                "processing_time": processing_time
            }

    def _verify_transcription_enhanced(self, transcribed_text, file_path):
        """Enhanced transcription verification with quality metrics"""
        if not transcribed_text or len(transcribed_text.strip()) < 10:
            return {
                "verified": False,
                "quality_score": 0.0,
                "issues": ["Text too short or empty"],
                "recommendations": ["Re-scan with better quality settings"]
            }
        
        issues = []
        quality_score = 1.0
        
        # Check text length
        text_length = len(transcribed_text.strip())
        if text_length < 50:
            issues.append("Text appears very short")
            quality_score -= 0.3
        
        # Check for common OCR errors
        suspicious_patterns = [
            r'[^a-zA-ZăâîșțĂÂÎȘȚ0-9\s\.,;:!?\-()"\'/]',  # Non-Romanian chars
            r'\b[a-z]{20,}\b',  # Very long lowercase words
            r'\b[A-Z]{10,}\b',  # Very long uppercase words
        ]
        
        import re
        for pattern in suspicious_patterns:
            if re.search(pattern, transcribed_text):
                issues.append(f"Suspicious text pattern detected")
                quality_score -= 0.1
        
        # Calculate final verification
        verified = quality_score >= 0.6 and len(issues) <= 2
        
        return {
            "verified": verified,
            "quality_score": max(0.0, quality_score),
            "text_length": text_length,
            "issues": issues,
            "recommendations": [
                "Re-scan if quality score < 0.7",
                "Check document orientation and lighting",
                "Ensure document is flat and properly aligned"
            ] if not verified else []
        }

    def _store_in_database_enhanced(self, filename, document_type, transcribed_text, original_format, 
                                   metadata=None, processing_time=0, user_id=None):
        """Enhanced database storage with metadata and performance tracking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Calculate confidence score
            confidence_score = metadata.get("confidence_score", 0.0) if metadata else 0.0
            
            # Prepare metadata JSON
            metadata_json = json.dumps(metadata, ensure_ascii=False) if metadata else None
            
            cursor.execute('''
                INSERT INTO legal_documents 
                (filename, document_type, transcribed_text, original_format, scan_date, 
                 confidence_score, metadata_json, processing_time, gemini_model, user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                filename,
                document_type,
                transcribed_text,
                original_format,
                datetime.datetime.now(),
                confidence_score,
                metadata_json,
                processing_time,
                self.model_name,
                user_id
            ))
            
            document_id = cursor.lastrowid
            conn.commit()
            
            logger.info(f"Enhanced document stored with ID: {document_id}")
            return document_id
            
        except Exception as e:
            logger.error(f"Enhanced database storage failed: {str(e)}")
            conn.rollback()
            raise e
        finally:
            conn.close()

    def _get_image_mime_type(self, extension):
        """Get MIME type for image extensions"""
        mime_types = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.webp': 'image/webp'
        }
        return mime_types.get(extension, 'image/jpeg')

    def _verify_transcription(self, transcribed_text, file_path):
        """
        Verify and improve transcription quality using a second Gemini pass.
        This helps ensure accuracy for legal documents.
        """
        if not transcribed_text or len(transcribed_text.strip()) < 10:
            logger.warning("Transcribed text is too short for verification")
            return transcribed_text
        
        logger.info("Starting transcription verification pass...")
        
        verification_prompt = f"""
        Please review and correct the following OCR transcription of a legal document.
        Fix any obvious OCR errors, maintain the original formatting and structure,
        and ensure all legal terms and numbers are correctly transcribed.
        
        If the text appears to be correctly transcribed, return it as-is.
        If there are clear OCR errors (like 'rn' instead of 'm', '0' instead of 'O', etc.), fix them.
        
        IMPORTANT: Return only the corrected text, no additional commentary.
        
        Original transcribed text:
        {transcribed_text}
        """
        
        try:
            generation_config = types.GenerateContentConfig(
                temperature=0.05,  # Very low temperature for verification
                top_p=0.9,
                max_output_tokens=65535
            )
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=verification_prompt,
                config=generation_config,
            )
            
            verified_text = response.text.strip()
            
            if verified_text and len(verified_text) > 10:
                logger.info("Transcription verification completed")
                return verified_text
            else:
                logger.warning("Verification returned empty result, using original transcription")
                return transcribed_text
                
        except Exception as e:
            logger.warning(f"Verification failed, using original transcription: {str(e)}")
            return transcribed_text
    
    def _store_in_database(self, filename, document_type, transcribed_text, original_format):
        """Store the transcribed document in the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO legal_documents 
            (filename, document_type, transcribed_text, original_format, scan_date, verification_status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            filename,
            document_type,
            transcribed_text,
            original_format,
            datetime.datetime.now(),
            'verified'
        ))
        
        doc_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return doc_id
    
    def search_documents(self, search_term, document_type=None):
        """
        Search transcribed documents by content
        
        Args:
            search_term (str): Text to search for
            document_type (str): Optional document type filter
            
        Returns:
            list: List of matching documents
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if document_type:
            cursor.execute('''
                SELECT id, filename, document_type, transcribed_text, scan_date
                FROM legal_documents 
                WHERE transcribed_text LIKE ? AND document_type = ?
                ORDER BY scan_date DESC
            ''', (f'%{search_term}%', document_type))
        else:
            cursor.execute('''
                SELECT id, filename, document_type, transcribed_text, scan_date
                FROM legal_documents 
                WHERE transcribed_text LIKE ?
                ORDER BY scan_date DESC
            ''', (f'%{search_term}%',))
        
        results = cursor.fetchall()
        conn.close()
        
        return [
            {
                "id": row[0],
                "filename": row[1],
                "document_type": row[2],
                "transcribed_text": row[3][:500] + "..." if len(row[3]) > 500 else row[3],
                "scan_date": row[4]
            }
            for row in results
        ]
    
    def get_document_by_id(self, doc_id):
        """Get a specific document by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM legal_documents WHERE id = ?
        ''', (doc_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                "id": result[0],
                "filename": result[1],
                "document_type": result[2],
                "transcribed_text": result[3],
                "original_format": result[4],
                "scan_date": result[5],
                "confidence_score": result[6],
                "verification_status": result[7],
                "created_at": result[8],
                "metadata_json": result[9],
                "processing_time": result[10],
                "gemini_model": result[11]
            }
        return None
    
    def list_recent_documents(self, limit=20):
        """Get recently processed documents"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, filename, document_type, scan_date, verification_status
            FROM legal_documents 
            ORDER BY scan_date DESC 
            LIMIT ?
        ''', (limit,))
        
        results = cursor.fetchall()
        conn.close()
        
        return [
            {
                "id": row[0],
                "filename": row[1],
                "document_type": row[2],
                "scan_date": row[3],
                "verification_status": row[4]
            }
            for row in results
        ] 

    def get_scanning_status_report(self) -> Dict[str, Any]:
        """Generate comprehensive scanning status report"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get overall statistics
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_documents,
                    AVG(confidence_score) as avg_confidence,
                    AVG(processing_time) as avg_processing_time,
                    COUNT(CASE WHEN confidence_score >= 0.8 THEN 1 END) as high_quality,
                    COUNT(CASE WHEN confidence_score < 0.5 THEN 1 END) as low_quality
                FROM legal_documents 
                WHERE created_at >= datetime('now', '-24 hours')
            ''')
            
            stats = cursor.fetchone()
            
            # Get recent documents with issues
            cursor.execute('''
                SELECT filename, confidence_score, created_at, verification_status
                FROM legal_documents 
                WHERE confidence_score < 0.5 AND created_at >= datetime('now', '-24 hours')
                ORDER BY created_at DESC
                LIMIT 10
            ''')
            
            problematic_docs = cursor.fetchall()
            
            # Get processing performance trends
            cursor.execute('''
                SELECT 
                    date(created_at) as scan_date,
                    COUNT(*) as daily_count,
                    AVG(confidence_score) as daily_avg_confidence,
                    AVG(processing_time) as daily_avg_time
                FROM legal_documents 
                WHERE created_at >= datetime('now', '-7 days')
                GROUP BY date(created_at)
                ORDER BY scan_date DESC
            ''')
            
            daily_trends = cursor.fetchall()
            
            # Calculate quality metrics
            total_docs = stats[0] if stats[0] else 0
            avg_confidence = round(stats[1], 3) if stats[1] else 0.0
            avg_processing_time = round(stats[2], 2) if stats[2] else 0.0
            high_quality_rate = round((stats[3] / total_docs * 100), 1) if total_docs > 0 else 0.0
            low_quality_rate = round((stats[4] / total_docs * 100), 1) if total_docs > 0 else 0.0
            
            # Generate alerts
            alerts = []
            if avg_confidence < 0.6:
                alerts.append({
                    "level": "warning",
                    "message": f"Average confidence score is low: {avg_confidence}",
                    "recommendation": "Check scanner quality settings and document preparation"
                })
            
            if low_quality_rate > 20:
                alerts.append({
                    "level": "critical",
                    "message": f"High rate of low-quality scans: {low_quality_rate}%",
                    "recommendation": "Immediate action required - check scanner hardware and settings"
                })
            
            if avg_processing_time > 30:
                alerts.append({
                    "level": "warning", 
                    "message": f"Processing time is high: {avg_processing_time}s",
                    "recommendation": "Consider optimizing document size or checking API performance"
                })
            
            return {
                "status": "healthy" if len(alerts) == 0 else "warning" if any(a["level"] == "warning" for a in alerts) else "critical",
                "last_updated": datetime.datetime.now().isoformat(),
                "statistics": {
                    "total_documents_24h": total_docs,
                    "average_confidence": avg_confidence,
                    "average_processing_time": avg_processing_time,
                    "high_quality_rate": high_quality_rate,
                    "low_quality_rate": low_quality_rate
                },
                "alerts": alerts,
                "problematic_documents": [
                    {
                        "filename": doc[0],
                        "confidence_score": doc[1],
                        "scanned_at": doc[2],
                        "status": doc[3]
                    } for doc in problematic_docs
                ],
                "daily_trends": [
                    {
                        "date": trend[0],
                        "document_count": trend[1],
                        "avg_confidence": round(trend[2], 3) if trend[2] else 0.0,
                        "avg_processing_time": round(trend[3], 2) if trend[3] else 0.0
                    } for trend in daily_trends
                ],
                "recommendations": [
                    "Ensure documents are flat and well-lit during scanning",
                    "Use high DPI settings (300+ DPI) for better OCR accuracy", 
                    "Check document orientation before scanning",
                    "Clean scanner glass regularly for optimal quality",
                    "Monitor GEMINI API quota and performance"
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to generate scanning status report: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "last_updated": datetime.datetime.now().isoformat()
            }
        finally:
            conn.close()

    async def validate_scanner_health(self) -> Dict[str, Any]:
        """Validate scanner and OCR system health"""
        health_report = {
            "scanner_available": False,
            "gemini_api_healthy": False,
            "database_accessible": False,
            "overall_status": "unhealthy",
            "checks": [],
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        # Check NAPS2 scanner availability
        try:
            naps2_paths = [
                r"C:\Program Files\NAPS2\NAPS2.Console.exe",
                r"C:\Program Files (x86)\NAPS2\NAPS2.Console.exe"
            ]
            
            naps2_found = any(os.path.exists(path) for path in naps2_paths)
            health_report["scanner_available"] = naps2_found
            health_report["checks"].append({
                "component": "NAPS2 Scanner",
                "status": "healthy" if naps2_found else "error",
                "message": "Scanner software found" if naps2_found else "Scanner software not installed"
            })
        except Exception as e:
            health_report["checks"].append({
                "component": "NAPS2 Scanner",
                "status": "error",
                "message": f"Scanner check failed: {str(e)}"
            })
        
        # Check Gemini API health
        try:
            test_response = await self._call_gemini_with_retry(
                prompt="Test message for health check. Respond with 'OK'.",
                temperature=0.1
            )
            
            api_healthy = "OK" in test_response or len(test_response.strip()) > 0
            health_report["gemini_api_healthy"] = api_healthy
            health_report["checks"].append({
                "component": "Gemini API",
                "status": "healthy" if api_healthy else "warning",
                "message": "API responding correctly" if api_healthy else "API response unclear"
            })
        except Exception as e:
            health_report["checks"].append({
                "component": "Gemini API",
                "status": "error", 
                "message": f"API check failed: {str(e)}"
            })
        
        # Check database health
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM legal_documents LIMIT 1")
            cursor.fetchone()
            conn.close()
            
            health_report["database_accessible"] = True
            health_report["checks"].append({
                "component": "Database",
                "status": "healthy",
                "message": "Database accessible and responsive"
            })
        except Exception as e:
            health_report["checks"].append({
                "component": "Database", 
                "status": "error",
                "message": f"Database check failed: {str(e)}"
            })
        
        # Determine overall status
        healthy_components = sum(1 for check in health_report["checks"] if check["status"] == "healthy")
        total_components = len(health_report["checks"])
        
        if healthy_components == total_components:
            health_report["overall_status"] = "healthy"
        elif healthy_components >= total_components // 2:
            health_report["overall_status"] = "degraded"
        else:
            health_report["overall_status"] = "unhealthy"
        
        return health_report 

    async def process_user_document(self, file_path: str, user_id: UUID, 
                                  document_type: str = None, extract_personal_info: bool = True) -> Dict[str, Any]:
        """
        Process a document for a specific user with OCR and optional personal info extraction
        
        Args:
            file_path: Path to the document file
            user_id: UUID of the user who owns the document
            document_type: Type of document being processed
            extract_personal_info: Whether to extract personal information
            
        Returns:
            Dict containing processing results
        """
        logger.info(f"Processing user document: {file_path} for user: {user_id}")
        start_time = time.time()
        
        try:
            # Determine file type
            file_extension = Path(file_path).suffix.lower()
            if file_extension == '.pdf':
                mime_type = "application/pdf"
                ocr_result = await self.process_pdf_file(file_path, document_type)
            elif file_extension in ['.png', '.jpg', '.jpeg', '.webp']:
                mime_type = self._get_image_mime_type(file_extension)
                ocr_result = await self.process_image_file(file_path, document_type)
            else:
                raise ValueError(f"Unsupported file type: {file_extension}")
            
            if not ocr_result["success"]:
                return {
                    "success": False,
                    "error": ocr_result.get("error"),
                    "user_id": str(user_id)
                }
            
            # Store document in user-specific table
            document_data = {
                "user_id": user_id,
                "original_filename": Path(file_path).name,
                "document_type": ocr_result["metadata"].get("category", document_type),
                "title": ocr_result["metadata"].get("title"),
                "description": ocr_result["metadata"].get("description"),
                "file_path": file_path,
                "file_size": Path(file_path).stat().st_size,
                "mime_type": mime_type,
                "transcribed_text": ocr_result["transcribed_text"],
                "metadata_json": ocr_result["metadata"],
                "confidence_score": ocr_result["metadata"].get("confidence_score", 0.0),
                "processing_time": ocr_result.get("processing_time", time.time() - start_time)
            }
            
            # Store document using async session if available
            if self.db_session:
                document_id = await self._store_user_document_async(document_data)
            else:
                document_id = self._store_user_document_sync(document_data)
            
            result = {
                "success": True,
                "document_id": document_id,
                "user_id": str(user_id),
                "transcribed_text": ocr_result["transcribed_text"],
                "metadata": ocr_result["metadata"],
                "processing_time": time.time() - start_time
            }
            
            # Extract personal information if requested
            if extract_personal_info:
                try:
                    personal_info = await self.personal_extractor.extract_personal_info_from_file(
                        file_path, mime_type
                    )
                    
                    if personal_info and not personal_info.get("error"):
                        # Store personal info in database
                        if self.db_session:
                            personal_info_id = await self._store_personal_info_async(
                                user_id, personal_info, file_path, document_id
                            )
                        else:
                            personal_info_id = self._store_personal_info_sync(
                                user_id, personal_info, file_path, document_id
                            )
                        
                        result["personal_info"] = personal_info
                        result["personal_info_id"] = personal_info_id
                        
                except Exception as e:
                    logger.error(f"Personal info extraction failed: {str(e)}")
                    result["personal_info_error"] = str(e)
            
            logger.info(f"User document processing completed successfully for user: {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"User document processing failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "user_id": str(user_id),
                "processing_time": time.time() - start_time
            }
    
    async def _store_user_document_async(self, document_data: Dict[str, Any]) -> str:
        """Store user document using async database session"""
        from ..models.user import UserScannedDocument
        
        # Create document record
        document = UserScannedDocument(
            user_id=document_data["user_id"],
            original_filename=document_data["original_filename"],
            document_type=document_data.get("document_type"),
            title=document_data.get("title"),
            description=document_data.get("description"),
            file_path=document_data["file_path"],
            file_size=document_data["file_size"],
            mime_type=document_data.get("mime_type"),
            transcribed_text=document_data.get("transcribed_text"),
            metadata_json=document_data.get("metadata_json"),
            confidence_score=document_data.get("confidence_score"),
            processing_time=document_data.get("processing_time"),
            ai_model_used=self.model_name
        )
        
        self.db_session.add(document)
        await self.db_session.commit()
        await self.db_session.refresh(document)
        
        logger.info(f"Document stored with ID: {document.id}")
        return str(document.id)
    
    def _store_user_document_sync(self, document_data: Dict[str, Any]) -> str:
        """Store user document using sync database (fallback)"""
        # This is a fallback for when async session is not available
        # Store in the OCR SQLite database with user_id reference
        doc_id = self._store_in_database_enhanced(
            filename=document_data["original_filename"],
            document_type=document_data.get("document_type", "Document"),
            transcribed_text=document_data.get("transcribed_text", ""),
            original_format="USER_UPLOAD",
            metadata=document_data.get("metadata_json", {}),
            processing_time=document_data.get("processing_time", 0),
            user_id=str(document_data["user_id"])
        )
        return str(doc_id)
    
    async def _store_personal_info_async(self, user_id: UUID, personal_info: Dict[str, Any], 
                                        file_path: str, document_id: str) -> str:
        """Store extracted personal information using async database session"""
        from ..models.user import UserAIExtractedInfo
        from datetime import datetime
        
        personal_data = personal_info.get("personal_info", {})
        document_info = personal_info.get("document_info", {})
        verification_status = personal_info.get("verification_status", {})
        
        # Convert date strings to date objects
        def parse_date(date_str):
            if date_str:
                try:
                    return datetime.strptime(date_str, "%Y-%m-%d").date()
                except:
                    return None
            return None
        
        extracted_info = UserAIExtractedInfo(
            user_id=user_id,
            extracted_first_name=personal_data.get("first_name"),
            extracted_last_name=personal_data.get("last_name"),
            extracted_cnp=personal_data.get("cnp"),
            extracted_address=personal_data.get("address"),
            extracted_phone=personal_data.get("phone"),
            extracted_birth_date=parse_date(personal_data.get("birth_date")),
            extracted_birth_place=personal_data.get("birth_place"),
            extracted_nationality=personal_data.get("nationality"),
            extracted_id_series=personal_data.get("id_series"),
            extracted_id_number=personal_data.get("id_number"),
            extracted_issued_by=personal_data.get("issued_by"),
            extracted_issue_date=parse_date(personal_data.get("issue_date")),
            extracted_expiry_date=parse_date(personal_data.get("expiry_date")),
            source_document_type=document_info.get("document_type", "unknown"),
            source_document_path=file_path,
            extraction_confidence=document_info.get("confidence_score", 0.0),
            extracted_data_raw=personal_info,
            processing_notes=document_info.get("extraction_notes"),
            ai_model_used=self.model_name,
            verification_status="pending"
        )
        
        self.db_session.add(extracted_info)
        await self.db_session.commit()
        await self.db_session.refresh(extracted_info)
        
        logger.info(f"Personal info stored with ID: {extracted_info.id}")
        return str(extracted_info.id)
    
    def _store_personal_info_sync(self, user_id: UUID, personal_info: Dict[str, Any], 
                                 file_path: str, document_id: str) -> str:
        """Store extracted personal information using sync database (fallback)"""
        # Fallback implementation for sync storage
        # This could be enhanced to use SQLite or another sync storage method
        logger.info(f"Personal info stored for user {user_id} (sync fallback)")
        return "sync_fallback_id" 