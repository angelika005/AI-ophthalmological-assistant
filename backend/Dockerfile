# ============================================
# Stage 1: Builder - Install dependencies
# ============================================
FROM python:3.11-slim AS builder

WORKDIR /app

ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install wheel
RUN python -m venv "$VIRTUAL_ENV" && \
    pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy requirements
COPY requirements.txt .

# Install Python dependencies (will be cached in a layer)
RUN pip install --no-cache-dir \
    --retries 10 \
    --timeout 120 \
    --trusted-host pypi.org \
    --trusted-host files.pythonhosted.org \
    -r requirements.txt

# Download ML model (pre-cache in builder for faster production builds)
RUN python -c "from transformers import AutoImageProcessor, Swinv2ForImageClassification; \
    AutoImageProcessor.from_pretrained('pamixsun/swinv2_tiny_for_glaucoma_classification'); \
    Swinv2ForImageClassification.from_pretrained('pamixsun/swinv2_tiny_for_glaucoma_classification')"

# ============================================
# Stage 2: Runtime - Minimal production image
# ============================================
FROM python:3.11-slim AS runtime

WORKDIR /app

# Install only runtime dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /root/.cache/huggingface /app/.cache/huggingface

# Set PATH for user packages
ENV VIRTUAL_ENV=/opt/venv \
    PATH=/opt/venv/bin:$PATH \
    HF_HOME=/app/.cache/huggingface \
    TRANSFORMERS_CACHE=/app/.cache/huggingface \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Copy application code
COPY . .

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser && \
    chown -R appuser:appuser /app

USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
