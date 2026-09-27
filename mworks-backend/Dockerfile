FROM python:3.12.8-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN adduser --disabled-password --gecos "" --uid 10001 appuser

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY scripts ./scripts
RUN chmod +x /app/scripts/entrypoint.sh /app/scripts/gen_jwt_keys.sh \
    && mkdir -p /app/secrets \
    && chown -R appuser:appuser /app

USER appuser
EXPOSE 8000
HEALTHCHECK --interval=20s --timeout=5s --retries=5 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=4)"
ENTRYPOINT ["/app/scripts/entrypoint.sh"]
