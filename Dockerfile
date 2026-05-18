FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=7860

WORKDIR /app

COPY requirements-space.txt ./
RUN pip install --no-cache-dir -r requirements-space.txt

RUN mkdir -p /app/data

COPY src ./src
COPY infra ./infra
COPY data/so_ky_hieu_lookup.json ./data/so_ky_hieu_lookup.json
COPY data/short_title_mapping.json ./data/short_title_mapping.json
COPY README.md ./

EXPOSE 7860

CMD ["sh", "-c", "uvicorn infra.api.app:app --host 0.0.0.0 --port ${PORT:-7860}"]
