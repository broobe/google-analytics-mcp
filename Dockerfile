FROM python:3.12-slim AS builder

WORKDIR /app
COPY pyproject.toml README.md ./
COPY analytics_mcp/ analytics_mcp/
RUN pip install --no-cache-dir .

FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin/analytics-mcp /usr/local/bin/analytics-mcp
COPY --from=builder /usr/local/bin/google-analytics-mcp /usr/local/bin/google-analytics-mcp

ENV PYTHONUNBUFFERED=1

COPY run_http.py /usr/local/bin/run_http.py

ENTRYPOINT ["analytics-mcp"]
