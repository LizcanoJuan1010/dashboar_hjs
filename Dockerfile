FROM python:3.9-slim

WORKDIR /app

# Install system dependencies for psycopg2 and pdfplumber/mupdf if needed
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy ETL Scripts
COPY etl/extract_divipole.py .
COPY etl/generar_dim_grupos.py .
COPY etl/load_censo.py .
COPY etl/load_empresas.py .
COPY etl/load_empleados.py .
COPY etl/load_hjs.py .
COPY etl/inspect_excel.py .
COPY etl/load_seguimiento.py .
COPY etl/load_representantes.py .
COPY etl/load_relaciones.py .

CMD ["python", "extract_divipole.py"]
