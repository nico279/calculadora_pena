FROM python:3.11-slim

WORKDIR /app

# Copia e instala dependencias
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto del código
COPY app/ .

EXPOSE 5000

# *** EL CAMBIO CRUCIAL: Usa Gunicorn ***
# gunicorn --bind 0.0.0.0:PUERTO NOMBRE_DEL_ARCHIVO_SIN_PY:NOMBRE_DE_LA_VARIABLE_FLASK
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "main:app"]