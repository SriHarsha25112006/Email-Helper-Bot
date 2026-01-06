# 📧 Email Helper Bot

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)](https://streamlit.io)
[![Azure OpenAI](https://img.shields.io/badge/Azure%20OpenAI-0078D4?style=for-the-badge&logo=microsoftazure&logoColor=white)](https://azure.microsoft.com)
[![Status](https://img.shields.io/badge/Status-Active-success?style=for-the-badge)]()

**A streamlined AI-powered workbench for professionals to rewrite, optimize, and evaluate emails.** This tool goes beyond simple text generation. It features a **Dual Workspace** for testing against both static and dynamically generated datasets, and includes a rigorous **AI Evaluation System** to score quality and detect enterprise-level defects.

---

## 📖 Table of Contents
- [🚀 Key Features](#-key-features)
- [🧠 AI Judge & Metrics](#-ai-judge--metrics)
- [🏆 Enterprise Challenge Scenarios](#-enterprise-challenge-scenarios)
- [🛠️ Installation & Setup](#-installation--setup)
- [🚦 Usage Guide](#-usage-guide)
- [📂 Project Structure](#-project-structure)

---

## 🚀 Key Features

| Feature | Description |
| :--- | :--- |
| **⚡ AI Rewrite Actions** | Instantly **Shorten**, **Lengthen**, or apply specific **Tones** (Professional, Diplomatic, Witty) to your drafts. |
| **🎲 Dynamic Data Engine** | Built-in synthetic data generator (`generate.py`) that creates fresh test cases on demand. |
| **🧪 Dual Workspace** | Switch seamlessly between pre-set **"Original Datasets"** and your own dynamically **"Generated Mails"**. |
| **⚖️ Robust Evaluation** | A sophisticated evaluation engine that scores your rewritten emails on **6 key metrics**. |

### The Data Engine
The generator creates two types of dynamic datasets:
* **Mixed Mails:** Randomized email scenarios to test general performance.
* **Challenge Mails:** Specialized datasets designed to break the model (e.g., testing for URL preservation).

---

## 🧠 AI Judge & Metrics

We don't just guess if the email is good; we measure it. The AI Judge scores every rewrite on a **1-5 scale** across these dimensions:

### 📊 General Quality
* **Faithfulness:** Does it keep the original meaning?
* **Completeness:** Are key details preserved?
* **Robustness:** Is the structure logical and error-free?

### 🛡️ Enterprise Defect Detection
* **URL Preservation:** *Strict Check.* Did the AI break or strip any links?
* **Edge Case Stability:** *Logic Check.* Did the AI rewrite only the intended scope without logic breaks?

---

## 🏆 Enterprise Challenge Scenarios

This project explicitly addresses real-world defects often found in LLM applications:

> **🚩 Scenario 1: The Broken Link**
> * **Problem:** Language models often strip or break URLs when rewriting text.
> * **Solution:** The `challenge.jsonl` dataset generates emails with specific URLs. The **URL Preservation** metric strictly checks if every link in the original text exists in the rewrite.

> **🚩 Scenario 2: Scope Creep**
> * **Problem:** Models often hallucinate new topics or rewrite an entire email when only a specific section was targeted.
> * **Solution:** The **Edge Case Stability** metric evaluates if the rewrite stays within the logical boundaries of the original request.

> **🚩 Scenario 3: The Confused Comedian**
> * **Problem:** Models asked to be "Witty" often copy user typos and "um/uh" fillers.
> * **Solution:** Strict prompts enforce **Clarity First**, ensuring wit is polished, not sloppy.

---

## 🛠️ Installation & Setup

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd Email-Helper-Bot
### 2. Create a Virtual Environment
Windows:

PowerShell

python -m venv venv
venv\Scripts\Activate.ps1
macOS/Linux:

Bash

python3 -m venv venv
source venv/bin/activate
### 3. Install Dependencies
Bash

pip install -r requirements.txt
### 4. Configure Environment
Create a .env file in the root directory with your Azure credentials:

Ini, TOML

GENERATOR_DEPLOYMENT=gpt-4o-mini
JUDGE_DEPLOYMENT=gpt-4.1
AZURE_OPENAI_API_KEY=your_key_here
AZURE_OPENAI_ENDPOINT=your_endpoint_here
### 🚦 Usage Guide
## Step 1: Generate Fresh Data 🎲
Before running the app, generate your synthetic test data.

Bash

python generate.py
Output: Updates datasets/mixed.jsonl and datasets/challenge.jsonl with fresh scenarios.

## Step 2: Run the App 🏃‍♂️
Bash

streamlit run app.py
## Step 3: Using the Interface 🖥️
1. Select Source (Sidebar):

Original Datasets: Specific task-based files (Short/Long/Tone Mails).

Generated Mails: Select "Mixed Mails" for general testing, "Challenge (URLs)" for defect testing, or "Adversarial" for robust testing.

2. Select an Email: Pick an ID to load content.

3. Edit & Rewrite: Use the Action Buttons (⚡ Shorten, 📝 Lengthen, 🎭 Apply Tone).

4. Judge: Click ⚖️ Judge Email to run the 5-metric evaluation.

### 📂 Project Structure

Email-Helper-Bot/
├── 📂 datasets/          # Stores .jsonl data files
├── 🐍 app.py             # Main Streamlit application UI and logic
├── 🐍 generate.py        # Script to generate synthetic datasets via Azure OpenAI
├── 🐍 batch_runner.py    # Script to run comprehensive automated tests
├── ⚙️ prompts.yaml       # System prompts for generation and evaluation metrics
├── 📄 requirements.txt   # Project dependencies
├── 📄 .env               # API keys (not committed)
└── 📄 README.md          # Documentation