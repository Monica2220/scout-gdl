# 🏗️ Scout GDL — Agente de Scouting Inmobiliario

Agente automatizado que escanea internet cada mañana a las **7:00 am** buscando prospectos inmobiliarios en la Zona Metropolitana de Guadalajara. Genera una base de datos en CSV + un briefing ejecutivo del día.

---

## ¿Qué hace?

1. **Busca señales** en noticias, Google Maps, LinkedIn y Twitter/X
2. **Analiza con IA** (Claude) cada prospecto y le asigna un score de potencial
3. **Genera un CSV** listo para importar a tu CRM o Excel
4. **Escribe un briefing** con los 3 mejores prospectos del día y qué hacer primero

---

## Instalación rápida

```bash
# 1. Clona el repo
git clone https://github.com/TU_USUARIO/scout-gdl.git
cd scout-gdl

# 2. Instala dependencias
pip install -r requirements.txt

# 3. Configura tus claves
cp .env.example .env
# Edita .env con tu editor favorito y agrega tus API keys

# 4. Prueba que funciona
python -c "from src.agent import run; run()"
```

---

## Configuración de API Keys

### 1. Anthropic (Claude) — OBLIGATORIA
- Ve a https://console.anthropic.com
- Crea una API key
- Agrégala en `.env` como `ANTHROPIC_API_KEY`

### 2. NewsAPI — GRATIS
- Regístrate en https://newsapi.org
- Plan gratuito: 100 peticiones/día (suficiente)
- Cubre: El Informador, Mural, Milenio, El Economista
- Agrega en `.env` como `NEWSAPI_KEY`

### 3. Google Places — GRATIS (con límite)
- Ve a https://console.cloud.google.com
- Activa "Places API"
- Google da $200 USD de crédito gratis al mes
- Agrega en `.env` como `GOOGLE_PLACES_KEY`

### 4. Apollo.io — LINKEDIN (50 créditos gratis/mes)
- Regístrate en https://app.apollo.io
- Ve a Settings → Integrations → API
- Copia tu API key
- Próximamente en el agente (ver roadmap)

---

## Ejecución automática con GitHub Actions ⭐ Recomendado

No necesitas tener tu computadora encendida. GitHub lo corre solo.

**Pasos:**

1. Sube el repo a GitHub
2. Ve a **Settings → Secrets and variables → Actions**
3. Agrega estos secrets:
   - `ANTHROPIC_API_KEY`
   - `NEWSAPI_KEY`
   - `GOOGLE_PLACES_KEY`
4. Ve a **Actions** y activa los workflows
5. Listo — cada día a las 7 am corre solo ✅

Los resultados (CSV + briefing) quedan disponibles en la pestaña **Actions → tu ejecución → Artifacts**.

---

## Ejecución local (alternativa)

Si prefieres correrlo en tu máquina:

```bash
# Opción A: una sola vez ahora mismo
python -c "from src.agent import run; run()"

# Opción B: scheduler permanente (mantén la terminal abierta)
python scheduler.py
```

---

## Archivos de salida

Cada ejecución genera en la carpeta `output/`:

| Archivo | Descripción |
|---|---|
| `scouting_GDL_YYYY-MM-DD.csv` | Base de datos completa (importable a Excel/CRM) |
| `scouting_GDL_YYYY-MM-DD.json` | Mismos datos en JSON (para integraciones) |
| `briefing_YYYY-MM-DD.txt` | Resumen ejecutivo del día |

### Columnas del CSV

| Columna | Descripción |
|---|---|
| empresa | Nombre de la empresa |
| contacto | Nombre del contacto (si disponible) |
| zona | Municipio de la ZMG |
| fuente | noticias / google_maps / linkedin / twitter |
| score | 0-100 (potencial como prospecto) |
| prioridad | hot / warm / cold |
| señal | Señal de intención detectada |
| url | Fuente original |
| fecha_deteccion | Fecha del escaneo |

---

## Roadmap

- [ ] Integración Apollo.io para datos de LinkedIn
- [ ] Integración Twitter/X API o Nitter
- [ ] Notificación por WhatsApp (Twilio) con el briefing del día
- [ ] Dashboard web con histórico de prospectos
- [ ] Deduplicación automática entre días

---

## Estructura del proyecto

```
scout-gdl/
├── .github/
│   └── workflows/
│       └── scout.yml        # Ejecución automática diaria
├── src/
│   └── agent.py             # Lógica principal del agente
├── output/                  # Resultados diarios (en .gitignore)
├── logs/                    # Logs de ejecución (en .gitignore)
├── scheduler.py             # Scheduler local (alternativa a GitHub Actions)
├── requirements.txt
├── .env.example             # Plantilla de variables de entorno
├── .gitignore
└── README.md
```
