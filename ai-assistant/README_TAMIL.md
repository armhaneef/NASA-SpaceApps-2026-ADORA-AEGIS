# ADORA AEGIS AI Assistant – Tamil Guide

இந்த மாட்யூல், விண்வெளி வீரர் சுகாதார விளக்கங்கள், பாதுகாப்பான கேள்வி-பதில், மற்றும் உள்ளூர் அறிவு தேடல் ஆகியவற்றுக்கான Member 3 AI மாதிரி ஆகும். இது மருத்துவ சோதனை அல்ல; மாதிரி தரவு மட்டுமே பயன்படுத்தப்படுகிறது.

## எளிய setup

Windows-ல்:

```bat
cd ai-assistant
START_WINDOWS.bat
```

கையேடு:

```bat
cd ai-assistant
python -m venv .venv
.venv\Scripts\activate.bat
python -m pip install -r requirements.txt
set LLM_PROVIDER=offline
python -m uvicorn app.main:app --reload
```

## API endpoints

- `GET /api/v1/health`
- `GET /api/v1/demo`
- `POST /api/v1/alerts/explain`
- `POST /api/v1/chat`
- `POST /api/v1/knowledge/search`
- `GET /api/v1/knowledge/status`
- `GET /api/v1/voice-demo`
- `GET /api/v1/voice/status`
- `POST /api/v1/voice/transcribe`
- `POST /api/v1/voice/speak`

## Real LLM activation

```bat
cd ai-assistant
set LLM_PROVIDER=openai_compatible
set LLM_MODEL=gpt-4o-mini
set LLM_BASE_URL=https://api.openai.com/v1/chat/completions
set LLM_API_KEY=your_api_key_here
set LLM_TIMEOUT_SECONDS=30
python -m uvicorn app.main:app --reload
```

அல்லது Ollama-வுக்கு:

```bat
set LLM_PROVIDER=ollama
set LLM_MODEL=llama3.1
set LLM_BASE_URL=http://localhost:11434
python -m uvicorn app.main:app --reload
```

## Browser voice test

1. Server start செய்யுங்கள்.
2. Browser-ல் `http://127.0.0.1:8000/api/v1/voice-demo` திறக்கவும்.
3. Allow microphone தேர்வு செய்யவும்.
4. "Explain my heart rate alert" போன்ற கேள்வி சொல்லவும்.
5. AI பதில் speaker-ல் கேட்கும்.
6. Microphone இல்லாவிட்டால் typed chat fallback பயன்படுத்தவும்.

## முக்கிய எச்சரிக்கை

- இது synthetic data மட்டுமே; NASA live telemetry இல்லை.
- மருத்துவ diagnosis அல்லது treatment உத்தரவு கொடுக்காது.
- anomaly score மருத்துவ நிகழ்தகவு இல்லை.
- AI, fabricated citation, invalid diagnosis, அல்லது measurement invent செய்யக் கூடாது.
