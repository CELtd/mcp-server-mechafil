# Dockerfile for MCP Server
FROM python:3.11-slim

WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies using uv
RUN uv pip install --system --no-cache fastmcp mcp pydantic requests

# Copy application files
COPY server.py ./
COPY system-prompt.txt ./
COPY documentation-and-instructions/ ./documentation-and-instructions/

# Expose port
EXPOSE 8080

# Set environment variables
ENV MCP_TRANSPORT=http
ENV PORT=8080
ENV MECHAFIL_SERVER_URL=https://mechafil-api.fly.dev

# Run the server
CMD ["python", "server.py"]
