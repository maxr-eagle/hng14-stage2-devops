import redis
import time
import os
import signal
import sys

r = redis.Redis(
    host=os.getenv("REDIS_HOST", "redis"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    password=os.getenv("REDIS_PASSWORD", None),
    decode_responses=True
)


def handle_shutdown(signum, frame):
    print("Shutdown signal received, exiting cleanly...")
    sys.exit(0)


signal.signal(signal.SIGTERM, handle_shutdown)
signal.signal(signal.SIGINT, handle_shutdown)


def wait_for_redis():
    while True:
        try:
            r.ping()
            print("Connected to Redis")
            break
        except redis.exceptions.ConnectionError:
            print("Waiting for Redis...")
            time.sleep(2)


def process_job(job_id):
    print(f"Processing job {job_id}")
    try:
        time.sleep(2)
        r.hset(f"job:{job_id}", "status", "completed")
        print(f"Done: {job_id}")
    except Exception as e:
        print(f"Failed to process job {job_id}: {e}")
        try:
            r.hset(f"job:{job_id}", "status", "failed")
        except Exception:
            print(f"Could not update status for job {job_id}")


wait_for_redis()

while True:
    try:
        job = r.brpop("jobs", timeout=5)
        if job:
            _, job_id = job
            process_job(job_id)
    except redis.exceptions.ConnectionError as e:
        print(f"Redis connection error: {e}. Retrying in 5 seconds...")
        time.sleep(5)
    except Exception as e:
        print(f"Unexpected error: {e}")
        time.sleep(1)
        