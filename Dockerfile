# Dockerfile
FROM python:latest

WORKDIR /app

# Copy and install dependencies
COPY ./requirements.txt /app
RUN pip install --upgrade pip && pip install -r requirements.txt --no-cache-dir

# Copy the rest of the code
COPY . /app
# Set work directory

# Default command (can be overridden by docker-compose)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
