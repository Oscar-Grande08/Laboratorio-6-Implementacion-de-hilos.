#imagen base
FROM python:3.11

#instalar dependencias del sistema para MediaPipe y OpenCV
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libatlas3-base \
    libjpeg-dev \
    libpng-dev \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    v4l-utils \
    libv4l-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

#directorio de trabajo
WORKDIR /app
#copiar dependencias
COPY requerimientos.txt .
#instalar dependencias de Python
RUN pip install --no-cache-dir -r requerimientos.txt
#copiar aplicacion
COPY . .
#exponer Streamlit
EXPOSE 8501
#ejecutar Streamlit
CMD ["streamlit", "run", "gestos.py", "--server.address=0.0.0.0"]
