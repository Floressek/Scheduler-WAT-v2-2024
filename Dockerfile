# Use the official Python image from DockerHub
FROM python:3.12.6-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Define environment variables for Railway compatibility
ENV PYTHONPATH="/app:$PYTHONPATH"

# Create a working directory
WORKDIR /app

# Copy the requirements.txt first to leverage Docker's caching mechanism
COPY requirements.txt /app/

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . /app/

# Create the /storage directory
RUN mkdir /storage

# Expose port 5000 for Gunicorn
EXPOSE 5000

ENV OAUTHLIB_INSECURE_TRANSPORT=1
ENV FLASK_APP=src/app.py

# Run the Flask app with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "src.app:app"]