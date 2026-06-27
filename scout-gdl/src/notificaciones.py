"""
notificaciones.py — Envío de briefing diario por WhatsApp y Email
Servicios usados:
  - WhatsApp: Twilio (plan gratuito incluye sandbox de WhatsApp)
  - Email:    Resend (100 emails/día gratis) o Gmail SMTP
"""

import os
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from pathlib import Path

log = logging.getLogger(__name__)

# ── Credenciales desde variables de entorno ────────────────────────────────────
TWILIO_ACCOUNT_SID  = os.environ.get("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN   = os.environ.get("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP_FROM = os.environ.get("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")  # sandbox Twilio
TU_WHATSAPP          = os.environ.get("TU_WHATSAPP", "")   # ej: whatsapp:+523311234567

RESEND_API_KEY      = os.environ.get("RESEND_API_KEY", "")
EMAIL_DESTINO       = os.environ.get("EMAIL_DESTINO", "")
EMAIL_REMITENTE     = os.environ.get("EMAIL_REMITENTE", "scout@tudominio.com")

# Alternativa: Gmail SMTP (si no usas Resend)
GMAIL_USER          = os.environ.get("GMAIL_USER", "")
GMAIL_APP_PASSWORD  = os.environ.get("GMAIL_APP_PASSWORD", "")  # App Password, no tu contraseña normal


# ── WhatsApp vía Twilio ────────────────────────────────────────────────────────

def enviar_whatsapp(briefing: str, prospectos: list[dict], fecha: str) -> bool:
    """
    Envía el briefing por WhatsApp usando Twilio.
    Plan gratuito (sandbox): funciona perfecto para uso personal.
    """
    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TU_WHATSAPP]):
        log.warning("WhatsApp: faltan credenciales Twilio en .env")
        return False

    try:
        from twilio.rest import Client
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

        # Contar prospectos por prioridad
        hot   = [p for p in prospectos if p.get("prioridad") == "hot"]
        warm  = [p for p in prospectos if p.get("prioridad") == "warm"]
        total = len(prospectos)

        # Mensaje corto y accionable para WhatsApp
        top3 = sorted(prospectos, key=lambda x: x.get("score", 0), reverse=True)[:3]
        top3_txt = "\n".join(
            f"  {i+1}. *{p['empresa']}* ({p['zona']}) — Score {p['score']}\n"
            f"     _{p['señal']}_"
            for i, p in enumerate(top3)
        )

        mensaje = (
            f"🏗️ *Scout GDL — {fecha}*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 {total} prospectos encontrados hoy\n"
            f"🔴 Calientes: {len(hot)}   🟡 Tibios: {len(warm)}\n\n"
            f"*Top 3 del día:*\n{top3_txt}\n\n"
            f"📋 *Análisis IA:*\n{briefing[:600]}{'...' if len(briefing) > 600 else ''}\n\n"
            f"_CSV disponible en GitHub Actions → Artifacts_"
        )

        client.messages.create(
            from_=TWILIO_WHATSAPP_FROM,
            to=TU_WHATSAPP,
            body=mensaje,
        )
        log.info(f"✅ WhatsApp enviado a {TU_WHATSAPP}")
        return True

    except ImportError:
        log.error("Instala twilio: pip install twilio")
        return False
    except Exception as e:
        log.error(f"Error enviando WhatsApp: {e}")
        return False


# ── Email vía Resend ───────────────────────────────────────────────────────────

def _html_email(briefing: str, prospectos: list[dict], fecha: str, csv_path: Path) -> str:
    """Genera el HTML del email con tabla de prospectos."""
    hot  = len([p for p in prospectos if p.get("prioridad") == "hot"])
    warm = len([p for p in prospectos if p.get("prioridad") == "warm"])
    cold = len([p for p in prospectos if p.get("prioridad") == "cold"])
    top  = sorted(prospectos, key=lambda x: x.get("score", 0), reverse=True)[:10]

    color_prio = {"hot": "#dc2626", "warm": "#d97706", "cold": "#2563eb"}
    label_prio = {"hot": "Caliente", "warm": "Tibio", "cold": "Frío"}
    label_fuente = {"noticias": "Noticias", "google_maps": "Google Maps",
                    "linkedin": "LinkedIn", "twitter": "Twitter/X"}

    filas = ""
    for p in top:
        color = color_prio.get(p.get("prioridad", "cold"), "#2563eb")
        filas += f"""
        <tr style="border-bottom:1px solid #f0f0f0">
          <td style="padding:10px 12px;font-weight:500">{p.get('empresa','')}</td>
          <td style="padding:10px 12px;color:#666">{p.get('zona','')}</td>
          <td style="padding:10px 12px;color:#666">{label_fuente.get(p.get('fuente',''),'')}</td>
          <td style="padding:10px 12px;text-align:center">
            <span style="background:#f0f9ff;color:#0369a1;padding:2px 8px;border-radius:4px;font-size:13px;font-weight:600">
              {p.get('score',0)}
            </span>
          </td>
          <td style="padding:10px 12px">
            <span style="color:{color};font-size:12px;font-weight:600">
              ● {label_prio.get(p.get('prioridad',''),'—')}
            </span>
          </td>
          <td style="padding:10px 12px;color:#555;font-size:13px">{p.get('señal','')}</td>
        </tr>"""

    briefing_html = briefing.replace("\n", "<br>")

    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f8f8f8;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif">
  <div style="max-width:680px;margin:32px auto;background:#fff;border-radius:12px;overflow:hidden;border:1px solid #e8e8e8">

    <!-- Header -->
    <div style="background:#0f172a;padding:28px 32px">
      <div style="font-size:22px;font-weight:600;color:#fff">🏗️ Scout GDL</div>
      <div style="color:#94a3b8;font-size:14px;margin-top:4px">Reporte diario — {fecha}</div>
    </div>

    <!-- Métricas -->
    <div style="display:flex;gap:0;border-bottom:1px solid #f0f0f0">
      <div style="flex:1;padding:20px 24px;border-right:1px solid #f0f0f0;text-align:center">
        <div style="font-size:28px;font-weight:700;color:#0f172a">{len(prospectos)}</div>
        <div style="font-size:12px;color:#888;margin-top:2px">Prospectos totales</div>
      </div>
      <div style="flex:1;padding:20px 24px;border-right:1px solid #f0f0f0;text-align:center">
        <div style="font-size:28px;font-weight:700;color:#dc2626">{hot}</div>
        <div style="font-size:12px;color:#888;margin-top:2px">Calientes 🔴</div>
      </div>
      <div style="flex:1;padding:20px 24px;border-right:1px solid #f0f0f0;text-align:center">
        <div style="font-size:28px;font-weight:700;color:#d97706">{warm}</div>
        <div style="font-size:12px;color:#888;margin-top:2px">Tibios 🟡</div>
      </div>
      <div style="flex:1;padding:20px 24px;text-align:center">
        <div style="font-size:28px;font-weight:700;color:#2563eb">{cold}</div>
        <div style="font-size:12px;color:#888;margin-top:2px">Fríos 🔵</div>
      </div>
    </div>

    <div style="padding:28px 32px">

      <!-- Briefing IA -->
      <div style="background:#f0f9ff;border-left:4px solid #0369a1;border-radius:0 8px 8px 0;padding:16px 20px;margin-bottom:28px">
        <div style="font-size:12px;font-weight:600;color:#0369a1;text-transform:uppercase;letter-spacing:.5px;margin-bottom:8px">
          Análisis IA del día
        </div>
        <div style="font-size:14px;line-height:1.7;color:#1e293b">{briefing_html}</div>
      </div>

      <!-- Tabla top 10 -->
      <div style="font-size:15px;font-weight:600;color:#0f172a;margin-bottom:14px">
        Top {len(top)} prospectos del día
      </div>
      <table style="width:100%;border-collapse:collapse;font-size:13px">
        <thead>
          <tr style="background:#f8f8f8">
            <th style="padding:10px 12px;text-align:left;color:#888;font-weight:500">Empresa</th>
            <th style="padding:10px 12px;text-align:left;color:#888;font-weight:500">Zona</th>
            <th style="padding:10px 12px;text-align:left;color:#888;font-weight:500">Fuente</th>
            <th style="padding:10px 12px;text-align:center;color:#888;font-weight:500">Score</th>
            <th style="padding:10px 12px;text-align:left;color:#888;font-weight:500">Prioridad</th>
            <th style="padding:10px 12px;text-align:left;color:#888;font-weight:500">Señal detectada</th>
          </tr>
        </thead>
        <tbody>{filas}</tbody>
      </table>

      <!-- Footer -->
      <div style="margin-top:28px;padding-top:20px;border-top:1px solid #f0f0f0;font-size:12px;color:#aaa;text-align:center">
        Scout GDL • Guadalajara Zona Metropolitana<br>
        CSV completo disponible en GitHub Actions → Artifacts
      </div>
    </div>
  </div>
</body>
</html>"""


def enviar_email_resend(briefing: str, prospectos: list[dict], fecha: str, csv_path: Path) -> bool:
    """Envía el briefing por email usando Resend (100 emails/día gratis)."""
    if not all([RESEND_API_KEY, EMAIL_DESTINO]):
        log.warning("Email Resend: faltan RESEND_API_KEY o EMAIL_DESTINO en .env")
        return False

    try:
        import resend
        resend.api_key = RESEND_API_KEY

        resend.Emails.send({
            "from": EMAIL_REMITENTE,
            "to": EMAIL_DESTINO,
            "subject": f"🏗️ Scout GDL — {len(prospectos)} prospectos — {fecha}",
            "html": _html_email(briefing, prospectos, fecha, csv_path),
        })
        log.info(f"✅ Email enviado a {EMAIL_DESTINO} vía Resend")
        return True

    except ImportError:
        log.warning("Resend no instalado — intentando Gmail SMTP...")
        return enviar_email_gmail(briefing, prospectos, fecha, csv_path)
    except Exception as e:
        log.error(f"Error enviando email Resend: {e}")
        return False


def enviar_email_gmail(briefing: str, prospectos: list[dict], fecha: str, csv_path: Path) -> bool:
    """Alternativa: envía por Gmail SMTP (usa App Password, no tu contraseña)."""
    if not all([GMAIL_USER, GMAIL_APP_PASSWORD, EMAIL_DESTINO]):
        log.warning("Email Gmail: faltan GMAIL_USER, GMAIL_APP_PASSWORD o EMAIL_DESTINO en .env")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"🏗️ Scout GDL — {len(prospectos)} prospectos — {fecha}"
        msg["From"]    = GMAIL_USER
        msg["To"]      = EMAIL_DESTINO

        html = _html_email(briefing, prospectos, fecha, csv_path)
        msg.attach(MIMEText(html, "html", "utf-8"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_USER, EMAIL_DESTINO, msg.as_string())

        log.info(f"✅ Email enviado a {EMAIL_DESTINO} vía Gmail")
        return True

    except Exception as e:
        log.error(f"Error enviando email Gmail: {e}")
        return False


# ── Función principal ─────────────────────────────────────────────────────────

def notificar(briefing: str, prospectos: list[dict], csv_path: Path):
    """Llama a esta función desde agent.py para enviar todas las notificaciones."""
    fecha = datetime.now().strftime("%Y-%m-%d")
    log.info("📨 Enviando notificaciones...")

    wa_ok    = enviar_whatsapp(briefing, prospectos, fecha)
    email_ok = enviar_email_resend(briefing, prospectos, fecha, csv_path)

    if wa_ok:
        log.info("✅ WhatsApp enviado")
    if email_ok:
        log.info("✅ Email enviado")
    if not wa_ok and not email_ok:
        log.warning("⚠️  Ninguna notificación enviada — revisa tus credenciales en .env")
