import os
import yaml
import json
import random
import re  # Added for Regex cleaning
import concurrent.futures
from dotenv import load_dotenv
from openai import AzureOpenAI
from tqdm import tqdm  # Progress bar library

load_dotenv()

# Load prompts
try:
    with open("prompts.yaml", "r", encoding="utf-8") as f:
        prompts = yaml.safe_load(f)
except FileNotFoundError:
    prompts = {}

class GenerateEmail:
    def __init__(self, deployment_name):
        self.client = AzureOpenAI(
            api_version="2024-02-01"
        )
        self.model = deployment_name

    def _call_api(self, messages):
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Error: {str(e)}"

    def get_prompt(self, action, role, **kwargs):
        template = prompts.get(action, {}).get(role)
        return template.format(**kwargs) if template else ""

    @staticmethod
    def _clean_body(text: str) -> str:
        """
        Aggressively cleans email body to remove salutations, sign-offs, 
        and placeholders like [Name].
        """
        # 1. Remove text inside brackets like [Your Name], [Date], [Insert Here]
        text = re.sub(r"\[.*?\]", "", text)
        
        # 2. Define patterns to strip
        banned_starts = (
            "subject:", "dear", "to:", "from:", "hi ", "hello ", "greetings", 
            "regards", "best regards", "sincerely", "best,", "cheers", 
            "thank you", "thanks,", "yours truly", "warm regards"
        )
        
        lines = text.splitlines()
        cleaned = []
        for line in lines:
            s_line = line.strip().lower()
            
            # Skip empty lines (optional, but keeps it tight)
            if not s_line:
                continue
                
            # If a line is short (< 10 words) and starts with a banned phrase, skip it
            if len(s_line.split()) < 10 and s_line.startswith(banned_starts):
                continue
            
            # If the line is JUST a name (sometimes models output "John Doe" at end), skip it
            # Heuristic: less than 4 words, no punctuation at end
            if len(s_line.split()) < 4 and not s_line.endswith(('.', '!', '?')):
                continue

            cleaned.append(line)
            
        result = "\n".join(cleaned).strip()
        return result if result else text

    def generate(self, action: str, selected_text: str, tone_type: str = "Professional") -> str:
        args = {"selected_text": selected_text, "tone_type": tone_type}
        user_prompt_template = self.get_prompt(action, "user", **args)
        
        if not user_prompt_template:
            return "Error: Prompt template not found."

        system_prompt = (
            "You are a professional writing assistant.\n"
            "Rules:\n"
            "- Output ONLY the rewritten paragraph content.\n"
            "- Return plain text only."
        )
        user_prompt = user_prompt_template.replace("email", "paragraph")
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        return self._clean_body(self._call_api(messages))

    def evaluate(self, metric: str, original_text: str, rewritten_text: str) -> str:
        args = {"original_text": original_text, "rewritten_text": rewritten_text}
        system_prompt = "You are an AI quality judge. Evaluate the text objectively."
        user_prompt = self.get_prompt(metric, "user", **args)
        
        if not user_prompt:
            return "Error: Metric prompt not found."

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        return self._call_api(messages)

    def synthesize_data(self, topic, persona, tone, length, id_num):
        """Generates a synthetic email in JSON format."""
        args = {
            "topic": topic,
            "persona": persona,
            "tone": tone,
            "length": length,
            "id_num": id_num
        }
        user_prompt = self.get_prompt("data_synthesis", "user", **args)
        
        if not user_prompt:
            return '{"error": "Prompt data_synthesis not found in yaml"}'

        messages = [
            {"role": "system", "content": "You are a data generator. Output valid JSON only. Do not use Markdown formatting."},
            {"role": "user", "content": user_prompt},
        ]
        return self._call_api(messages)


# ==========================================
#  DATA GENERATION SCRIPT
# ==========================================
if __name__ == "__main__":
    print("Initializing Data Generator...")
    generator = GenerateEmail(deployment_name=os.getenv("GENERATOR_DEPLOYMENT", "gpt-4o-mini"))

    # --- INGREDIENTS ---
    personas = [
        "a strict project manager", "an enthusiastic intern", "a confused client",
        "an apologetic support agent", "a busy executive", "a meticulous accountant",
        "a creative marketing lead", "a frustrated engineer", "a polite HR rep"
    ]
    tones = [
        "urgent", "professional", "casual", "sympathetic", "angry", 
        "encouraging", "neutral", "inquisitive", "formal"
    ]
    topics = [
        "rescheduling a meeting", "asking for a raise", "reporting a bug", 
        "product launch", "requesting PTO", "declining job offer", 
        "complaining about service", "thanking a colleague", "project delay", 
        "budget approval", "resignation", "welcoming new hire", "feedback request",
        "clarifying requirements", "downtime notification", "promotion congrats",
        "reference request", "invoice follow-up", "partnership proposal", 
        "contract termination", "policy change", "security incident", "tech support",
        "interview schedule", "remote work request", "noise complaint", 
        "team building", "mentorship request", "recommendation", "billing dispute",
        "benefits inquiry", "harassment report", "layoff announcement"
    ]
    lengths = ["very short (5-10 words)", "short (1-2 sentences)", 
               "medium (3-4 sentences)", "long (5-6 sentences)", "very long (100+ words)"]

    # Fake User Data for "Sender"
    first_names = ["alex", "jordan", "taylor", "morgan", "casey", "riley", "quinn", "avery", "jamie"]
    last_names = ["smith", "jones", "williams", "brown", "miller", "davis", "garcia", "rodriguez"]
    domains = ["gmail.com", "outlook.com", "yahoo.com", "corp.net", "tech.io"]

    def get_random_sender():
        return f"{random.choice(first_names)}.{random.choice(last_names)}@{random.choice(domains)}"

    def process_single_email(i, filename):
        """Helper function for a single thread work unit."""
        topic = random.choice(topics)
        persona = random.choice(personas)
        tone = random.choice(tones)
        
        if "short" in filename: 
            length = "long (80-100 words)"
        elif "long" in filename:
            length = "very short (10-20 words)"
        else:
            length = random.choice(lengths)

        # 1. Call LLM
        result = generator.synthesize_data(topic, persona, tone, length, i)
        
        # 2. Strip Markdown
        clean_json = result.replace("```json", "").replace("```", "").strip()
        
        try:
            data = json.loads(clean_json)
            
            # 3. Inject Random Sender
            data["sender"] = get_random_sender()
            
            # 4. Clean the Content
            if "content" in data:
                data["content"] = generator._clean_body(data["content"])
            
            # 5. Ensure ID match
            data["id"] = i
            
            return json.dumps(data)
        except json.JSONDecodeError:
            return None

    def generate_file(filename, count):
        print(f"\n--- Generating {filename} ---")
        
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(process_single_email, i, filename) for i in range(1, count + 1)]
            
            for future in tqdm(concurrent.futures.as_completed(futures), total=count, desc="Progress", unit="email"):
                res = future.result()
                if res:
                    results.append(res)
        
        with open(filename, "w", encoding="utf-8") as f:
            for line in results:
                f.write(line + "\n")

    # --- EXECUTE ---
    # Generating 10 emails per file (Adjust as needed)
    generate_file("short.jsonl", 25)
    generate_file("long.jsonl", 25)
    generate_file("toned.jsonl", 25)
    print("\n✅ All files generated, cleaned, and updated with sender info!")