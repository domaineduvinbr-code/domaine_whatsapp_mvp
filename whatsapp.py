import os
import requests
from dotenv import load_dotenv

load_dotenv()

WABA_TOKEN = os.getenv("WABA_ACCESS_TOKEN")
WABA_PHONE_ID = os.getenv("WABA_PHONE_NUMBER_ID")
DEFAULT_LANG = os.getenv("DEFAULT_TEMPLATE_LANG", "pt_BR")

GRAPH_API_URL = f"https://graph.facebook.com/v20.0/{WABA_PHONE_ID}/messages"

class WhatsAppClient:
    def __init__(self, token: str = None, phone_id: str = None):
        self.token = token or WABA_TOKEN
        self.phone_id = phone_id or WABA_PHONE_ID

    def send_template(self, to: str, template: str, components: dict | None = None, lang: str = None):
        lang_code = lang or DEFAULT_LANG
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": {
                "name": template,
                "language": {"code": lang_code},
            },
        }
        if components:
            payload["template"]["components"] = self._components_to_wa_format(components)

        resp = requests.post(GRAPH_API_URL, headers=headers, json=payload, timeout=20)
        if resp.status_code >= 400:
            raise RuntimeError(f"WA send error {resp.status_code}: {resp.text}")
        return resp.json()

    def _components_to_wa_format(self, components: dict):
        result = []
        for comp_type, elements in components.items():
            result.append({
                "type": comp_type,
                "parameters": elements
            })
        return result
