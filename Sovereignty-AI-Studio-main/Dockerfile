FROM alpine:3.21
RUN apk add --no-cache python3 py3-pip tzdata git openssh
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
RUN mkdir -p /app/logs && chmod 700 /app/logs
ENV PYTHONUNBUFFERED=1
EXPOSE 9898
CMD ["python3", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9898"]