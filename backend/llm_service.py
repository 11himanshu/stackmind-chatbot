import os
import requests
import re
from typing import List, Dict
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file in backend directory
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# Choose your LLM provider by setting environment variable
# Options: "groq", "huggingface", "together", "gemini", "ollama"
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")

# System prompt for clean, conversational responses
# System prompt for clean, conversational responses
SYSTEM_PROMPT = """You are Himanshu’s Bot.If someone asks who built or owns you, reply:
"I was built by Himanshu, followed by a playful, respectful title.
You are helpful, smart, and mildly sarcastic in a friendly way.
Answers must be correct first, funny second.
Sound like a real person who enjoys explaining things.
No markdown or formatting symbols.
Keep responses short, clear, and entertaining."""


def preprocess_response(text: str) -> str:
    """
    Clean and preprocess LLM response to remove markdown and formatting
    """
    if not text:
        return text
    
    # Remove markdown bold (**text** or __text__)
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'__(.*?)__', r'\1', text)
    
    # Remove markdown italic (*text* or _text_)
    text = re.sub(r'(?<!\*)\*(?!\*)([^*]+?)(?<!\*)\*(?!\*)', r'\1', text)
    text = re.sub(r'(?<!_)_(?!_)([^_]+?)(?<!_)_(?!_)', r'\1', text)
    
    # Remove markdown code blocks (```code```)
    text = re.sub(r'```[\s\S]*?```', '', text)
    
    # Remove inline code (`code`)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    
    # Remove markdown headers (# Header)
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    
    # Remove markdown links [text](url)
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    
    # Remove markdown lists (- item or * item)
    text = re.sub(r'^[\s]*[-*+]\s+', '', text, flags=re.MULTILINE)
    
    # Remove markdown numbered lists
    text = re.sub(r'^\d+\.\s+', '', text, flags=re.MULTILINE)
    
    # Clean up extra whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    return text


def call_groq_api(message: str, conversation_history: List[Dict]) -> str:
    """Call Groq API (Fast & Free) with prompt engineering"""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return "Error: GROQ_API_KEY not set in environment variables"
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Format conversation history with system prompt
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    # Add conversation history (last 10 messages for context)
    for msg in conversation_history[-10:]:
        messages.append({
            "role": msg["role"],
            "content": msg["message"]
        })
    
    # Add current user message
    messages.append({"role": "user", "content": message})
    
    data = {
        "model": "llama-3.1-8b-instant",  # or "mixtral-8x7b-32768"
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 1024
    }
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=10)
        response.raise_for_status()
        raw_response = response.json()["choices"][0]["message"]["content"]
        # Preprocess to remove markdown
        return preprocess_response(raw_response)
    except Exception as e:
        return f"Error calling Groq API: {str(e)}"


def call_huggingface_api(message: str, conversation_history: List[Dict]) -> str:
    """Call Hugging Face Inference API (Free) with prompt engineering"""
    api_key = os.getenv("HUGGINGFACE_API_KEY")
    if not api_key:
        return "Error: HUGGINGFACE_API_KEY not set"
    
    url = "https://api-inference.huggingface.co/models/meta-llama/Llama-3.2-3B-Instruct"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Build prompt with system instructions
    prompt = f"{SYSTEM_PROMPT}\n\n"
    
    # Add conversation context
    if len(conversation_history) >= 2:
        last_exchange = conversation_history[-2:]
        prompt += f"Previous conversation:\nUser: {last_exchange[0]['message']}\nAssistant: {last_exchange[1]['message']}\n\n"
    
    prompt += f"User: {message}\nAssistant:"
    
    data = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 512,
            "temperature": 0.7,
            "return_full_text": False
        }
    }
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=30)
        response.raise_for_status()
        result = response.json()
        if isinstance(result, list) and len(result) > 0:
            raw_response = result[0].get("generated_text", "").strip()
        else:
            raw_response = str(result)
        
        # Preprocess to remove markdown
        return preprocess_response(raw_response)
    except Exception as e:
        return f"Error calling Hugging Face API: {str(e)}"


def call_together_api(message: str, conversation_history: List[Dict]) -> str:
    """Call Together AI API with prompt engineering"""
    api_key = os.getenv("TOGETHER_API_KEY")
    if not api_key:
        return "Error: TOGETHER_API_KEY not set"
    
    url = "https://api.together.xyz/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Format conversation history with system prompt
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    for msg in conversation_history[-10:]:
        messages.append({
            "role": msg["role"],
            "content": msg["message"]
        })
    messages.append({"role": "user", "content": message})
    
    data = {
        "model": "meta-llama/Llama-3-8b-chat-hf",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 1024
    }
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=10)
        response.raise_for_status()
        raw_response = response.json()["choices"][0]["message"]["content"]
        # Preprocess to remove markdown
        return preprocess_response(raw_response)
    except Exception as e:
        return f"Error calling Together AI API: {str(e)}"


def call_ollama_api(message: str, conversation_history: List[Dict]) -> str:
    """Call Ollama API (Local) with prompt engineering"""
    url = "http://localhost:11434/api/generate"
    
    # Build prompt with system instructions
    prompt = f"{SYSTEM_PROMPT}\n\n"
    
    # Add conversation context
    if len(conversation_history) >= 2:
        last_exchange = conversation_history[-2:]
        prompt += f"Previous conversation:\nUser: {last_exchange[0]['message']}\nAssistant: {last_exchange[1]['message']}\n\n"
    
    prompt += f"User: {message}\nAssistant:"
    
    data = {
        "model": "llama3.2",  # or "mistral", "phi3"
        "prompt": prompt,
        "stream": False
    }
    
    try:
        response = requests.post(url, json=data, timeout=30)
        response.raise_for_status()
        raw_response = response.json().get("response", "No response")
        # Preprocess to remove markdown
        return preprocess_response(raw_response)
    except Exception as e:
        return f"Error calling Ollama API. Make sure Ollama is running: {str(e)}"


def get_llm_response(message: str, conversation_history: List[Dict]) -> str:
    """Main function to get LLM response based on provider"""
    if LLM_PROVIDER == "groq":
        return call_groq_api(message, conversation_history)
    elif LLM_PROVIDER == "huggingface":
        return call_huggingface_api(message, conversation_history)
    elif LLM_PROVIDER == "together":
        return call_together_api(message, conversation_history)
    elif LLM_PROVIDER == "ollama":
        return call_ollama_api(message, conversation_history)
    else:
        return f"Unknown LLM provider: {LLM_PROVIDER}. Set LLM_PROVIDER environment variable."

