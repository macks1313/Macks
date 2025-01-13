worker: python macks.py
web: python macks.py
web: gunicorn macks:app
web: gunicorn bot:app --worker-class aiohttp.worker.GunicornWebWorker
