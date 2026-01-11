# Free LLM API Options

## 1. Groq (Recommended - Fast & Free)

**URL:** `https://api.groq.com/openai/v1/chat/completions`  
**Model:** `llama-3.1-8b-instant` or `mixtral-8x7b-32768`  
**Free Tier:** 30 requests/minute, 14,400 requests/day  
**API Key:** Get free at https://console.groq.com/

**Setup:**
```bash
pip install openai
```

**Environment Variable:**
```bash
GROQ_API_KEY=your_api_key_here
```

---

## 2. Hugging Face Inference API (Free)

**URL:** `https://api-inference.huggingface.co/models/meta-llama/Llama-3.2-3B-Instruct`  
**Model:** `meta-llama/Llama-3.2-3B-Instruct` or `mistralai/Mistral-7B-Instruct-v0.2`  
**Free Tier:** Unlimited (with rate limits)  
**API Key:** Get free at https://huggingface.co/settings/tokens

**Setup:**
```bash
pip install requests
```

**Environment Variable:**
```bash
HUGGINGFACE_API_KEY=your_api_key_here
```

---

## 3. Together AI (Free Tier)

**URL:** `https://api.together.xyz/v1/chat/completions`  
**Model:** `meta-llama/Llama-3-8b-chat-hf` or `mistralai/Mixtral-8x7B-Instruct-v0.1`  
**Free Tier:** $25 free credits  
**API Key:** Get free at https://api.together.xyz/

**Setup:**
```bash
pip install openai
```

**Environment Variable:**
```bash
TOGETHER_API_KEY=your_api_key_here
```

---

## 4. Google Gemini (Free Tier)

**URL:** `https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent`  
**Model:** `gemini-pro` or `gemini-pro-vision`  
**Free Tier:** 60 requests/minute  
**API Key:** Get free at https://makersuite.google.com/app/apikey

**Setup:**
```bash
pip install google-generativeai
```

**Environment Variable:**
```bash
GEMINI_API_KEY=your_api_key_here
```

---

## 5. Ollama (Local - Completely Free)

**URL:** `http://localhost:11434/api/generate`  
**Model:** `llama3.2`, `mistral`, `phi3` (download locally)  
**Free Tier:** Unlimited, runs on your machine  
**Setup:** Download from https://ollama.com/

**No API key needed** - runs locally

---

## Recommended: Groq (Fastest & Easiest)

1. Sign up at https://console.groq.com/
2. Get your free API key
3. Add to `.env` file: `GROQ_API_KEY=your_key`
4. Use the implementation example below

