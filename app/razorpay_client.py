import uuid
from app.config import RAZORPAY_CONFIGURED, RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET

_client = None

if RAZORPAY_CONFIGURED:
    import razorpay
    _client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))


def create_order(amount_inr, receipt_note):
    """
    Creates a Razorpay order in test mode.
    If no keys are configured yet, falls back to a mock order so the rest
    of the pipeline (agent, gate, audit log) can still be built and tested
    before real test-mode keys are added to .env.
    """
    if not RAZORPAY_CONFIGURED:
        return {
            "mock": True,
            "id": f"mock_order_{uuid.uuid4().hex[:12]}",
            "amount": amount_inr * 100,  # razorpay uses paise
            "currency": "INR",
            "status": "created",
            "note": "RAZORPAY_KEY_ID / RAZORPAY_KEY_SECRET not set, this is a mock response",
        }

    order = _client.order.create({
        "amount": amount_inr * 100,
        "currency": "INR",
        # Razorpay enforces a 40-character max on receipt
        "receipt": receipt_note[:40],
        # notes make the order easy to find in the Razorpay dashboard
        "notes": {
            "source": "AgentGate",
            "receipt_full": receipt_note,
        },
    })
    order["mock"] = False
    return order
