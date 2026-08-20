from pydantic import BaseModel
from typing import Optional


class Product(BaseModel):
    id: str
    name: str
    price_inr: int
    stock: int
    description: str


class OrderRequest(BaseModel):
    session_id: str
    product_id: str
    quantity: int


class GateDecision(BaseModel):
    allowed: bool
    reason: str
    session_total_spent: int
    session_order_count: int


class OrderResult(BaseModel):
    success: bool
    message: str
    razorpay_order_id: Optional[str] = None
    amount_inr: Optional[int] = None
