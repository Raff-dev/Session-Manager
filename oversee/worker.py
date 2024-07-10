import logging
import time

import requests
from celery import Celery

from oversee.constants import (
    REDIS_URL,
    SESSION_KEEP_ALIVE_DELAY,
    SESSION_MANAGER_TIMEOUT,
    SESSION_MANAGER_URL,
    WORKER_JOB_DURATION,
)
from oversee.session_monitor import send_heartbeat

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)

# Initialize Celery
app = Celery("worker", broker=REDIS_URL, backend=REDIS_URL)
app.config_from_object("oversee.celeryconfig")


@app.task
def worker_task():
    while True:
        try:
            response = requests.get(
                f"{SESSION_MANAGER_URL}/get_session", timeout=SESSION_MANAGER_TIMEOUT
            )
            if response.status_code == 200:
                session = response.json().get("session")
                logging.info("Worker using %s", session)
                start_time = time.time()
                while time.time() - start_time < WORKER_JOB_DURATION:
                    send_heartbeat(session)
                    time.sleep(SESSION_KEEP_ALIVE_DELAY)
                requests.post(
                    f"{SESSION_MANAGER_URL}/release_session",
                    json={"session": session},
                    timeout=SESSION_MANAGER_TIMEOUT,
                )
                logging.info("Worker releasing %s", session)
                break
            if response.status_code == 204:
                logging.info("No available sessions, retrying in 1 second.")
                time.sleep(1)
            else:
                logging.error("Unexpected status code: %d", response.status_code)
                time.sleep(1)
        except requests.RequestException as e:
            logging.error("Error in worker task: %s", e)
            time.sleep(1)
        except ValueError as e:
            logging.error("Error parsing JSON response: %s", e)
            time.sleep(1)


def main():
    # Start workers
    for _ in range(10):
        worker_task.delay()


if __name__ == "__main__":
    main()
