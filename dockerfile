# Use the official Python image from the Docker Hub
FROM python:3.11-slim

#intall dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*


# Copy the requirements file into the container
COPY . /usr/app/

# Set the working directory in the container
WORKDIR /usr/app/

COPY requirements.txt .

# Install the dependencies
RUN pip install -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Command to run the application
CMD ["python", "discordbot.py"]