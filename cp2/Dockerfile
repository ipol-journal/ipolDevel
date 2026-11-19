FROM python:3.12-slim

# Install uv globally
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set workdir
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install python dependencies globally
RUN uv pip install --system -r pyproject.toml

# Copy project files
COPY . .

# Expose port
EXPOSE 8002


# Run gunicorn directly in the ControlPanel directory where wsgi is
WORKDIR /app/ControlPanel
CMD ["gunicorn", "--bind", "0.0.0.0:8002", "ControlPanel.wsgi", "--workers", "3", "--log-level=debug"]
