import os
import yaml
from dotenv import load_dotenv
from openai import AzureOpenAI # Using specialized Azure client

# Load keys from .env
load_dotenv()

# Load prompts from YAML
try:
    with open("prompts.yaml", "r", encoding="utf-8") as f:
        prompts = yaml.safe_load(f)
except FileNotFoundError:
    prompts = {}

class GenerateEmail:
    def __init__(self, model: str):
        # Initialize client with variables from .env
        self.client = AzureOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_KEY"),
            api_version="2024-02-01" 
        )
        self.model = model

    def _call_api(self, messages):
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7, # Higher temperature allows for creative lengthening
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
        Removes subject lines and standalone greetings/signatures.
        """
        banned_starts = ("subject:", "dear", "regards:", "sincerely,", "best,")
        lines = text.splitlines()
        cleaned = []
        
        for line in lines:
            low_line = line.lower().strip()
            # Only remove the line if it starts with a banned word and is short
            if len(low_line.split()) < 4 and low_line.startswith(banned_starts):
                continue
            cleaned.append(line)

        result = "\n".join(cleaned).strip()
        return result if result else text

    def generate(self, action: str, selected_text: str, tone_type: str = "Professional") -> str:
        args = {
            "selected_text": selected_text,
            "tone_type": tone_type,
        }

        # Hard guardrails to prevent conversational filler
        system_prompt = (
            "You are a professional writing assistant.\n"
            "Rules:\n"
            "- Output ONLY the rewritten paragraph content.\n"
            "- Do NOT include subject lines, greetings, or signatures.\n"
            "- Do NOT provide explanations or conversational filler.\n"
            "- Return plain text only."
        )

        # Focus the model on content by avoiding the word 'email'
        user_prompt = (
            self.get_prompt(action, "user", **args)
            .replace("email", "paragraph")
            .replace("Email", "paragraph")
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        raw_output = self._call_api(messages)
        return self._clean_body(raw_output)