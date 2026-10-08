from openai import OpenAI
from.config import settings

class GrokService:
    """
    Uses Groq API with openai/gpt-oss-20b
    Keeps class name GrokService so rag_service.py doesn't break
    """
    def __init__(self) -> None:
        settings.validate()
        self.client = OpenAI(
            api_key=settings.groq_api_key,
            base_url="https://api.groq.com/openai/v1",
        )

    def generate(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=settings.groq_model, # openai/gpt-oss-20b
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        return response.choices[0].message.content

    def generate_answer(self, question: str, context: str) -> str:
        # kept for backward compatibility
        from.prompt_service import PromptService
        prompt = PromptService.build_prompt(question, context, "zero_shot")
        return self.generate(prompt)
