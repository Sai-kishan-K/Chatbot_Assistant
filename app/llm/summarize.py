import os
import google.generativeai as genai
from app.utils.logger import get_logger
from dotenv import load_dotenv

log = get_logger()

# def summarize_documentation(text: str) -> str:
#     load_dotenv()
#     # 1. Setup API Key
#     api_key = os.getenv("GEMINI_API_KEY")
#     if not api_key:
#         return "Error: GEMINI_API_KEY not found in .env"

#     genai.configure(api_key=api_key)

#     try:
#         log.info("Phase 4: Sending text to Gemini 1.5 Flash...")
        
#         # 2. Initialize Model
#         model = genai.GenerativeModel('gemini-1.5-flash-latest')
        
#         # 3. Create the Prompt
#         prompt = f"""
#         You are an expert technical documentation assistant. 
#         Below is text extracted from documentation (via OCR or Web Scraping).
        
#         TASK:
#         Provide a comprehensive summary of this documentation. 
#         Use clear headings, bullet points, and a 'Quick Start' section if applicable.
#         Ignore any remaining garbage text or navigation artifacts.

#         DOCUMENTATION TEXT:
#         {text}
#         """

#         # 4. Generate Response
#         response = model.generate_content(prompt)
        
#         return response.text

#     except Exception as e:
#         log.error(f"Gemini API Error: {e}")
#         return f"Failed to summarize: {e}"

# import os
# import google.generativeai as genai
# from app.utils.logger import get_logger
# from dotenv import load_dotenv

# log = get_logger()

def summarize_documentation(text: str) -> str:
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        return "Error: GEMINI_API_KEY not found in .env"

    # Explicitly configure the API
    genai.configure(api_key=api_key)

    try:
        log.info("Phase 4: Sending text to Gemini...")
        
        # USE THIS EXACT STRING - Trial keys are very picky about the 'models/' prefix
        model = genai.GenerativeModel('models/gemini-2.5-flash')
        
        prompt = f"Summarize this text as a technical guide:\n\n{text}"
        
        # Add a timeout and try-block specifically for the network call
        response = model.generate_content(prompt)
        
        # Check if the response actually contains text
        try:
            return response.text
        except ValueError:
            # If the response was blocked by safety filters
            return "Error: Gemini blocked the response due to safety filters or empty content."

    except Exception as e:
        log.error(f"Gemini API Error: {str(e)}")
        
        # This part MUST run if an error occurs
        print("\n--- ATTEMPTING EMERGENCY MODEL LIST ---")
        try:
            models = [m.name for m in genai.list_models()]
            print(f"Your key has access to: {models}")
            return f"Failed. Your key supports these models: {models}. Error was: {e}"
        except Exception as list_err:
            return f"Failed to summarize and could not list models. Is your API key correct? (Error: {e})"