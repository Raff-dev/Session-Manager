import logging
import threading
import time

from oversee import app, redis_client, redlock
from oversee.api import create_session, ping_session
from oversee.constants import MAX_SESSIONS

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)

# Redis keys
SESSIONS_KEY = "sessions"
ACTIVE_SESSIONS_KEY = "active_sessions"
HEARTBEAT_KEY_PREFIX = "heartbeat_"

# Lock key
SESSION_MANAGER_LOCK = "session_manager_lock"


class SessionManager:
    def __init__(self):
        # Clear existing sessions
        redis_client.delete(SESSIONS_KEY)
        redis_client.delete(ACTIVE_SESSIONS_KEY)
        logging.info("Session manager initialized, all sessions cleared.")

    def get_session(self):
        try:
            lock = redlock.lock(SESSION_MANAGER_LOCK, 1000)
            if not lock:
                logging.info("Could not acquire lock, no available sessions.")
                return None

            try:
                active_sessions_count = redis_client.llen(ACTIVE_SESSIONS_KEY)
                logging.info("Active sessions count: %d", active_sessions_count)
                if active_sessions_count >= MAX_SESSIONS:
                    logging.info("Max sessions limit reached, no available sessions.")
                    return None

                session = redis_client.lpop(SESSIONS_KEY)
                if session:
                    session = session.decode("utf-8")
                if session and not ping_session(session):
                    logging.info("Session %s is dead, creating a new session", session)
                    session = create_session()
                elif not session:
                    session = create_session()
                    logging.info("Creating a new session")

                redis_client.rpush(ACTIVE_SESSIONS_KEY, session)
                redis_client.set(f"{HEARTBEAT_KEY_PREFIX}{session}", time.time())
                active_sessions_count = redis_client.llen(ACTIVE_SESSIONS_KEY)
                logging.info("Active sessions: %d", active_sessions_count)

                return session
            finally:
                redlock.unlock(lock)
        except Exception as e:
            logging.error("Error acquiring lock: %s", e)
            return None

    def release_session(self, session):
        try:
            lock = redlock.lock(SESSION_MANAGER_LOCK, 1000)
            if not lock:
                logging.info("Could not acquire lock to release session.")
                return

            try:
                redis_client.lrem(ACTIVE_SESSIONS_KEY, 1, session)
                redis_client.rpush(SESSIONS_KEY, session)
                redis_client.delete(f"{HEARTBEAT_KEY_PREFIX}{session}")
                active_sessions_count = redis_client.llen(ACTIVE_SESSIONS_KEY)
                logging.info(
                    "Released session %s. Active sessions: %d",
                    session,
                    active_sessions_count,
                )
            finally:
                redlock.unlock(lock)
        except Exception as e:
            logging.error("Error releasing session: %s", e)


session_manager = SessionManager()

if __name__ == "__main__":
    from oversee.session_monitor import keep_sessions_alive, monitor_heartbeats

    def main():
        # Start the session keep-alive thread
        keep_alive_thread = threading.Thread(target=keep_sessions_alive, daemon=True)
        keep_alive_thread.start()

        # Start the heartbeat monitoring thread
        heartbeat_thread = threading.Thread(target=monitor_heartbeats, daemon=True)
        heartbeat_thread.start()

    main()
    app.run(host="0.0.0.0", port=5000)
