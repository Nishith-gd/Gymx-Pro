"""
Gunicorn configuration for GymX Pro.

Usage:
    gunicorn "app:create_app()" --config gunicorn.conf.py

Override any setting with environment variables or CLI flags.
"""
import os
import multiprocessing

# ---------------------------------------------------------------------------
# Server socket
# ---------------------------------------------------------------------------
bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"
backlog = 2048

# ---------------------------------------------------------------------------
# Worker processes
# ---------------------------------------------------------------------------
# A common formula: (2 × CPU cores) + 1
workers = int(os.getenv('WEB_CONCURRENCY', multiprocessing.cpu_count() * 2 + 1))
worker_class = 'sync'   # use 'gevent' if you add gevent to requirements.txt
threads = 1
worker_connections = 1000

# ---------------------------------------------------------------------------
# Timeouts
# ---------------------------------------------------------------------------
timeout = 30
keepalive = 2
graceful_timeout = 30

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
accesslog = '-'     # stdout
errorlog  = '-'     # stderr
loglevel  = os.getenv('LOG_LEVEL', 'info')
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)sµs'

# ---------------------------------------------------------------------------
# Process naming
# ---------------------------------------------------------------------------
proc_name = 'gymx-pro'

# ---------------------------------------------------------------------------
# Security
# ---------------------------------------------------------------------------
# Limit request line and header size to reduce exposure to slow-loris / request-smuggling.
limit_request_line = 4096
limit_request_fields = 100
limit_request_field_size = 8190
