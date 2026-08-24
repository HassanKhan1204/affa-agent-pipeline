# AFFA agent pipeline — Python container.
#
# Build:  docker build -t affa-pipeline .
# Run:    docker run --rm --env-file .env -v "$PWD":/app affa-pipeline
#         (or: docker compose run pipeline)
#
# The container has no entrypoint magic: it runs run_pipeline.sh by default,
# but any script can be run directly too, e.g.
#   docker compose run pipeline python funding_agent.py

FROM python:3.12-slim

WORKDIR /app

# Install dependencies first so this layer is cached across code changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x run_pipeline.sh

CMD ["./run_pipeline.sh"]
