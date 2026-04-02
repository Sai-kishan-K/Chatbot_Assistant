import os
from app.utils.files import get_latest_summary
import google.generativeai as genai
from dotenv import load_dotenv


CHAT_INSTRUCTIONS = """
You are a helpful assistant. I have provided a DOCUMENTATION section below.

INSTRUCTIONS:
1. Answer the user's question using the DOCUMENTATION whenever possible.
2. The user may write in English or French. Always understand both languages.
3. Reply in the same language as the user's question unless they explicitly ask for another language.
4. If the answer is not in the documentation, provide a generally helpful answer and clearly say that it was not found in the documentation.
5. Do not claim the documentation says something unless it is actually supported by the provided text.
""".strip()


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
    print("Type 'exit', 'quit', 'quitter', or 'sortir' to quit.")

    while True:
        user_query = input("\nYou: ")
        if user_query.strip().lower() in ["exit", "quit", "quitter", "sortir"]:
            break

        # We "inject" the knowledge into every prompt context
        prompt = f"""
        {CHAT_INSTRUCTIONS}

        DOCUMENTATION:
        {knowledge_base}

        QUESTION:
        {user_query}
        """
        
        response = chat.send_message(prompt)
        print(f"\nAI: {response.text}")

if __name__ == "__main__":
    start_chat()
