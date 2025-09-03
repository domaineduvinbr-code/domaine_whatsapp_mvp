import re

def normalize_br_phone(raw: str) -> str:
    if not raw:
        return raw
    s = re.sub(r"[^0-9+]", "", raw)
    if not s.startswith("+"):
        s = re.sub(r"^0+", "", s)
        if not s.startswith("55"):
            s = "55" + s
        s = "+" + s
    return s
