
run llm model locally

# ✅ Option 1 — Use Ollama (Easiest)

ollama run deepseek-r1

✔ Very simple  
✔ Auto model download  
✔ Built-in API server  
✔ Good for development

Best for:

- Quick setup
    
- Personal use
    
- Small internal tools
    

---

# ✅ Option 2 — Use vLLM (Production-Oriented)

pip install vllm  
python -m vllm.entrypoints.openai.api_server \  
  --model deepseek-ai/deepseek-llm-7b

✔ Much faster  
✔ Better for GPU servers  
✔ OpenAI-compatible API  
✔ Good for high concurrency

Best for:

- Backend services
    
- High QPS
    
- Production workloads
    

---

# ✅ Option 3 — Use llama.cpp

Run quantized GGUF models:

./main -m deepseek.gguf

✔ Runs on CPU  
✔ Lightweight  
✔ Works on laptops

Best for:

- Low-resource machines
    
- No GPU
    

---

# 🧠 Which One Should You Use?

Since you usually work with backend systems and Go:

If you're:

### 🧪 Just testing locally

→ Use Ollama (fastest setup)

### 🚀 Building production API service

→ Use vLLM

### 💻 Running on laptop without GPU

→ Use llama.cpp