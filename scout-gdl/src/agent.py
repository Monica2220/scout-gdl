"""
Scout GDL — Agente de scouting inmobiliario para Guadalajara ZMG
Ejecución diaria automática a las 7:00 am
"""

import os
import json
import csv
import time
import logging
from datetime import datetime
from pathlib import Path

import requests
from anthropic import Anthropic
from src.notificaciones import notificar

# ── Configuración ──────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(f"logs/scout_{datetime.now().strftime('%Y%m%d')}.log"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
NEWSAPI_KEY       = os.environ.get("NEWSAPI_KEY", "")       # newsapi.org (gratis)
GOOGLE_PLACES_KEY = os.environ.get("GOOGLE_PLACES_KEY", "") # Google Places API

client = Anthropic(api_key=ANTHROPIC_API_KEY)

ZONAS_ZMG = [
    "Guadalajara", "Zapopan", "Tlaquepaque",
    "Tonalá", "Tlajomulco de Zúñiga", "El Salto", "Juanacatlán",
]

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)


# ── 1. Fuentes de datos ────────────────────────────────────────────────────────

def buscar_noticias_gdl() -> list[dict]:
    """
    Busca noticias recientes de desarrollo inmobiliario en GDL.
    Usa NewsAPI (plan gratuito: 100 req/día).
    """
    if not NEWSAPI_KEY:
        log.warning("NEWSAPI_KEY no configurada — omitiendo noticias")
        return []

    resultados = []
    queries = [
        "desarrollo inmobiliario Guadalajara",
        "inversión construcción Zapopan",
        "proyecto residencial Jalisco",
        "torre departamentos Guadalajara",
        "fraccionamiento Tlajomulco",
    ]

    for q in queries:
        try:
            r = requests.get(
                "https://newsapi.org/v2/everything",
                params={
                    "q": q,
                    "language": "es",
                    "sortBy": "publishedAt",
                    "pageSize": 5,
                    "apiKey": NEWSAPI_KEY,
                },
                timeout=10,
            )
            for art in r.json().get("articles", []):
                resultados.append({
                    "fuente": "noticias",
                    "titulo": art.get("title", ""),
                    "descripcion": art.get("description", ""),
                    "url": art.get("url", ""),
                    "fecha": art.get("publishedAt", "")[:10],
                    "medio": art.get("source", {}).get("name", ""),
                })
            time.sleep(0.3)
        except Exception as e:
            log.error(f"Error buscando noticias '{q}': {e}")

    log.info(f"Noticias obtenidas: {len(resultados)}")
    return resultados


def buscar_lugares_gdl() -> list[dict]:
    """
    Busca empresas inmobiliarias y constructoras en Google Places.
    """
    if not GOOGLE_PLACES_KEY:
        log.warning("GOOGLE_PLACES_KEY no configurada — omitiendo Google Places")
        return []

    resultados = []
    # Centro aproximado de GDL
    lat, lng = 20.6597, -103.3496
    tipos = [
        "real_estate_agency",
        "general_contractor",
        "home_builder",
    ]

    for tipo in tipos:
        try:
            r = requests.get(
                "https://maps.googleapis.com/maps/api/place/nearbysearch/json",
                params={
                    "location": f"{lat},{lng}",
                    "radius": 25000,   # 25 km cubre ZMG
                    "type": tipo,
                    "key": GOOGLE_PLACES_KEY,
                },
                timeout=10,
            )
            for lugar in r.json().get("results", []):
                resultados.append({
                    "fuente": "google_maps",
                    "nombre": lugar.get("name", ""),
                    "direccion": lugar.get("vicinity", ""),
                    "rating": lugar.get("rating", 0),
                    "reseñas": lugar.get("user_ratings_total", 0),
                    "place_id": lugar.get("place_id", ""),
                    "tipos": ", ".join(lugar.get("types", [])),
                })
            time.sleep(0.5)
        except Exception as e:
            log.error(f"Error Google Places '{tipo}': {e}")

    log.info(f"Lugares obtenidos: {len(resultados)}")
    return resultados


def buscar_linkedin_simulado() -> list[dict]:
    """
    LinkedIn no tiene API pública gratuita.
    Opciones reales:
      - LinkedIn Sales Navigator API (de pago)
      - PhantomBuster (scraper con límites)
      - Apollo.io API (tiene plan gratis con 50 créditos/mes)
    
    Por ahora retorna estructura vacía lista para conectar.
    Ver README para instrucciones de Apollo.io.
    """
    log.info("LinkedIn: conecta Apollo.io para datos reales (ver README)")
    return []


def buscar_twitter_simulado() -> list[dict]:
    """
    Twitter/X API Básica tiene costo ($100/mes).
    Alternativa gratuita: monitoreo de hashtags con nitter (instancia propia).
    
    Por ahora retorna estructura vacía lista para conectar.
    Ver README para instrucciones.
    """
    log.info("Twitter/X: ver README para opciones de monitoreo")
    return []


# ── 2. Scoring con IA ─────────────────────────────────────────────────────────

def analizar_prospectos_con_ia(datos_crudos: list[dict]) -> list[dict]:
    """
    Envía los datos crudos a Claude para que:
    1. Identifique empresas/personas como prospectos inmobiliarios
    2. Asigne score de potencial (0-100)
    3. Detecte la señal de intención de compra
    4. Clasifique prioridad (hot/warm/cold)
    """
    if not datos_crudos:
        log.warning("Sin datos crudos para analizar")
        return []

    prompt = f"""Eres un agente especializado en scouting inmobiliario para la Zona Metropolitana de Guadalajara (ZMG), México.

Analiza estos datos crudos recopilados hoy de múltiples fuentes y extrae prospectos potenciales para servicios inmobiliarios (compra/venta de terrenos, desarrollos residenciales, proyectos comerciales, inversión inmobiliaria).

DATOS CRUDOS:
{json.dumps(datos_crudos, ensure_ascii=False, indent=2)}

Para cada prospecto identificado, devuelve un JSON con esta estructura exacta:
{{
  "prospectos": [
    {{
      "empresa": "nombre de la empresa",
      "contacto": "nombre del contacto si está disponible, sino vacío",
      "zona": "municipio dentro de ZMG",
      "fuente": "noticias|google_maps|linkedin|twitter",
      "score": 0-100,
      "prioridad": "hot|warm|cold",
      "señal": "señal de intención detectada en máximo 80 caracteres",
      "url": "url de la fuente si existe",
      "fecha_deteccion": "{datetime.now().strftime('%Y-%m-%d')}"
    }}
  ]
}}

Criterios de scoring:
- 80-100 (hot): señal clara de compra/inversión inmediata, expansion activa, búsqueda explícita de terrenos
- 60-79 (warm): crecimiento visible, contrataciones clave, menciones en medios sobre proyectos futuros
- 40-59 (cold): presencia relevante en el sector pero sin señal inmediata clara

Devuelve SOLO el JSON, sin texto adicional."""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        texto = response.content[0].text.strip()
        # Limpiar posibles backticks
        if texto.startswith("```"):
            texto = texto.split("```")[1]
            if texto.startswith("json"):
                texto = texto[4:]
        resultado = json.loads(texto)
        prospectos = resultado.get("prospectos", [])
        log.info(f"IA identificó {len(prospectos)} prospectos")
        return prospectos
    except Exception as e:
        log.error(f"Error en análisis IA: {e}")
        return []


# ── 3. Guardar resultados ─────────────────────────────────────────────────────

def guardar_csv(prospectos: list[dict], fecha: str) -> Path:
    path = OUTPUT_DIR / f"scouting_GDL_{fecha}.csv"
    if not prospectos:
        log.warning("Sin prospectos para guardar")
        return path

    campos = ["empresa","contacto","zona","fuente","score","prioridad","señal","url","fecha_deteccion"]
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=campos, extrasaction="ignore")
        w.writeheader()
        w.writerows(prospectos)

    log.info(f"CSV guardado: {path}")
    return path


def guardar_json(prospectos: list[dict], fecha: str) -> Path:
    path = OUTPUT_DIR / f"scouting_GDL_{fecha}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"fecha": fecha, "total": len(prospectos), "prospectos": prospectos}, f, ensure_ascii=False, indent=2)
    log.info(f"JSON guardado: {path}")
    return path


def generar_resumen_ia(prospectos: list[dict]) -> str:
    """Genera un briefing ejecutivo de los mejores prospectos del día."""
    if not prospectos:
        return "Sin prospectos para resumir hoy."

    top = sorted(prospectos, key=lambda x: x.get("score", 0), reverse=True)[:8]

    prompt = f"""Eres mi asistente de ventas inmobiliarias en Guadalajara.

Aquí están los mejores prospectos detectados hoy:
{json.dumps(top, ensure_ascii=False, indent=2)}

Redacta un briefing ejecutivo en español (máximo 200 palabras) que incluya:
1. Los 3 prospectos más calientes y por qué contactarlos HOY
2. La zona más activa del día
3. Una recomendación de acción inmediata

Sé directo y accionable, como si fuera un resumen de WhatsApp para arrancar el día."""

    try:
        r = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}],
        )
        return r.content[0].text.strip()
    except Exception as e:
        log.error(f"Error generando resumen: {e}")
        return "Error generando resumen."


# ── 4. Pipeline principal ─────────────────────────────────────────────────────

def run():
    fecha = datetime.now().strftime("%Y-%m-%d")
    log.info(f"═══ Scout GDL iniciando — {fecha} ═══")

    # Recopilar datos de todas las fuentes
    datos_crudos = []
    datos_crudos.extend(buscar_noticias_gdl())
    datos_crudos.extend(buscar_lugares_gdl())
    datos_crudos.extend(buscar_linkedin_simulado())
    datos_crudos.extend(buscar_twitter_simulado())

    log.info(f"Total registros crudos: {len(datos_crudos)}")

    if not datos_crudos:
        log.warning("Sin datos crudos — verifica tus API keys en .env")
        return

    # Analizar con IA
    prospectos = analizar_prospectos_con_ia(datos_crudos)

    # Ordenar por score descendente
    prospectos.sort(key=lambda x: x.get("score", 0), reverse=True)

    # Guardar resultados
    guardar_csv(prospectos, fecha)
    guardar_json(prospectos, fecha)

    # Briefing del día
    resumen = generar_resumen_ia(prospectos)
    resumen_path = OUTPUT_DIR / f"briefing_{fecha}.txt"
    resumen_path.write_text(resumen, encoding="utf-8")

    log.info("\n" + "─" * 50)
    log.info("📋 BRIEFING DEL DÍA:")
    log.info(resumen)
    log.info("─" * 50)
    log.info(f"✅ Scout GDL completado — {len(prospectos)} prospectos encontrados")

    # Enviar notificaciones por WhatsApp y Email
    csv_path = OUTPUT_DIR / f"scouting_GDL_{fecha}.csv"
    notificar(resumen, prospectos, csv_path)


if __name__ == "__main__":
    run()
