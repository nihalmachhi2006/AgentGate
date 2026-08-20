import time
from app.config import SESSION_SPEND_CAP_INR, MAX_QTY_PER_ITEM, MIN_SECONDS_BETWEEN_ORDERS
from app.catalog import get_product
from app.models import GateDecision

# per-session state, keyed by session_id, similar to how DPI-Engine keys
# flow state by a hashed 5-tuple. here the "flow" is an agent session.
_sessions = {}


def _get_session(session_id):
    if session_id not in _sessions:
        _sessions[session_id] = {
            "total_spent": 0,
            "order_count": 0,
            "last_order_time": None,
        }
    return _sessions[session_id]


def check_order(session_id, product_id, quantity):
    """
    Runs an order request through the gate before it's allowed to reach Razorpay.
    Returns a GateDecision with allowed=True/False and the reason why.
    """
    session = _get_session(session_id)

    product = get_product(product_id)
    if product is None:
        return GateDecision(
            allowed=False,
            reason=f"unknown product_id '{product_id}'",
            session_total_spent=session["total_spent"],
            session_order_count=session["order_count"],
        )

    # rate limit check, catches rapid-fire duplicate orders
    now = time.time()
    if session["last_order_time"] is not None:
        elapsed = now - session["last_order_time"]
        if elapsed < MIN_SECONDS_BETWEEN_ORDERS:
            return GateDecision(
                allowed=False,
                reason=f"rate limit hit, only {elapsed:.1f}s since last order, "
                       f"minimum gap is {MIN_SECONDS_BETWEEN_ORDERS}s",
                session_total_spent=session["total_spent"],
                session_order_count=session["order_count"],
            )

    # quantity bound check
    if quantity > MAX_QTY_PER_ITEM:
        return GateDecision(
            allowed=False,
            reason=f"quantity {quantity} exceeds max allowed per item ({MAX_QTY_PER_ITEM})",
            session_total_spent=session["total_spent"],
            session_order_count=session["order_count"],
        )

    if quantity > product.stock:
        return GateDecision(
            allowed=False,
            reason=f"requested quantity {quantity} exceeds available stock ({product.stock})",
            session_total_spent=session["total_spent"],
            session_order_count=session["order_count"],
        )

    # spend bound check
    order_amount = product.price_inr * quantity
    projected_total = session["total_spent"] + order_amount
    if projected_total > SESSION_SPEND_CAP_INR:
        return GateDecision(
            allowed=False,
            reason=f"order of Rs.{order_amount} would bring session total to Rs.{projected_total}, "
                   f"exceeding the session cap of Rs.{SESSION_SPEND_CAP_INR}",
            session_total_spent=session["total_spent"],
            session_order_count=session["order_count"],
        )

    # all checks passed
    return GateDecision(
        allowed=True,
        reason="passed spend, quantity, and rate checks",
        session_total_spent=session["total_spent"],
        session_order_count=session["order_count"],
    )


def record_order(session_id, amount_inr):
    """Call this only after a Razorpay order actually succeeds."""
    session = _get_session(session_id)
    session["total_spent"] += amount_inr
    session["order_count"] += 1
    session["last_order_time"] = time.time()


def reset_session(session_id):
    """Useful for tests and demos, wipes a session's state."""
    if session_id in _sessions:
        del _sessions[session_id]
