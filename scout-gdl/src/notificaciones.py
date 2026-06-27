"""
notificaciones.py - Envio de briefing diario por WhatsApp y Email
"""

import os
import smtplib
import logging
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from pathlib import Path

log = logging.getLogger(__name__)

TWILIO_ACCOUNT_SID   = os.environ.get("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN    = os.environ.get("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP_FROM = os.environ.get("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")
TU_WHATSAPP          = os.environ.get("TU_WHATSAPP", "")

RESEND_API_KEY   = os.environ.get("RESEND_API_KEY", "")
EMAIL_DESTINO    = os.environ.get("EMAIL_DESTINO", "")
EMAIL_REMITENTE  = os.environ.get("EMAIL_REMITENTE", "onboarding@resend.dev")

GMAIL_USER         = os.environ.get("GMAIL_USER", "")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")


def enviar_whatsapp(briefing: str, prospectos: list, fecha: str) -> bool:
    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TU_WHATSAPP]):
        log.warning("WhatsApp: faltan credenciales Twilio en .env")
        return False

    try:
        from twilio.rest import Client
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

        hot  = [p for p in prospectos if p.get("prioridad") == "hot"]
        warm = [p for p in prospectos if p.get("prioridad") == "warm"]
        top3 = sorted(prospectos, key=lambda x: x.get("score", 0), reverse=True)[:3]

        top3_txt = ""
        for i, p in enumerate(top3):
            url = p.get("url", "")
            ref = f"\n     {url}" if url else ""
            top3_txt += (
                f"  {i+1}. *{p.get('empresa','')}* ({p.get('zona','')}) - Score {p.get('score','')}\n"
                f"     _{p.get('senal', p.get('señal',''))}_"
                f"{ref}\n"
            )

        mensaje = (
            f"🏗️ *Scout GDL - {fecha}*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 {len(prospectos)} prospectos encontrados hoy\n"
            f"🔴 Calientes: {len(hot)}   🟡 Tibios: {len(warm)}\n\n"
            f"*Top 3 del dia:*\n{top3_txt}\n"
            f"📋 *Analisis IA:*\n{briefing[:500]}{'...' if len(briefing) > 500 else ''}\n\n"
            f"_CSV adjunto en tu correo_"
        )

        client.messages.create(
            from_=TWILIO_WHATSAPP_FROM,
            to=TU_WHATSAPP,
            body=mensaje,
        )
        log.info(f"WhatsApp enviado a {TU_WHATSAPP}")
        return True

    except ImportError:
        log.error("Instala twilio: pip install twilio")
        return False
    except Exception as e:
        log.error(f"Error enviando WhatsApp: {e}")
        return False


def _html_email(briefing: str, prospectos: list, fecha: str) -> str:
    hot  = len([p for p in prospectos if p.get("prioridad") == "hot"])
    warm = len([p for p in prospectos if p.get("prioridad") == "warm"])
    cold = len([p for p in prospectos if p.get("prioridad") == "cold"])
    top  = sorted(prospectos, key=lambda x: x.get("score", 0), reverse=True)[:15]

    color_prio = {"hot": "#dc2626", "warm": "#d97706", "cold": "#2563eb"}
    label_prio = {"hot": "Caliente", "warm": "Tibio", "cold": "Frio"}
    label_fuente = {
        "noticias": "Noticias",
        "google_maps": "Google Maps",
        "linkedin": "LinkedIn",
        "linkedin_apollo": "LinkedIn",
        "twitter": "Twitter/X",
        "google_trends": "Google Trends",
    }
    icon_fuente = {
        "noticias": "📰",
        "google_maps": "📍",
        "linkedin": "💼",
        "linkedin_apollo": "💼",
        "twitter": "🐦",
        "google_trends": "🔍",
    }

    filas = ""
    for p in top:
        color = color_prio.get(p.get("prioridad", "cold"), "#2563eb")
        fuente_key = p.get("fuente", "")
        fuente_label = label_fuente.get(fuente_key, fuente_key)
        fuente_icon = icon_fuente.get(fuente_key, "")
        url = p.get("url", "")
        empresa = p.get("empresa", "")
        senal = p.get("senal", p.get("señal", ""))

        empresa_cell = (
            f'<a href="{url}" style="color:#185FA5;text-decoration:none;font-weight:500">{empresa} ↗</a>'
            if url else
            f'<span style="font-weight:500">{empresa}</span>'
        )

        filas += f"""
        <tr style="border-bottom:1px solid #f0f0f0">
          <td style="padding:10px 12px">{empresa_cell}</td>
          <td style="padding:10px 12px;color:#666;font-size:13px">{p.get('zona','')}</td>
          <td style="padding:10px 12px;color:#666;font-size:13px">{fuente_icon} {fuente_label}</td>
          <td style="padding:10px 12px;text-align:center">
            <span style="background:#f0f9ff;color:#0369a1;padding:2px 8px;border-radius:4px;font-size:13px;font-weight:600">
              {p.get('score',0)}
            </span>
          </td>
          <td style="padding:10px 12px">
            <span style="color:{color};font-size:12px;font-weight:600">
              {label_prio.get(p.get('prioridad',''), '-')}
            </span>
          </td>
          <td style="padding:10px 12px;color:#555;font-size:12px">{senal}</td>
        </tr>"""

    briefing_html = briefing.replace("\n", "<br>")

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f8f8f8;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif">
  <div style="max-width:720px;margin:32px auto;background:#fff;border-radius:12px;overflow:hidden;border:1px solid #e8e8e8">

    <div style="background:#0f172a;padding:28px 32px">
      <div style="font-size:22px;font-weight:600;color:#fff">🏗️ Scout GDL</div>
      <div style="color:#94a3b8;font-size:14px;margin-top:4px">Reporte diario — {fecha}</div>
    </div>

    <div style="display:flex;border-bottom:1px solid #f0f0f0">
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
        <div style="font-size:12px;color:#888;margin-top:2px">Frios 🔵</div>
      </div>
    </div>

    <div style="padding:28px 32px">

      <div style="background:#f0f9ff;border-left:4px solid #0369a1;border-radius:0 8px 8px 0;padding:16px 20px;margin-bottom:28px">
        <div style="font-size:12px;font-weight:600;color:#0369a1;text-transform:uppercase;letter-spacing:.5px;margin-bottom:8px">
          Analisis IA del dia
        </div>
        <div style="font-size:14px;line-height:1.7;color:#1e293b">{briefing_html}</div>
      </div>

      <div style="font-size:15px;font-weight:600;color:#0f172a;margin-bottom:14px">
        Top {len(top)} prospectos del dia
      </div>
      <table style="width:100%;border-collapse:collapse;font-size:13px">
        <thead>
          <tr style="background:#f8f8f8">
            <th style="padding:10px 12px;text-align:left;color:#888;font-weight:500">Empresa / Link</th>
            <th style="padding:10px 12px;text-align:left;color:#888;font-weight:500">Zona</th>
            <th style="padding:10px 12px;text-align:left;color:#888;font-weight:500">Fuente</th>
            <th style="padding:10px 12px;text-align:center;color:#888;font-weight:500">Score</th>
            <th style="padding:10px 12px;text-align:left;color:#888;font-weight:500">Prioridad</th>
            <th style="padding:10px 12px;text-align:left;color:#888;font-weight:500">Senal detectada</th>
          </tr>
        </thead>
        <tbody>{filas}</tbody>
      </table>

      <div style="margin-top:20px;padding:14px 16px;background:#f8f8f8;border-radius:8px;font-size:12px;color:#666">
        📎 El CSV completo con todos los prospectos va adjunto en este correo.
      </div>

      <div style="margin-top:28px;padding-top:20px;border-top:1px solid #f0f0f0;font-size:12px;color:#aaa;text-align:center">
        Scout GDL • Guadalajara Zona Metropolitana<br>
        Generado automaticamente a las 7:00 AM
      </div>
    </div>
  </div>
</body>
</html>"""


def enviar_email_resend(briefing: str, prospectos: list, fecha: str, csv_path: Path) -> bool:
    if not all([RESEND_API_KEY, EMAIL_DESTINO]):
        log.warning("Email Resend: faltan RESEND_API_KEY o EMAIL_DESTINO en .env")
        return False

    try:
        import resend
        resend.api_key = RESEND_API_KEY

        attachments = []
        if csv_path and csv_path.exists():
            with open(csv_path, "rb") as f:
                csv_data = base64.b64encode(f.read()).decode("utf-8")
            attachments.append({
                "filename": csv_path.name,
                "content": csv_data,
            })

        params = {
            "from": EMAIL_REMITENTE,
            "to": EMAIL_DESTINO,
            "subject": f"🏗️ Scout GDL - {len(prospectos)} prospectos - {fecha}",
            "html": _html_email(briefing, prospectos, fecha),
        }
        if attachments:
            params["attachments"] = attachments

        resend.Emails.send(params)
        log.info(f"Email enviado a {EMAIL_DESTINO} via Resend (con CSV adjunto)")
        return True

    except ImportError:
        log.warning("Resend no instalado - intentando Gmail SMTP...")
        return enviar_email_gmail(briefing, prospectos, fecha, csv_path)
    except Exception as e:
        log.error(f"Error enviando email Resend: {e}")
        return False


def enviar_email_gmail(briefing: str, prospectos: list, fecha: str, csv_path: Path) -> bool:
    if not all([GMAIL_USER, GMAIL_APP_PASSWORD, EMAIL_DESTINO]):
        log.warning("Email Gmail: faltan credenciales en .env")
        return False

    try:
        msg = MIMEMultipart("mixed")
        msg["Subject"] = f"🏗️ Scout GDL - {len(prospectos)} prospectos - {fecha}"
        msg["From"]    = GMAIL_USER
        msg["To"]      = EMAIL_DESTINO

        html_part = MIMEText(_html_email(briefing, prospectos, fecha), "html", "utf-8")
        msg.attach(html_part)

        if csv_path and csv_path.exists():
            with open(csv_path, "rb") as f:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header("Content-Disposition", f"attachment; filename={csv_path.name}")
                msg.attach(part)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_USER, EMAIL_DESTINO, msg.as_string())

        log.info(f"Email enviado a {EMAIL_DESTINO} via Gmail (con CSV adjunto)")
        return True

    except Exception as e:
        log.error(f"Error enviando email Gmail: {e}")
        return False


def notificar(briefing: str, prospectos: list, csv_path: Path):
    fecha = datetime.now().strftime("%Y-%m-%d")
    log.info("Enviando notificaciones...")

    wa_ok    = enviar_whatsapp(briefing, prospectos, fecha)
    email_ok = enviar_email_resend(briefing, prospectos, fecha, csv_path)

    if wa_ok:
        log.info("WhatsApp enviado")
    if email_ok:
        log.info("Email enviado")
    if not wa_ok and not email_ok:
        log.warning("Ninguna notificacion enviada - revisa tus credenciales en .env")
