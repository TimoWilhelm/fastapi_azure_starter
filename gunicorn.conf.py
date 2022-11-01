import multiprocessing

from app import settings

workers = multiprocessing.cpu_count() * 2 + 1

loglevel = settings.LOG_LEVEL
