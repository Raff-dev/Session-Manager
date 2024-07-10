import redis
from flask import Flask
from redlock import Redlock

from oversee.constants import REDIS_URL

app = Flask(__name__)

# Initialize Redis
redis_client = redis.StrictRedis.from_url(REDIS_URL)
redlock = Redlock([REDIS_URL])

# Import routes
import oversee.views
