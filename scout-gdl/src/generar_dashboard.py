"""
generar_dashboard.py - Genera el dashboard HTML con los prospectos del dia
Se llama desde agent.py al final de cada ejecucion
"""

import json
from datetime import datetime
from pathlib import Path


def generar_html(prospectos: list, briefing: str, fecha: str) -> str:

    hot  = len([p for p in prospectos if p.get("prioridad") == "hot"])
    warm = len([p for p in prospectos if p.get("prioridad") == "warm"])
    cold = len([p for p in prospectos if p.get("prioridad") == "cold"])

    color_prio = {"hot": "#dc2626", "warm": "#d97706", "cold": "#2563eb"}
    bg_prio    = {"hot": "#fef2f2", "warm": "#fffbeb", "cold": "#eff6ff"}
    label_prio = {"hot": "Caliente", "warm": "Tibio", "cold": "Frio"}
    icon_fuente = {
        "noticias": "📰",
        "google_maps": "📍",
        "linkedin": "💼",
        "linkedin_apollo": "💼",
        "twitter": "🐦",
        "google_trends": "🔍",
    }
    label_fuente = {
        "noticias": "Noticias",
        "google_maps": "Google Maps",
        "linkedin": "LinkedIn",
        "linkedin_apollo": "LinkedIn",
        "twitter": "Twitter/X",
        "google_trends": "Google Trends",
    }

    tarjetas = ""
    for p in prospectos:
        prio = p.get("prioridad", "cold")
        fuente_key = p.get("fuente", "")
        url = p.get("url", "")
        empresa = p.get("empresa", "")
        senal = p.get("senal", p.get("señal", ""))
        score = p.get("score", 0)

        empresa_html = (
            f'<a href="{url}" target="_blank" class="empresa-link">{empresa} ↗</a>'
            if url else
            f'<span class="empresa-nombre">{empresa}</span>'
        )

        tarjetas += f"""
        <div class="card" data-prioridad="{prio}" data-fuente="{fuente_key}">
          <div class="card-header" style="border-left:4px solid {color_prio[prio]}">
            <div class="card-empresa">{empresa_html}</div>
            <div class="card-score" style="background:{bg_prio[prio]};color:{color_prio[prio]}">{score}</div>
          </div>
          <div class="card-meta">
            <span class="badge-zona">📍 {p.get('zona','')}</span>
            <span class="badge-fuente">{icon_fuente.get(fuente_key,'')} {label_fuente.get(fuente_key,fuente_key)}</span>
            <span class="badge-prio" style="background:{bg_prio[prio]};color:{color_prio[prio]}">
              {label_prio[prio]}
            </span>
          </div>
          <div class="card-senal">{senal}</div>
          {f'<a href="{url}" target="_blank" class="card-link">Ver fuente ↗</a>' if url else ''}
        </div>"""

    briefing_html = briefing.replace("\n", "<br>").replace("**", "")

    prospectos_json = json.dumps(prospectos, ensure_ascii=False)

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Scout GDL - {fecha}</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f8fafc; color: #1e293b; }}

    .topbar {{ background: #0f172a; color: white; padding: 16px 32px; display: flex; align-items: center; justify-content: space-between; }}
    .topbar-title {{ font-size: 20px; font-weight: 600; }}
    .topbar-date {{ font-size: 13px; color: #94a3b8; }}
    .live-dot {{ display: inline-block; width: 8px; height: 8px; background: #22c55e; border-radius: 50%; margin-right: 6px; animation: pulse 2s infinite; }}
    @keyframes pulse {{ 0%,100%{{opacity:1}} 50%{{opacity:.4}} }}

    .metrics {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 0; border-bottom: 1px solid #e2e8f0; background: white; }}
    .metric {{ padding: 20px 24px; text-align: center; border-right: 1px solid #e2e8f0; }}
    .metric:last-child {{ border-right: none; }}
    .metric-val {{ font-size: 32px; font-weight: 700; }}
    .metric-label {{ font-size: 12px; color: #64748b; margin-top: 4px; }}

    .briefing {{ background: #eff6ff; border-left: 4px solid #2563eb; margin: 24px 32px; padding: 16px 20px; border-radius: 0 8px 8px 0; }}
    .briefing-title {{ font-size: 12px; font-weight: 600; color: #2563eb; text-transform: uppercase; letter-spacing: .5px; margin-bottom: 8px; }}
    .briefing-text {{ font-size: 14px; line-height: 1.7; color: #1e293b; }}

    .filters {{ padding: 0 32px 16px; display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }}
    .filter-label {{ font-size: 13px; color: #64748b; }}
    .pill {{ padding: 5px 14px; border-radius: 20px; border: 1px solid #e2e8f0; background: white; font-size: 13px; cursor: pointer; color: #475569; transition: all .15s; }}
    .pill:hover {{ border-color: #94a3b8; }}
    .pill.active {{ background: #0f172a; color: white; border-color: #0f172a; }}
    .search {{ flex: 1; min-width: 200px; padding: 7px 14px; border: 1px solid #e2e8f0; border-radius: 20px; font-size: 13px; outline: none; }}
    .search:focus {{ border-color: #94a3b8; }}

    .cards {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 16px; padding: 0 32px 32px; }}
    .card {{ background: white; border-radius: 10px; border: 1px solid #e2e8f0; padding: 16px; transition: box-shadow .15s; }}
    .card:hover {{ box-shadow: 0 4px 12px rgba(0,0,0,.08); }}
    .card.hidden {{ display: none; }}

    .card-header {{ display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; padding-left: 10px; margin-bottom: 10px; }}
    .card-empresa {{ font-weight: 500; font-size: 15px; }}
    .empresa-link {{ color: #185FA5; text-decoration: none; }}
    .empresa-link:hover {{ text-decoration: underline; }}
    .empresa-nombre {{ color: #1e293b; }}
    .card-score {{ font-size: 18px; font-weight: 700; padding: 4px 10px; border-radius: 8px; white-space: nowrap; }}

    .card-meta {{ display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 10px; }}
    .badge-zona, .badge-fuente, .badge-prio {{ font-size: 11px; padding: 2px 8px; border-radius: 4px; background: #f1f5f9; color: #475569; }}
    .badge-prio {{ font-weight: 600; }}

    .card-senal {{ font-size: 13px; color: #64748b; line-height: 1.5; margin-bottom: 8px; }}
    .card-link {{ font-size: 12px; color: #185FA5; text-decoration: none; }}
    .card-link:hover {{ text-decoration: underline; }}

    .empty {{ text-align: center; color: #94a3b8; padding: 48px; font-size: 15px; display: none; }}

    .footer {{ text-align: center; padding: 24px; font-size: 12px; color: #94a3b8; border-top: 1px solid #e2e8f0; }}

    @media (max-width: 600px) {{
      .metrics {{ grid-template-columns: repeat(2, 1fr); }}
      .topbar, .briefing, .filters, .cards {{ padding-left: 16px; padding-right: 16px; }}
    }}
  </style>
</head>
<body>

<div class="topbar">
  <div class="topbar-title">🏗️ Scout GDL</div>
  <div class="topbar-date"><span class="live-dot"></span>Actualizado: {fecha} · 7:00 AM</div>
</div>

<div class="metrics">
  <div class="metric"><div class="metric-val">{len(prospectos)}</div><div class="metric-label">Prospectos hoy</div></div>
  <div class="metric"><div class="metric-val" style="color:#dc2626">{hot}</div><div class="metric-label">Calientes 🔴</div></div>
  <div class="metric"><div class="metric-val" style="color:#d97706">{warm}</div><div class="metric-label">Tibios 🟡</div></div>
  <div class="metric"><div class="metric-val" style="color:#2563eb">{cold}</div><div class="metric-label">Frios 🔵</div></div>
</div>

<div class="briefing">
  <div class="briefing-title">Analisis IA del dia</div>
  <div class="briefing-text">{briefing_html}</div>
</div>

<div class="filters">
  <span class="filter-label">Filtrar:</span>
  <span class="pill active" onclick="filtrar(this,'all')">Todos</span>
  <span class="pill" onclick="filtrar(this,'hot')">🔴 Caliente</span>
  <span class="pill" onclick="filtrar(this,'warm')">🟡 Tibio</span>
  <span class="pill" onclick="filtrar(this,'cold')">🔵 Frio</span>
  <span class="pill" onclick="filtrar(this,'google_maps')">📍 Maps</span>
  <span class="pill" onclick="filtrar(this,'noticias')">📰 Noticias</span>
  <span class="pill" onclick="filtrar(this,'google_trends')">🔍 Trends</span>
  <span class="pill" onclick="filtrar(this,'linkedin_apollo')">💼 LinkedIn</span>
  <input class="search" type="text" placeholder="Buscar empresa o zona..." oninput="buscar(this.value)">
</div>

<div class="cards" id="cards">{tarjetas}</div>
<div class="empty" id="empty">Sin resultados para este filtro</div>

<div class="footer">
  Scout GDL · Guadalajara Zona Metropolitana · Generado automaticamente cada dia a las 7:00 AM
</div>

<script>
const prospectos = {prospectos_json};
let filtroActivo = 'all';
let busquedaActiva = '';

function filtrar(el, val) {{
  filtroActivo = val;
  document.querySelectorAll('.pill').forEach(p => p.classList.remove('active'));
  el.classList.add('active');
  aplicarFiltros();
}}

function buscar(val) {{
  busquedaActiva = val.toLowerCase();
  aplicarFiltros();
}}

function aplicarFiltros() {{
  const cards = document.querySelectorAll('.card');
  let visibles = 0;
  cards.forEach(card => {{
    const prio = card.dataset.prioridad;
    const fuente = card.dataset.fuente;
    const texto = card.innerText.toLowerCase();
    const matchFiltro = filtroActivo === 'all' || prio === filtroActivo || fuente === filtroActivo;
    const matchBusqueda = busquedaActiva === '' || texto.includes(busquedaActiva);
    if (matchFiltro && matchBusqueda) {{
      card.classList.remove('hidden');
      visibles++;
    }} else {{
      card.classList.add('hidden');
    }}
  }});
  document.getElementById('empty').style.display = visibles === 0 ? 'block' : 'none';
}}
</script>
</body>
</html>"""


def generar_dashboard(prospectos: list, briefing: str, fecha: str, output_dir: Path):
    html = generar_html(prospectos, briefing, fecha)
    path = output_dir / "index.html"
    path.write_text(html, encoding="utf-8")
    print(f"Dashboard generado: {path}")
    return path
