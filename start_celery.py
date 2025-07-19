#!/usr/bin/env python3
"""
Startup script for Celery worker and beat scheduler
"""

import subprocess
import sys
import os

def start_celery_worker():
    """Start the Celery worker"""
    print("Starting Celery worker...")
    subprocess.run([
        sys.executable, "-m", "celery", "-A", "app.celery", "worker",
        "--loglevel=info", "--pool=solo", "--concurrency=1"
    ])

def start_celery_beat():
    """Start the Celery beat scheduler"""
    print("Starting Celery beat scheduler...")
    subprocess.run([
        sys.executable, "-m", "celery", "-A", "app.celery", "beat",
        "--loglevel=info"
    ])

if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "worker":
            start_celery_worker()
        elif command == "beat":
            start_celery_beat()
        else:
            print("Usage: python start_celery.py [worker|beat]")
    else:
        print("Usage: python start_celery.py [worker|beat]")
        print("  worker - Start Celery worker")
        print("  beat   - Start Celery beat scheduler") 