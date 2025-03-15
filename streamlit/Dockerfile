# Stage 1: Builder Stage
FROM python:3.10-slim AS builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Development Stage
FROM python:3.10-slim AS development

WORKDIR /app

# Copy dependencies from builder stage
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Install watchdog for better file change detection
RUN pip install --no-cache-dir watchdog

EXPOSE 8501

# In development mode, code will be mounted as a volume
# Command runs Streamlit with auto-reloading enabled
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.runOnSave=true"]

# Stage 3: Production Stage
FROM python:3.10-slim AS production

WORKDIR /app

# Copy dependencies from builder stage
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]