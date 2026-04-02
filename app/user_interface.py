import streamlit as st
import os
import google.generativeai as genai
from dotenv import load_dotenv
from utils.files import get_latest_summary

CHAT_INSTRUCTIONS = """
You are a helpful assistant for processed documentation.

INSTRUCTIONS:
1. The user may write in English or French. Always understand both languages.
2. Reply in the same language as the user's message unless they explicitly request another language.
3. Base your answer on the provided documentation whenever possible.
4. If the answer is not in the documentation, provide a generally helpful answer and clearly say it was not found in the documentation.
5. Do not pretend the documentation contains facts that are not supported by the provided text.
""".strip()

# --- CONFIGURATION ---
st.set_page_config(page_title="DocuMind AI", page_icon="🤖")
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('models/gemini-2.5-flash')

# --- INITIALIZE SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []

knowledge_base = None
knowledge_source = None

# --- SIDEBAR: Load the Knowledge ---
with st.sidebar:
    st.title("Settings")
    uploaded_summary = st.file_uploader(
        "Upload summary file",
        type=["md", "txt"],
        help="Use a generated summary file if the app cannot find one locally.",
    )
    latest_file = get_latest_summary()

    if uploaded_summary is not None:
        knowledge_base = uploaded_summary.getvalue().decode("utf-8")
        knowledge_source = uploaded_summary.name
        st.success(f"Using uploaded file: {uploaded_summary.name}")
    elif latest_file:
        st.success(f"Connected to: {os.path.basename(latest_file)}")
        knowledge_source = latest_file
        with open(latest_file, "r", encoding="utf-8") as f:
            knowledge_base = f.read()
    else:
        st.warning("No summary file detected.")
        st.markdown(
            "Add `data/final_summary.md`, commit an `outputs/.../final_summary.md`, "
            "or upload a `.md`/`.txt` summary here."
        )

# --- MAIN CHAT INTERFACE ---
st.title("💬 CraftAI Chatbot")
st.caption("Ask questions in English or French about your processed documentation.")

if knowledge_source:
    st.caption(f"Knowledge source: `{os.path.basename(knowledge_source)}`")
else:
    st.info(
        "Documentation is not loaded yet. Upload a generated summary in the sidebar "
        "or commit `data/final_summary.md` to the repository for Streamlit deployment."
    )

# Display chat history from session state
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- CHAT LOGIC ---
prompt = st.chat_input(
    "Ask me about the documentation... / Pose-moi une question sur la documentation...",
    disabled=knowledge_base is None,
)

if prompt and knowledge_base:
    # 1. Display user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Generate AI response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        # We inject the knowledge base and response rules into the prompt context.
        full_prompt = (
            f"{CHAT_INSTRUCTIONS}\n\n"
            f"DOCUMENTATION:\n{knowledge_base}\n\n"
            f"USER QUESTION:\n{prompt}"
        )
        
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
