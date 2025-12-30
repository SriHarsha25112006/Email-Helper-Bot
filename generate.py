import os
import yaml
import json
import random
import re
import concurrent.futures
from dotenv import load_dotenv
from openai import AzureOpenAI
from tqdm import tqdm

load_dotenv()

DATASET_DIR = "datasets"
os.makedirs(DATASET_DIR, exist_ok=True)

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
        text = re.sub(r"\[.*?\]", "", text)
        banned_starts = (
            "subject:", "dear", "to:", "from:", "hi ", "hello ", "greetings", 
            "regards", "best regards", "sincerely", "best,", "cheers", 
            "thank you", "thanks,", "yours truly", "warm regards"
        )
        lines = text.splitlines()
        cleaned = []
        for line in lines:
            s_line = line.strip().lower()
            if not s_line: continue
            if len(s_line.split()) < 10 and s_line.startswith(banned_starts): continue
            if len(s_line.split()) < 4 and not s_line.endswith(('.', '!', '?')): continue
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
            return f"Error: Metric prompt for '{metric}' not found."

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        return self._call_api(messages)

    def synthesize_data(self, topic, persona, tone, length, id_num, is_challenge=False):
        prompt_key = "challenge_synthesis" if is_challenge else "data_synthesis"
        
        args = {
            "topic": topic, "persona": persona, "tone": tone, 
            "length": length, "id_num": id_num
        }
        user_prompt = self.get_prompt(prompt_key, "user", **args)
        
        if not user_prompt:
            return f'{{"error": "Prompt {prompt_key} not found in yaml"}}'

        messages = [
            {"role": "system", "content": "You are a data generator. Output valid JSON only. Do not use Markdown formatting."},
            {"role": "user", "content": user_prompt},
        ]
        return self._call_api(messages)

if __name__ == "__main__":
    print("Initializing Data Generator...")
    generator = GenerateEmail(deployment_name=os.getenv("GENERATOR_DEPLOYMENT", "gpt-4o-mini"))

    personas = ["strict project manager", "enthusiastic intern", "confused client", "apologetic support agent"]
    tones = ["urgent", "professional", "casual", "sympathetic", "angry", "diplomatic", "witty"]
    topics = ["rescheduling a meeting", "asking for a raise", "reporting a bug", "product launch"]
    lengths = ["very short (5-10 words)", "short (1-2 sentences)", "medium (3-4 sentences)", "long (5-6 sentences)"]

    first_names = ["alex", "jordan", "taylor", "morgan"]
    last_names = ["smith", "jones", "williams", "brown"]
    domains = ["gmail.com", "corp.net", "tech.io"]

    def get_random_sender():
        return f"{random.choice(first_names)}.{random.choice(last_names)}@{random.choice(domains)}"

    def process_single_email(i, filename):
        topic = random.choice(topics)
        persona = random.choice(personas)
        tone = random.choice(tones)
        length = random.choice(lengths)
        is_challenge = (filename == "challenge.jsonl")

        result = generator.synthesize_data(topic, persona, tone, length, i, is_challenge=is_challenge)
        clean_json = result.replace("```json", "").replace("```", "").strip()
        
        try:
            data = json.loads(clean_json)
            data["sender"] = get_random_sender()
            if "content" in data:
                data["content"] = generator._clean_body(data["content"])
            data["id"] = i
            return json.dumps(data)
        except json.JSONDecodeError:
            return None

    def generate_file(filename, count):
        print(f"\n--- Generating {filename} ---")
        filepath = os.path.join(DATASET_DIR, filename) 
        
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(process_single_email, i, filename) for i in range(1, count + 1)]
            for future in tqdm(concurrent.futures.as_completed(futures), total=count):
                res = future.result()
                if res: results.append(res)
        
        with open(filepath, "w", encoding="utf-8") as f:
            for line in results:
                f.write(line + "\n")
        print(f"Saved to {filepath}")

    generate_file("mixed.jsonl", 50)
    generate_file("challenge.jsonl", 50)
    
    print("\n✅ Mixed & Challenge files generated in 'datasets/' folder!")