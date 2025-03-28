FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install uv
RUN pip install uv

# Copy only dependency definition files first for caching
COPY pyproject.toml ./

# Install dependencies using uv
# Use --system to install globally in the container image, common for Docker
RUN uv pip install --system ".[dev]"

# Copy the rest of the application code
COPY . .

# Expose the port the app runs on (adjust if needed)
EXPOSE 8001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
