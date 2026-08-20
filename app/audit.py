import sqlite3
import json
import time
from app.config import DB_PATH


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp REAL,
            session_id TEXT,
            action TEXT,
            allowed INTEGER,
            reason TEXT,
            product_id TEXT,
            quantity INTEGER,
            amount_inr INTEGER,
            razorpay_response TEXT
        )
    """)
    conn.commit()
    conn.close()


def log_event(session_id, action, allowed, reason, product_id=None,
              quantity=None, amount_inr=None, razorpay_response=None):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO audit_log
        (timestamp, session_id, action, allowed, reason, product_id, quantity, amount_inr, razorpay_response)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        time.time(),
        session_id,
        action,
        1 if allowed else 0,
        reason,
        product_id,
        quantity,
        amount_inr,
        json.dumps(razorpay_response) if razorpay_response else None,
    ))
    conn.commit()
    conn.close()


def get_log(session_id=None, limit=50):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    if session_id:
        cur.execute(
            "SELECT * FROM audit_log WHERE session_id = ? ORDER BY id DESC LIMIT ?",
            (session_id, limit),
        )
    else:
        cur.execute("SELECT * FROM audit_log ORDER BY id DESC LIMIT ?", (limit,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows
