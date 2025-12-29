import streamlit as st
import json
import os
from dotenv import load_dotenv
from generate import GenerateEmail

load_dotenv()

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Email Helper App", page_icon="📧", layout="wide")

generator_bot = GenerateEmail(
    deployment_name=os.getenv("GENERATOR_DEPLOYMENT", "gpt-4o-mini")
)
judge_bot = GenerateEmail(deployment_name=os.getenv("JUDGE_DEPLOYMENT", "gpt-4.1"))


# ---------------- DATA LOADING ----------------
@st.cache_data
def load_emails_from_jsonl(*file_names):
    """
    Loads emails from multiple JSONL files and merges them.
    Re-assigns IDs to ensure uniqueness across files.
    """
    data = []
    
    for file_name in file_names:
        paths = [file_name, f"datasets/{file_name}"]
        path = next((p for p in paths if os.path.exists(p)), None)
        
        if path:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        data.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue

    if not data:
        return {"emails": {}, "ids": []}

    # Re-index emails to avoid ID collisions
    emails = {}
    for idx, item in enumerate(data):
        new_id = idx + 1
        item["id"] = new_id
        emails[new_id] = item
        
    return {"emails": emails, "ids": list(emails.keys())}


data_files = {
    "shorten": load_emails_from_jsonl("shorten.jsonl", "short.jsonl"),
    "lengthen": load_emails_from_jsonl("lengthen.jsonl", "long.jsonl"),
    "tone": load_emails_from_jsonl("tone.jsonl", "toned.jsonl"),
}

# ---------------- SIDEBAR ----------------
st.sidebar.title("Configuration")
action_map = {
    "Short Emails": "shorten",
    "Longer Emails": "lengthen",
    "Toned Emails": "tone",
}
selected_label = st.sidebar.selectbox("1. Select Action", list(action_map.keys()))
action = action_map[selected_label]

email_ids = data_files[action]["ids"]

if not email_ids:
    st.error(f"Error: No data found for '{action}'. Run generate.py first.")
    st.stop()

email_id = st.sidebar.selectbox("2. Select Email ID", email_ids)
email = data_files[action]["emails"][email_id]

# ---------------- SESSION STATE ----------------
body_key = f"body_{action}_{email_id}"
orig_key = f"orig_{action}_{email_id}"
metrics_key = f"metrics_{action}_{email_id}"

if body_key not in st.session_state:
    st.session_state[body_key] = email.get("content", "")
if orig_key not in st.session_state:
    st.session_state[orig_key] = email.get("content", "")
if metrics_key not in st.session_state:
    st.session_state[metrics_key] = {"faithfulness": None, "completeness": None}

# ---------------- UI LAYOUT ----------------
st.markdown("### 📧 Email Details")
st.markdown(f"**From:** {email.get('sender', 'Unknown Sender')}")
st.markdown(f"**Subject:** {email.get('subject', 'No Subject')}")
st.markdown("---")

st.markdown("### ✏️ Email Body")
st.text_area(label="Edit text below:", height=250, key=body_key)


# ---------------- CALLBACKS ----------------
def run_ai(action_type, tone=None):
    current = st.session_state[body_key].strip()
    if not current:
        return

    with st.spinner("Generating..."):
        if action_type == "tone":
            res = generator_bot.generate("tone", current, tone_type=tone)
        else:
            res = generator_bot.generate(action_type, current)

    if not res.startswith("Error:"):
        st.session_state[body_key] = res
        st.session_state[metrics_key] = {"faithfulness": None, "completeness": None}
    else:
        st.error(res)


def run_judge():
    original = st.session_state[orig_key].strip()
    current = st.session_state[body_key].strip()

    if not current:
        return

    if original == current:
        msg = "You haven't modified the email."
        st.session_state[metrics_key] = {"faithfulness": msg, "completeness": msg}
        st.warning(msg)
    else:
        with st.spinner("Judging Metrics..."):
            f_score = judge_bot.evaluate("faithfulness", original, current)
            c_score = judge_bot.evaluate("completeness", original, current)
            st.session_state[metrics_key] = {
                "faithfulness": f_score,
                "completeness": c_score,
            }


def reset():
    st.session_state[body_key] = st.session_state[orig_key]
    st.session_state[metrics_key] = {"faithfulness": None, "completeness": None}


# ---------------- BUTTONS SECTION ----------------
st.markdown("### ✨ Actions")

c1, c2, c3 = st.columns(3)
with c1:
    st.button(
        "⚡ Shorten", on_click=run_ai, args=("shorten",), use_container_width=True
    )
with c2:
    st.button(
        "📝 Lengthen", on_click=run_ai, args=("lengthen",), use_container_width=True
    )
with c3:
    t = st.selectbox(
        "Tone",
        ["Friendly", "Sympathetic", "Professional"],
        label_visibility="collapsed",
    )
    st.button(
        "🎭 Apply Tone", on_click=run_ai, args=("tone", t), use_container_width=True
    )

st.markdown("")

if st.button(
    "⚖️ Judge Email", on_click=run_judge, use_container_width=True, type="primary"
):
    pass

# ---------------- METRICS DISPLAY ----------------
metrics = st.session_state[metrics_key]
if metrics["faithfulness"] or metrics["completeness"]:
    st.markdown("#### ⚖️ Judge Metrics")
    m1, m2 = st.columns(2)
    with m1:
        st.info(f"{metrics['faithfulness']}")
    with m2:
        st.info(f"{metrics['completeness']}")

# ---------------- RESET SECTION ----------------
st.divider()
if st.button("🔄 Reset to Original Content", on_click=reset):
    st.toast("Restored!")