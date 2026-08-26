FROM python:3.11-slim

WORKDIR /app

# Install uv (fast Python package manager)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy project definition first for better layer caching
COPY mcp-server/pyproject.toml ./
COPY mcp-server/mcp_server ./mcp_server

# Install dependencies and the package itself (editable)
RUN uv sync --no-dev

# Directory for generated invoices
RUN mkdir -p /app/invoices

EXPOSE 9911

CMD ["uv", "run", "financial-mcp"]
