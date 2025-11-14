import streamlit as st
from threading import Lock
from concurrent.futures import ThreadPoolExecutor
import string
import time

# Diccionario de palabras
positive_words = {"bueno", "excelente", "maravilloso", "genial", "fantástico", "encantó", "buenisimo", "lindo", "bonito"}
negative_words = {"malo", "terrible", "horrible", "pésimo", "desastre","malisimo", "horrendo", "feo"}
# Lock para evitar condiciones de carrera
lock = Lock()

# Funciones de analisis
def clean_text(text):
    """Limpia puntuación y pone todo en minúscula."""
    return text.lower().translate(str.maketrans("", "", string.punctuation))

def analyze_comment(comment):
    """Analiza un solo comentario y retorna el sentimiento."""
    words = clean_text(comment).split()
    sentiment = "neutral"
    if any(word in positive_words for word in words):
        sentiment = "positive"
    elif any(word in negative_words for word in words):
        sentiment = "negative"
    return (comment, sentiment)

def process_comments_parallel(comments, chunk_size, num_threads):
    """Aca procesa comentarios en paralelo en chunks usando ThreadPoolExecutor y Lock."""
    results = []

    # Buscar dividir en chunks
    chunks = [comments[i:i+chunk_size] for i in range(0, len(comments), chunk_size)]

    def process_chunk(chunk):
        local_results = []
        for comment in chunk:
            local_results.append(analyze_comment(comment))
        # Guardarlos resultados globales con Lock
        with lock:
            results.extend(local_results)

    # Ejecutar cada chunk en paralelo con hilos
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        executor.map(process_chunk, chunks)

    return results

# Streamlit UI

st.title("Análisis de Sentimientos en Paralelo (Threading)")

st.write("Ingresa varios comentarios separados por líneas. La app procesará los comentarios en paralelo.")

text_input = st.text_area("Comentarios", height=800)
num_threads = st.slider("Número de hilos:", 1, 10, 3)
chunk_size = st.slider("Tamaño de cada chunk:", 1, 5, 2)

if st.button("Procesar"):
    if not text_input.strip():
        st.error("Por favor escribe al menos un comentario.")
    else:
        comments = [c.strip() for c in text_input.split("\n") if c.strip()]
        st.info("Procesando los comentarios en paralelo...")

        start_time = time.time()
        results = process_comments_parallel(comments, chunk_size, num_threads)
        end_time = time.time()

        st.success("Procesamiento completado! :)")
        st.write(f"Tiempo total: {end_time - start_time:.4f} segundos")

        # Mostrar resultados
        st.subheader("Resultados del Análisis")
        st.table({"Comentario": [r[0] for r in results],
                  "Sentimiento": [r[1] for r in results]})

        # Conteo de sentimientos
        counts = {"positive":0, "negative":0, "neutral":0}
        for _, s in results:
            counts[s] += 1
        st.write(" Conteo de sentimientos:", counts)
