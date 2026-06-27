"""
Scout GDL - Agente de scouting inmobiliario para Guadalajara ZMG
Ejecucion diaria automatica a las 7:00 am
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
NEWSAPI_KEY       = os.environ.get("NEWSAPI_KEY", "")
GOOGLE_PLACES_KEY = os.environ.get("GOOGLE_PLACES_KEY", "")
APOLLO_API_KEY    = os.environ.get("APOLLO_API_KEY", "")

client = Anthropic(api_key=ANTHROPIC_API_KEY)

ZONAS_ZMG = [
    "Guadalajara", "Zapopan", "Tlaquepaque",
    "Tonala", "Tlajomulco de Zuniga", "El Salto", "Juanacatlan",
]

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)


def buscar_noticias_gdl() -> list:
    if not NEWSAPI_KEY:
        log.warning("NEWSAPI_KEY no configurada - omitiendo noticias")
        return []

    resultados = []
    queries = [
        "desarrollo inmobiliario Guadalajara",
        "inversion construccion Zapopan",
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


def buscar_lugares_gdl() -> list:
    if not GOOGLE_PLACES_KEY:
        log.warning("GOOGLE_PLACES_KEY no configurada - omitiendo Google Places")
        return []

    resultados = []
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
                    "radius": 25000,
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
                    "resenas": lugar.get("user_ratings_total", 0),
                    "place_id": lugar.get("place_id", ""),
                    "tipos": ", ".join(lugar.get("types", [])),
                })
            time.sleep(0.5)
        except Exception as e:
            log.error(f"Error Google Places '{tipo}': {e}")

    log.info(f"Lugares obtenidos: {len(resultados)}")
    return resultados


def buscar_apollo_linkedin() -> list:
    if not APOLLO_API_KEY:
        log.warning("Apollo.io: falta APOLLO_API_KEY en .env")
        return []

    resultados = []
    titulos = [
        "Director General", "Director Comercial", "Director de Desarrollo",
        "Gerente de Ventas", "Director de Proyectos", "CEO", "Founder",
    ]
    keywords = ["inmobiliaria", "desarrolladora", "constructora", "bienes raices"]

    for keyword in keywords:
        try:
            r = requests.post(
                "https://api.apollo.io/v1/mixed_people/search",
                headers={
                    "Content-Type": "application/json",
                    "Cache-Control": "no-cache",
                    "X-Api-Key": APOLLO_API_KEY,
                },
                json={
                    "q_organization_keyword_tags": [keyword],
                    "person_locations": ["Guadalajara, Jalisco, Mexico"],
                    "person_titles": titulos,
                    "page": 1,
                    "per_page": 10,
                },
                timeout=15,
            )
            data = r.json()
            for persona in data.get("people", []):
                org = persona.get("organization", {}) or {}
                resultados.append({
                    "fuente": "linkedin_apollo",
                    "nombre": persona.get("name", ""),
                    "cargo": persona.get("title", ""),
                    "empresa": org.get("name", ""),
                    "linkedin": persona.get("linkedin_url", ""),
                    "email": persona.get("email", ""),
                    "ciudad": "Guadalajara",
                    "empleados": org.get("estimated_num_employees", 0),
                    "industria": org.get("industry", ""),
                })
            time.sleep(1)
        except Exception as e:
            log.error(f"Error Apollo.io '{keyword}': {e}")

    log.info(f"Contactos Apollo/LinkedIn obtenidos: {len(resultados)}")
    return resultados


def buscar_twitter_simulado() -> list:
    log.info("Twitter/X: pendiente de configurar")
    return []


def analizar_prospectos_con_ia(datos_crudos: list) -> list:
    if not datos_crudos:
        log.warning("Sin datos crudos para analizar")
        return []

    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    prompt = f"""Eres un agente especializado en scouting inmobiliario para la Zona Metropolitana de Guadalajara (ZMG), Mexico.

Analiza estos datos crudos recopilados hoy de multiples fuentes y extrae prospectos potenciales para servicios inmobiliarios (compra/venta de terrenos, desarrollos residenciales, proyectos comerciales, inversion inmobiliaria).

DATOS CRUDOS:
{json.dumps(datos_crudos, ensure_ascii=False, indent=2)}

Para cada prospecto identificado, devuelve un JSON con esta estructura exacta:
{{
  "prospectos": [
    {{
      "empresa": "nombre de la empresa",
      "contacto": "nombre del contacto si esta disponible, sino vacio",
      "zona": "municipio dentro de ZMG",
      "fuente": "noticias|google_maps|linkedin|twitter",
      "score": 0-100,
      "prioridad": "hot|warm|cold",
      "senal": "senal de intencion detectada en maximo 80 caracteres",
      "url": "url de la fuente si existe",
      "fecha_deteccion": "{fecha_hoy}"
    }}
  ]
}}

Criterios de scoring:
- 80-100 (hot): senal clara de compra/inversion inmediata, expansion activa, busqueda explicita de terrenos
- 60-79 (warm): crecimiento visible, contrataciones clave, menciones en medios sobre proyectos futuros
- 40-59 (cold): presencia relevante en el sector pero sin senal inmediata clara

Devuelve SOLO el JSON, sin texto adicional."""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        texto = response.content[0].text.strip()
        if texto.startswith("```"):
            texto = texto.split("```")[1]
            if texto.startswith("json"):
                texto = texto[4:]
        resultado = json.loads(texto)
        prospectos = resultado.get("prospectos", [])
        log.info(f"IA identifico {len(prospectos)} prospectos")
        return prospectos
    except Exception as e:
        log.error(f"Error en analisis IA: {e}")
        return []


def guardar_csv(prospectos: list, fecha: str) -> Path:
    path = OUTPUT_DIR / f"scouting_GDL_{fecha}.csv"
    if not prospectos:
        log.warning("Sin prospectos para guardar")
        return path

    campos = ["empresa","contacto","zona","fuente","score","prioridad","senal","url","fecha_deteccion"]
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=campos, extrasaction="ignore")
        w.writeheader()
        w.writerows(prospectos)

    log.info(f"CSV guardado: {path}")
    return path


def guardar_json(prospectos: list, fecha: str) -> Path:
    path = OUTPUT_DIR / f"scouting_GDL_{fecha}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"fecha": fecha, "total": len(prospectos), "prospectos": prospectos}, f, ensure_ascii=False, indent=2)
    log.info(f"JSON guardado: {path}")
    return path


def generar_resumen_ia(prospectos: list) -> str:
    if not prospectos:
        return "Sin prospectos para resumir hoy."

    top = sorted(prospectos, key=lambda x: x.get("score", 0), reverse=True)[:8]

    prompt = f"""Eres mi asistente de ventas inmobiliarias en Guadalajara.

Aqui estan los mejores prospectos detectados hoy:
{json.dumps(top, ensure_ascii=False, indent=2)}

Redacta un briefing ejecutivo en espanol (maximo 200 palabras) que incluya:
1. Los 3 prospectos mas calientes y por que contactarlos HOY
2. La zona mas activa del dia
3. Una recomendacion de accion inmediata

Se directo y accionable, como si fuera un resumen de WhatsApp para arrancar el dia."""

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


def run():
    fecha = datetime.now().strftime("%Y-%m-%d")
    log.info(f"Scout GDL iniciando - {fecha}")

    datos_crudos = []
    datos_crudos.extend(buscar_noticias_gdl())
    datos_crudos.extend(buscar_lugares_gdl())
    datos_crudos.extend(buscar_apollo_linkedin())
    datos_crudos.extend(buscar_twitter_simulado())

    log.info(f"Total registros crudos: {len(datos_crudos)}")

    if not datos_crudos:
        log.warning("Sin datos crudos - verifica tus API keys")
        return

    prospectos = analizar_prospectos_con_ia(datos_crudos)
    prospectos.sort(key=lambda x: x.get("score", 0), reverse=True)

    guardar_csv(prospectos, fecha)
    guardar_json(prospectos, fecha)

    resumen = generar_resumen_ia(prospectos)
    resumen_path = OUTPUT_DIR / f"briefing_{fecha}.txt"
    resumen_path.write_text(resumen, encoding="utf-8")

    log.info(f"BRIEFING DEL DIA:\n{resumen}")
    log.info(f"Scout GDL completado - {len(prospectos)} prospectos encontrados")

    csv_path = OUTPUT_DIR / f"scouting_GDL_{fecha}.csv"
    notificar(resumen, prospectos, csv_path)


if __name__ == "__main__":
    run()
