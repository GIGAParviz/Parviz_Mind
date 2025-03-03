import multiprocessing

# Bind to 0.0.0.0:5000
bind = "0.0.0.0:5000"

# Worker settings
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "gevent"
worker_connections = 1000
timeout = 300
keepalive = 2

# Server mechanics
daemon = False
loglevel = "info"
accesslog = "-"
errorlog = "-"

# Process naming
proc_name = "parviz-mind"
