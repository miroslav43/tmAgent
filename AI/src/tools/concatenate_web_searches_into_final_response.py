import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
from datetime import datetime
import re
import json

# Load environment variables
load_dotenv()

# Get API key from environment
GEMINI_API_KEY = os.getenv("GEMINI_KEY")
CURRENT_DATE = datetime.now().strftime("%Y-%m-%d")

def load_concatenation_system_prompt(response_style: str = "detailed"):
    """Load the system prompt for concatenating web search results based on response style"""
    try:
        # Get the directory where this script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Go up to src directory, then to instructions/concatenate_responses_get_final_response
        
        # Select the appropriate prompt file based on response style
        if response_style == "compact":
            prompt_filename = "concatenate_web_searches_compact.txt"
        else:
            prompt_filename = "concatenate_web_searches.txt"  # Default to detailed
        
        prompts_path = os.path.join(script_dir, "..", "instructions", "concatenate_responses_get_final_response", prompt_filename)
        prompts_path = os.path.normpath(prompts_path)
        
        with open(prompts_path, "r", encoding="utf-8") as file:
            system_prompt = file.read().strip()
            # Replace the date placeholder with current date
            system_prompt = system_prompt.replace("{CURRENT_DATE}", CURRENT_DATE)
            print(f"✅ Loaded {response_style} response style prompt from {prompt_filename}")
            return system_prompt
    except FileNotFoundError:
        print(f"❌ Error: {prompt_filename} file not found at {prompts_path}")
        print(f"Expected location: src/instructions/concatenate_responses_get_final_response/{prompt_filename}")
        return None
    except Exception as e:
        print(f"❌ Error loading concatenation system prompt: {e}")
        return None

def load_rag_context_file(domain_name: str, rag_context_path: str = "rag_context") -> str:
    """
    Load RAG context file for a specific domain (dfmt.ro or timpark.ro)
    
    Args:
        domain_name: The domain name (e.g., 'dfmt.ro', 'timpark.ro')
        rag_context_path: The path to RAG context files directory
    
    Returns:
        Content of the RAG context file or None if not found
    """
    try:
        # Get the directory where this script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Go up to src directory, then to the specified RAG context path
        rag_context_file_path = os.path.join(script_dir, "..", rag_context_path, domain_name)
        rag_context_file_path = os.path.normpath(rag_context_file_path)
        
        if os.path.exists(rag_context_file_path):
            with open(rag_context_file_path, "r", encoding="utf-8") as file:
                content = file.read().strip()
                print(f"✅ Loaded RAG context for {domain_name} ({len(content)} characters)")
                return content
        else:
            print(f"⚠️ RAG context file not found for domain {domain_name} at {rag_context_file_path}")
            return None
    except Exception as e:
        print(f"❌ Error loading RAG context for {domain_name}: {e}")
        return None

def extract_relevant_rag_contexts(selected_domains: list, rag_config: dict = None) -> dict:
    """
    Extract RAG contexts for domains that have corresponding RAG files
    
    Args:
        selected_domains: List of domains selected by trusted_sites_search
        rag_config: RAG configuration from agent_config.json
    
    Returns:
        Dictionary mapping domain names to their RAG context content
    """
    # Check if RAG context is enabled
    if not rag_config or not rag_config.get('use_rag_context', False):
        print(f"📝 RAG context integration is disabled in configuration")
        return {}
    
    # Get configured RAG domains and path
    configured_rag_domains = rag_config.get('rag_domains', ['dfmt.ro', 'timpark.ro'])
    rag_context_path = rag_config.get('rag_context_path', 'rag_context')
    
    relevant_contexts = {}
    
    if not selected_domains:
        return relevant_contexts
    
    print(f"\n🔍 Checking for RAG contexts in selected domains: {selected_domains}")
    print(f"📚 Configured RAG domains: {configured_rag_domains}")
    print(f"📁 RAG context path: {rag_context_path}")
    
    for domain in selected_domains:
        # Check if this domain is in the configured RAG domains list
        if domain in configured_rag_domains:
            rag_content = load_rag_context_file(domain, rag_context_path)
            if rag_content:
                relevant_contexts[domain] = rag_content
                print(f"✅ Added RAG context for {domain}")
    
    if relevant_contexts:
        print(f"📚 Total RAG contexts loaded: {len(relevant_contexts)} domains")
    else:
        print(f"📝 No RAG contexts found for the selected domains")
    
    return relevant_contexts

def create_user_input_for_gemini(
    original_question: str,
    reformulated_query: str = None,
    regular_web_search_results: str = None,
    trusted_sites_search_results: dict = None,
    rag_contexts: dict = None
) -> str:
    """
    Create the structured user input for Gemini to process all the information
    Now includes RAG context integration
    """
    
    user_input = f"""**ÎNTREBAREA ORIGINALĂ A UTILIZATORULUI:**
{original_question}

"""
    
    if reformulated_query:
        user_input += f"""**INTEROGAREA REFORMULATĂ:**
{reformulated_query}

"""
    else:
        user_input += f"""**INTEROGAREA REFORMULATĂ:**
Nu a fost utilizată reformularea - s-a folosit întrebarea originală.

"""
    
    if regular_web_search_results:
        user_input += f"""**REZULTATELE CĂUTĂRII WEB GENERALE (Perplexity):**
{regular_web_search_results}

"""
    else:
        user_input += f"""**REZULTATELE CĂUTĂRII WEB GENERALE (Perplexity):**
Căutarea web generală nu a fost activată sau nu a produs rezultate.

"""
    
    if trusted_sites_search_results and trusted_sites_search_results.get('success'):
        domains = trusted_sites_search_results.get('selected_domains', [])
        search_text = trusted_sites_search_results.get('search_results', '')
        
        user_input += f"""**REZULTATELE CĂUTĂRII PE SITE-URI DE ÎNCREDERE (Perplexity pe domenii selectate de Gemini):**
Domenii guvernamentale românești selectate ({len(domains)} total):
{', '.join(domains)}

Rezultatele căutării pe site-urile de încredere:
{search_text}

"""
    else:
        user_input += f"""**REZULTATELE CĂUTĂRII PE SITE-URI DE ÎNCREDERE (Perplexity pe domenii selectate de Gemini):**
Căutarea pe site-uri de încredere nu a fost activată sau nu a produs rezultate.

"""
    
    # NEW: Add RAG context section if available
    if rag_contexts and len(rag_contexts) > 0:
        user_input += f"""**CONTEXT RAG DETALIAT DIN BAZELE DE DATE LOCALE:**
Am identificat informații detaliate din bazele de date locale pentru următoarele domenii selectate:

"""
        for domain, context_content in rag_contexts.items():
            user_input += f"""**Context pentru {domain.upper()}:**
{context_content}

"""
        
        user_input += f"""**INSTRUCȚIUNI PENTRU UTILIZAREA CONTEXTULUI RAG:**
- Contextul RAG de mai sus conține informații oficiale extrase și procesate din site-urile guvernamentale românești
- Aceste informații sunt foarte actuale și detaliate pentru domeniile specifice ({', '.join(rag_contexts.keys())})
- Folosiți acest context pentru a oferi informații foarte precise, specifice și detaliate în răspunsul final
- Contextul RAG completează rezultatele căutării pe site-uri de încredere cu detalii suplimentare oficiale
- Prioritizați informațiile din contextul RAG pentru aspectele tehnice, proceduri exacte, taxe specifice, și detalii administrative
- Integrați natural aceste informații în răspunsul final fără să menționați explicit "contextul RAG"

"""
    
    return user_input

def concatenate_web_searches_into_final_response(
    original_question: str,
    reformulated_query: str = None,
    regular_web_search_results: str = None,
    trusted_sites_search_results: dict = None,
    # Gemini parameters
    temperature: float = 0.1,
    max_tokens: int = 15000,
    model: str = "gemini-2.5-flash-preview-04-17",
    # RAG configuration parameters
    rag_config: dict = None,
    # Response style configuration
    response_style: str = "detailed",
    # Output parameters
    save_to_file: bool = True
) -> str:
    """
    Concatenate and synthesize web search results into a final comprehensive response
    Now enhanced with configurable RAG context integration and response style selection
    
    Args:
        original_question: The user's original question
        reformulated_query: The reformulated query (if used)
        regular_web_search_results: Results from regular web search
        trusted_sites_search_results: Results dict from trusted sites search
        temperature: Controls randomness (0.0-1.0, lower = more focused)
        max_tokens: Maximum tokens to generate
        model: Gemini model to use
        rag_config: RAG configuration dict from agent_config.json
        response_style: Response style ("detailed" or "compact")
        save_to_file: Whether to save the final response to file
    
    Returns:
        The final synthesized response
    """
    
    print(f"\n🔧 FINAL RESPONSE GENERATION - DETAILED DEBUGGING")
    print("=" * 60)
    
    # Validate API key
    if not GEMINI_API_KEY:
        print("❌ Error: GEMINI_KEY not found in environment variables")
        return None
    
    print(f"✅ API Key loaded: {GEMINI_API_KEY[:10]}...{GEMINI_API_KEY[-10:]}")
    
    # Load system prompt based on response style
    system_prompt = load_concatenation_system_prompt(response_style)
    if not system_prompt:
        print("❌ Failed to load system prompt")
        return None
    
    print(f"✅ System prompt loaded successfully ({len(system_prompt)} characters)")
    print(f"📝 System prompt preview: {system_prompt[:200]}...")
    
    # NEW: Extract RAG contexts based on selected domains and configuration
    rag_contexts = {}
    if trusted_sites_search_results and trusted_sites_search_results.get('success'):
        selected_domains = trusted_sites_search_results.get('selected_domains', [])
        rag_contexts = extract_relevant_rag_contexts(selected_domains, rag_config)
    
    print(f"\n🔧 Final Response Generation Configuration:")
    print(f"   Model: {model}")
    print(f"   Temperature: {temperature}")
    print(f"   Max Tokens: {max_tokens}")
    print(f"   Response Style: {response_style}")
    print(f"   Original Question: '{original_question}'")
    print(f"   Has Reformulated Query: {'Yes' if reformulated_query else 'No'}")
    print(f"   Has Regular Search Results: {'Yes' if regular_web_search_results else 'No'}")
    print(f"   Has Trusted Sites Results: {'Yes' if trusted_sites_search_results and trusted_sites_search_results.get('success') else 'No'}")
    print(f"   RAG Context Enabled: {'Yes' if rag_config and rag_config.get('use_rag_context', False) else 'No'}")
    print(f"   RAG Contexts Available: {len(rag_contexts)} domains ({', '.join(rag_contexts.keys()) if rag_contexts else 'None'})")
    
    # Create structured user input with RAG context integration
    user_input = create_user_input_for_gemini(
        original_question=original_question,
        reformulated_query=reformulated_query,
        regular_web_search_results=regular_web_search_results,
        trusted_sites_search_results=trusted_sites_search_results,
        rag_contexts=rag_contexts  # NEW: Pass RAG contexts
    )
    
    print(f"\n📄 User input created successfully ({len(user_input)} characters)")
    print(f"📝 User input preview (first 300 chars):")
    print("-" * 40)
    print(user_input[:300] + "...")
    print("-" * 40)
    
    try:
        # Initialize the new Gen AI client
        print(f"\n🔌 Initializing Gemini API client...")
        client = genai.Client(api_key=GEMINI_API_KEY)
        print("✅ Gemini API client configured for final response generation")
        
        # Prepare content using the new SDK structure
        print(f"\n📦 Preparing content structure...")
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=user_input),
                ],
            ),
        ]
        print(f"✅ Content structure prepared with {len(contents)} message(s)")
        print(f"📊 First content role: {contents[0].role}")
        print(f"📊 First content parts count: {len(contents[0].parts)}")
        print(f"📊 First part text length: {len(contents[0].parts[0].text)} characters")
        
        # Generate final response with system instruction in config
        print(f"\n⚙️ Preparing generation config...")
        generate_content_config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=temperature,
            max_output_tokens=max_tokens,
            response_mime_type="text/plain"
        )
        print(f"✅ Generation config prepared:")
        print(f"   📊 Temperature: {generate_content_config.temperature}")
        print(f"   📊 Max tokens: {generate_content_config.max_output_tokens}")
        print(f"   📊 MIME type: {generate_content_config.response_mime_type}")
        print(f"   📊 System instruction length: {len(generate_content_config.system_instruction)} characters")
        
        print(f"\n🚀 Making API call to {model}...")
        print(f"📡 Sending request with:")
        print(f"   🔹 Model: {model}")
        print(f"   🔹 Contents: {len(contents)} messages")
        print(f"   🔹 Total input size: ~{len(user_input) + len(system_prompt)} characters")
        
        # Check if input might be too large
        total_input_size = len(user_input) + len(system_prompt)
        if total_input_size > 30000:
            print(f"⚠️ Input size ({total_input_size} chars) is quite large, this might cause timeout issues")
        
        try:
            response = client.models.generate_content(
                model=model,
                contents=contents,
                config=generate_content_config
            )
            print(f"✅ API call completed successfully!")
        except Exception as api_error:
            print(f"❌ API call failed: {api_error}")
            print(f"🔄 Trying with reduced input size...")
            
            # Try with a smaller user input
            if len(user_input) > 8000:
                print(f"📉 Reducing user input from {len(user_input)} to ~8000 characters...")
                truncated_input = user_input[:8000] + "\n\n[INPUT TRUNCATED DUE TO SIZE LIMITATIONS]"
                
                contents_fallback = [
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_text(text=truncated_input),
                        ],
                    ),
                ]
                
                try:
                    response = client.models.generate_content(
                        model=model,
                        contents=contents_fallback,
                        config=generate_content_config
                    )
                    print(f"✅ Fallback API call with reduced input completed successfully!")
                except Exception as fallback_error:
                    print(f"❌ Fallback API call also failed: {fallback_error}")
                    raise fallback_error
            else:
                raise api_error
        
        # Debug response structure
        print(f"\n🔍 RESPONSE DEBUGGING:")
        print(f"   📊 Response type: {type(response)}")
        print(f"   📊 Response object: {response}")
        
        if hasattr(response, 'text'):
            print(f"   📊 Has .text attribute: Yes")
            print(f"   📊 .text value: {repr(response.text)}")
            print(f"   📊 .text type: {type(response.text)}")
            if response.text:
                print(f"   📊 .text length: {len(response.text)}")
            else:
                print(f"   ⚠️ .text is None or empty")
        else:
            print(f"   ❌ No .text attribute found")
        
        if hasattr(response, 'candidates'):
            print(f"   📊 Has .candidates attribute: Yes")
            print(f"   📊 Candidates count: {len(response.candidates) if response.candidates else 0}")
            if response.candidates:
                for i, candidate in enumerate(response.candidates):
                    print(f"   📊 Candidate {i}: {candidate}")
                    if hasattr(candidate, 'content'):
                        print(f"   📊 Candidate {i} content: {candidate.content}")
                    if hasattr(candidate, 'finish_reason'):
                        print(f"   📊 Candidate {i} finish_reason: {candidate.finish_reason}")
            else:
                print(f"   ⚠️ .candidates is None or empty")
        else:
            print(f"   ❌ No .candidates attribute found")
        
        if hasattr(response, '__dict__'):
            print(f"   📊 Response attributes: {list(response.__dict__.keys())}")
            for key, value in response.__dict__.items():
                if key not in ['text', 'candidates']:
                    print(f"   📊 {key}: {value}")
        
        # Extract response text
        if response and response.text:
            final_response = response.text
            print(f"✅ Final response generated successfully! ({len(final_response)} characters)")
            print(f"📝 Response preview (first 200 chars):")
            print("-" * 40)
            print(final_response[:200] + "...")
            print("-" * 40)
            
            # Save to file if requested
            if save_to_file:
                filename = save_final_response_to_file(
                    original_question=original_question,
                    final_response=final_response,
                    generation_metadata={
                        "model": model,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                        "response_style": response_style,
                        "has_reformulated_query": bool(reformulated_query),
                        "has_regular_search": bool(regular_web_search_results),
                        "has_trusted_search": bool(trusted_sites_search_results and trusted_sites_search_results.get('success')),
                        "rag_contexts_used": list(rag_contexts.keys()) if rag_contexts else []  # NEW: Track RAG usage
                    }
                )
                print(f"💾 Final response saved to: {filename}")
            
            return final_response
        else:
            print("❌ No text found in response")
            print("🔍 Attempting to extract text from alternative sources...")
            
            # Try alternative extraction methods
            extracted_text = None
            if hasattr(response, 'candidates') and response.candidates:
                for i, candidate in enumerate(response.candidates):
                    print(f"   🔍 Checking candidate {i}...")
                    if hasattr(candidate, 'content') and candidate.content:
                        if hasattr(candidate.content, 'parts') and candidate.content.parts:
                            for j, part in enumerate(candidate.content.parts):
                                print(f"   🔍 Checking candidate {i}, part {j}...")
                                if hasattr(part, 'text') and part.text:
                                    extracted_text = part.text
                                    print(f"   ✅ Found text in candidate {i}, part {j}!")
                                    break
                            if extracted_text:
                                break
                        elif hasattr(candidate.content, 'text') and candidate.content.text:
                            extracted_text = candidate.content.text
                            print(f"   ✅ Found text in candidate {i} content!")
                            break
                    if extracted_text:
                        break
            
            if extracted_text:
                print(f"✅ Successfully extracted text via alternative method! ({len(extracted_text)} characters)")
                return extracted_text
            else:
                print("❌ Could not extract text from any source")
                return None
        
    except Exception as e:
        print(f"❌ Error making Gemini API call for final response: {e}")
        print(f"🔍 Exception type: {type(e)}")
        import traceback
        print(f"📄 Full traceback:")
        print(traceback.format_exc())
        return None

def save_final_response_to_file(original_question, final_response, generation_metadata, filename=None):
    """Save the final synthesized response to a file"""
    if filename is None:
        # Create filename from question
        clean_query = re.sub(r'[^\w\s-]', '', original_question)
        clean_query = re.sub(r'\s+', '_', clean_query)
        clean_query = clean_query[:50].strip('_')
        timestamp = datetime.now().strftime("%m_%d_%H_%M")
        filename = f"FINAL_{clean_query}_{timestamp}.txt"
    
    try:
        with open(filename, "w", encoding="utf-8") as file:
            file.write("="*80 + "\n")
            file.write("RĂSPUNS FINAL SINTETIZAT - AGENT CIVIC ROMÂN\n")
            file.write("="*80 + "\n\n")
            file.write(f"Întrebarea Originală: {original_question}\n")
            file.write(f"Data Procesării: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            file.write("-"*80 + "\n\n")
            file.write("CONFIGURAȚIA SINTEZEI:\n")
            file.write(f"   Model: {generation_metadata['model']}\n")
            file.write(f"   Temperature: {generation_metadata['temperature']}\n")
            file.write(f"   Max Tokens: {generation_metadata['max_tokens']}\n")
            file.write(f"   Response Style: {generation_metadata.get('response_style', 'detailed')}\n")
            file.write(f"   Reformulare folosită: {'Da' if generation_metadata['has_reformulated_query'] else 'Nu'}\n")
            file.write(f"   Căutare web regulată: {'Da' if generation_metadata['has_regular_search'] else 'Nu'}\n")
            file.write(f"   Căutare site-uri de încredere: {'Da' if generation_metadata['has_trusted_search'] else 'Nu'}\n")
            # NEW: Track RAG context usage
            rag_contexts_used = generation_metadata.get('rag_contexts_used', [])
            file.write(f"   Context RAG folosit: {'Da' if rag_contexts_used else 'Nu'}")
            if rag_contexts_used:
                file.write(f" ({', '.join(rag_contexts_used)})")
            file.write("\n")
            file.write("-"*80 + "\n\n")
            file.write("RĂSPUNSUL FINAL SINTETIZAT:\n")
            file.write("-"*30 + "\n")
            file.write(final_response)
            file.write("\n\n" + "="*80 + "\n")
            file.write("NOTA: Acest răspuns a fost generat prin sinteza inteligentă a rezultatelor\n")
            file.write("din căutări multiple, prioritizând sursele oficiale guvernamentale românești")
            if rag_contexts_used:
                file.write(f"\nși integrând context RAG detaliat din: {', '.join(rag_contexts_used)}")
            file.write(".\n")
            file.write("="*80 + "\n")
        
        print(f"💾 Final response saved to: {filename}")
        return filename
    except Exception as e:
        print(f"❌ Error saving final response: {e}")
        return None

if __name__ == "__main__":
    print("=" * 80)
    print("FINAL RESPONSE GENERATION - CONCATENATE WEB SEARCHES + RAG CONTEXT")
    print("=" * 80)
    print("🔄 This tool synthesizes results from multiple search tools:")
    print("   1️⃣  Query reformulation results")
    print("   2️⃣  Regular web search results")  
    print("   3️⃣  Trusted government sites search results")
    print("   4️⃣  🆕 RAG context integration (configurable)")
    print("   5️⃣  Final synthesized response")
    print("=" * 80)
    
    # Test with sample data
    TEST_QUESTION = "taxe locuinta timisoara 2025"
    TEST_REFORMULATED = "Care sunt taxele și impozitele locale pentru locuințe în Timișoara pentru anul 2025, cum se calculează, unde se plătesc și care sunt termenele?"
    TEST_REGULAR_SEARCH = "Pentru taxele de locuință în Timișoara în 2025... [rezultate căutare regulată]"
    TEST_TRUSTED_SEARCH = {
        "success": True,
        "selected_domains": ["dfmt.ro", "evpers.primariatm.ro", "timpark.ro"],  # Including dfmt.ro for testing
        "search_results": "Taxele locale pentru locuințe în Timișoara... [rezultate oficiale]"
    }
    
    # Load actual agent configuration to test real settings
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, "..", "agent_config.json")
        config_path = os.path.normpath(config_path)
        
        with open(config_path, "r", encoding="utf-8") as f:
            agent_config = json.load(f)
        
        # Extract RAG configuration from agent config
        RAG_CONFIG = agent_config.get("final_response_generation", {}).get("rag_context", {
            "use_rag_context": False,
            "rag_domains": ["dfmt.ro", "timpark.ro"],
            "rag_context_path": "rag_context"
        })
        
        print(f"\n📚 Loading RAG configuration from agent_config.json:")
        print(f"   🔧 RAG Context Enabled: {RAG_CONFIG.get('use_rag_context', False)}")
        print(f"   🔧 RAG Domains: {RAG_CONFIG.get('rag_domains', [])}")
        print(f"   🔧 RAG Context Path: {RAG_CONFIG.get('rag_context_path', 'rag_context')}")
        
    except Exception as e:
        print(f"⚠️  Could not load agent_config.json, using fallback RAG configuration: {e}")
        # Fallback RAG Configuration for testing
        RAG_CONFIG = {
            "use_rag_context": True,
            "rag_domains": ["dfmt.ro", "timpark.ro"],
            "rag_context_path": "rag_context"
        }
    
    print(f"\n🎯 Testing final response generation with RAG context for: '{TEST_QUESTION}'")
    print("-" * 80)
    
    # Generate final response
    result = concatenate_web_searches_into_final_response(
        original_question=TEST_QUESTION,
        reformulated_query=TEST_REFORMULATED,
        regular_web_search_results=TEST_REGULAR_SEARCH,
        trusted_sites_search_results=TEST_TRUSTED_SEARCH,
        rag_config=RAG_CONFIG,  # Use actual agent configuration
        response_style="detailed",
        save_to_file=True
    )
    
    if result:
        print(f"\n🎉 FINAL RESPONSE WITH RAG CONTEXT GENERATED SUCCESSFULLY!")
        print("-" * 60)
        print(f"Response length: {len(result)} characters")
        print(f"First 200 characters: {result[:200]}...")
    else:
        print(f"\n❌ FINAL RESPONSE GENERATION FAILED")
    
    print("\n" + "=" * 80)
    print("✨ This tool now supports configurable RAG contexts!")
    print("   📚 Configure RAG integration in agent_config.json:")
    print("   📝 'use_rag_context': true/false - Enable/disable RAG")
    print("   📝 'rag_domains': ['dfmt.ro', 'timpark.ro'] - Domains to check")
    print("   📝 'rag_context_path': 'rag_context' - Path to RAG files")
    print("   🔧 When enabled and matching domains are selected by trusted_sites_search,")
    print("   🔧 their corresponding detailed RAG context files are loaded automatically")
    print("=" * 80)
