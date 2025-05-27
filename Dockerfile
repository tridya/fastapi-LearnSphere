# Gunakan image Python resmi
FROM python:3.11-slim

# Set direktori kerja di container
WORKDIR /app

# Salin file ke container
COPY ./app /app
COPY requirements.txt .

# Install dependensi
RUN pip install --no-cache-dir -r requirements.txt

# Jalankan aplikasi FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
