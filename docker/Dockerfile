FROM python:3.11-slim

WORKDIR /app

# copy requirements (root-level)
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# copy API code only
COPY api/ ./api

WORKDIR /app/api

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]