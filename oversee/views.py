import logging
import time

from flask import jsonify, request

from oversee import app, redis_client
from oversee.session_manager import HEARTBEAT_KEY_PREFIX, session_manager


@app.route("/get_session", methods=["GET"])
def get_session():
    try:
        session = session_manager.get_session()
        if session:
            return jsonify(session=session), 200
        return "", 204
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


@app.route("/heartbeat", methods=["POST"])
def heartbeat():
    try:
        session = request.json["session"]
        redis_client.set(f"{HEARTBEAT_KEY_PREFIX}{session}", time.time())
        return "", 200
    except Exception as e:
        logging.error("Error in /heartbeat: %s", e)
        return jsonify(error=str(e)), 500
