
## Self-Healing LLM Gateway
**Python · LiteLLM · FastAPI · Redis · Prometheus · Grafana**  
*Estimated build time: 2 to 3 weeks part time*

### Why this project signals
* This is the project that reads as infrastructure rather than experimentation, which is exactly the transition you are trying to signal.
* It also gives you the strongest demo of the six, because you can break a provider live and show traffic rerouting on a dashboard while you talk.

---

### PHASE 1: Route every model call through one service
* Build a FastAPI service that accepts an OpenAI compatible request shape so existing clients need almost no change to adopt it.
* Use LiteLLM to normalize provider differences.
* Configure at least three providers so failover has somewhere to go.
* Require metadata on every request: tenant, feature, and request id.
* Without these you can never attribute cost, and cost attribution is half the value of a gateway.

---

### PHASE 2: Track health per provider
* Maintain a rolling window per provider covering success rate, p50, p95, and p99 latency, and a proper error taxonomy separating rate limits, timeouts, server errors, content filters, and auth failures.
* Keep counters in Redis using a sliding window so restarts do not reset your view of provider health.
* Expose a `/metrics` endpoint for Prometheus.
* Instrument before you build failover, because failover logic you cannot observe is guesswork.

---

### PHASE 3: Fail over automatically
* Implement a circuit breaker per provider with closed, open, and half open states.
* Trip on error rate above threshold within the window, or p95 latency above budget.
* When a breaker opens, route to the next provider in the preference list for that request class.
* Preference lists differ by class, since a cheap classification call and a long form generation call should not fail over the same way.
* Half open probes are what make it self healing.
* Send a small percentage of traffic back to a recovering provider, close the breaker if it succeeds, reopen immediately if it does not.
* For latency sensitive classes, add hedged requests: fire a second provider after N milliseconds, take whichever returns first, cancel the loser.
* Document the cost trade off, because hedging roughly doubles spend on hedged calls.

---

### PHASE 4: Queue and retry deferrable work
* Classify requests as interactive or deferrable at the API boundary.
* Interactive calls fail fast, deferrable calls survive an outage.
* Push deferrable work to a Redis queue with exponential backoff and jitter when every provider is degraded, instead of returning an error to the caller.
* Attach idempotency keys so a retry cannot duplicate a side effect.
* This is the detail that signals you have operated something in production.

---

### PHASE 5: Put it on a Grafana board and then break it on purpose
* Panels worth building: requests per second by provider, error rate, p95 latency, circuit state timeline, failover events, queue depth, and cost per hour by tenant and by feature.
* Add a chaos endpoint or proxy that injects errors and latency into one provider on demand.
* Record a ninety second screen capture: healthy traffic, a provider degraded, the breaker tripping, traffic rerouting, and the breaker closing again as it recovers.
* That video goes at the top of the README.
* It communicates more in ninety seconds than a page of architecture description.

---

### Done when
* You can degrade a provider live while traffic keeps flowing, and the dashboard shows the trip, the reroute, and the automatic recovery.
* **Resume line:** Built an LLM gateway with per provider circuit breaking and automatic failover; sustained x percent availability through simulated provider outages with per tenant cost attribution.

---

### Where this usually goes wrong
* No cost attribution, which removes the main reason companies build gateways.
* Retrying calls that are not idempotent, which turns a blip into duplicated side effects.
* No half open state, so the breaker opens once and never heals.
* A dashboard with no chaos test, which leaves the failover logic unproven.

---

### Stretch goals:
* Add a semantic cache layer.
* A model tiering router that sends easy requests to a small model.
* Per tenant rate limits and budgets.
* Request logging with PII redaction.


### What's Improve:
* Uses LiteLLM only for provider normalization.
* Not completely depend on for these working principles build from scratch like Fallback , Cooldown , Retries , Circuit Breaker , health window and routing mechanism . 

### Architecture Overview :
                 
Client Request (OpenAI Standard Format)
  ↓
FastAPI Router (`app/routers/chat.py`)
  ↓
Authentication & Metadata (`app/middleware/auth.py`)
  ↓
PII Redaction & Model Tiering (`app/middleware/guardrails.py`)
  ↓
Redis State & Sliding Window Health Tracker (`app/storage/`)
  ↓
Circuit Breaker & Fallback Engine





1. Circuit Breaker: Use a "Sliding Window" instead of Simple Counter

• What most beginners do: Open the circuit breaker if 5 absolute errors happen in a row.
• The Engineer Move: If Groq handles 10,000 requests a minute, 5 sequential errors might just be random network blips. Instead, implement a Time-Based Sliding Window. Keep track of the error rate over the last 30 seconds (e.g., if the error rate crosses 15% of total traffic, then trip the circuit to OPEN). This keeps your primary high-speed provider online longer during brief network jitters.

2. Streaming Fallbacks: Protect User Experience

• What most beginners do: Wait for a blocking, complete non-streamed text payload to fail before triggering a fallback.
• The Engineer Move: If your client apps are utilizing token streaming (stream=True for chat interfaces), your gateway must handle streaming fallback cleanly. If Groq drops its connection halfway through generation (e.g., at token #45), your loop layer needs to capture that, open a connection to Gemini, pass the message history plus the generated 45 tokens, and tell the fallback provider to continue writing from there seamlessly.

3. Chaos Engineering: Automate Failure Scenarios

• What most beginners do: Test the fallback code by manually changing a URL string to be invalid.
• The Engineer Move: Build an automated /chaos/inject endpoint into your app/ files. When toggled, it deliberately drops 30% of incoming connections, injects artificial 429 Too Many Requests status codes, or spins up high latency (e.g., a 12-second delay). Showing that your Grafana dashboard registers these chaos injections and your gateway automatically self-heals by cleanly failing over is a massive talking point during interview stages.

4. Redis Async Connection Pooling

• What most beginners do: Open and close Redis sessions on every HTTP query.
• The Engineer Move: Use strict ConnectionPool handling within an asyncio loop lifecycle context manager (lifespan in FastAPI). This prevents connection leaks when handling concurrent traffic from both of your application clients at the same time.




