# Build stage
FROM python:3.12-slim as builder

WORKDIR /app

COPY requirements.txt .

# Install dependencies into a virtual environment
RUN python -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"
RUN pip install --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.12-slim

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

# Copy source code
COPY src ./src

# Create a non-root user
RUN useradd -m appuser && chown -R appuser /app
USER appuser

# Expose port (LM Studio connects to this)
EXPOSE 8000

# Set environment variables for potential configuration
ENV PYTHONUNBUFFERED=1

# Run the server via python script to leverage mcp.run() or custom startup logic
CMD ["python", "src/server.py"]
