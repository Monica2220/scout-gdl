

import schedule
import time
import logging
from datetime import datetime
from src.agent import run

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)


def job():
    log.info(f"⏰ Ejecución programada: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    try:
        run()
    except Exception as e:
        log.error(f"Error en ejecución: {e}")


# Programar para las 7:00 am todos los días
schedule.every().day.at("07:00").do(job)

log.info("🕐 Scheduler activo — esperando las 7:00 am...")
log.info("   Presiona Ctrl+C para detener")



while True:
    schedule.run_pending()
    time.sleep(60)
