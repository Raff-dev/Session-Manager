import logging

import requests

from oversee.constants import SESSION_MANAGER_TIMEOUT, SESSION_MANAGER_URL


class SessionManagerClient:

    @staticmethod
    def get_session():
        logging.info("Requesting a new session")
        response = requests.get(
            f"{SESSION_MANAGER_URL}/get_session", timeout=SESSION_MANAGER_TIMEOUT
        )
        response.raise_for_status()
        session = response.json()["session"]
        logging.info("Received session %s", session)
        return session

    @staticmethod
    def release_session(session):
        logging.info("Releasing session %s", session)
        response = requests.post(
            f"{SESSION_MANAGER_URL}/release_session",
            json={"session": session},
            timeout=SESSION_MANAGER_TIMEOUT,
        )
        response.raise_for_status()
        logging.info("Released session %s", session)
