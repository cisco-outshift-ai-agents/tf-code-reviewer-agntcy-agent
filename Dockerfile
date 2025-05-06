# Python base image
FROM python:3.12-slim

WORKDIR /workspace

# Install system dependencies (add Rust here)
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    libssl-dev \
    gcc \
    pkg-config \
    git \
    && curl https://sh.rustup.rs -sSf | sh -s -- -y \
    && . "$HOME/.cargo/env" \
    && export PATH="$HOME/.cargo/bin:$PATH"

# Set env path so Cargo is available in pip builds
ENV PATH="/root/.cargo/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy setup.py and install project in editable mode
COPY setup.py .
COPY app/ ./app/
COPY client/ ./client/
COPY tests/ ./tests/
COPY agent_workflow_server ./agent_workflow_server/
COPY pytest.ini .

RUN pip install -e .

ENV PYTHONPATH=/workspace

EXPOSE 8123

CMD ["python", "app/main.py"]