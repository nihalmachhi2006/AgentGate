# AgentGate

An explainable, bounded, and gated AI agent commerce layer, built for the Razorpay AI
Buildathon (Track 1: AI Growth & Agentic Commerce).

AgentGate sits between an AI shopping agent and Razorpay's test-mode payment APIs.
Every money action the agent wants to take passes through a gate first, which checks
it against spend limits, quantity limits, and rate limits before it's allowed to reach
Razorpay. Every decision, allowed or blocked, is written to a persistent audit log with
the reasoning behind it.

The gate is a direct extension of two things already built independently of this
hackathon:

- **DPI-Engine**, a multithreaded packet inspection engine, contributed the idea of
  inspecting every unit of traffic against rules before it's allowed through, and
  tracking per-flow state. Here, an agent session plays the role a network flow does.
- **MeshPay**, an offline payment protocol, contributed the idea of never trusting an
  action until it explicitly passes a verification step. The gate plays the same role
  MeshPay's handshake does.

## How it works

1. A buyer talks to the AI agent.
2. The agent reads the catalog and decides what to do, using tools: `list_products`,
   `create_order`.
3. `create_order` doesn't call Razorpay directly. It's intercepted by `gate.py`, which
   checks the request against a per-session spend cap, a per-item quantity cap, and a
   minimum interval between orders.
4. If the gate approves, a real Razorpay test-mode order is created and the result goes
   back to the agent.
5. If the gate blocks the request, the agent is told why, and it explains that to the
   buyer in plain language and suggests a valid way forward.
6. Every step is logged to `audit.db` (SQLite): timestamp, session, action, decision,
   reasoning, and the Razorpay response if there was one.

## Project structure

```
agentgate/
├── app/
│   ├── config.py          env vars and gate limits
│   ├── models.py          pydantic schemas
│   ├── catalog.py         loads data/catalog.json
│   ├── gate.py             the trust/inspection layer, the core of this project
│   ├── audit.py            SQLite audit log
│   ├── razorpay_client.py  Razorpay test-mode integration, mock fallback if no keys
│   ├── agent.py             the LLM tool-calling loop
│   └── main.py              FastAPI app (optional, for a web interface)
├── data/catalog.json       sample product catalog
├── tests/test_gate.py       gate tests, no API keys needed
├── run_demo.py              CLI demo, interactive or scripted failure mode
├── requirements.txt
└── .env.example
```

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# add your Groq key and Razorpay test-mode keys to .env
```

Without any keys, the gate and audit log still work standalone (see the tests), and
Razorpay calls fall back to a mock response so the rest of the pipeline is testable
before real test-mode keys are added.

## Running it

```bash
# interactive chat with the agent
python run_demo.py

# scripted demo that deliberately triggers the spend cap,
# useful for the pitch video's failure-recovery moment
python run_demo.py --failure

# gate tests, no keys required
python -m pytest tests/

# optional web API
uvicorn app.main:app --reload
```

## Known limitations

- Gate state is in-memory per process, it resets if the server restarts. Fine for a
  demo, would move to Redis or a DB-backed session store for anything longer-lived.
- Only one currency (INR) and one gate policy set (spend, quantity, rate) are
  implemented. More policies (e.g. flagging unusual item combinations) are a natural
  next step.
- The agent only has two tools (`list_products`, `create_order`). A `confirm_payment`
  step for handling Razorpay webhooks asynchronously is a natural extension, left out
  here to keep the demo scope tight and finishable.
