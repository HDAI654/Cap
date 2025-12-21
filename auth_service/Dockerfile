# ---- Base Image ----
FROM python:3.11-slim

# ---- Environment ----
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# ---- Dependencies ----
RUN apt-get update && apt-get install -y \
    build-essential \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# ---- Workdir ----
WORKDIR /app

# ---- Install Requirements ----
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# ---- Copy Project ----
COPY . /app/

# ---- Entrypoint for waiting DB ----
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]

# ---- CMD ----
CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000"]
