import time

from oversee.constants import NUMBER_OF_WORKERS, WORKER_CREATION_DELAY
from oversee.worker import worker_task


def main():
    for _ in range(NUMBER_OF_WORKERS):
        worker_task.delay()
        time.sleep(WORKER_CREATION_DELAY)


if __name__ == "__main__":
    main()
