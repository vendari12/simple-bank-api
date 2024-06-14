import asyncio
import logging
from typing import Callable

# Hypothetical in-memory task queue
task_queue = asyncio.Queue()

# Function to enqueue a task
def enqueue_task(task: Callable):
    task_queue.put_nowait(task)

# Background task processor
async def process_tasks():
    while True:
        task = await task_queue.get()
        try:
            await task()
        except Exception as e:
            logging.error(f"Failed to process task: {e}")
        finally:
            task_queue.task_done()
