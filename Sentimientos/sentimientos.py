from concurrent.futures import ThreadPoolExecutor
from threading import Lock
import string

# Diccionario de palabras positivas y negativas
positive_words = {"bueno", "excelente", "maravilloso", "genial", "fantástico", "encantó", "buenisimo", "lindo", "bonito"}
negative_words = {"malo", "terrible", "horrible", "pésimo", "desastre","malisimo", "horrendo", "feo"}

# Variable compartida entre hilos
results = []
lock = Lock()

def clean_text(text):
    """Este impia puntuación para evitar falsos positivos."""
    return text.lower().translate(str.maketrans("", "", string.punctuation))

def analyze_comment(comment):
    """Este analiza un solo comentario y retorna el sentimiento."""
    cleaned = clean_text(comment)
    words = cleaned.split()

    sentiment = "neutral"
    if any(w in positive_words for w in words):
        sentiment = "positive"
    elif any(w in negative_words for w in words):
        sentiment = "negative"

    return (comment, sentiment)

def analyze_sentiment_chunk(chunk):
    """Este procesa un subconjunto de comentarios y usa Lock para evitar carrera."""
    local_results = []
    for comment in chunk:
        local_results.append(analyze_comment(comment))

    # Guardar resultados en la lista global con protección
    with lock:
        results.extend(local_results)

# Programa como tal

comments = [
    "Me encantó este producto",
    "Fue terrible, no me gustó",
    "Más o menos, nada especial",
    "Excelente calidad, lo recomiendo",
    "Horrible experiencia"
]

chunk_size = 2

# Dividir comentarios
chunks = [comments[i:i + chunk_size] for i in range(0, len(comments), chunk_size)]

# Aca lo que hacemos es procesar con hilos usando ThreadPoolExecutor
with ThreadPoolExecutor(max_workers=len(chunks)) as executor:
    executor.map(analyze_sentiment_chunk, chunks)

print("\nRESULTADOS DEL ANÁLISIS:")
for c, s in results:
    print(f"- {c} → {s}")

