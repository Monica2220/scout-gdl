"""
generar_dashboard.py - Dashboard Scout GDL mejorado v3
"""

import json
from datetime import datetime
from pathlib import Path


def generar_html(prospectos: list, briefing: str, fecha: str, historial: list = None) -> str:

    hot  = len([p for p in prospectos if p.get("prioridad") == "hot"])
    warm = len([p for p in prospectos if p.get("prioridad") == "warm"])
    cold = len([p for p in prospectos if p.get("prioridad") == "cold"])

    color_prio  = {"hot": "#dc2626", "warm": "#d97706", "cold": "#2563eb"}
    bg_prio     = {"hot": "#fef2f2", "warm": "#fffbeb", "cold": "#eff6ff"}
    label_prio  = {"hot": "Caliente", "warm": "Tibio", "cold": "Frio"}
    icon_fuente = {"noticias":"📰","google_maps":"📍","linkedin":"💼","linkedin_apollo":"💼","twitter":"🐦","google_trends":"🔍"}
    label_fuente= {"noticias":"Noticias","google_maps":"Google Maps","linkedin":"LinkedIn","linkedin_apollo":"LinkedIn","twitter":"Twitter/X","google_trends":"Google Trends"}

    # Zonas
    zonas_count = {}
    for p in prospectos:
        z = p.get("zona","Otro")
        zonas_count[z] = zonas_count.get(z,0)+1
    zona_max = max(zonas_count.values(), default=1)
    zonas_html = ""
    for zona, cnt in sorted(zonas_count.items(), key=lambda x: x[1], reverse=True)[:6]:
        pct = int(cnt/zona_max*100)
        zonas_html += f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:7px"><span style="font-size:12px;color:#475569;width:90px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{zona}</span><div style="flex:1;height:7px;background:#f1f5f9;border-radius:4px;overflow:hidden"><div style="width:{pct}%;height:100%;background:#185FA5;border-radius:4px"></div></div><span style="font-size:12px;color:#64748b;width:18px;text-align:right">{cnt}</span></div>'

    # Trends
    trends = sorted([p for p in prospectos if p.get("fuente")=="google_trends"], key=lambda x: x.get("score",0), reverse=True)[:5]
    trends_html = ""
    for t in trends:
        s = t.get("score",0)
        c = "#dc2626" if s>=80 else "#d97706" if s>=60 else "#185FA5"
        trends_html += f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;padding-bottom:8px;border-bottom:1px solid #f1f5f9"><span style="font-size:12px;font-weight:500;flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{t.get("empresa","")}</span><div style="width:70px;height:6px;background:#f1f5f9;border-radius:3px;overflow:hidden"><div style="width:{min(s,100)}%;height:100%;background:{c};border-radius:3px"></div></div><span style="font-size:12px;color:#64748b;width:28px;text-align:right">{s}</span><span style="font-size:12px;color:#16a34a">↑</span></div>'
    if not trends_html:
        trends_html = '<p style="font-size:12px;color:#94a3b8">Sin datos de tendencias hoy</p>'

    # Historial
    hist_html = ""
    if historial:
        hist_max = max((h.get("total",0) for h in historial), default=1)
        for h in historial[-7:]:
            d = h.get("fecha","")[-5:]
            cnt = h.get("total",0)
            pct = int(cnt/hist_max*100) if hist_max>0 else 0
            it = h.get("fecha","")==fecha
            c = "#185FA5" if it else "#94a3b8"
            fw = "600" if it else "400"
            hist_html += f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:5px"><span style="font-size:11px;color:{c};font-weight:{fw};width:40px">{d}</span><div style="flex:1;height:6px;background:#f1f5f9;border-radius:3px;overflow:hidden"><div style="width:{pct}%;height:100%;background:{c};border-radius:3px"></div></div><span style="font-size:11px;color:{c};font-weight:{fw};width:18px;text-align:right">{cnt}</span></div>'
    else:
        hist_html = '<p style="font-size:12px;color:#94a3b8">El historial se acumula dia a dia</p>'

    # Fechas unicas para selector
    fechas_unicas = sorted(set(p.get("fecha_deteccion", fecha) for p in prospectos), reverse=True)

    # Tarjetas
    tarjetas = ""
    for i, p in enumerate(prospectos):
        prio = p.get("prioridad","cold")
        fk   = p.get("fuente","")
        url  = p.get("url","")
        emp  = p.get("empresa","")
        senal= p.get("senal", p.get("señal",""))
        score= p.get("score",0)
        zona = p.get("zona","")
        cont = p.get("contacto","")
        em   = p.get("email","")
        li   = p.get("linkedin","")
        fp   = p.get("fecha_deteccion", fecha)

        emp_html = f'<a href="{url}" target="_blank" style="color:#185FA5;text-decoration:none;font-size:14px;font-weight:500;word-break:break-word">{emp} ↗</a>' if url else f'<span style="font-size:14px;font-weight:500;color:#0f172a;word-break:break-word">{emp}</span>'

        cont_html = ""
        if cont: cont_html += f'<div style="font-size:12px;color:#64748b;margin-top:2px">{cont}</div>'
        if em:   cont_html += f'<a href="mailto:{em}" style="font-size:11px;color:#185FA5;word-break:break-all">{em}</a>'

        links_html = ""
        if url: links_html += f'<a href="{url}" target="_blank" style="font-size:11px;color:#185FA5;text-decoration:none;padding:3px 8px;border:1px solid #bfdbfe;border-radius:4px;background:#eff6ff;margin-right:4px">Ver fuente ↗</a>'
        if li:  links_html += f'<a href="{li}" target="_blank" style="font-size:11px;color:#185FA5;text-decoration:none;padding:3px 8px;border:1px solid #bfdbfe;border-radius:4px;background:#eff6ff">LinkedIn ↗</a>'

        tarjetas += f"""
        <div class="card" id="card-{i}" data-prioridad="{prio}" data-fuente="{fk}" data-zona="{zona.lower()}" data-fecha="{fp}" data-texto="{emp.lower()} {zona.lower()} {senal.lower()}">
          <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:10px;margin-bottom:8px">
            <div style="flex:1;min-width:0">{emp_html}{cont_html}</div>
            <div style="width:38px;height:38px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:700;flex-shrink:0;background:{bg_prio.get(prio,'#f1f5f9')};color:{color_prio.get(prio,'#475569')}">{score}</div>
          </div>
          <div style="display:flex;gap:5px;flex-wrap:wrap;margin-bottom:8px">
            <span style="font-size:11px;padding:2px 7px;border-radius:4px;background:#f1f5f9;color:#475569">📍 {zona}</span>
            <span style="font-size:11px;padding:2px 7px;border-radius:4px;background:#f1f5f9;color:#475569">{icon_fuente.get(fk,'')} {label_fuente.get(fk,fk)}</span>
            <span style="font-size:11px;padding:2px 7px;border-radius:4px;font-weight:600;background:{bg_prio.get(prio,'#f1f5f9')};color:{color_prio.get(prio,'#475569')}">{label_prio.get(prio,'')}</span>
          </div>
          <div style="font-size:12px;color:#64748b;line-height:1.6;margin-bottom:8px" id="senal-{i}">{senal}</div>
          {f'<div style="margin-bottom:8px">{links_html}</div>' if links_html else ''}
          <div style="padding-top:8px;border-top:1px solid #f1f5f9;display:flex;justify-content:space-between;align-items:center">
            <button onclick="marcarRevisado({i})" id="btn-rev-{i}" style="font-size:11px;padding:3px 9px;border:1px solid #e2e8f0;border-radius:5px;background:white;color:#475569;cursor:pointer">⬜ Por revisar</button>
            <span style="font-size:11px;color:#94a3b8">{fp}</span>
          </div>
        </div>"""

    # Briefing completo como JSON para expandir
    briefing_limpio = briefing.replace("`","'").replace("\\","")
    briefing_preview = briefing.replace("\n","<br>").replace("**","<b>").replace("##","").replace("#","")
    prospectos_json = json.dumps(prospectos, ensure_ascii=False)
    fechas_json = json.dumps(fechas_unicas)

    csv_rows = ["empresa,contacto,zona,fuente,score,prioridad,senal,url,fecha_deteccion"]
    for p in prospectos:
        row = [p.get("empresa","").replace(",",""), p.get("contacto","").replace(",",""), p.get("zona",""), p.get("fuente",""), str(p.get("score",0)), p.get("prioridad",""), p.get("senal",p.get("señal","")).replace(",",""), p.get("url",""), p.get("fecha_deteccion","")]
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
    .btn-top{{font-size:12px;padding:6px 14px;border-radius:6px;border:1px solid rgba(255,255,255,.2);background:rgba(255,255,255,.08);color:white;cursor:pointer}}
    .btn-top:hover{{background:rgba(255,255,255,.18)}}
    .kpis{{display:grid;grid-template-columns:repeat(4,1fr);background:white;border-bottom:1px solid #e2e8f0}}
    .kpi{{padding:16px 12px;text-align:center;border-right:1px solid #e2e8f0}}
    .kpi:last-child{{border-right:none}}
    .kpi-val{{font-size:28px;font-weight:700}}
    .kpi-label{{font-size:11px;color:#64748b;margin-top:2px}}
    .main{{display:grid;grid-template-columns:1fr 260px}}
    .left{{padding:20px 24px;min-width:0}}
    .right{{border-left:1px solid #e2e8f0;padding:20px;background:white}}
    .sec{{font-size:11px;font-weight:600;color:#64748b;text-transform:uppercase;letter-spacing:.5px;margin-bottom:12px}}
    .briefing-box{{background:#eff6ff;border-left:3px solid #2563eb;padding:12px 16px;border-radius:0 8px 8px 0;margin-bottom:16px;font-size:13px;line-height:1.7;color:#1e40af}}
    .briefing-toggle{{font-size:12px;color:#2563eb;cursor:pointer;margin-top:8px;display:inline-block;text-decoration:underline}}
    .filters{{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:16px;align-items:center}}
    .pill{{font-size:12px;padding:4px 12px;border-radius:20px;border:1px solid #e2e8f0;background:white;color:#475569;cursor:pointer;transition:all .15s;white-space:nowrap}}
    .pill:hover{{border-color:#94a3b8}}
    .pill.active{{background:#0f172a;color:white;border-color:#0f172a}}
    .search-box{{flex:1;min-width:140px;padding:5px 12px;border:1px solid #e2e8f0;border-radius:20px;font-size:12px;outline:none}}
    .date-inputs{{display:flex;align-items:center;gap:6px;font-size:12px;color:#475569}}
    .date-input{{padding:4px 8px;border:1px solid #e2e8f0;border-radius:6px;font-size:12px;color:#1e293b;outline:none;background:white}}
    .cards{{display:grid;grid-template-columns:repeat(auto-fill,minmax(290px,1fr));gap:12px}}
    .card{{background:white;border:1px solid #e2e8f0;border-radius:10px;padding:14px;border-left:4px solid #e2e8f0}}
    .card[data-prioridad="hot"]{{border-left-color:#dc2626}}
    .card[data-prioridad="warm"]{{border-left-color:#d97706}}
    .card[data-prioridad="cold"]{{border-left-color:#2563eb}}
    .card.hidden{{display:none}}
    .card.revisado{{opacity:.5}}
    .empty{{text-align:center;color:#94a3b8;padding:48px;font-size:14px;display:none}}
    .divider{{height:1px;background:#e2e8f0;margin:16px 0}}
    .footer{{text-align:center;padding:20px;font-size:12px;color:#94a3b8;border-top:1px solid #e2e8f0;background:white}}
    @media(max-width:700px){{.kpis{{grid-template-columns:repeat(2,1fr)}}.main{{grid-template-columns:1fr}}.right{{border-left:none;border-top:1px solid #e2e8f0}}.topbar,.left,.right{{padding:14px 16px}}}}
  </style>
</head>
<body>

<div class="topbar">
  <div>
    <div class="topbar-title">🏗️ Scout GDL</div>
    <div class="topbar-sub">Guadalajara · Zona Metropolitana · {fecha}</div>
  </div>
  <div style="display:flex;gap:8px;flex-wrap:wrap">
    <button class="btn-top" onclick="descargarCSV()">⬇ Descargar CSV</button>
    <button class="btn-top" onclick="descargarPorRevisar()">⬇ Por revisar</button>
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

    <div class="briefing-box" style="margin-top:4px">
      <div id="briefing-texto" style="overflow:hidden;max-height:80px;transition:max-height .3s ease">{briefing_preview}</div>
      <span class="briefing-toggle" onclick="toggleBriefing(this)">Ver completo ▼</span>
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
      <div class="date-inputs">
        <span>Desde</span>
        <input type="date" class="date-input" id="fecha-desde" onchange="aplicarFiltros()">
        <span>hasta</span>
        <input type="date" class="date-input" id="fecha-hasta" onchange="aplicarFiltros()">
      </div>
      <input class="search-box" type="text" placeholder="Buscar empresa o zona..." oninput="buscar(this.value)">
    </div>

    <div class="cards" id="cards">{tarjetas}</div>
    <div class="empty" id="empty">Sin resultados para este filtro</div>

  </div>

  <div class="right">
    <div class="sec">Google Trends — Jalisco</div>
    {trends_html}
    <div class="divider"></div>
    <div class="sec">Prospectos por zona</div>
    {zonas_html}
    <div class="divider"></div>
    <div class="sec">Historial 7 dias</div>
    {hist_html}
    <div class="divider"></div>
    <div style="background:#f8fafc;border-radius:8px;padding:12px;font-size:12px;color:#475569">
      <div style="font-weight:600;margin-bottom:4px;color:#1e293b">Estado de revision</div>
      <div id="estado-revision">0 revisados · {len(prospectos)} pendientes</div>
    </div>
  </div>
</div>

<div class="footer">Scout GDL · Guadalajara Zona Metropolitana · Actualizado cada dia a las 7:00 AM</div>

<script>
const prospectos = {prospectos_json};
const csvContent = `{csv_content}`;
const fecha = '{fecha}';
let filtroActivo = 'all';
let tipoFiltro = 'prio';
let busquedaActiva = '';
let soloRevisados = false;
const revisados = new Set();

// Briefing expandible
let briefingExpandido = false;
function toggleBriefing(el) {{
  const txt = document.getElementById('briefing-texto');
  briefingExpandido = !briefingExpandido;
  txt.style.maxHeight = briefingExpandido ? 'none' : '80px';
  el.textContent = briefingExpandido ? 'Ver menos ▲' : 'Ver completo ▼';
}}

function filtrar(el, val, tipo) {{
  filtroActivo = val; tipoFiltro = tipo; soloRevisados = false;
  document.querySelectorAll('.pill').forEach(p => p.classList.remove('active'));
  el.classList.add('active');
  aplicarFiltros();
}}

function filtrarRevisados(el) {{
  soloRevisados = !soloRevisados;
  el.classList.toggle('active', soloRevisados);
  aplicarFiltros();
}}

function buscar(val) {{ busquedaActiva = val.toLowerCase(); aplicarFiltros(); }}

function aplicarFiltros() {{
  const desde = document.getElementById('fecha-desde').value;
  const hasta = document.getElementById('fecha-hasta').value;
  const cards = document.querySelectorAll('.card');
  let visibles = 0;
  cards.forEach((card, i) => {{
    const prio   = card.dataset.prioridad;
    const fuente = card.dataset.fuente;
    const texto  = card.dataset.texto || '';
    const cf     = card.dataset.fecha || '';
    const esRev  = revisados.has(i);
    const mFiltro = filtroActivo==='all' || (tipoFiltro==='prio' && prio===filtroActivo) || (tipoFiltro==='fuente' && fuente===filtroActivo);
    const mBusq   = busquedaActiva==='' || texto.includes(busquedaActiva);
    const mRev    = !soloRevisados || esRev;
    const mDesde  = !desde || cf >= desde;
    const mHasta  = !hasta || cf <= hasta;
    if (mFiltro && mBusq && mRev && mDesde && mHasta) {{ card.classList.remove('hidden'); visibles++; }}
    else card.classList.add('hidden');
  }});
  document.getElementById('empty').style.display = visibles===0 ? 'block' : 'none';
}}

function marcarRevisado(i) {{
  const btn = document.getElementById('btn-rev-'+i);
  const card = document.getElementById('card-'+i);
  if (revisados.has(i)) {{
    revisados.delete(i);
    btn.innerHTML = '⬜ Por revisar';
    btn.style.cssText = 'font-size:11px;padding:3px 9px;border:1px solid #e2e8f0;border-radius:5px;background:white;color:#475569;cursor:pointer';
    card.classList.remove('revisado');
  }} else {{
    revisados.add(i);
    btn.innerHTML = '✅ Revisado';
    btn.style.cssText = 'font-size:11px;padding:3px 9px;border:1px solid #bbf7d0;border-radius:5px;background:#f0fdf4;color:#16a34a;cursor:pointer';
    card.classList.add('revisado');
  }}
  const rev = revisados.size;
  document.getElementById('estado-revision').textContent = rev+' revisados · '+(prospectos.length-rev)+' pendientes';
  document.getElementById('btn-revisados').style.display = rev>0 ? 'inline-block' : 'none';
}}

function descargarCSV() {{
  const blob = new Blob(['\\uFEFF'+csvContent], {{type:'text/csv;charset=utf-8'}});
  const a = document.createElement('a'); a.href = URL.createObjectURL(blob);
  a.download = 'scouting_GDL_'+fecha+'.csv'; a.click();
}}

function _csvDeArray(data) {{
  const rows = ['empresa,contacto,zona,fuente,score,prioridad,senal,url,fecha_deteccion'];
  data.forEach(p => rows.push([p.empresa,p.contacto||'',p.zona,p.fuente,p.score,p.prioridad,p.senal||p.señal||'',p.url||'',p.fecha_deteccion||''].map(v=>'"'+(v||'')+'"').join(',')));
  return rows.join('\\n');
}}

function descargarRevisados() {{
  const data = prospectos.filter((_,i) => revisados.has(i));
  const blob = new Blob(['\\uFEFF'+_csvDeArray(data)], {{type:'text/csv;charset=utf-8'}});
  const a = document.createElement('a'); a.href = URL.createObjectURL(blob);
  a.download = 'revisados_GDL_'+fecha+'.csv'; a.click();
}}

function descargarPorRevisar() {{
  const data = prospectos.filter((_,i) => !revisados.has(i));
  const blob = new Blob(['\\uFEFF'+_csvDeArray(data)], {{type:'text/csv;charset=utf-8'}});
  const a = document.createElement('a'); a.href = URL.createObjectURL(blob);
  a.download = 'por_revisar_GDL_'+fecha+'.csv'; a.click();
}}

// Poner fecha de hoy como valor por defecto en "hasta"
document.getElementById('fecha-hasta').value = fecha;
</script>
</body>
</html>"""


def generar_dashboard(prospectos: list, briefing: str, fecha: str, output_dir: Path, historial: list = None):
    html = generar_html(prospectos, briefing, fecha, historial)
    path = output_dir / "index.html"
    path.write_text(html, encoding="utf-8")
    print(f"Dashboard generado: {path}")
    return path
