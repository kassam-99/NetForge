# NetForge file-transfer server
# Standard-library-only service (Python 3.8+); no third-party runtime deps.
FROM python:3.12-slim

# Do not buffer stdout/stderr so logs stream out promptly, and don't write .pyc.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Copy the application source.
COPY . /app

# Create the runtime data/log directory and a non-root user that owns /app so
# the server can write uploads (FileServer/storage) and logs (FileServer/*.log).
RUN mkdir -p /app/FileServer/storage /app/reports \
    && useradd --create-home --uid 10001 appuser \
    && chown -R appuser:appuser /app

USER appuser

# TCP file-transfer port.
EXPOSE 8000

# Bind all interfaces on the fixed container port; the compose file / -p flag
# maps it to the host.
CMD ["python", "ServerDashboard.py", "--host", "0.0.0.0", "--port", "8000", "--verbose"]
