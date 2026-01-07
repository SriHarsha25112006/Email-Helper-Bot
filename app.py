import streamlit as st
import json
import os
import glob
import concurrent.futures
from dotenv import load_dotenv
from generate import GenerateEmail

load_dotenv()

st.set_page_config(page_title="Email Helper App", page_icon="📧", layout="wide")

generator_bot = GenerateEmail(
    deployment_name=os.getenv("GENERATOR_DEPLOYMENT", "gpt-4o-mini")
)
judge_bot = GenerateEmail(deployment_name=os.getenv("JUDGE_DEPLOYMENT", "gpt-4.1"))

DATASET_DIR = "datasets"

# --- HELPER FUNCTIONS ---
@st.cache_data
def load_single_jsonl(file_name):
    path = os.path.join(DATASET_DIR, file_name)
    data = []
    
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    data.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return data

def get_emails_dict(file_name):
    raw_data = load_single_jsonl(file_name)
    emails = {}
    for idx, item in enumerate(raw_data):
        new_id = idx + 1
        item["id"] = new_id
        emails[new_id] = item
    return {"emails": emails, "ids": list(emails.keys())}

# ---------------- SIDEBAR CONFIGURATION ----------------
st.sidebar.title("Configuration")

source_category = st.sidebar.selectbox(
    "Select Source",
    ["Original Datasets", "Generated Mails"]
)

selected_filename = None

if source_category == "Original Datasets":
    st.sidebar.markdown("### 📂 Original Files")
    file_map = {
        "Short Mails": "shorten.jsonl",
        "Long Mails": "lengthen.jsonl",
        "Tone Mails": "tone.jsonl"
    }
    friendly_name = st.sidebar.selectbox("Select File", list(file_map.keys()))
    selected_filename = file_map[friendly_name]

elif source_category == "Generated Mails":
    st.sidebar.markdown("### 🤖 Generated Mails")
    
    all_files = glob.glob(os.path.join(DATASET_DIR, "*.jsonl"))
    all_filenames = [os.path.basename(f) for f in all_files]
    
    # Logic to filter out the original static files
    excluded_files = [
        "shorten.jsonl", "lengthen.jsonl", "tone.jsonl", 
        "short.jsonl", "long.jsonl", "toned.jsonl"
    ]
    
    raw_generated_files = [f for f in all_filenames if f not in excluded_files]

    # Explicitly ensure our 3 key generated files are in the list if they exist on disk
    for req_file in ["mixed.jsonl", "challenge.jsonl", "adversarial.jsonl"]:
        if req_file in all_filenames and req_file not in raw_generated_files:
            raw_generated_files.append(req_file)

    if not raw_generated_files:
        st.sidebar.warning("No generated files found. Run generate.py.")
    else:
        # Define a formatting function to make filenames look professional in the dropdown
        def format_filename(filename):
            mapping = {
                "mixed.jsonl": "Mixed Mails (General)",
                "challenge.jsonl": "Challenge Mails (URLs)",
                "adversarial.jsonl": "Adversarial Mails (Edge Cases)"
            }
            return mapping.get(filename, filename)

        selected_filename = st.sidebar.selectbox(
            "Select File", 
            raw_generated_files, 
            format_func=format_filename
        )

# ---------------- LOAD CONTENT ----------------
if selected_filename:
    dataset_info = get_emails_dict(selected_filename)
    email_ids = dataset_info["ids"]

    if not email_ids:
        st.error(f"Error: No data found in '{selected_filename}'. Please check the file.")
        st.stop()

    email_id = st.sidebar.selectbox("Select Email ID", email_ids)
    email = dataset_info["emails"][email_id]
else:
    st.info("👈 Please select a file to begin.")
    st.stop()

# ---------------- STATE MANAGEMENT ----------------
state_id = f"{selected_filename}_{email_id}"
body_key = f"body_{state_id}"
orig_key = f"orig_{state_id}"
metrics_key = f"metrics_{state_id}"

# Expanded metrics structure (5 metrics)
default_metrics = {
    "faithfulness": None, 
    "completeness": None, 
    "robustness": None, 
    "url_preservation": None,
    "edge_case_scan": None
}

if body_key not in st.session_state:
    st.session_state[body_key] = email.get("content", "")
if orig_key not in st.session_state:
    st.session_state[orig_key] = email.get("content", "")
if metrics_key not in st.session_state:
    st.session_state[metrics_key] = default_metrics.copy()

# ---------------- MAIN UI ----------------
st.markdown(f"### 📧 Email Details")
st.caption(f"File: {selected_filename}")
st.markdown(f"**From:** {email.get('sender', 'Unknown Sender')}")
st.markdown(f"**Subject:** {email.get('subject', 'No Subject')}")
st.markdown("---")

st.markdown("### ✏️ Email Body")
st.text_area(label="Edit text below:", height=250, key=body_key)

# ---------------- LOGIC HANDLERS ----------------
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
        st.session_state[metrics_key] = default_metrics.copy()
    else:
        st.error(res)

def run_judge():
    original = st.session_state[orig_key].strip()
    current = st.session_state[body_key].strip()

    if not current:
        return

    if original == current:
        st.warning("You haven't modified the email.")
        return

    # UPDATED METRICS LIST (5 Core Metrics)
    metric_names = [
        "faithfulness", "completeness", "robustness", 
        "url_preservation", "edge_case_scan"
    ]
    results = {}

    with st.spinner("Judging Metrics (Running Evaluators)..."):
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_metric = {
                executor.submit(judge_bot.evaluate, m, original, current): m 
                for m in metric_names
            }
            
            for future in concurrent.futures.as_completed(future_to_metric):
                metric_name = future_to_metric[future]
                results[metric_name] = future.result()

    st.session_state[metrics_key] = results

def reset():
    st.session_state[body_key] = st.session_state[orig_key]
    st.session_state[metrics_key] = default_metrics.copy()

# ---------------- ACTION BUTTONS ----------------
st.markdown("### ✨ Actions")

c1, c2, c3 = st.columns(3)
with c1:
    st.button("⚡ Shorten", on_click=run_ai, args=("shorten",), use_container_width=True)
with c2:
    st.button("📝 Lengthen", on_click=run_ai, args=("lengthen",), use_container_width=True)
with c3:
    t = st.selectbox("Tone", ["Friendly", "Sympathetic", "Professional", "Diplomatic", "Witty"], label_visibility="collapsed")
    st.button("🎭 Apply Tone", on_click=run_ai, args=("tone", t), use_container_width=True)

st.markdown("")

if st.button("⚖️ Judge Email", on_click=run_judge, use_container_width=True, type="primary"):
    pass

# ---------------- METRICS DISPLAY ----------------
metrics = st.session_state[metrics_key]

if any(metrics.values()):
    st.markdown("#### ⚖️ General Metrics")
    m1, m2, m3 = st.columns(3)
    with m1: st.info(f"**Faithfulness**\n\n{metrics['faithfulness']}")
    with m2: st.info(f"**Completeness**\n\n{metrics['completeness']}")
    with m3: st.info(f"**Robustness**\n\n{metrics['robustness']}")
    
    st.markdown("#### 🚀 Enterprise Challenge Metrics")
    m4, m5 = st.columns(2)
    with m4: st.error(f"**URL Preservation**\n\n{metrics['url_preservation']}")
    with m5: st.warning(f"**Edge Case Stability**\n\n{metrics['edge_case_scan']}")

st.divider()
if st.button("🔄 Reset to Original Content", on_click=reset):
    st.toast("Restored!")