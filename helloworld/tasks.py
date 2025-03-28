from celery import shared_task

# This is a simple Celery task that simulates submitting a pipeline job.
# It takes a job ID as an argument and prints a message indicating that the job has been submitted.
# @shared_task
# def submit_pipeline_job(job_id):
#     print(f"[CELERY TASK] Job {job_id} submitted!")
#     return f"Job {job_id} acknowledged"

import os
import json
import redis
from django.conf import settings

# This Celery task handles the submission of a pipeline job.
# It generates a job file locally based on the provided job ID and pipeline data.
# The job file is saved in the specified directory.
# The task also handles any exceptions that may occur during the file writing process.
# @shared_task
# def submit_pipeline_job(job_id, pipeline_data):
#     job_file = os.path.join(settings.BASE_DIR, 'PersistentData', 'jobs', f'pipeline_{job_id}.json')
#     try:
#         with open(job_file, 'w') as f:
#             json.dump(pipeline_data, f, indent=2)
#         print(f"[CELERY TASK] Created job file for {job_id}")
#         return f"Job {job_id} enqueued and file created."
#     except Exception as e:
#         print(f"[CELERY TASK] Failed to write job file: {e}")
#         return f"Error creating job file: {str(e)}"
    

@shared_task
def submit_pipeline_job(job_id, pipeline_data):
    try:
        # Save pipeline JSON to jobs folder
        jobs_dir = os.path.join(settings.BASE_DIR, 'PersistentData', 'jobs')
        os.makedirs(jobs_dir, exist_ok=True)

        job_path = os.path.join(jobs_dir, f'pipeline_{job_id}.json')
        with open(job_path, 'w') as f:
            json.dump(pipeline_data, f, indent=2)

        print(f"[CELERY] Saved pipeline JSON for job {job_id} at {job_path}")

        # Push to Redis
        r = redis.StrictRedis(
            host="128.164.34.133",
            port=30036,
            password="password",
            decode_responses=True
        )

        job_payload = json.dumps({
            "job_id": job_id,
            "pipeline": pipeline_data
        })

        r.rpush("truespike_jobs", job_payload)
        print(f"[CELERY] ✅ Pushed job {job_id} to Redis")
        return f"✅ Job {job_id} pushed to Redis"

    except redis.exceptions.ConnectionError as conn_err:
        print(f"[ERROR] Redis connection error: {conn_err}")
        return f"❌ Failed to push job {job_id} to Redis"

    except redis.exceptions.RedisError as redis_err:
        print(f"[ERROR] Redis error: {redis_err}")
        return f"❌ Redis error for job {job_id}"

    except Exception as e:
        print(f"[ERROR] General error while handling job {job_id}: {e}")
        return f"❌ Unexpected error for job {job_id}"