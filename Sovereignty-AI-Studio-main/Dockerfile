FROM alpine:3.21
RUN apk add --no-cache python3 py3-pip tzdata git openssh
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir --break-system-packages -r requirements.txt
RUN mkdir -p /app/logs && chmod 700 /app/logs
ENV PYTHONUNBUFFERED=1
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1
CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]