from typing import Optional, Dict
import redis.asyncio as redis
from pydantic import BaseModel

# redis_client = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)