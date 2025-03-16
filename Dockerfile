# Use the official Python image from the Docker Hub
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the required files to the image
COPY .env .
COPY config.yaml .
COPY cache.json .
COPY marcel_davis.py .
COPY requirements.txt .

# install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Command to run the application
CMD ["python", "marcel_davis.py"]