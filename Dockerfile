# Stage 1: Builder Stage
FROM python:3.12-slim as builder
 
# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    libgl1 \
    build-essential && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
 
# Set working directory
WORKDIR /app
 
# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt
RUN pip3 install opencv-python-headless
# Stage 2: Production Stage
FROM python:3.12-slim
 
# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PATH=/root/.local/bin:$PATH
 
# Install necessary runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    \
    poppler-utils \
&& rm -rf /var/lib/apt/lists/* 
# Set working directory
WORKDIR /app
 
# Copy application code
COPY . .
RUN mkdir -p logs static
RUN apt-get update && apt-get install -y libgl1-mesa-glx
RUN wget https://github.com/PetrusNoleto/Error-in-install-cisco-packet-tracer-in-ubuntu-23.10-unmet-dependencies/releases/tag/CiscoPacketTracerFixUnmetDependenciesUbuntu23.10
RUN  dpkg -i libgl1-mesa-glx_23.0.4-0ubuntu1.22.04.1_amd64.deb=
RUN apt install -y libgl1
RUN apt update
RUN apt install -y libglx-mesa0
Copy only the installed dependencies from the builder stage
COPY --from=builder /root/.local /root/.local
 
# Ensure logs and static directories exist
 
# Expose the application port
EXPOSE 6321
 
# Command to run the application
CMD ["uvicorn", "fast_api:app", "--host", "0.0.0.0", "--port", "6321"]

# CMD ["gunicorn", "-w", "5", "-k", "uvicorn.workers.UvicornWorker", "fast_api:app", "--bind", "0.0.0.0:6321"]