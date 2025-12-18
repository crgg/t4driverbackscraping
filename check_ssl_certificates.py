import logging
import os
from datetime import datetime
from dotenv import load_dotenv

from ssl_checker.checker import SSLChecker

# Load env variables
load_dotenv()

# Setup basic logging configuration for the script execution
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

LOG_FILE = datetime.now().strftime("%Y-%m-%d") + ".log"
log_file_path = os.path.join(LOG_DIR, LOG_FILE)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file_path),
        logging.StreamHandler() # Always log to stdout as well
    ]
)

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    logger.info("Initializing SSL Certificate Checker...")
    try:
        checker = SSLChecker()
        checker.run()
        logger.info("SSL Checker execution finished successfully.")
    except Exception as e:
        logger.error(f"Fatal error during SSL Checker execution: {e}")