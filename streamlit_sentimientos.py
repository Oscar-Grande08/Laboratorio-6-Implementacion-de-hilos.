import streamlit as st
from threading import Thread, Lock
from concurrent.futures import ThreadPoolExecutor
import time

# Diccionario de palabras 
positive_words = {"bueno", "excelente", "maravilloso", "encantó", "perfecto", "genial"}
negative_words = {"malo", "terrible", "horrible", "pésimo", "defectuoso"}

lock = Lock()

def analyze_sentiment(comment):
    """Clasifica el sentimiento del comentario."""
    words = comment.lower().split()
    sentiment = "neutral"

    if any(word in positive_words for word in words):
        sentiment = "positive"
    elif any(word in negative_words for word in words):
        sentiment = "negative"

    return comment, sentiment


def process_comments_parallel(comments, num_threads):
    """Aca se procesa comentarios en paralelo usando ThreadPoolExecutor."""
    results = []

    def thread_task(comment):
        # Procesar sentimiento
        comment_text, sentiment = analyze_sentiment(comment)

        # Proteger la escritura (evitando condiciones de carrera)
        with lock:
            results.append((comment_text, sentiment))

    # Pool de hilos
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        executor.map(thread_task, comments)

    return results

#STREAMLIT 

st.title("🧠 Análisis de Sentimientos con Hilos (Threading)")

st.subheader(" Ingresa los comentarios en el recuadro (uno por línea)")
text_input = st.text_area("Comentarios", height=400)

num_threads = st.slider("Número de hilos:", 1, 10, 3)

if st.button("Procesar"):
    if not text_input.strip():
        st.error("Por favor escribe al menos un comentario.")
    else:
        comments = [c.strip() for c in text_input.split("\n") if c.strip()]

        st.info("Procesando comentarios...")

        start_time = time.time()
        results = process_comments_parallel(comments, num_threads)
        end_time = time.time()

        st.success("Procesamiento completado :) ")

        st.write(f"Tiempo total: {end_time - start_time:.4f} segundos")
        
        # Mostrar resultados
        st.subheader(" Resultados del Análisis")
        st.table({"Comentario": [r[0] for r in results],
                  "Sentimiento": [r[1] for r in results]})
