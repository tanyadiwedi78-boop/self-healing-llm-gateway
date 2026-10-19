# Provider test errors: root causes and fixes

## What was failing

I checked the provider test and the actual runtime errors were caused by three separate things:

1. Environment/dependency issue
   - Running the script with the system Python caused:
     - `ModuleNotFoundError: No module named 'litellm'`
   - Fix: use the project virtual environment and install dependencies.

   Example:
   ```powershell
   cd C:\Users\dell\llm_gateway
   .\.venv\Scripts\python -m pip install -r requirements.txt
   .\.venv\Scripts\python test_providers.py
   ```

2. Invalid or retired model names
   - Gemini was failing with a 404 because the configured model was no longer available:
     - `gemini/gemini-2.5-flash`
     - `gemini/gemini-2.0-flash`
   - The provider service returned a message telling us to use a newer Gemini model such as:
     - `gemini/gemini-3.8-flash`
   - Groq was also failing because the configured Groq model was not available in the account/access list:
     - `groq/llama-3.3-70b-versatile`

3. Provider billing / access problem
   - OpenAI returned a real API error:
     - `RateLimitError: You have no credits remaining.`
   - This is not a code bug. The key is valid enough to call the API, but the account has no remaining quota.

4. Windows console encoding issue
   - When printing a failure message with the red cross symbol (`❌`), Windows cp1252 could throw:
     - `UnicodeEncodeError: 'charmap' codec can't encode character '\u274c'`
   - This is a terminal compatibility issue, not a provider bug.

## Fixes applied

I kept the project logic intact and made only the error-related fixes:

- updated the default provider model values in [app/core/config.py](app/core/config.py)
- made the test script handle missing dependencies and ASCII-safe output in [test_providers.py](test_providers.py)

## Recommended settings for .env

Use a valid model per provider and make sure the accounts are active and funded.

```env
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini/gemini-3.8-flash

OPENAI_API_KEY=your_key_here
OPENAI_MODEL=openai/gpt-4o-mini

GROQ_API_KEY=your_key_here
GROQ_MODEL=groq/llama-3.1-8b-instant
```

Notes:
- If `gemini-3.8-flash` is not available in your region or account, use the exact model shown in your Google AI Studio dashboard.
- If `llama-3.1-8b-instant` is not available in your Groq account, use a model that is listed in the Groq console.
- For OpenAI, add credits or a valid funded account before testing again.

## Why providers were not working properly

The real cause was not the app logic itself — it was the provider configuration and account state:

- bad/retired model names
- no OpenAI billing balance
- no access to a Groq model
- using the wrong Python environment

## Final recommendation

After fixing the environment and model names, run:

```powershell
cd C:\Users\dell\llm_gateway
.\.venv\Scripts\python test_providers.py
```

If you still see provider failures, the next step is to verify these three things in the provider dashboard:

1. API key is active
2. account has credit or quota
3. the selected model exists for that account

These are external service issues, not application logic issues.
