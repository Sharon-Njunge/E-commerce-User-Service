# FROM python:3.11-slim

# WORKDIR /app

# # Install dependencies
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

# # Copy all code
# COPY . .

# # Set environment variable for Django
# ENV PYTHONPATH=/app

# EXPOSE 8000

# # Gunicorn command
# CMD ["gunicorn", "auth_service.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2"]


# Use official Python image
# Use official Python image
FROM python:3.11-slim

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1


# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . /app/

# Collect static files (correct path)
RUN python manage.py collectstatic --noinput
# RUN python manage.py collectstatic --noinput


# Expose port
EXPOSE 8000

# Run the app with Gunicorn
CMD ["gunicorn", "auth_service.wsgi:application", "--bind", "0.0.0.0:8000"]
