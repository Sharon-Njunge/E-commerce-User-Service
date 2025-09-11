FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# This keeps FastAPI running indefinitely
# CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
CMD ["uvicorn", "src.routes.main:app", "--host", "0.0.0.0", "--port", "8000"]
