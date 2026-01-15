FROM python:3.11-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates \
 && rm -rf /var/lib/apt/lists/*

COPY config/intermediate.crt /usr/local/share/ca-certificates/intermediate.crt
RUN update-ca-certificates
RUN pip install --upgrade certifi \
 && cat /usr/local/share/ca-certificates/intermediate.crt >> $(python -c "import certifi; print(certifi.where())")

COPY requirements.txt .
RUN apt-get update \
    && apt-get install -y curl --no-install-recommends \
    && pip install --no-cache-dir -r requirements.txt \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

CMD ["python", "/app/mcp_newarp.py"]