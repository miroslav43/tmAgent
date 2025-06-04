"""
Personal Information Extractor Service
Specialized AI service for extracting personal information from Romanian identity documents
"""

import os
import json
import logging
from typing import Dict, Optional, Any
from datetime import datetime, date
from pathlib import Path
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class PersonalInfoExtractor:
    """
    Specialized service for extracting personal information from Romanian identity documents
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable must be set")
        
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = "gemini-2.0-flash-001"
        
    def _get_personal_info_extraction_prompt(self) -> str:
        """Get specialized prompt for personal information extraction from Romanian documents"""
        return """
Ești un expert în extragerea informațiilor personale din documentele de identitate românești. Analizează cu atenție documentul și extrage TOATE informațiile personale identificabile.

TIPURI DE DOCUMENTE SUPORTATE:
- Carte de identitate
- Pașaport român
- Certificat de naștere
- Certificat de căsătorie
- Permis de conducere
- Carte de muncă
- Orice alt document oficial român cu date personale

CÂMPURI OBLIGATORII DE EXTRAS:
1. **Nume și prenume** (obligatoriu)
2. **CNP** (Codul Numeric Personal - 13 cifre)
3. **Adresa de domiciliu**
4. **Data nașterii**
5. **Locul nașterii**
6. **Nationalitatea**
7. **Seria și numărul documentului**
8. **Emis de** (autoritatea emitentă)
9. **Data emiterii**
10. **Data valabilității**
11. **Telefon** (dacă este prezent)

INSTRUCȚIUNI CRITICE:
1. Extrage DOAR informațiile care sunt CLAR VIZIBILE în document
2. Pentru CNP-ul românesc: verifică că are exact 13 cifre
3. Pentru date: folosește formatul YYYY-MM-DD
4. Pentru adrese: include orașul, strada, numărul
5. Nu inventa informații care nu sunt prezente
6. Dacă o informație nu este clară, lasă câmpul null

REGULI PENTRU ÎNCREDERE:
- confidence_high (0.8-1.0): Informația este clar vizibilă și corectă
- confidence_medium (0.5-0.7): Informația este parțial vizibilă
- confidence_low (0.2-0.4): Informația este neclară sau fragmentară

RETURNEAZĂ DOAR JSON:
{
    "personal_info": {
        "first_name": "string sau null",
        "last_name": "string sau null", 
        "full_name": "string sau null",
        "cnp": "string de 13 cifre sau null",
        "address": "string sau null",
        "birth_date": "YYYY-MM-DD sau null",
        "birth_place": "string sau null",
        "nationality": "string sau null",
        "id_series": "string sau null",
        "id_number": "string sau null",
        "issued_by": "string sau null",
        "issue_date": "YYYY-MM-DD sau null",
        "expiry_date": "YYYY-MM-DD sau null",
        "phone": "string sau null"
    },
    "document_info": {
        "document_type": "carte_identitate|pasaport|certificat_nastere|permis_conducere|other",
        "confidence_score": 0.0-1.0,
        "extraction_notes": "observații despre calitatea extragerii"
    },
    "verification_status": {
        "cnp_format_valid": true/false,
        "dates_logical": true/false,
        "all_required_fields_present": true/false
    }
}
"""

    async def extract_personal_info_from_file(self, file_path: str, mime_type: str) -> Dict[str, Any]:
        """
        Extract personal information from a file (PDF or image)
        
        Args:
            file_path: Path to the file
            mime_type: MIME type of the file
            
        Returns:
            Dict containing extracted personal information
        """
        logger.info(f"Starting personal info extraction from: {file_path}")
        
        try:
            # Read file content
            with open(file_path, 'rb') as file:
                file_content = file.read()
            
            if len(file_content) == 0:
                raise ValueError("File is empty")
            
            # Get extraction prompt
            prompt = self._get_personal_info_extraction_prompt()
            
            # Call Gemini API
            response = await self._call_gemini_api(prompt, file_content, mime_type)
            
            # Parse and validate response
            extracted_data = self._parse_and_validate_response(response)
            
            logger.info("Personal info extraction completed successfully")
            return extracted_data
            
        except Exception as e:
            logger.error(f"Personal info extraction failed: {str(e)}")
            return {
                "personal_info": {},
                "document_info": {
                    "document_type": "unknown",
                    "confidence_score": 0.0,
                    "extraction_notes": f"Extraction failed: {str(e)}"
                },
                "verification_status": {
                    "cnp_format_valid": False,
                    "dates_logical": False,
                    "all_required_fields_present": False
                },
                "error": str(e)
            }
    
    async def _call_gemini_api(self, prompt: str, file_data: bytes, mime_type: str) -> str:
        """Call Gemini API with retry logic"""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Calling Gemini API for personal info extraction (attempt {attempt + 1})")
                
                generation_config = types.GenerateContentConfig(
                    temperature=0.1,  # Low temperature for precise extraction
                    top_p=0.9,
                    max_output_tokens=2000,
                    response_mime_type="application/json"
                )
                
                # Create file part
                file_part = types.Part.from_bytes(
                    data=file_data,
                    mime_type=mime_type
                )
                
                # Create content with prompt and file
                content = types.Content(
                    parts=[
                        types.Part(text=prompt),
                        file_part
                    ]
                )
                
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=content,
                    config=generation_config
                )
                
                if response.text:
                    logger.info("Gemini API call successful")
                    return response.text
                else:
                    raise Exception("Empty response from Gemini API")
                    
            except Exception as e:
                logger.warning(f"Gemini API call failed on attempt {attempt + 1}: {str(e)}")
                if attempt == max_retries - 1:
                    raise Exception(f"Gemini API failed after {max_retries} attempts: {str(e)}")
    
    def _parse_and_validate_response(self, response_text: str) -> Dict[str, Any]:
        """Parse and validate the AI response"""
        try:
            data = json.loads(response_text)
            
            # Validate structure
            if "personal_info" not in data:
                data["personal_info"] = {}
            if "document_info" not in data:
                data["document_info"] = {"document_type": "unknown", "confidence_score": 0.0}
            if "verification_status" not in data:
                data["verification_status"] = {
                    "cnp_format_valid": False,
                    "dates_logical": False,
                    "all_required_fields_present": False
                }
            
            # Validate CNP format
            cnp = data["personal_info"].get("cnp")
            if cnp and len(str(cnp)) == 13 and str(cnp).isdigit():
                data["verification_status"]["cnp_format_valid"] = True
            
            # Validate date logic
            birth_date = data["personal_info"].get("birth_date")
            issue_date = data["personal_info"].get("issue_date")
            if birth_date and issue_date:
                try:
                    birth = datetime.strptime(birth_date, "%Y-%m-%d").date()
                    issued = datetime.strptime(issue_date, "%Y-%m-%d").date()
                    if issued > birth and (issued - birth).days > 14 * 365:  # At least 14 years
                        data["verification_status"]["dates_logical"] = True
                except:
                    pass
            
            # Check required fields
            required_fields = ["first_name", "last_name", "cnp"]
            present_fields = sum(1 for field in required_fields 
                               if data["personal_info"].get(field))
            if present_fields >= 2:  # At least 2 of 3 required fields
                data["verification_status"]["all_required_fields_present"] = True
            
            # Split full_name if individual names are missing
            if data["personal_info"].get("full_name") and not data["personal_info"].get("first_name"):
                name_parts = data["personal_info"]["full_name"].split()
                if len(name_parts) >= 2:
                    data["personal_info"]["last_name"] = name_parts[0]
                    data["personal_info"]["first_name"] = " ".join(name_parts[1:])
            
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {str(e)}")
            return {
                "personal_info": {},
                "document_info": {
                    "document_type": "unknown",
                    "confidence_score": 0.0,
                    "extraction_notes": f"JSON parsing failed: {str(e)}"
                },
                "verification_status": {
                    "cnp_format_valid": False,
                    "dates_logical": False,
                    "all_required_fields_present": False
                }
            }
    
    def detect_document_type(self, extracted_data: Dict[str, Any]) -> str:
        """Detect document type based on extracted information"""
        document_info = extracted_data.get("document_info", {})
        doc_type = document_info.get("document_type", "unknown")
        
        if doc_type != "unknown":
            return doc_type
        
        # Try to infer from available fields
        personal_info = extracted_data.get("personal_info", {})
        
        if personal_info.get("id_series") and personal_info.get("id_number"):
            return "carte_identitate"
        elif personal_info.get("cnp") and personal_info.get("birth_place"):
            return "certificat_nastere"
        elif personal_info.get("nationality") and personal_info.get("expiry_date"):
            return "pasaport"
        else:
            return "document_personal" 