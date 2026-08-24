# AFFA CRM API — FastAPI + SQLAlchemy, served with uvicorn.
#
# Build:  docker build -t affa-backend .
# Run:    docker run --rm -p 8000:8000 --env-file ../.env affa-backend
#         (or: docker compose up backend)

FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
