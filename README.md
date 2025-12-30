# Email Helper Bot 📧

A streamlined AI-powered application designed to assist professionals in rewriting, optimizing, and evaluating emails. This tool allows users to shorten, lengthen, or change the tone of emails and provides a robust **AI Evaluation System** to score the results.

## 🚀 Key Features

* **AI Rewrite Actions**: Instantly shorten, lengthen, or apply specific tones (Professional, Diplomatic, Witty, etc.) to your drafts.
* **Dynamic Data Generation**: A built-in generator (`generate.py`) that creates synthetic "Mixed Mail" datasets to test the app with fresh, random email scenarios.
* **AI Judge & Metrics**: A sophisticated evaluation engine that scores your rewritten emails on four key metrics:
    * **Faithfulness**: Does it keep the original meaning?
    * **Completeness**: are key details preserved?
    * **Robustness**: Is the structure logical and error-free?
    * **Professionalism**: Is the tone appropriate for business?
* **Dual Workspace**: Switch between working on pre-set "Original Datasets" and your own dynamically "Generated Mails".

---

## 🛠️ Installation & Setup

### 1. Clone the Repository
```bash
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
Step 1: Generate Fresh Data (Optional)
To create a new batch of random "Mixed Mails" for testing:

Bash

python generate.py
This creates/updates datasets/mixed.jsonl with diverse email scenarios.

Step 2: Run the App
Bash

streamlit run app.py
Step 3: Using the Interface
Select Source (Sidebar):

Original Datasets: Choose specific task-based files (Short Mails, Long Mails, Tone Mails).

Generated Mails: Select "Mixed Mails" to access the randomized dataset you generated in Step 1.

Select an Email: Pick an ID from the dropdown to load an email.

Edit & Rewrite: Use the text area to make changes, or click the Action Buttons (⚡ Shorten, 📝 Lengthen, 🎭 Apply Tone) to let AI do the work.

Judge: Click ⚖️ Judge Email to run the 4-metric evaluation and see your scores.

📂 Project Structure
app.py: Main Streamlit application containing the UI and logic.

generate.py: Script to generate synthetic email datasets using Azure OpenAI.

prompts.yaml: Configuration file containing system prompts for generation and evaluation metrics.

datasets/: Directory storing .jsonl data files (both original and generated).