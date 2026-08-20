"""
Run this to try AgentGate from the command line.

  python run_demo.py            interactive chat with the agent
  python run_demo.py --failure  runs a scripted scenario that deliberately
                                 triggers the spend cap, so you can see and
                                 record the gate blocking and explaining it

Needs GROQ_API_KEY in .env to actually chat. RAZORPAY_KEY_ID and
RAZORPAY_KEY_SECRET are optional, without them orders run in mock mode.
"""
import sys

# Ensure stdout uses UTF-8 to prevent UnicodeEncodeError with the Rupee symbol on Windows
sys.stdout.reconfigure(encoding='utf-8')

from app import audit
from app.agent import chat
from app.gate import reset_session

audit.init_db()


def interactive():
    session_id = "cli_session"
    reset_session(session_id)
    history = None
    print("AgentGate demo. Type 'quit' to exit, 'log' to see the audit trail.\n")

    while True:
        user_input = input("you: ").strip()
        if user_input.lower() == "quit":
            break
        if user_input.lower() == "log":
            for row in audit.get_log(session_id=session_id):
                print(row)
            continue

        reply, history = chat(session_id, user_input, history)
        print(f"agent: {reply}\n")


def scripted_failure_demo():
    """
    Deliberately walks the agent into a bound violation so the failure
    handling is easy to demo and record. Uses the 27-inch Monitor (sku_004,
    Rs.15999) which alone exceeds the default Rs.5000 session cap.
    """
    session_id = "failure_demo_session"
    reset_session(session_id)
    history = None

    print("--- scripted failure demo ---\n")

    steps = [
        "Hi, what do you have in stock?",
        "I'd like to order 1 unit of the 27-inch Monitor please.",
    ]

    for step in steps:
        print(f"you: {step}")
        reply, history = chat(session_id, step, history)
        print(f"agent: {reply}\n")

    print("--- audit log for this session ---")
    for row in audit.get_log(session_id=session_id):
        print(row)


if __name__ == "__main__":
    if "--failure" in sys.argv:
        scripted_failure_demo()
    else:
        interactive()
