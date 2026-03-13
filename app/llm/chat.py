import os
from app.utils.files import get_latest_summary
import google.generativeai as genai
from dotenv import load_dotenv

def start_chat():
    load_dotenv()
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel('models/gemini-2.5-flash')

    # 1. Load your summary as the "Knowledge Base"
    summary_path = get_latest_summary()

    if not summary_path:
        print("Error: No summary files found in 'outputs/'. Run the scraper first!")
        return
    
    print(f"Loading knowledge from: {summary_path}")
    with open(summary_path, "r", encoding="utf-8") as f:
        knowledge_base = f.read()

    # 2. Start the chat session with instructions
    chat = model.start_chat(history=[])
    
    print("\n--- Documentation Chatbot Active ---")
    print("Type 'exit' to quit.")

    while True:
        user_query = input("\nYou: ")
        if user_query.lower() in ["exit", "quit"]:
            break

        # We "inject" the knowledge into every prompt context

        # Use the following documentation to answer the user's question accurately.
        # If the answer isn't in the documentation, say you don't know.
        prompt = f"""
        You are a helpful assistant. I have provided a 'DOCUMENTATION' below.
        
        INSTRUCTIONS:
        1. Answer the question using the KNOWLEDGE BASE.
        2. If the answer is not there, try to provide a general helpful answer based on your training but DISCLOSE that it's not in the documentation.
        3. Do NOT just say 'I don't know' if you can find ANY related keywords

        DOCUMENTATION:
        {knowledge_base}
        
        QUESTION:
        {user_query}
        """
        
        response = chat.send_message(prompt)
        print(f"\nAI: {response.text}")

if __name__ == "__main__":
    start_chat()