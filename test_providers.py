"""
Test script to check connectivity and responses from active LLM providers (Gemini and Groq).
It uses asyncio to test each enabled provider defined in configuration.

Recommended models to put in your .env file:
- Gemini: GEMINI_MODEL=gemini/gemini-pro (or gemini/gemini-1.5-pro)
- Groq:   GROQ_MODEL=groq/llama3-8b-8192
"""

import sys
import asyncio

# Fix Windows Proactor/Selector event loop SSL transport bug
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

try:
    from app.providers.registry import get_enabled_providers
    from app.providers.litellm_client import call_provider
    from app.schemas.requests import ChatRequest, Message
except ModuleNotFoundError as exc:
    raise SystemExit(
        "Dependencies are missing. Activate the project venv and install requirements: "
        "./.venv/Scripts/python -m pip install -r requirements.txt"
    ) from exc


async def test_all_providers() -> None:
    """Fetch all enabled LLM providers and test sending a prompt to each."""
    enabled_providers = get_enabled_providers()
    
    if not enabled_providers:
        print("No enabled providers found. Please check your .env API keys.")
        return

    print(f"Enabled providers found: {[p.name for p in enabled_providers]}")
    print("------------------------------------------------------------\n")

    test_request = ChatRequest(
        messages=[Message(role="user", content="Explain Inference in one simple sentnce.")]
    )

    for provider in enabled_providers:
        print(f"Testing provider '{provider.name}'")
        print(f"  Model configured: {provider.model}")
        try:
            response = await call_provider(provider, test_request, max_tokens=50)
            print(f"  [SUCCESS] {provider.name}: {response.content.strip()}")
            print(f"            Latency: {response.latency_ms:.1f}ms\n")
        except Exception as error:
            print(f"  [FAILED]  {provider.name}: {error}")
            print(f"  [ADVICE]  Update your .env file with a valid model for '{provider.name}':")
            if provider.name == "gemini":
                print(f"            GEMINI_MODEL=gemini/gemini-pro")
            elif provider.name == "groq":
                print(f"            GROQ_MODEL=groq/llama3-8b-8192\n")
            else:
                print(f"            Check provider dashboard for supported model names.\n")

    # Brief pause to allow underlying HTTP/SSL transports to close cleanly before loop termination
    await asyncio.sleep(0.2)


def main() -> None:
    """Entry point for running the async provider test script."""
    try:
        asyncio.run(test_all_providers())
    except Exception:
        pass


if __name__ == "__main__":
    main()
