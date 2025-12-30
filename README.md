# Email Helper Bot 📧
A streamlined AI-powered application designed to assist professionals in rewriting, optimizing, and evaluating emails. This tool allows users to shorten, lengthen, or change the tone of emails and provides a robust AI Evaluation System to score the results.

🚀 Key Features
AI Rewrite Actions: Instantly shorten, lengthen, or apply specific tones (Professional, Diplomatic, Witty, etc.) to your drafts.

Dynamic Data Generation: A built-in generator (generate.py) that creates synthetic datasets:

Mixed Mails: Randomized email scenarios to test general performance.

Challenge Mails: Specialized datasets to test for specific defects (e.g., preserving URLs).

AI Judge & Metrics: A sophisticated evaluation engine that scores your rewritten emails on 6 key metrics:

Faithfulness: Does it keep the original meaning?

Completeness: Are key details preserved?

Robustness: Is the structure logical and error-free?

Professionalism: Is the tone appropriate for business?

URL Preservation (Enterprise Defect): Checks if links are broken or missing.

Scope Accuracy (Enterprise Defect): Checks if the AI rewrote only the intended scope without hallucinations.

Dual Workspace: Switch between working on pre-set "Original Datasets" and your own dynamically "Generated Mails".

🛠️ Installation & Setup
1. Clone the Repository
Bash

git clone <your-repo-url>
cd Email-Helper-Bot
2. Create a Virtual Environment
Windows:

Bash

python -m venv venv
venv\Scripts\Activate.ps1
macOS/Linux:

Bash

python3 -m venv venv
source venv/bin/activate
3. Install Dependencies
Bash

pip install -r requirements.txt
4. Configure Environment
Ensure you have a .env file in the root directory with your Azure OpenAI credentials:

Code snippet

GENERATOR_DEPLOYMENT=gpt-4o-mini
JUDGE_DEPLOYMENT=gpt-4.1
AZURE_OPENAI_API_KEY=your_key_here
AZURE_OPENAI_ENDPOINT=your_endpoint_here
🚦 Usage Guide
Step 1: Generate Fresh Data
To create new batches of "Mixed Mails" and "Challenge Mails" for testing:

Bash

python generate.py
This creates/updates datasets/mixed.jsonl and datasets/challenge.jsonl.

Step 2: Run the App
Bash

streamlit run app.py
Step 3: Using the Interface
Select Source (Sidebar):

Original Datasets: Choose specific task-based files (Short Mails, Long Mails, Tone Mails).

Generated Mails: Select "Mixed Mails" for general testing or "⚠️ Challenge (URLs)" to test specific defect scenarios.

Select an Email: Pick an ID from the dropdown to load an email.

Edit & Rewrite: Use the text area to make changes, or click the Action Buttons (⚡ Shorten, 📝 Lengthen, 🎭 Apply Tone) to let AI do the work.

Judge: Click ⚖️ Judge Email to run the 6-metric evaluation.

Look for the Enterprise Challenge Metrics section to see if your model passed the defect checks (URL Preservation & Scope Accuracy).

🏆 Enterprise Challenge Scenarios
This project explicitly addresses real-world enterprise defects:

Scenario 1: URL Preservation

Problem: Language models often strip or break URLs when rewriting text.

Solution: The challenge.jsonl dataset generates emails with specific URLs. The URL Preservation metric strictly checks if every link in the original text exists in the rewrite.

Scenario 2: Scope Accuracy

Problem: "Scope Creep" occurs when a model hallucinates new topics or rewrites the entire email when only a specific section was targeted.

Solution: The Scope Accuracy metric evaluates if the rewrite stays within the logical boundaries of the original request.

📂 Project Structure
app.py: Main Streamlit application containing the UI and logic.

generate.py: Script to generate synthetic email datasets using Azure OpenAI.

prompts.yaml: Configuration file containing system prompts for generation and evaluation metrics.

datasets/: Directory storing .jsonl data files (Originals, Mixed, and Challenge).