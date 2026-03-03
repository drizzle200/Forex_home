# Stage 1: Build the Application
FROM python:3.11 AS build

# Set the working directory
WORKDIR /usr/src/app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements.txt
COPY requirements.txt ./requirements.txt

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy the rest of the application
COPY . .

# Stage 2: Create the Final Production Image
FROM python:3.11

# Set the working directory
WORKDIR /usr/src/app

# Copy the virtual environment
COPY --from=build /opt/venv /opt/venv

# Copy the application code
COPY --from=build /usr/src/app .

# Set the virtual environment as active
ENV PATH="/opt/venv/bin:$PATH"

# Create volume for SQLite database
VOLUME /data

# Create a non-root user
RUN useradd -m -u 1000 appuser && \
    mkdir -p /data /usr/src/app/staticfiles && \
    chown -R appuser:appuser /usr/src/app /data
USER appuser

# Collect static files (THIS IS THE KEY LINE YOU WERE MISSING)
RUN python manage.py collectstatic --noinput

# Expose the port
ENV PORT=8080
EXPOSE $PORT

# Run migrations and start gunicorn (NOT python app.py)
CMD python manage.py migrate --noinput && \
    gunicorn tradingfx.wsgi:application --bind 0.0.0.0:8080
