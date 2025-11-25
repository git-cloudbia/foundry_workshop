# Usamos una imagen base oficial de Python ligera
FROM python:3.10-slim

# Establecemos el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiamos los archivos de requerimientos e instalamos dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el código del agente y la aplicación
COPY agente_financiero.py .
COPY app.py .
COPY .env .

# Creamos el directorio para los checkpoints (si usa almacenamiento de archivos local)
RUN mkdir -p /app/data/checkpoints

# Exponemos el puerto para FastAPI
EXPOSE 8000

# Comando para ejecutar el servidor web con uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]