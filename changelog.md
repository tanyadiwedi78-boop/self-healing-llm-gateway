# Changelog - Self-Healing LLM Gateway

All notable changes to this project will be documented in this file.

## [Unreleased] - 2026-10-15

# Design Decisions

| # | Decision | Why |
|---|----------|-----|
| 1 | LiteLLM is used only as a translator (`acompletion`, `num_retries=0`, no Router) | Retry, fallback, health, and breaker logic are the core of the project, so they are our own code |
| 2 | Three providers: OpenAI, Groq, Gemini | Failover needs at least two alternatives, and hedging needs a third |
| 3 | Health window is time-based (60s), not count-based | Old samples must not affect health during quiet periods |
| 4 | Minimum 10 samples before error rate can trip the breaker | One failed request out of one must not open the breaker |
| 5 | Errors carry `counts_against_provider` | A bad request from a user must not make a provider look unhealthy |
| 6 | Tenant identity comes from the API key, never from a header | Cost attribution cannot be faked |
| 7 | `feature` is restricted to a safe pattern | It is a Prometheus label, and unbounded values would break metrics |
| 8 | Cost is calculated from our own `pricing.json` | No dependency on a library for a core feature |

