FROM python:3.11-slim

RUN apt-get update \
    && apt-get install -y curl --no-install-recommends \
    && pip install --no-cache-dir ollama-mcp-bridge \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY mcp_config.json .
ENTRYPOINT ["ollama-mcp-bridge"]
CMD ["--config", "./mcp_config.json", "--host", "0.0.0.0"]