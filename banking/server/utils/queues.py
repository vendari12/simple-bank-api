import asyncio
from typing import Callable
from typing import  Optional
from threading import Lock
from rq import Queue
from .cache import get_sync_redis_client

class QueueManager:
    _queue: Optional[Queue] = None
    _lock: Lock = Lock()

    @classmethod
    def get_queue(cls) -> Queue:
        """Get a shared redis queue instance.
        
        Initializes the queue if it hasn't been created yet.
        
        Returns:
            Queue: The shared settings queue instance.
        """
        if cls._queue is None:
            with cls._lock:
                if cls._queue is None:
                    cls._queue = Queue(get_sync_redis_client())  # Replace with actual initialization logic as needed
        return cls._queue
    

def async_to_sync_wrapper(func: Callable, *args, **kwargs):
    loop = asyncio.get_event_loop()
    if asyncio.iscoroutine(func):
        loop.run_until_complete(func(*args, **kwargs))
    else:
        func(*args, **kwargs)
    

    
async def enqueue_task(func: Callable, **kwargs):
    queue = QueueManager.get_queue()
    return queue.enqueue(async_to_sync_wrapper, func, **kwargs)