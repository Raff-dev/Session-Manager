import logging
import threading
import time

import redis
from flask import Flask, jsonify, request

from oversee.api import create_session, keep_alive, ping_session
from oversee.constants import MAX_SESSIONS, REDIS_URL, SESSION_KEEP_ALIVE_DELAY

app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)

# Initialize Redis
redis_client: redis.StrictRedis = redis.StrictRedis.from_url(REDIS_URL)

# Redis keys
SESSIONS_KEY: str = "sessions"
ACTIVE_SESSIONS_KEY: str = "active_sessions"


class SessionManager:
    def __init__(self) -> None:
        self.lock: threading.Lock = threading.Lock()
        redis_client.delete(SESSIONS_KEY)
        redis_client.delete(ACTIVE_SESSIONS_KEY)

    def get_session(self) -> str | None:
        with self.lock:
            active_sessions_count: int = redis_client.llen(ACTIVE_SESSIONS_KEY)
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
            active_sessions_count = redis_client.llen(ACTIVE_SESSIONS_KEY)
            logging.info("Active sessions: %d", active_sessions_count)

            return session

    def release_session(self, session: str) -> None:
        with self.lock:
            redis_client.lrem(ACTIVE_SESSIONS_KEY, 1, session)
            redis_client.rpush(SESSIONS_KEY, session)
            active_sessions_count = redis_client.llen(ACTIVE_SESSIONS_KEY)
            logging.info(
                "Released session %s. Active sessions: %d",
                session,
                active_sessions_count,
            )

    def keep_sessions_alive(self) -> None:
        while True:
            with self.lock:
                sessions = redis_client.lrange(SESSIONS_KEY, 0, -1)
                for session in sessions:
                    keep_alive(session.decode("utf-8"))
            time.sleep(SESSION_KEEP_ALIVE_DELAY)


session_manager: SessionManager = SessionManager()


@app.route("/get_session", methods=["GET"])
def get_session() -> tuple[dict[str, str], int]:
    try:
        session = session_manager.get_session()
        if session:
            return jsonify(session=session), 200
        return jsonify(error="No available sessions"), 503
    except Exception as e:
        logging.error("Error in /get_session: %s", e)
        return jsonify(error=str(e)), 500


@app.route("/release_session", methods=["POST"])
def release_session() -> tuple[str, int]:
    try:
        session = request.json["session"]
        session_manager.release_session(session)
        return "", 200
    except Exception as e:
        logging.error("Error in /release_session: %s", e)
        return jsonify(error=str(e)), 500


if __name__ == "__main__":

    def main() -> None:
        keep_alive_thread: threading.Thread = threading.Thread(
            target=session_manager.keep_sessions_alive, daemon=True
        )
        keep_alive_thread.start()

    main()
    app.run(host="0.0.0.0", port=5000)
