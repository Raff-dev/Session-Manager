import logging
import time

import requests
from redlock import Redlock

from oversee.api import keep_alive
from oversee.constants import (
    REDIS_URL,
    SESSION_KEEP_ALIVE_DELAY,
    SESSION_MANAGER_TIMEOUT,
    SESSION_MANAGER_URL,
)
from oversee.session_manager import (
    HEARTBEAT_KEY_PREFIX,
    SESSION_MANAGER_LOCK,
    SessionManager,
    redis_client,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)

# Initialize Redis lock
redlock = Redlock([REDIS_URL])


def send_heartbeat(session):
    try:
        requests.post(
            f"{SESSION_MANAGER_URL}/heartbeat",
            json={"session": session},
            timeout=SESSION_MANAGER_TIMEOUT,
        )
    except requests.RequestException as e:
        logging.error("Failed to send heartbeat: %s", e)


def keep_sessions_alive():
    while True:
        lock = redlock.lock(SESSION_MANAGER_LOCK, 1000)
        if not lock:
            logging.info("Could not acquire lock to keep sessions alive.")
            time.sleep(SESSION_KEEP_ALIVE_DELAY)
            continue

        try:
            sessions = redis_client.lrange("sessions", 0, -1)
            for session in sessions:
                keep_alive(session.decode("utf-8"))
        finally:
            redlock.unlock(lock)

        time.sleep(SESSION_KEEP_ALIVE_DELAY)  # Keep alive every minute


def monitor_heartbeats():
    while True:
        current_time = time.time()
        lock = redlock.lock(SESSION_MANAGER_LOCK, 1000)
        if not lock:
            logging.info("Could not acquire lock to monitor heartbeats.")
            time.sleep(SESSION_KEEP_ALIVE_DELAY)
            continue

        try:
            active_sessions = redis_client.lrange("active_sessions", 0, -1)
            for session in active_sessions:
                session = session.decode("utf-8")
                last_heartbeat = float(
                    redis_client.get(f"{HEARTBEAT_KEY_PREFIX}{session}") or 0
                )
                if current_time - last_heartbeat > 2 * SESSION_KEEP_ALIVE_DELAY:
                    logging.warning("Session %s is orphaned, reclaiming it", session)
                    session_manager = SessionManager()
                    session_manager.release_session(session)
        finally:
            redlock.unlock(lock)

        time.sleep(SESSION_KEEP_ALIVE_DELAY)
