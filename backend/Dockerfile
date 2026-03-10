# Use Python 3.12 slim image for a smaller footprint
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies needed for compiling certain python packages
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file first for better caching
COPY farmxpert/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the application code
# We copy the inner farmxpert directory because the main app runs from within there
COPY farmxpert/ ./farmxpert/

# We also need to copy the alembic config and migrations
COPY alembic/ ./alembic/
COPY alembic.ini .

# Expose the API port
EXPOSE 8000

# Command to run the application using uvicorn
CMD ["uvicorn", "farmxpert.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
