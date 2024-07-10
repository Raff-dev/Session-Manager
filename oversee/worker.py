import logging
import time

from celery import Celery

from oversee.constants import REDIS_URL, WORKER_JOB_DURATION
from oversee.session_manager_client import SessionManagerClient

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)

# Initialize Celery
app = Celery("worker", broker=REDIS_URL, backend=REDIS_URL)
app.config_from_object("oversee.celeryconfig")


@app.task
def worker_task():
    session = SessionManagerClient.get_session()
    logging.info("Worker using %s", session)
    time.sleep(WORKER_JOB_DURATION)  # Simulate job duration
    SessionManagerClient.release_session(session)
    logging.info("Worker releasing %s", session)
