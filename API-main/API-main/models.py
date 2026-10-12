import os
from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()


def get_model(provider: str, **kwargs):
    temperature = kwargs.get("temperature", 0.7)
    model_name = kwargs.get("model_name")

    match provider:
        case "qwen":
            return ChatOllama(
                model=model_name or "qwen3.5:9b",
                temperature=temperature,
            )

        case "gemma":
            return ChatOllama(
                model=model_name or "gemma4:12b",
                temperature=temperature
            )
        
        case "deepseek":
            return ChatOpenAI(
                model=model_name or "deepseek-chat",
                temperature=temperature,
                api_key=os.getenv("DEEPSEEK_API_KEY"),
                base_url="https://api.deepseek.com",
            )

        case "gemini":
            return ChatGoogleGenerativeAI(
                model=model_name or "gemini-3.5-flash",
                temperature=temperature,
                google_api_key=os.getenv("GEMINI_API_KEY"),
            )

        case _:
            raise ValueError(f"Unknown provider: {provider}. Use ollama, deepseek, or gemini.")
