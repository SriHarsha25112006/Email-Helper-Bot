import os
import yaml
from dotenv import load_dotenv
from openai import AzureOpenAI

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
                temperature=0.7,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Error: {str(e)}"

    def get_prompt(self, action, role, **kwargs):
        template = prompts.get(action, {}).get(role)
        return template.format(**kwargs) if template else ""

    @staticmethod
    def _clean_body(text: str) -> str:
        banned_starts = ("subject:", "dear", "regards:", "sincerely,", "best,")
        lines = text.splitlines()
        cleaned = []
        for line in lines:
            low_line = line.lower().strip()
            if len(low_line.split()) < 4 and low_line.startswith(banned_starts):
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