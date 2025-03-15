# Use the official Python image from the Docker Hub
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements.txt file into the container and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy additional required files into the container at /app
COPY .env .
COPY config.yaml .
COPY marcel_davis.py .

# Command to run the application
CMD ["python", "marcel_davis.py"]