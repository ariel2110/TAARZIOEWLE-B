
from urllib.parse import quote


class WhatsAppLauncherService:
    def normalize_phone(self, phone: str) -> str:
        digits = ''.join(ch for ch in phone if ch.isdigit())
        if digits.startswith('0'):
            digits = '972' + digits[1:]
        return digits

    def build_link(self, phone: str, message: str) -> dict:
        normalized = self.normalize_phone(phone)
        return {
            'normalized_phone': normalized,
            'whatsapp_url': f'https://wa.me/{normalized}?text={quote(message)}',
            'message': message,
        }
