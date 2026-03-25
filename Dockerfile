FROM python:3.13-slim-bookworm

WORKDIR /app


COPY requirements/requirements.txt requirements/requirements.txt
RUN pip install --no-cache-dir -r requirements/requirements.txt

COPY src/ ./src/
COPY .env .env

# dont forget to remove this when deploying
# can cause skipping cloud run's health check

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8001

ENTRYPOINT ["/entrypoint.sh"]
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "1"]
