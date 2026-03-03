ARG PYTHON_VERSION=3.11-slim

FROM python:${PYTHON_VERSION}

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install psycopg2 dependencies.
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create app directory for code (not the volume mount point)
RUN mkdir -p /app
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt /tmp/requirements.txt
RUN set -ex && \
    pip install --upgrade pip && \
    pip install -r /tmp/requirements.txt && \
    rm -rf /root/.cache/

# Copy the rest of the application code to /app
COPY . /app

# Create directory for persistent data (will be mounted as volume)
RUN mkdir -p /data

# Use build arg for collectstatic (dummy value, actual secret comes from env)
ARG SECRET_KEY=dummy-value-for-collectstatic
ENV SECRET_KEY=$SECRET_KEY
RUN python manage.py collectstatic --noinput

EXPOSE 8000

# Use shell form to allow environment variable substitution
CMD gunicorn tradingfx.wsgi:application --bind :8000 --workers 2