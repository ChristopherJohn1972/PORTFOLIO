FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY portfolio-api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY portfolio-api/ .

RUN DJANGO_SECRET_KEY=build-time-placeholder python manage.py collectstatic --noinput 2>/dev/null || true

COPY portfolio-api/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

EXPOSE 8000

CMD ["/app/entrypoint.sh"]
