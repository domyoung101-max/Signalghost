"""main.py — Signalghost entry point.

Runs one complete edition session chronologically.

Usage:
    python main.py                     # Run one edition
    python main.py --init-only         # Initialize database with Ed033 seed
    python main.py --init-fresh-ed01   # STRATEGIC RESET: Initialize with Ed01 fresh seed
                                       # (preserves architecture, resets content)
"""

import sys
import os

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from persistence import init_db
from session_executor import SessionExecutor


def main():
    if "--init-only" in sys.argv:
        print("Initializing database...")
        init_db()
        from calibration_state import SEED_DATA
        from persistence import get_connection
        conn = get_connection()
        SEED_DATA(conn)
        conn.close()
        print("Database initialized and seeded with Ed033 data.")
        return

    if "--init-fresh-ed01" in sys.argv:
        print("STRATEGIC RESET — Initializing database with Ed01 fresh seed...")
        print("Architecture preserved (v1.3.0). Content reset.")
        init_db()
        from seed_ed01 import SEED_ED01
        from persistence import get_connection
        conn = get_connection()
        SEED_ED01(conn)
        conn.close()
        print("Database initialized and seeded with Ed01 fresh data.")
        print("Ready for Ed02 sweep (run: python main.py).")
        return

    executor = SessionExecutor()
    result = executor.run()

    print()
    print("Session complete.")
    print(f"  Edition: {result['edition']}")
    print(f"  Brier Score: {result['scores']['brier_score']}")
    print(f"  PDF: {result['pdf_path']}")
    print(f"  Session State: {result['session_state_path']}")


if __name__ == "__main__":
    main()
