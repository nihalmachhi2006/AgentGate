"""
Basic tests for the gate, run with: python -m pytest tests/
These don't need any API keys since they test the gate module directly.
"""
import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.gate import check_order, record_order, reset_session


def test_normal_order_is_allowed():
    reset_session("test_1")
    decision = check_order("test_1", "sku_001", 1)  # wireless mouse, Rs.799
    assert decision.allowed is True


def test_order_exceeding_spend_cap_is_blocked():
    reset_session("test_2")
    decision = check_order("test_2", "sku_004", 1)  # monitor, Rs.15999, cap default 5000
    assert decision.allowed is False
    assert "cap" in decision.reason


def test_order_exceeding_quantity_cap_is_blocked():
    reset_session("test_3")
    decision = check_order("test_3", "sku_001", 99)
    assert decision.allowed is False


def test_unknown_product_is_blocked():
    reset_session("test_4")
    decision = check_order("test_4", "sku_does_not_exist", 1)
    assert decision.allowed is False
    assert "unknown product_id" in decision.reason


def test_rate_limit_blocks_rapid_orders():
    reset_session("test_5")
    decision1 = check_order("test_5", "sku_001", 1)
    assert decision1.allowed is True
    record_order("test_5", 799)

    decision2 = check_order("test_5", "sku_001", 1)
    assert decision2.allowed is False
    assert "rate limit" in decision2.reason


def test_spend_accumulates_across_orders():
    reset_session("test_6")
    decision1 = check_order("test_6", "sku_003", 1)  # usb hub, Rs.1299
    assert decision1.allowed is True
    record_order("test_6", 1299)

    time.sleep(2.1)  # clear rate limit window

    decision2 = check_order("test_6", "sku_002", 1)  # keyboard, Rs.3499, total would be 4798
    assert decision2.allowed is True


if __name__ == "__main__":
    test_normal_order_is_allowed()
    test_order_exceeding_spend_cap_is_blocked()
    test_order_exceeding_quantity_cap_is_blocked()
    test_unknown_product_is_blocked()
    test_rate_limit_blocks_rapid_orders()
    test_spend_accumulates_across_orders()
    print("all tests passed")
