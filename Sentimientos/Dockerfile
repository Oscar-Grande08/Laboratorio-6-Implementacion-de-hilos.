# Imagen base oficial de Python
FROM python:3.11-slim

# Crear un directorio dentro del contenedor
WORKDIR /Sentimientos

# Copiar los archivos de dependencias
COPY requirements.txt .

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del proyecto
COPY . .

# Exponer el puerto donde corre Streamlit
EXPOSE 8501

# Comando para ejecutar Streamlit
CMD ["streamlit", "run", "streamlit_sentimientos.py", "--server.port=8501", "--server.address=0.0.0.0"]
