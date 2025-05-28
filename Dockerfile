# Gunakan image Python resmi
FROM python:3.11-slim

# Set direktori kerja di container
WORKDIR /app

# Salin file ke container
COPY ./app /app/app
COPY ./main.py /app/main.py
COPY ./requirements.txt /app/requirements.txt
COPY ./school.db /app/data/school.db

# Install dependensi
RUN pip install --no-cache-dir -r requirements.txt

# Buat direktori untuk SQLite
RUN mkdir -p /app/data

# Tentukan volume untuk persistensi data
VOLUME /app/data

# Jalankan aplikasi FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]