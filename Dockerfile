# Dockerfile
FROM python:3.10.12

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies (including PostgreSQL client)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the project files
COPY . .

# Expose the port
EXPOSE 8006