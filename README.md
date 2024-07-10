# Oversee

## Overview

Oversee is a session manager for a flight reservation system API. It manages a pool of sessions that can be reused by multiple worker processes, helping to save time and reduce costs associated with session creation and closure.

## Features

- Session pooling
- Session reuse between worker jobs
- Heartbeat mechanism to monitor session health
- Graceful handling of session and manager failures
- Distributed locking using Redis and Redlock

## Getting Started

### Prerequisites

- Docker
- Docker Compose

### Running the Project

1. Build the Docker images and start the services:

    ```bash
    docker-compose up --build
    ```

3. The worker processes will automatically start and connect to the session manager.
