from db.alerted_errors import init_db
import logging
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Initializing Database Schema...")
    try:
        init_db()
        print("Success: 'alerted_errors' table created/verified.")
    except Exception as e:
        print(f"Error: {e}")
