# Use the official Python 3.12 image from the Docker Hub
FROM python:3.12-slim

# Install Poetry
RUN pip install --upgrade pip && pip install poetry

# Set the working directory in the container
WORKDIR /app

# Copy the pyproject.toml and poetry.lock files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry config virtualenvs.create false && poetry install --no-root

# Copy the rest of the application code into the container
COPY oversee .
