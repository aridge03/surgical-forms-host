import streamlit as st
from openai import AzureOpenAI

class OpenAIClient:
    def __init__(self):
        self.client = AzureOpenAI(
            api_key=st.secrets["AZURE_OPENAI_API_KEY"],
            azure_endpoint=st.secrets["AZURE_OPENAI_ENDPOINT"],
            api_version=st.secrets["AZURE_OPENAI_VERSION"]
        )

    def chat_completion(self, messages, model=None):
        model = model or st.secrets["AZURE_OPENAI_DEPLOYMENT"]
        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
        )
        return response.choices[0].message.content
