# General constants
SESSION_CREATION_DELAY = 1.5
SESSION_KEEP_ALIVE_DELAY = 60  # 1 minute
WORKER_JOB_DURATION = 10
WORKER_CREATION_DELAY = 0.1  # 1 second delay between creating workers
NUMBER_OF_WORKERS = 10

# Redis constants
REDIS_URL = "redis://redis:6379/0"

# Session manager URL and timeout
SESSION_MANAGER_URL = "http://session_manager:5000"
SESSION_MANAGER_TIMEOUT = 60  # Timeout in seconds

# Session manager constants
MAX_SESSIONS = 5
