import os, json, datetime as dt
from fastapi import FastAPI, Request, HTTPException
from dotenv import load_dotenv
from zoneinfo import ZoneInfo
from .db import init_db, get_conn
from .utils import normalize_br_phone
from .whatsapp import WhatsAppClient
from .scheduler import start_scheduler

load_dotenv()

TZ = os.getenv("TZ", "America/Sao_Paulo")
TEMPLATE_ORDER = os.getenv("WABA_TEMPLATE_ORDER", "pedido_confirmado")

app = FastAPI(title="Domaine WhatsApp MVP")

@app.on_event("startup")
def on_startup():
    init_db()
    start_scheduler()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/webhooks/bling/order")
async def bling_order_webhook(request: Request):
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    order_id = payload.get("order_id")
    customer = payload.get("customer", {})
    customer_name = customer.get("name")
    customer_phone = normalize_br_phone(customer.get("phone",""))
    created_at = payload.get("created_at") or dt.datetime.now(ZoneInfo(TZ)).isoformat()
    items = payload.get("items") or []

    if not (order_id and customer_phone):
        raise HTTPException(status_code=400, detail="Missing order_id or customer_phone")

    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO orders(order_id, customer_name, customer_phone, created_at_iso, items_json) VALUES (?,?,?,?,?)",
                    (order_id, customer_name, customer_phone, created_at, json.dumps(items, ensure_ascii=False)))
        conn.commit()
    except Exception:
        pass

    wa = WhatsAppClient()
    components = {
        "body": [
            {"type": "text", "text": customer_name or "cliente"},
            {"type": "text", "text": order_id}
        ]
    }
    try:
        wa.send_template(to=customer_phone, template=TEMPLATE_ORDER, components=components)
        cur.execute("INSERT INTO messages(order_id, msg_type, sent_at_iso) VALUES (?,?,?)",
                    (order_id, "order", dt.datetime.now(ZoneInfo(TZ)).isoformat()))
        conn.commit()
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=f"WA send error: {e}")
    conn.close()

    return {"ok": True, "order_id": order_id}

@app.post("/test/send")
async def test_send(req: Request):
    data = await req.json()
    to = data.get("to")
    template = data.get("template")
    components = data.get("components")
    if not (to and template):
        raise HTTPException(status_code=400, detail="to and template required")
    from .utils import normalize_br_phone
    to_norm = normalize_br_phone(to)
    wa = WhatsAppClient()
    try:
        res = wa.send_template(to=to_norm, template=template, components=components)
        return {"ok": True, "response": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
