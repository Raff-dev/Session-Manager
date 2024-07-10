import logging
import threading
import time

import redis
from flask import Flask, jsonify, request

from oversee.api import close_session, create_session, keep_alive, ping_session
from oversee.constants import REDIS_URL, SESSION_KEEP_ALIVE_DELAY

app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)

# Initialize Redis
redis_client = redis.StrictRedis.from_url(REDIS_URL)


class SessionManager:
    def __init__(self, max_sessions):
        self.max_sessions = max_sessions
        self.active_sessions_lock = threading.Lock()

    def get_session(self):
        with self.active_sessions_lock:
            session = redis_client.lpop("sessions")
            if session and not ping_session(session):
                logging.info("Session %s is dead, creating a new session", session)
                session = create_session()
            elif not session:
                session = create_session()
                logging.info("Creating a new session")

            redis_client.rpush("active_sessions", session)
            active_sessions_count = redis_client.llen("active_sessions")
            logging.info("Active sessions: %d", active_sessions_count)

        return session

    def release_session(self, session):
        with self.active_sessions_lock:
            redis_client.lrem("active_sessions", 1, session)
            redis_client.rpush("sessions", session)
            active_sessions_count = redis_client.llen("active_sessions")
            logging.info(
                "Released session %s. Active sessions: %d",
                session,
                active_sessions_count,
            )

    def keep_sessions_alive(self):
        while True:
            with self.active_sessions_lock:
                sessions = redis_client.lrange("sessions", 0, -1)
                for session in sessions:
                    keep_alive(session)
            time.sleep(SESSION_KEEP_ALIVE_DELAY)  # Keep alive every minute

    def shutdown(self):
        with self.active_sessions_lock:
            sessions = redis_client.lrange("sessions", 0, -1)
            for session in sessions:
                close_session(session)


session_manager = SessionManager(max_sessions=5)


@app.route("/get_session", methods=["GET"])
def get_session():
    try:
        session = session_manager.get_session()
        return jsonify(session=session)
    except Exception as e:
        logging.error("Error in /get_session: %s", e)
        return jsonify(error=str(e)), 500


@app.route("/release_session", methods=["POST"])
def release_session():
    try:
        session = request.json["session"]
        session_manager.release_session(session)
        return "", 200
    except Exception as e:
        logging.error("Error in /release_session: %s", e)
        return jsonify(error=str(e)), 500


if __name__ == "__main__":

    def main():
        # Start the session keep-alive thread
        keep_alive_thread = threading.Thread(
            target=session_manager.keep_sessions_alive, daemon=True
        )
        keep_alive_thread.start()

    main()
    app.run(host="0.0.0.0", port=5000)
