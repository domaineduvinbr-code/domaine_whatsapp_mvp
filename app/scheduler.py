import os, json, datetime as dt
from zoneinfo import ZoneInfo
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from .db import get_conn
from .whatsapp import WhatsAppClient

TZ = os.getenv("TZ", "America/Sao_Paulo")
REPLEN_DAYS = int(os.getenv("REPLENISH_DAYS", "20"))
TEMPLATE_REPLEN = os.getenv("WABA_TEMPLATE_REPLEN", "recompra_20dias")

def check_and_send_replenishments():
    conn = get_conn()
    cur = conn.cursor()
    cutoff = dt.datetime.now(ZoneInfo(TZ)) - dt.timedelta(days=REPLEN_DAYS)
    cur.execute("""
        SELECT o.order_id, o.customer_name, o.customer_phone, o.created_at_iso, o.items_json
        FROM orders o
        WHERE datetime(o.created_at_iso) <= datetime(?)
          AND NOT EXISTS (
            SELECT 1 FROM messages m WHERE m.order_id = o.order_id AND m.msg_type = 'replen'
          )
    """, (cutoff.isoformat(),))
    rows = cur.fetchall()
    if not rows:
        conn.close()
        return

    wa = WhatsAppClient()
    for r in rows:
        items = json.loads(r["items_json"]) if r["items_json"] else []
        first_item = items[0]["name"] if items else "seu vinho"
        components = {
            "body": [
                {"type": "text", "text": r["customer_name"] or "cliente"},
                {"type": "text", "text": first_item}
            ]
        }
        try:
            wa.send_template(to=r["customer_phone"], template=TEMPLATE_REPLEN, components=components)
            cur.execute("INSERT INTO messages(order_id, msg_type, sent_at_iso) VALUES (?,?,?)",
                        (r["order_id"], "replen", dt.datetime.now(ZoneInfo(TZ)).isoformat()))
            conn.commit()
        except Exception as e:
            print(f"[REPLEN ERROR] order {r['order_id']}: {e}")
    conn.close()

def start_scheduler():
    sched = BackgroundScheduler(timezone=TZ)
    sched.add_job(check_and_send_replenishments, IntervalTrigger(hours=2))
    sched.start()
    return sched
