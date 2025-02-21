import os
from typing import Union

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_ollama import OllamaLLM

from ..config import Config


def get_llm() -> Union[OllamaLLM, ChatGoogleGenerativeAI, ChatGroq]:
    """Get the configured LLM provider instance.

    Returns:
        A language model instance based on the configured provider.

    Raises:
        ValueError: If the configured model provider is unknown.
    """
    if Config.MODEL_PROVIDER == "ollama":
        return OllamaLLM(
            base_url=f"https://{os.environ.get('OLLAMA_HOST')}", model="mistral:7b"
        )
    elif Config.MODEL_PROVIDER == "gemini":
        return ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=os.environ.get("GOOGLE_API_KEY"),
            temperature=0,
        )
    elif Config.MODEL_PROVIDER == "groq":
        return ChatGroq(
            model_name="qwen-2.5-32b",  # "deepseek-r1-distill-qwen-32b",
            groq_api_key=os.environ.get("GROQ_API_KEY"),
            temperature=0,
        )
    else:
        raise ValueError(f"Unknown model provider: {Config.MODEL_PROVIDER}")
