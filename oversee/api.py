import logging
import time

from oversee.constants import SESSION_CREATION_DELAY

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)


def create_session():
    logging.info("Creating session")
    time.sleep(SESSION_CREATION_DELAY)  # Simulate delay
    return f"session_{int(time.time())}"


def close_session(session):
    logging.info("Closing session %s", session)
    time.sleep(SESSION_CREATION_DELAY)  # Simulate delay


def keep_alive(session):
    logging.info("Keeping session %s alive", session)


def ping_session(session):
    logging.info("Pinging session %s", session)
    return True  # Simulate always alive
