import streamlit as st
import io
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# ------------------ SETUP ------------------
client = OpenAI(api_key=OPENAI_API_KEY)
MODEL = "gpt-4o-mini"

# ------------------ CAAP SCRIPT ------------------
CAAP_SCRIPT = """
You are RootedAI, a calm, neutral, and supportive professional interviewer. 
You are delivering the Clinical Adult Attachment Protocol (CAAP).

Rules:
- Ask ONE scripted question at a time, in order, from the list provided.
- Wait for the participant’s answer before moving on.
- If the answer is vague, incomplete, or unclear → ask ONE gentle clarification.
- If the answer is clear → briefly acknowledge ("Thank you.") and then proceed to the next scripted question.
- Do NOT skip, rephrase, or invent questions.
- End the interview politely with a closing statement - "This concludes our interview. I appreciate your openness and insights throughout our conversation. Have a great day!" when all questions are completed.

Here is the full CAAP script:

1. Can you share an early memory that best describes your relationship with your parents or primary caregivers?
2. How do you usually handle stress or conflict in close relationships?
3. Do you find it easy or difficult to trust others? Can you share why?
4. What has been the most meaningful way someone has supported you in a difficult time?
5. When someone close to you is upset with you, how do you usually respond?
6. How would you describe your role in your closest relationships (for example, caregiver, peacemaker, independent)?
7. In what ways do you feel your childhood experiences still influence your relationships today?
8. What qualities do you value most in the people you let close to you?
9. Is there anything else you’d like to share about how you connect with and relate to others?
"""

# ------------------ REPORT GENERATOR ------------------
def generate_attachment_report(transcript: str) -> str:
    system_prompt = (
        "You are an expert in adult attachment theory. "
        "Analyze the transcript and output:\n"
        "1. Attachment classification: Secure/Autonomous, Dismissing, Preoccupied, or Unresolved.\n"
        "2. Narrative justification with references to transcript.\n"
    )
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "system", "content": system_prompt},
                  {"role": "user", "content": transcript}]
    )
    return resp.choices[0].message.content.strip()

# ------------------ PAGE & CSS ------------------
st.set_page_config(page_title="RootedAI CAAP Chat", layout="centered")

st.markdown(
    """
    <style>
    main > div.block-container {
        max-width: 920px;
        margin: 28px auto !important;
        background: linear-gradient(180deg, #fbfdff 0%, #ffffff 100%);
        border-radius: 14px;
        padding: 22px 28px;
        box-shadow: 0 10px 30px rgba(15, 23, 42, 0.06);
        border: 1px solid rgba(2,6,23,0.06);
    }
    body { background-color: #f3f6fb; }
    .main-title { text-align: center; font-size: 2.2rem; font-weight: 700; margin-bottom: 1rem; color: #2c3e50; }
    .chat-bubble-user {
        background-color: #2563eb; color: white;
        padding: 10px 15px; border-radius: 14px 14px 0 14px;
        margin: 6px 0; margin-left: auto; max-width: 75%;
        white-space: pre-wrap;
    }
    .chat-bubble-assistant {
        background-color: #374151; color: #e5e7eb;
        padding: 10px 15px; border-radius: 14px 14px 14px 0;
        margin: 6px 0; max-width: 75%;
        white-space: pre-wrap;
    }
    div.stButton > button {
        background-color: #2563eb !important;
        color: white !important;
        border-radius: 8px !important;
        padding: 8px 14px !important;
        font-weight: 700 !important;
        box-shadow: 0 4px 10px rgba(37,99,235,0.15) !important;
    }
    div.stDownloadButton > button {
        background-color: #10b981 !important;
        color: white !important;
        border-radius: 8px !important;
        padding: 8px 14px !important;
        font-weight: 700 !important;
        box-shadow: 0 4px 10px rgba(16,185,129,0.12) !important;
    }
    .transcript-area { font-family: monospace; white-space: pre-wrap; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="main-title">🌱 RootedAI — CAAP Interview</div>', unsafe_allow_html=True)

# ------------------ SESSION STATE ------------------
if "started" not in st.session_state: st.session_state.started = False
if "user_name" not in st.session_state: st.session_state.user_name = ""
if "messages" not in st.session_state: st.session_state.messages = []
if "closing" not in st.session_state: st.session_state.closing = False

# ------------------ START SCREEN ------------------
if not st.session_state.started:
    name_input = st.text_input("👋 Please enter your name to begin:", key="input_name")
    if st.button("🚀 Start Interview") and 2 <= len(name_input.strip()) <= 24:
        st.session_state.user_name = name_input.strip()
        st.session_state.started = True
        st.session_state.messages = [
            {"role": "system", "content": CAAP_SCRIPT},
            {"role": "assistant", "content": f"🌱 Hello {st.session_state.user_name}! Let’s begin the interview.\n\n"
                                             "Can you share an early memory that best describes your relationship with your parents or primary caregivers?"}
        ]
        st.rerun()

# ------------------ CHAT HISTORY ------------------
for msg in st.session_state.messages:
    if msg["role"] == "assistant":
        st.markdown(f"<div class='chat-bubble-assistant'>{msg['content']}</div>", unsafe_allow_html=True)
    elif msg["role"] == "user":
        st.markdown(f"<div class='chat-bubble-user'>{msg['content']}</div>", unsafe_allow_html=True)

# ------------------ CHAT INPUT ------------------
if st.session_state.started and not st.session_state.closing:
    if user_input := st.chat_input("Type your answer..."):
        # show user message immediately
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.rerun()

# ------------------ GPT RESPONSE ------------------
if st.session_state.started and not st.session_state.closing:
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        with st.spinner("Thinking..."):
            resp = client.chat.completions.create(
                model=MODEL,
                messages=st.session_state.messages
            )
            reply = resp.choices[0].message.content.strip()

        st.session_state.messages.append({"role": "assistant", "content": reply})

        # detect closing signal
        if "this concludes our interview" in reply.lower() or reply.startswith("✅"):
            st.session_state.closing = True

        st.rerun()

# ------------------ AFTER INTERVIEW ------------------
if st.session_state.closing:
    transcript = f"**Interview Transcript for {st.session_state.user_name}**\n\n"
    for msg in st.session_state.messages:
        if msg["role"] == "assistant":
            transcript += f"[Assistant]: {msg['content']}\n"
        elif msg["role"] == "user":
            transcript += f"[Participant]: {msg['content']}\n"

    with st.expander("📝 View Transcript", expanded=False):
        st.markdown(f"<div class='transcript-area'>{transcript}</div>", unsafe_allow_html=True)
        transcript_io = io.BytesIO(transcript.encode("utf-8"))
        st.download_button("📥 Download Transcript", data=transcript_io,
                           file_name=f"{st.session_state.user_name}_transcript.txt",
                           mime="text/plain")

    if st.button("🔍 Generate Attachment Report", use_container_width=True):
        with st.spinner("Generating report..."):
            try:
                report = generate_attachment_report(transcript)
                st.subheader("📋 Attachment-Style Report")
                st.markdown(report)
                report_io = io.BytesIO(report.encode("utf-8"))
                st.download_button("📥 Download Report", data=report_io,
                                   file_name=f"{st.session_state.user_name}_report.txt",
                                   mime="text/plain")
            except Exception as e:
                st.error(f"Error generating report: {e}")