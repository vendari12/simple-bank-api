import multiprocessing

from server.utils.constants import SERVICE_PORT

bind = f"0.0.0.0:{SERVICE_PORT}"
timeout = 120
worker_class = "uvicorn.workers.UvicornWorker"
workers = multiprocessing.cpu_count()
