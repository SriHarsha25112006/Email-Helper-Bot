from openai import OpenAI
import yaml

# Load prompts
with open("prompts.yaml", "r", encoding="utf-8") as f:
    prompts = yaml.safe_load(f)


class GenerateEmail:
    def __init__(self, model: str):
        self.client = OpenAI(
            base_url="http://localhost:11434/v1",
            api_key="ollama",  # placeholder
        )
        self.model = model

    def _call_api(self, messages):
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.4,  # lower = stricter outputs
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print("API Error:", e)
            return "Error: Failed to generate response."

    def get_prompt(self, action, role, **kwargs):
        template = prompts.get(action, {}).get(role)
        if not template:
            return ""
        return template.format(**kwargs)

    @staticmethod
    def _clean_body(text: str) -> str:
        """
        Safety net: removes greetings, subjects, and signatures
        """
        banned_starts = (
            "hi", "hello", "dear", "subject:",
            "regards", "thanks", "sincerely", "best"
        )

        lines = text.splitlines()
        cleaned = [
            line for line in lines
            if not line.lower().strip().startswith(banned_starts)
        ]

        return "\n".join(cleaned).strip()

    def generate(self, action: str, selected_text: str, tone_type: str = "Professional") -> str:
        args = {
            "selected_text": selected_text,
            "tone_type": tone_type,
        }

        # 🔒 HARD SYSTEM RULES (Gemma-friendly)
        system_prompt = (
            "You are rewriting a SINGLE TEXT PARAGRAPH.\n"
            "Rules:\n"
            "- Output ONLY the rewritten paragraph\n"
            "- Do NOT add a subject line\n"
            "- Do NOT add greetings or salutations\n"
            "- Do NOT add signatures or sign-offs\n"
            "- Do NOT add explanations\n"
            "- Return plain text only\n"
        )

        # ⚠️ Never use the word 'email' with small models
        user_prompt = (
            self.get_prompt(action, "user", **args)
            .replace("email", "paragraph")
            .replace("Email", "paragraph")
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        result = self._call_api(messages)
        return self._clean_body(result)
