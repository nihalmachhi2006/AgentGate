import json
from app.config import GROQ_API_KEY, GROQ_CONFIGURED, GROQ_MODEL, RAZORPAY_KEY_ID, RAZORPAY_CONFIGURED
from app.catalog import list_products, get_product
from app.gate import check_order, record_order
from app.razorpay_client import create_order
from app import audit

SYSTEM_PROMPT = """You are a shopping assistant for an online store. You help the buyer find
products and place orders. You can only take real actions through your tools -
never claim an order succeeded unless the create_order tool told you it did.

If a tool tells you an order was blocked, explain clearly to the buyer why, in plain
language, and suggest a valid way forward (e.g. reduce quantity, wait a moment, pick a
cheaper item). Don't apologize excessively, just be direct and helpful.
"""

TOOLS = [
    {
        "name": "list_products",
        "description": "Returns the full product catalog with prices, stock, and descriptions.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "create_order",
        "description": (
            "Attempts to place an order for a product. This call passes through a gate "
            "that checks spend limits, quantity limits, and rate limits before any real "
            "payment action happens. It may be blocked; if so, explain why to the buyer."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string", "description": "id of the product from the catalog"},
                "quantity": {"type": "integer", "description": "how many units to order"},
            },
            "required": ["product_id", "quantity"],
        },
    },
]

GROQ_TOOLS = [{"type": "function", "function": tool} for tool in TOOLS]


def _run_tool(tool_name, tool_input, session_id):
    if tool_name == "list_products":
        return {"products": list_products()}

    if tool_name == "create_order":
        product_id = tool_input["product_id"]
        quantity = tool_input["quantity"]

        decision = check_order(session_id, product_id, quantity)

        if not decision.allowed:
            audit.log_event(
                session_id=session_id, action="create_order", allowed=False,
                reason=decision.reason, product_id=product_id, quantity=quantity,
            )
            return {
                "success": False,
                "reason": decision.reason,
            }

        product = get_product(product_id)
        amount = product.price_inr * quantity
        razorpay_response = create_order(amount, receipt_note=f"{session_id}_{product_id}")

        record_order(session_id, amount)
        audit.log_event(
            session_id=session_id, action="create_order", allowed=True,
            reason=decision.reason, product_id=product_id, quantity=quantity,
            amount_inr=amount, razorpay_response=razorpay_response,
        )

        return {
            "success": True,
            "amount_inr": amount,
            "razorpay_order_id": razorpay_response["id"],
            "mock": razorpay_response.get("mock", False),
            # key_id is the PUBLIC razorpay key — safe to send to the browser
            # so Checkout.js can open the payment modal
            "key_id": RAZORPAY_KEY_ID if RAZORPAY_CONFIGURED else None,
        }

    return {"error": f"unknown tool {tool_name}"}


def chat(session_id, user_message, history=None):
    """
    Runs one turn of the agent loop. history is a list of prior {role, content}
    messages for multi-turn conversations, keep it None for a fresh conversation.
    Returns (reply_text, updated_history).
    """
    if not GROQ_CONFIGURED:
        return (
            "GROQ_API_KEY is not set yet, so I can't reason over the catalog. "
            "Add your key to .env and try again. In the meantime, the gate and audit "
            "log modules work standalone, see tests/test_gate.py.",
            history or [],
        )

    from groq import Groq
    client = Groq(api_key=GROQ_API_KEY)

    messages = list(history) if history else []
    if not messages:
        messages.append({"role": "system", "content": SYSTEM_PROMPT})
    messages.append({"role": "user", "content": user_message})

    while True:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            max_tokens=1024,
            tools=GROQ_TOOLS,
            tool_choice="auto",
            messages=messages,
        )
        assistant_message = response.choices[0].message
        messages.append(assistant_message.model_dump(exclude_none=True))

        if not assistant_message.tool_calls:
            return assistant_message.content or "I couldn't generate a response.", messages

        for tool_call in assistant_message.tool_calls:
            try:
                tool_input = json.loads(tool_call.function.arguments)
                result = _run_tool(tool_call.function.name, tool_input, session_id)
            except (json.JSONDecodeError, KeyError) as error:
                result = {"error": f"invalid tool input: {error}"}
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(result),
            })
