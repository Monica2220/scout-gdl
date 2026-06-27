"""
generar_dashboard.py - Dashboard Scout GDL mejorado
"""

import json
from datetime import datetime
from pathlib import Path


def generar_html(prospectos: list, briefing: str, fecha: str, historial: list = None) -> str:

    hot  = len([p for p in prospectos if p.get("prioridad") == "hot"])
    warm = len([p for p in prospectos if p.get("prioridad") == "warm"])
    cold = len([p for p in prospectos if p.get("prioridad") == "cold"])
    score_max = max((p.get("score", 0) for p in prospectos), default=0)

    color_prio = {"hot": "#dc2626", "warm": "#d97706", "cold": "#2563eb"}
    bg_prio    = {"hot": "#fef2f2", "warm": "#fffbeb", "cold": "#eff6ff"}
    label_prio = {"hot": "Caliente", "warm": "Tibio", "cold": "Frio"}

    icon_fuente = {
        "noticias": "📰", "google_maps": "📍",
        "linkedin": "💼", "linkedin_apollo": "💼",
        "twitter": "🐦", "google_trends": "🔍",
    }
    label_fuente = {
        "noticias": "Noticias", "google_maps": "Google Maps",
        "linkedin": "LinkedIn", "linkedin_apollo": "LinkedIn",
        "twitter": "Twitter/X", "google_trends": "Google Trends",
    }

    zonas_count = {}
    for p in prospectos:
        z = p.get("zona", "Otro")
        zonas_count[z] = zonas_count.get(z, 0) + 1
    zonas_sorted = sorted(zonas_count.items(), key=lambda x: x[1], reverse=True)
    zona_max = max(zonas_count.values(), default=1)

    zonas_html = ""
    for zona, cnt in zonas_sorted[:6]:
        pct = int(cnt / zona_max * 100)
        zonas_html += f"""<div style="display:flex;align-items:center;gap:8px;margin-bottom:7px">
          <span style="font-size:12px;color:#475569;width:90px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{zona}</span>
          <div style="flex:1;height:7px;background:#f1f5f9;border-radius:4px;overflow:hidden">
            <div style="width:{pct}%;height:100%;background:#185FA5;border-radius:4px"></div>
          </div>
          <span style="font-size:12px;color:#64748b;width:18px;text-align:right">{cnt}</span>
        </div>"""

    trends = [p for p in prospectos if p.get("fuente") == "google_trends"]
    trends_sorted = sorted(trends, key=lambda x: x.get("score", 0), reverse=True)[:5]
    trends_html = ""
    for t in trends_sorted:
        empresa = t.get("empresa", "")
        score = t.get("score", 0)
        pct = min(score, 100)
        color = "#dc2626" if score >= 80 else "#d97706" if score >= 60 else "#185FA5"
        arrow_color = "#16a34a"
        trends_html += f"""<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;padding-bottom:8px;border-bottom:1px solid #f1f5f9">
          <span style="font-size:12px;font-weight:500;flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{empresa}</span>
          <div style="width:70px;height:6px;background:#f1f5f9;border-radius:3px;overflow:hidden">
            <div style="width:{pct}%;height:100%;background:{color};border-radius:3px"></div>
          </div>
          <span style="font-size:12px;color:#64748b;width:28px;text-align:right">{score}</span>
          <span style="font-size:12px;color:{arrow_color}">↑</span>
        </div>"""
    if not trends_html:
        trends_html = '<p style="font-size:12px;color:#94a3b8">Sin datos de tendencias hoy</p>'

    hist_html = ""
    if historial:
        hist_max = max((h.get("total", 0) for h in historial), default=1)
        for h in historial[-7:]:
            d = h.get("fecha", "")[-5:]
            cnt = h.get("total", 0)
            pct = int(cnt / hist_max * 100) if hist_max > 0 else 0
            is_today = h.get("fecha", "") == fecha
            color = "#185FA5" if is_today else "#94a3b8"
            fw = "600" if is_today else "400"
            hist_html += f"""<div style="display:flex;align-items:center;gap:8px;margin-bottom:5px">
              <span style="font-size:11px;color:{color};font-weight:{fw};width:40px">{d}</span>
              <div style="flex:1;height:6px;background:#f1f5f9;border-radius:3px;overflow:hidden">
                <div style="width:{pct}%;height:100%;background:{color};border-radius:3px"></div>
              </div>
              <span style="font-size:11px;color:{color};font-weight:{fw};width:18px;text-align:right">{cnt}</span>
            </div>"""
    else:
        hist_html = '<p style="font-size:12px;color:#94a3b8">El historial se acumula dia a dia</p>'

    tarjetas = ""
    fechas_unicas = sorted(set(p.get("fecha_deteccion", fecha) for p in prospectos), reverse=True)

    for i, p in enumerate(prospectos):
        prio = p.get("prioridad", "cold")
        fuente_key = p.get("fuente", "")
        url = p.get("url", "")
        empresa = p.get("empresa", "")
        senal = p.get("senal", p.get("señal", ""))
        score = p.get("score", 0)
        zona = p.get("zona", "")
        contacto = p.get("contacto", "")
        email_p = p.get("email", "")
        linkedin = p.get("linkedin", "")
        fecha_p = p.get("fecha_deteccion", fecha)

        empresa_html = (
            f'<a href="{url}" target="_blank" style="color:#185FA5;text-decoration:none;font-size:14px;font-weight:500">{empresa} ↗</a>'
            if url else
            f'<span style="font-size:14px;font-weight:500;color:#0f172a">{empresa}</span>'
        )

        contacto_html = ""
        if contacto:
            contacto_html += f'<div style="font-size:12px;color:#64748b;margin-top:2px">{contacto}</div>'
        if email_p:
            contacto_html += f'<a href="mailto:{email_p}" style="font-size:11px;color:#185FA5">{email_p}</a>'

        links_html = ""
        if url:
            links_html += f'<a href="{url}" target="_blank" style="font-size:11px;color:#185FA5;text-decoration:none;padding:3px 8px;border:1px solid #bfdbfe;border-radius:4px;background:#eff6ff;margin-right:4px">Ver fuente ↗</a>'
        if linkedin:
            links_html += f'<a href="{linkedin}" target="_blank" style="font-size:11px;color:#185FA5;text-decoration:none;padding:3px 8px;border:1px solid #bfdbfe;border-radius:4px;background:#eff6ff">LinkedIn ↗</a>'

        tarjetas += f"""
        <div class="card" id="card-{i}" data-prioridad="{prio}" data-fuente="{fuente_key}" data-zona="{zona.lower()}" data-fecha="{fecha_p}" data-texto="{empresa.lower()} {zona.lower()} {senal.lower()}">
          <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:10px;margin-bottom:8px">
            <div style="flex:1;min-width:0">
              {empresa_html}
              {contacto_html}
            </div>
            <div style="width:38px;height:38px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:700;flex-shrink:0;background:{bg_prio.get(prio,'#f1f5f9')};color:{color_prio.get(prio,'#475569')}">{score}</div>
          </div>

          <div style="display:flex;gap:5px;flex-wrap:wrap;margin-bottom:8px">
            <span style="font-size:11px;padding:2px 7px;border-radius:4px;background:#f1f5f9;color:#475569">📍 {zona}</span>
            <span style="font-size:11px;padding:2px 7px;border-radius:4px;background:#f1f5f9;color:#475569">{icon_fuente.get(fuente_key,'')} {label_fuente.get(fuente_key,fuente_key)}</span>
            <span style="font-size:11px;padding:2px 7px;border-radius:4px;font-weight:600;background:{bg_prio.get(prio,'#f1f5f9')};color:{color_prio.get(prio,'#475569')}">{label_prio.get(prio,'')}</span>
          </div>

          <div style="font-size:12px;color:#64748b;line-height:1.5;margin-bottom:10px">{senal}</div>

          {f'<div style="margin-bottom:10px">{links_html}</div>' if links_html else ''}

          <div style="padding-top:8px;border-top:1px solid #f1f5f9;display:flex;justify-content:space-between;align-items:center">
            <button onclick="marcarRevisado({i})" id="btn-rev-{i}" style="font-size:11px;padding:3px 9px;border:1px solid #e2e8f0;border-radius:5px;background:white;color:#475569;cursor:pointer">
              ⬜ Por revisar
            </button>
            <span style="font-size:11px;color:#94a3b8">{fecha_p}</span>
          </div>
        </div>"""

    briefing_html = briefing.replace("\n", "<br>").replace("**", "").replace("##", "").replace("#", "")
    prospectos_json = json.dumps(prospectos, ensure_ascii=False)
    fechas_json = json.dumps(fechas_unicas)

    csv_rows = ["empresa,contacto,zona,fuente,score,prioridad,senal,url,fecha_deteccion"]
    for p in prospectos:
        row = [
            p.get("empresa","").replace(",",""),
            p.get("contacto","").replace(",",""),
            p.get("zona",""),
            p.get("fuente",""),
            str(p.get("score",0)),
            p.get("prioridad",""),
            p.get("senal", p.get("señal","")).replace(",",""),
            p.get("url",""),
            p.get("fecha_deteccion",""),
        ]
        csv_rows.append(",".join(f'"{v}"' for v in row))
    csv_content = "\\n".join(csv_rows)

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>Scout GDL - {fecha}</title>
  <style>
    *{{box-sizing:border-box;margin:0;padding:0}}
    body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f8fafc;color:#1e293b}}
    .topbar{{background:#0f172a;color:white;padding:14px 28px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px}}
    .topbar-title{{font-size:18px;font-weight:600}}
    .topbar-sub{{font-size:12px;color:#94a3b8;margin-top:2px}}
    .topbar-right{{display:flex;align-items:center;gap:8px;flex-wrap:wrap}}
    .btn-top{{font-size:12px;padding:6px 14px;border-radius:6px;border:1px solid rgba(255,255,255,.2);background:rgba(255,255,255,.08);color:white;cursor:pointer;display:inline-flex;align-items:center;gap:5px}}
    .btn-top:hover{{background:rgba(255,255,255,.18)}}
    .kpis{{display:grid;grid-template-columns:repeat(4,1fr);background:white;border-bottom:1px solid #e2e8f0}}
    .kpi{{padding:16px 12px;text-align:center;border-right:1px solid #e2e8f0}}
    .kpi:last-child{{border-right:none}}
    .kpi-val{{font-size:28px;font-weight:700}}
    .kpi-label{{font-size:11px;color:#64748b;margin-top:2px}}
    .main{{display:grid;grid-template-columns:1fr 260px}}
    .left{{padding:20px 24px;min-width:0}}
    .right{{border-left:1px solid #e2e8f0;padding:20px;background:white}}
    .section-title{{font-size:11px;font-weight:600;color:#64748b;text-transform:uppercase;letter-spacing:.5px;margin-bottom:12px}}
    .briefing{{background:#eff6ff;border-left:3px solid #2563eb;padding:12px 16px;border-radius:0 8px 8px 0;margin-bottom:16px;font-size:13px;line-height:1.6;color:#1e40af}}
    .filters{{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:16px;align-items:center}}
    .pill{{font-size:12px;padding:4px 12px;border-radius:20px;border:1px solid #e2e8f0;background:white;color:#475569;cursor:pointer;transition:all .15s}}
    .pill:hover{{border-color:#94a3b8}}
    .pill.active{{background:#0f172a;color:white;border-color:#0f172a}}
    .search-box{{flex:1;min-width:140px;padding:5px 12px;border:1px solid #e2e8f0;border-radius:20px;font-size:12px;outline:none}}
    .date-select{{font-size:12px;padding:4px 10px;border:1px solid #e2e8f0;border-radius:20px;background:white;color:#475569;cursor:pointer;outline:none}}
    .cards{{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:12px}}
    .card{{background:white;border:1px solid #e2e8f0;border-radius:10px;padding:14px;border-left:4px solid #e2e8f0;transition:box-shadow .15s}}
    .card:hover{{box-shadow:0 2px 8px rgba(0,0,0,.06)}}
    .card[data-prioridad="hot"]{{border-left-color:#dc2626}}
    .card[data-prioridad="warm"]{{border-left-color:#d97706}}
    .card[data-prioridad="cold"]{{border-left-color:#2563eb}}
    .card.hidden{{display:none}}
    .card.revisado{{opacity:.5}}
    .empty{{text-align:center;color:#94a3b8;padding:48px;font-size:14px;display:none}}
    .divider{{height:1px;background:#e2e8f0;margin:16px 0}}
    .footer{{text-align:center;padding:20px;font-size:12px;color:#94a3b8;border-top:1px solid #e2e8f0;background:white}}
    @media(max-width:700px){{
      .kpis{{grid-template-columns:repeat(2,1fr)}}
      .main{{grid-template-columns:1fr}}
      .right{{border-left:none;border-top:1px solid #e2e8f0}}
      .topbar,.left,.right{{padding:14px 16px}}
    }}
  </style>
</head>
<body>

<div class="topbar">
  <div>
    <div class="topbar-title">🏗️ Scout GDL</div>
    <div class="topbar-sub">Guadalajara · Zona Metropolitana · {fecha}</div>
  </div>
  <div class="topbar-right">
    <button class="btn-top" onclick="descargarCSV()">⬇ Descargar CSV</button>
    <button class="btn-top" onclick="descargarPorRevisar()" id="btn-por-revisar">⬇ Por revisar</button>
    <button class="btn-top" onclick="descargarRevisados()" id="btn-revisados" style="display:none">⬇ Revisados</button>
  </div>
</div>

<div class="kpis">
  <div class="kpi"><div class="kpi-val">{len(prospectos)}</div><div class="kpi-label">Prospectos hoy</div></div>
  <div class="kpi"><div class="kpi-val" style="color:#dc2626">{hot}</div><div class="kpi-label">Calientes 🔴</div></div>
  <div class="kpi"><div class="kpi-val" style="color:#d97706">{warm}</div><div class="kpi-label">Tibios 🟡</div></div>
  <div class="kpi"><div class="kpi-val" style="color:#2563eb">{cold}</div><div class="kpi-label">Frios 🔵</div></div>
</div>

<div class="main">
  <div class="left">

    <div class="briefing" style="margin-top:4px">
      {briefing_html[:500]}{'...' if len(briefing_html) > 500 else ''}
    </div>

    <div class="filters">
      <span class="pill active" onclick="filtrar(this,'all','prio')">Todos</span>
      <span class="pill" onclick="filtrar(this,'hot','prio')">🔴 Caliente</span>
      <span class="pill" onclick="filtrar(this,'warm','prio')">🟡 Tibio</span>
      <span class="pill" onclick="filtrar(this,'cold','prio')">🔵 Frio</span>
      <span class="pill" onclick="filtrar(this,'google_maps','fuente')">📍 Maps</span>
      <span class="pill" onclick="filtrar(this,'google_trends','fuente')">🔍 Trends</span>
      <span class="pill" onclick="filtrar(this,'noticias','fuente')">📰 Noticias</span>
      <span class="pill" onclick="filtrar(this,'linkedin_apollo','fuente')">💼 LinkedIn</span>
      <span class="pill" onclick="filtrarRevisados(this)">✅ Revisados</span>
      <select class="date-select" id="date-select" onchange="filtrarFecha(this.value)">
        <option value="all">Todas las fechas</option>
      </select>
      <input class="search-box" type="text" placeholder="Buscar empresa o zona..." oninput="buscar(this.value)">
    </div>

    <div class="cards" id="cards">{tarjetas}</div>
    <div class="empty" id="empty">Sin resultados para este filtro</div>

  </div>

  <div class="right">

    <div class="section-title">Google Trends — Jalisco</div>
    {trends_html}

    <div class="divider"></div>

    <div class="section-title">Prospectos por zona</div>
    {zonas_html}

    <div class="divider"></div>

    <div class="section-title">Historial 7 dias</div>
    {hist_html}

    <div class="divider"></div>

    <div style="background:#f8fafc;border-radius:8px;padding:12px;font-size:12px;color:#475569;line-height:1.6">
      <div style="font-weight:600;margin-bottom:4px;color:#1e293b">Estado de revision</div>
      <div id="estado-revision">0 revisados · {len(prospectos)} pendientes</div>
    </div>

  </div>
</div>

<div class="footer">
  Scout GDL · Guadalajara Zona Metropolitana · Actualizado automaticamente cada dia a las 7:00 AM
</div>

<script>
const prospectos = {prospectos_json};
const csvContent = `{csv_content}`;
const fecha = '{fecha}';
const fechasUnicas = {fechas_json};
let filtroActivo = 'all';
let tipoFiltro = 'prio';
let busquedaActiva = '';
let soloRevisados = false;
let filtroFecha = 'all';
const revisados = new Set();

// Poblar selector de fechas
const sel = document.getElementById('date-select');
fechasUnicas.forEach(f => {{
  const opt = document.createElement('option');
  opt.value = f;
  opt.textContent = f;
  sel.appendChild(opt);
}});

function filtrar(el, val, tipo) {{
  filtroActivo = val;
  tipoFiltro = tipo;
  soloRevisados = false;
  document.querySelectorAll('.pill').forEach(p => p.classList.remove('active'));
  el.classList.add('active');
  aplicarFiltros();
}}

function filtrarRevisados(el) {{
  soloRevisados = !soloRevisados;
  el.classList.toggle('active', soloRevisados);
  aplicarFiltros();
}}

function filtrarFecha(val) {{
  filtroFecha = val;
  aplicarFiltros();
}}

function buscar(val) {{
  busquedaActiva = val.toLowerCase();
  aplicarFiltros();
}}

function aplicarFiltros() {{
  const cards = document.querySelectorAll('.card');
  let visibles = 0;
  cards.forEach((card, i) => {{
    const prio = card.dataset.prioridad;
    const fuente = card.dataset.fuente;
    const texto = card.dataset.texto || '';
    const cardFecha = card.dataset.fecha || '';
    const esRevisado = revisados.has(i);
    const matchFiltro = filtroActivo === 'all' ||
      (tipoFiltro === 'prio' && prio === filtroActivo) ||
      (tipoFiltro === 'fuente' && fuente === filtroActivo);
    const matchBusqueda = busquedaActiva === '' || texto.includes(busquedaActiva);
    const matchRevisado = !soloRevisados || esRevisado;
    const matchFecha = filtroFecha === 'all' || cardFecha === filtroFecha;
    if (matchFiltro && matchBusqueda && matchRevisado && matchFecha) {{
      card.classList.remove('hidden');
      visibles++;
    }} else {{
      card.classList.add('hidden');
    }}
  }});
  document.getElementById('empty').style.display = visibles === 0 ? 'block' : 'none';
}}

function marcarRevisado(i) {{
  const btn = document.getElementById('btn-rev-' + i);
  const card = document.getElementById('card-' + i);
  if (revisados.has(i)) {{
    revisados.delete(i);
    btn.innerHTML = '⬜ Por revisar';
    btn.style.background = 'white';
    btn.style.color = '#475569';
    btn.style.borderColor = '#e2e8f0';
    card.classList.remove('revisado');
  }} else {{
    revisados.add(i);
    btn.innerHTML = '✅ Revisado';
    btn.style.background = '#f0fdf4';
    btn.style.color = '#16a34a';
    btn.style.borderColor = '#bbf7d0';
    card.classList.add('revisado');
  }}
  actualizarEstado();
}}

function actualizarEstado() {{
  const total = prospectos.length;
  const rev = revisados.size;
  document.getElementById('estado-revision').textContent = rev + ' revisados · ' + (total - rev) + ' pendientes';
  document.getElementById('btn-revisados').style.display = rev > 0 ? 'inline-flex' : 'none';
}}

function descargarCSV() {{
  const blob = new Blob(['\\uFEFF' + csvContent], {{type: 'text/csv;charset=utf-8'}});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'scouting_GDL_' + fecha + '.csv';
  a.click();
}}

function descargarRevisados() {{
  const data = prospectos.filter((_, i) => revisados.has(i));
  const rows = ['empresa,contacto,zona,fuente,score,prioridad,senal,url,fecha_deteccion'];
  data.forEach(p => {{
    rows.push([p.empresa,p.contacto||'',p.zona,p.fuente,p.score,p.prioridad,p.senal||p.senal||'',p.url||'',p.fecha_deteccion||''].map(v => '"'+(v||'')+'"').join(','));
  }});
  const blob = new Blob(['\\uFEFF' + rows.join('\\n')], {{type: 'text/csv;charset=utf-8'}});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'revisados_GDL_' + fecha + '.csv';
  a.click();
}}

function descargarPorRevisar() {{
  const data = prospectos.filter((_, i) => !revisados.has(i));
  const rows = ['empresa,contacto,zona,fuente,score,prioridad,senal,url,fecha_deteccion'];
  data.forEach(p => {{
    rows.push([p.empresa,p.contacto||'',p.zona,p.fuente,p.score,p.prioridad,p.senal||'',p.url||'',p.fecha_deteccion||''].map(v => '"'+(v||'')+'"').join(','));
  }});
  const blob = new Blob(['\\uFEFF' + rows.join('\\n')], {{type: 'text/csv;charset=utf-8'}});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'por_revisar_GDL_' + fecha + '.csv';
  a.click();
}}
</script>
</body>
</html>"""


def generar_dashboard(prospectos: list, briefing: str, fecha: str, output_dir: Path, historial: list = None):
    html = generar_html(prospectos, briefing, fecha, historial)
    path = output_dir / "index.html"
    path.write_text(html, encoding="utf-8")
    print(f"Dashboard generado: {path}")
    return path
