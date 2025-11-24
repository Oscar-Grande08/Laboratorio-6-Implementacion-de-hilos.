# Laboratorio-6-Implementacion-de-hilos.
##📝 Introducción##

Este proyecto compila el desarrollo de tres ejercicios enfocados en la comprensión, implementación y despliegue de aplicaciones que utilizan concurrencia, procesamiento en tiempo real y contenedorización mediante Docker. A lo largo del trabajo, se integraron principios fundamentales de sistemas operativos, programación concurrente, visión por computadora y orquestación de servicios, con el fin de obtener soluciones robustas, reproducibles y ejecutables en diferentes entornos.

🎮 1. Videojuego en Python con concurrencia

En el primer ejercicio se desarrolló un videojuego estilo plataforma utilizando Pygame, al cual se le incorporaron:

Hilos (threads) para ejecutar tareas en paralelo.

Semáforos y mutex para controlar el acceso a recursos compartidos.

Secciones críticas debidamente protegidas para evitar condiciones de carrera.

Además, se integraron procesos adicionales como un módulo de análisis alterno que corría concurrentemente con la lógica del juego.
Este ejercicio permitió evidenciar cómo la concurrencia afecta el flujo de ejecución y cómo sincronizar tareas dentro de un programa interactivo.

Posteriormente, el videojuego fue empaquetado en Docker y configurado para ejecutarse con soporte gráfico mediante X11, abordando retos como:

Dependencias para SDL y Pygame

Soporte de aceleración gráfica

Manejo de drivers y librerías de entorno de escritorio

Configuración de volúmenes para interacción con el host

🤖 2. Aplicación de reconocimiento de gestos con Streamlit

En el segundo ejercicio se implementó una aplicación web interactiva que:

Capta video desde la cámara en tiempo real.

Procesa las imágenes mediante MediaPipe y OpenCV.

Reconoce gestos o posiciones de manos.

Renderiza resultados en una interfaz construida con Streamlit.

La aplicación fue contenerizada y optimizada dentro de Docker, lo que implicó:

Instalación manual de dependencias del sistema para MediaPipe.

Configuración de acceso al dispositivo de video dentro del contenedor.

Ajuste de permisos, drivers V4L2 y librerías multimedia.

Ejecución del servidor Streamlit mediante docker-compose.

Este ejercicio permitió cubrir temas avanzados relacionados con dispositivos de hardware desde contenedores, manipulación de flujos de video y despliegue de aplicaciones web interactivas.

🐳 3. Construcción y Debugging de Imágenes Docker Complejas

A lo largo del proyecto, se resolvieron problemas reales y frecuentes al construir imágenes:

Paquetes obsoletos en Debian.

Errores de timeout al instalar dependencias Python.

Manejo de capas para reducir el tamaño de la imagen.

Control de versiones en docker-compose.

Permisos para acceder a X11, cámara, audio y dispositivo GPU.

Se aplicaron buenas prácticas como:

Minimizar dependencias innecesarias.

Limpiar cachés para reducir peso de la imagen.

Uso adecuado de volumes, networks y modos de ejecución.

Separación clara entre entorno de desarrollo y entorno de ejecución.

📌 Objetivo General

El objetivo de este proyecto fue integrar conceptos avanzados de concurrencia, multimedia y despliegue de software en contenedores, logrando aplicaciones funcionales y portables que puedan ejecutarse en diferentes máquinas sin necesidad de instalar entornos complejos.

🧱 ¿Qué aporta este proyecto?

Comprensión práctica de la programación concurrente.

Integración real de aplicaciones multimedia en tiempo real.

Capacidad de contenerizar sistemas que requieren GUI, cámara o aceleración gráfica.

Manejo profundo de debugging en Docker.

Despliegue de aplicaciones web interactivas con visión por computadora.
