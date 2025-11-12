import os
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()


class OpenAIClient:
    def __init__(self):
        self.client = AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_version=os.getenv("AZURE_OPENAI_VERSION")
    )

    def chat_completion(self, messages, model=os.getenv("AZURE_OPENAI_DEPLOYMENT")):
        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
        )
        return response.choices[0].message.content