# Use the official Python image from the Docker Hub
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# temporarily load requirements file as bind to install reqs. only copied for this single run instruction
RUN --mount=type=bind,source=requirements.txt,target=/tmp/requirements.txt \
    pip install --requirement /tmp/requirements.txt
# Copy the requirements.txt file first to leverage Docker cache
# COPY requirements.txt .

# # Install the required packages
# RUN pip install --no-cache-dir -r requirements.txt

# Copy the necessary folders into the /app directory
COPY ./src ./src
COPY ./conf ./conf
COPY ./data ./data

WORKDIR /app/src
# Command to run the application
CMD ["python", "marcel_davis.py"]