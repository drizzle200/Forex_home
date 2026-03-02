# Stage 1: Build the Application
FROM python:3.11 AS build

# Set the working directory inside the container
WORKDIR /usr/src/app

# Install system dependencies if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements.txt (fixed the wildcard)
COPY requirements.txt ./requirements.txt

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy the rest of the application source code
COPY . .

# Stage 2: Create the Final Production Image
FROM python:3.11

# Set the working directory
WORKDIR /usr/src/app

# Copy the virtual environment from the build stage
COPY --from=build /opt/venv /opt/venv

# Copy the application code
COPY --from=build /usr/src/app .

# Set the virtual environment as the active Python environment
ENV PATH="/opt/venv/bin:$PATH"

# Create volume for SQLite database
VOLUME /data

# Create a non-root user to run the application
RUN useradd -m -u 1000 appuser && \
    mkdir -p /data && \
    chown -R appuser:appuser /usr/src/app /data
USER appuser

# Expose the port your app runs on
ENV PORT=8080
EXPOSE $PORT

# FIXED: Run gunicorn for Django, NOT python app.py
CMD gunicorn tradingfx.wsgi:application --bind 0.0.0.0:$PORT
