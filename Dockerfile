#imagen base con Python
FROM python:3.11
#instalar dependencias necesarias para Pygame y  multimedia
RUN apt-get update && apt-get install -y \
    python3-dev \
    libsdl2-dev \
    libsdl2-image-dev \
    libsdl2-mixer-dev \
    libsdl2-ttf-dev \
    libportmidi-dev \
    libx11-6 \
    libxext6 \
    libxrender1 \
    libxrandr2 \
    libfreetype6-dev \
    libavformat-dev \
    libswscale-dev \
    libjpeg-dev \
    libpng-dev \
    libsm6 \
    x11-apps \
    && rm -rf /var/lib/apt/lists/*

#configuración para usar X11 (VISUALIZACION)
ENV DISPLAY=${DISPLAY}
#directorio de trabajo
WORKDIR /app
#copiar dependencias de Python
COPY requerimientos.txt .

#instalar dependencias de Python
RUN pip install --no-cache-dir -r requerimientos.txt

#copiar el código del juego
COPY . .

#comando por defecto para iniciar el juego
CMD ["python3", "JuegoMarioBross.py"]
