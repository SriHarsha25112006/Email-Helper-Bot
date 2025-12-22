import streamlit as st
import json
import os
from dotenv import load_dotenv
from generate import GenerateEmail

load_dotenv()

# ---------------- CONFIG ----------------
st.set_page_config(page_title="AI Email Editor", page_icon="📧", layout="wide")

MODEL_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4.1") 
generator = GenerateEmail(model=MODEL_NAME)

# ---------------- DATA LOADING ----------------
@st.cache_data
def load_emails_from_jsonl(file_path):
    if os.path.exists(file_path):
        path = file_path
    elif os.path.exists(f"datasets/{file_path}"):
        path = f"datasets/{file_path}"
    else:
        return {"emails": {}, "ids": []}

    data = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                data.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    emails = {item["id"]: item for item in data}
    return {"emails": emails, "ids": list(emails.keys())}

data_files = {
    "shorten": load_emails_from_jsonl("shorten.jsonl"),
    "lengthen": load_emails_from_jsonl("lengthen.jsonl"),
    "tone": load_emails_from_jsonl("tone.jsonl"),
}

action = st.sidebar.selectbox("1. Select Action", ["shorten", "lengthen", "tone"])

email_ids = data_files[action]["ids"]
emails = data_files[action]["emails"]

if not email_ids:
    st.error(f"Error: {action}.jsonl not found or empty.")
    st.stop()

email_id = st.sidebar.selectbox("2. Select Email ID", email_ids)
email = emails[email_id]
original_body = email.get("content", "")

# ---------------- SESSION KEYS ----------------
body_key = f"body_{action}_{email_id}"
orig_key = f"orig_{action}_{email_id}"

if body_key not in st.session_state:
    st.session_state[body_key] = original_body

if orig_key not in st.session_state:
    st.session_state[orig_key] = original_body

# ---------------- UI DISPLAY ----------------
st.markdown("## 📧 Email Details")
st.markdown(f"**From:** {email.get('sender', '-')}")
st.markdown(f"**Subject:** {email.get('subject', '-')}")

st.divider()

st.markdown("### ✏️ Email Body")
st.text_area(label="Edit text below:", height=250, key=body_key)

# ---------------- CALLBACKS ----------------
def run_ai(action_type, tone=None):
    content = st.session_state[body_key].strip()
    if not content:
        return
    if action_type == "tone":
        result = generator.generate("tone", content, tone_type=tone)
    else:
        result = generator.generate(action_type, content)

    if not result.startswith("Error:"):
        st.session_state[body_key] = result
    else:
        st.error(result)

def reset_body():
    st.session_state[body_key] = st.session_state[orig_key]

# ---------------- BUTTONS ----------------
st.markdown("### ✨ Actions")

# Create three columns for the three main actions
col1, col2, col3 = st.columns(3)

with col1:
    st.button("⚡ Shorten", on_click=run_ai, args=("shorten",), use_container_width=True)

with col2:
    st.button("📝 Lengthen", on_click=run_ai, args=("lengthen",), use_container_width=True)

with col3:
    # Keep the tone selector above its specific button
    tone_choice = st.selectbox("Select Tone Style", ["Friendly", "Sympathetic", "Professional"], label_visibility="collapsed")
    st.button("🎭 Apply Tone", on_click=run_ai, args=("tone", tone_choice), use_container_width=True)

st.divider()

# Reset button centered below the main actions
if st.button("🔄 Reset to Original Content", on_click=reset_body):
    st.info("Content restored to original state.")