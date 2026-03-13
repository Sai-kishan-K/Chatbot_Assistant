import streamlit as st
import os
import google.generativeai as genai
from dotenv import load_dotenv
from app.utils.files import get_latest_summary

# --- CONFIGURATION ---
st.set_page_config(page_title="DocuMind AI", page_icon="🤖")
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('models/gemini-2.5-flash')

# --- INITIALIZE SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- SIDEBAR: Load the Knowledge ---
with st.sidebar:
    st.title("Settings")
    latest_file = get_latest_summary()
    if latest_file:
        st.success(f"Connected to: {os.path.basename(latest_file)}")
        with open(latest_file, "r") as f:
            knowledge_base = f.read()
    else:
        st.error("No documentation found. Run the scraper first!")
        st.stop()

# --- MAIN CHAT INTERFACE ---
st.title("💬 CraftAI Chatbot")
st.caption("I'm an AI ")

# Display chat history from session state
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- CHAT LOGIC ---
if prompt := st.chat_input("Ask me about the documentation..."):
    # 1. Display user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Generate AI response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        # We inject the knowledge base into the system prompt context
        full_prompt = f"Using this doc: {knowledge_base}\n\nUser Question: {prompt}"
        
        try:
            # Note: 2026 Streamlit supports streaming natively for a 'typewriter' effect
            response = model.generate_content(full_prompt, stream=True)
            for chunk in response:
                full_response += chunk.text
                message_placeholder.markdown(full_response + "▌")
            
            message_placeholder.markdown(full_response)
        except Exception as e:
            full_response = f"Error: {e}"
            message_placeholder.error(full_response)

    # 3. Save assistant response to history
    st.session_state.messages.append({"role": "assistant", "content": full_response})
