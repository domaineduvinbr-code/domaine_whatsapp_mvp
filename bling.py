import datetime as dt
from typing import Dict, Any

def parse_bling_order(payload: Dict[str, Any]) -> Dict[str, Any]:
    if "order_id" in payload and "customer" in payload:
        return payload
    out = {
        "order_id": str(payload.get("numero") or payload.get("id") or ""),
        "created_at": payload.get("data") or payload.get("created_at") or dt.datetime.now().isoformat(),
        "customer": {
            "name": payload.get("cliente", {}).get("nome") or payload.get("cliente", {}).get("razaoSocial") or "",
            "phone": payload.get("cliente", {}).get("celular") or payload.get("cliente", {}).get("fone") or "",
        },
        "items": []
    }
    itens = payload.get("itens") or payload.get("items") or []
    for it in itens:
        out["items"].append({
            "sku": it.get("codigo") or it.get("sku") or "",
            "name": it.get("descricao") or it.get("name") or "",
            "qty": int(it.get("quantidade") or it.get("qty") or 1),
            "price": float(it.get("valor") or it.get("price") or 0.0),
        })
    return out
