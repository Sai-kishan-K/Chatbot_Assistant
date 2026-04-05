import streamlit as st
import os
import google.generativeai as genai
from dotenv import load_dotenv
from utils.files import get_latest_summary

CHAT_INSTRUCTIONS = """
You are a helpful assistant for processed documentation.

INSTRUCTIONS:
1. The user may write in English or French. Always understand both languages.
2. Detect the language of the current user question and reply in that same language.
3. If the current user question is in English, reply only in English unless the user explicitly asks for another language.
4. If the current user question is in French, reply only in French unless the user explicitly asks for another language.
5. Base your answer on the provided documentation whenever possible.
6. If the answer is not in the documentation, provide a generally helpful answer and clearly say it was not found in the documentation.
7. Do not pretend the documentation contains facts that are not supported by the provided text.
""".strip()

# --- CONFIGURATION ---
st.set_page_config(page_title="DocuMind AI", page_icon="🤖")
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('models/gemini-2.5-flash')

st.markdown(
    """
    <style>
    .composer-row {
        display: flex;
        align-items: flex-end;
        gap: 0.75rem;
    }

    .composer-row [data-testid="stTextInput"] {
        flex: 1 1 auto;
    }

    .composer-row [data-testid="stAudioInput"] {
        flex: 0 0 220px;
        min-width: 220px;
    }

    .composer-row [data-testid="stButton"] {
        flex: 0 0 120px;
        min-width: 120px;
    }

    .composer-row [data-testid="stButton"] button,
    .composer-row [data-testid="stAudioInput"] button,
    .composer-row [data-testid="stTextInput"] input {
        height: 3rem;
    }

    .composer-row [data-testid="stButton"] button {
        white-space: nowrap;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- INITIALIZE SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_voice_signature" not in st.session_state:
    st.session_state.last_voice_signature = None
if "draft_query" not in st.session_state:
    st.session_state.draft_query = ""
if "submitted_text_query" not in st.session_state:
    st.session_state.submitted_text_query = ""

knowledge_base = None
knowledge_source = None


def transcribe_voice_query(audio_file):
    audio_bytes = audio_file.getvalue()
    transcription_prompt = """
Transcribe this user question from audio.

Rules:
- Return only the spoken words.
- Keep the original language.
- Do not add labels, notes, or explanations.
- If the audio is unclear, return your best short transcription.
""".strip()

    response = model.generate_content(
        [
            transcription_prompt,
            {
                "mime_type": audio_file.type or "audio/wav",
                "data": audio_bytes,
            },
        ]
    )
    return response.text.strip()


def run_chat_turn(prompt, knowledge_base):
    # 1. Display user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Generate AI response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        full_prompt = (
            f"{CHAT_INSTRUCTIONS}\n\n"
            f"RESPONSE LANGUAGE:\nReply in the same language as the USER QUESTION.\n\n"
            f"DOCUMENTATION:\n{knowledge_base}\n\n"
            f"USER QUESTION:\n{prompt}"
        )

        try:
            response = model.generate_content(full_prompt, stream=True)
            for chunk in response:
                chunk_text = getattr(chunk, "text", "")
                if not chunk_text:
                    continue
                full_response += chunk_text
                message_placeholder.markdown(full_response + "▌")

            message_placeholder.markdown(full_response)
        except Exception as e:
            full_response = f"Error: {e}"
            message_placeholder.error(full_response)

    # 3. Save assistant response to history
    st.session_state.messages.append({"role": "assistant", "content": full_response})


def submit_text_query():
    st.session_state.submitted_text_query = st.session_state.draft_query.strip()
    st.session_state.draft_query = ""

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

st.markdown("Type a question or use the microphone button to record one.")

prompt = None
voice_query = None
send_text = False

with st.container():
    st.markdown('<div class="composer-row">', unsafe_allow_html=True)

    input_col, voice_col, send_col = st.columns([7, 2.4, 1.4], vertical_alignment="bottom")

    with input_col:
        st.text_input(
            "Message",
            key="draft_query",
            placeholder="Ask me about the documentation... / Pose-moi une question...",
            disabled=knowledge_base is None,
            label_visibility="collapsed",
        )

    with voice_col:
        voice_query = st.audio_input(
            "Voice question",
            disabled=knowledge_base is None,
            label_visibility="collapsed",
            key="voice_query",
        )

    with send_col:
        send_text = st.button(
            "Send",
            disabled=knowledge_base is None or (
                not st.session_state.draft_query.strip() and voice_query is None
            ),
            use_container_width=True,
            type="primary",
            on_click=submit_text_query if st.session_state.draft_query.strip() else None,
        )

    st.markdown("</div>", unsafe_allow_html=True)

# --- CHAT LOGIC ---
if send_text and knowledge_base:
    typed_prompt = st.session_state.submitted_text_query.strip()

    if typed_prompt:
        st.session_state.submitted_text_query = ""
        run_chat_turn(typed_prompt, knowledge_base)

    elif voice_query is not None:
        voice_signature = (
            voice_query.name,
            voice_query.size,
            voice_query.type,
            hash(voice_query.getvalue()),
        )

        if voice_signature != st.session_state.last_voice_signature:
            with st.spinner("Transcribing your voice question..."):
                try:
                    prompt = transcribe_voice_query(voice_query)
                    st.session_state.last_voice_signature = voice_signature
                except Exception as e:
                    prompt = None
                    st.error(f"Voice transcription failed: {e}")

            if prompt:
                st.caption(f"Transcribed question: {prompt}")
                run_chat_turn(prompt, knowledge_base)
        else:
            st.info("This recording was already submitted. Record a new question to send another voice query.")
    else:
        st.info("Type a message or record a voice question before sending.")
