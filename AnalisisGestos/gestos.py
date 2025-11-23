"""
streamlit_gestures.py
Detector de gestos con MediaPipe + Streamlit usando hilos, semáforo y mutex.
Controles:
 - Abre la app web (streamlit run streamlit_gestures.py)
 - Start/Stop captura desde la UI.
"""
import streamlit as st
import cv2
import mediapipe as mp
import threading
import time
import numpy as np
from collections import deque

# -----------------------------
# CONFIGURACIÓN UI / GLOBALS
# -----------------------------
st.set_page_config(page_title="Detector de Gestos (MediaPipe + Hilos)", layout="wide")

# Shared state (seguro por mutex)
shared_frame = None           # frame BGR (world coordinates)
shared_frame_lock = threading.Lock()   # <--- MUTEX (Lock) que protege acceso a shared_frame

# Semaphore que indica "hay frame disponible para procesar"
frame_semaphore = threading.Semaphore(0)   # <--- SEMÁFORO

# Cola simple para últimos resultados (no crítica pero protegida por lock)
result_lock = threading.Lock()
latest_result = {"gesture": None, "score": 0.0}

# Flags de control
capture_running = False
capture_thread_obj = None
process_thread_obj = None

# Buffer para mostrar FPS y estabilidad
frame_times = deque(maxlen=20)

# MediaPipe tools (creadas dentro del hilo de procesado para evitar freeze en import)
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

# -----------------------------
# FUNCIÓN: heurísticas simples de gesto
# Usa landmarks de MediaPipe Hands para determinar gesto.
# -----------------------------
def finger_is_up(hand_landmarks, finger_tip, finger_pip):
    """Devuelve True si la punta del dedo (tip) está por encima (en y menor) que el pip (en coordenadas normalizadas)."""
    return hand_landmarks.landmark[finger_tip].y < hand_landmarks.landmark[finger_pip].y

def classify_basic_gesture(hand_landmarks):
    """
    Clasificación rápida (heurística) para gestos:
    - THUMBS_UP: pulgar arriba, otros dedos doblados
    - THUMBS_DOWN: pulgar abajo, otros doblados
    - VICTORY: index y middle arriba
    - OPEN_PALM: todos arriba
    - FIST: ninguno arriba
    - WAVE: muchos dedos arriba (se usa OPEN_PALM como proxy)
    - ROCK/LOVE: index + pinky arriba (approx -> 'rock')
    """
    # indices landmarks (MediaPipe)
    TIP = {"thumb": 4, "index": 8, "middle": 12, "ring": 16, "pinky": 20}
    PIP = {"thumb": 2, "index": 6, "middle": 10, "ring": 14, "pinky": 18}

    # check fingers up
    thumb_up = hand_landmarks.landmark[TIP["thumb"]].x < hand_landmarks.landmark[PIP["thumb"]].x and \
               abs(hand_landmarks.landmark[TIP["thumb"]].y - hand_landmarks.landmark[PIP["thumb"]].y) < 0.12
    # For simplicity, consider thumb horizontal direction + small y difference; robust solutions use vectors.

    index_up = finger_is_up(hand_landmarks, TIP["index"], PIP["index"])
    middle_up = finger_is_up(hand_landmarks, TIP["middle"], PIP["middle"])
    ring_up = finger_is_up(hand_landmarks, TIP["ring"], PIP["ring"])
    pinky_up = finger_is_up(hand_landmarks, TIP["pinky"], PIP["pinky"])

    up_count = sum([thumb_up, index_up, middle_up, ring_up, pinky_up])

    # Heurísticas:
    if up_count == 0:
        return "FIST", 0.9
    if index_up and middle_up and not ring_up and not pinky_up:
        return "VICTORY", 0.95
    if thumb_up and not index_up and not middle_up:
        return "THUMBS_UP", 0.9
    if (not thumb_up) and index_up and not middle_up and not ring_up and pinky_up:
        return "ROCK", 0.9
    if up_count >= 4:
        return "OPEN_PALM", 0.9
    # fallback
    return ("UNKNOWN", 0.5)

# -----------------------------
# HILO 1: captura de frames desde la cámara (producer)
# - Lee cv2.VideoCapture(0)
# - Escribe en shared_frame (sección crítica protegida por shared_frame_lock)
# - Llama frame_semaphore.release() para avisar al procesador
# -----------------------------
def camera_capture_thread(device=0, width=640, height=480):
    global capture_running, shared_frame
    cap = cv2.VideoCapture(device)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    if not cap.isOpened():
        st.error("No se pudo abrir la cámara (verifique /dev/video0 o permissions).")
        capture_running = False
        return

    while capture_running:
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.01)
            continue

        # Guardar frame en sección crítica
        with shared_frame_lock:   # <-- sección crítica protegida por mutex
            shared_frame = frame.copy()
        # Señalamos que hay frame nuevo
        try:
            frame_semaphore.release()
        except ValueError:
            # si semáforo está en un estado raro, ignorar
            pass

        # pequeño sleep para limitar FPS de captura
        time.sleep(0.01)
    cap.release()

# -----------------------------
# HILO 2: procesador (consumer)
# - Espera frame_semaphore.acquire() → indica que hay frame nuevo
# - Copia el frame desde shared_frame (sección crítica protegida)
# - Ejecuta MediaPipe Hands y clasificación heurística
# - Guarda resultado en latest_result (sección crítica protected por result_lock)
# -----------------------------
def processing_thread():
    global capture_running, latest_result, frame_times
    # Crear el objeto MediaPipe Hands (se ejecuta en este hilo)
    hands = mp_hands.Hands(static_image_mode=False,
                           max_num_hands=2,
                           min_detection_confidence=0.5,
                           min_tracking_confidence=0.5)
    try:
        while capture_running:
            # Esperar señal de que hay frame
            frame_semaphore.acquire()

            # Copiar frame de la zona crítica
            with shared_frame_lock:
                frame_copy = None if shared_frame is None else shared_frame.copy()

            if frame_copy is None:
                continue

            t0 = time.time()
            image_rgb = cv2.cvtColor(frame_copy, cv2.COLOR_BGR2RGB)
            results = hands.process(image_rgb)

            gesture_name = "NO_HAND"
            score = 0.0
            annotated = frame_copy.copy()

            if results.multi_hand_landmarks:
                # Tomamos la primera mano detectada para clasificación simple
                hand_landmarks = results.multi_hand_landmarks[0]
                # Clasificar por heurística usando landmarks normalizados
                g_name, g_score = classify_basic_gesture(hand_landmarks)
                gesture_name = g_name
                score = g_score

                # Dibujar landmarks en la imagen
                mp_drawing.draw_landmarks(annotated, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            # Guardar resultado en sección crítica (result_lock)
            with result_lock:
                latest_result["gesture"] = gesture_name
                latest_result["score"] = score
                latest_result["image"] = annotated

            # actualizar FPS buffer
            frame_times.append(time.time() - t0)

            # small throttle
            time.sleep(0.005)
    finally:
        hands.close()

# -----------------------------
# FUNCIONES DE UI
# -----------------------------
def start_capture(device=0):
    global capture_running, capture_thread_obj, process_thread_obj
    if capture_running:
        return
    capture_running = True
    # Hilo de captura (Thread: producer)
    capture_thread_obj = threading.Thread(target=camera_capture_thread, args=(device,), daemon=True)
    capture_thread_obj.start()
    # Hilo de procesamiento (Thread: consumer)
    process_thread_obj = threading.Thread(target=processing_thread, daemon=True)
    process_thread_obj.start()

def stop_capture():
    global capture_running
    capture_running = False
    # Semaforo release para desbloquear process thread si está esperando
    try:
        frame_semaphore.release()
    except:
        pass

# -----------------------------
# STREAMLIT LAYOUT
# -----------------------------
st.title("🔮 Detector de Gestos con MediaPipe + Hilos")
col1, col2 = st.columns([2, 1])

with col1:
    # panel de video
    stframe = st.image(np.zeros((480, 640, 3), dtype=np.uint8), channels="BGR")
    if st.button("Start Capture"):
        start_capture(device=0)
    if st.button("Stop Capture"):
        stop_capture()

with col2:
    st.markdown("### Estado")
    g_text = st.empty()
    st.markdown("### Estadísticas")
    fps_box = st.empty()
    st.markdown("### Controles")
    st.write(" - Ajusta parámetros en el código si necesitas.")
    st.write("Semáforo usado para sincronizar frames. Lock protege shared_frame y latest_result.")

# Loop principal de la UI: muestra frame procesado y resultado
while True:
    # Leer resultado de forma segura
    with result_lock:
        res = dict(latest_result)  # copia
    if res.get("image") is not None:
        stframe.image(res["image"], channels="BGR")
    gesture = res.get("gesture", "NO_HAND")
    score = res.get("score", 0.0)
    g_text.markdown(f"**Gesto:** {gesture}  \n**Confianza:** {score:.2f}")

    # Mostrar FPS estimado del procesamiento
    if len(frame_times) > 0:
        avg_dt = sum(frame_times) / len(frame_times)
        fps_box.markdown(f"FPS (proc): {1.0/avg_dt:.1f}")
    else:
        fps_box.markdown("FPS (proc): -")

    # Small sleep to avoid locking UI thread too hard
    time.sleep(0.03)

# Nota: La app se cierra con Ctrl+C en terminal o deteniendo Streamlit.
