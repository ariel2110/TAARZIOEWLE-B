"""
TAZO Voice Stream Microservice
================================
Real-time multi-language AI voice call handler.

Architecture:
  Phone ↔ Twilio ↔ [WebSocket] ↔ THIS SERVER
                                      |
                             Whisper STT (buffered μ-law)
                                      |
                             GPT-4o-mini streaming
                                      |
                         ElevenLabs WebSocket TTS
                         (text-in → mulaw_8000-out)
                                      |
                              [WebSocket] → Twilio → Phone

Language selection:
  At call start a multilingual menu is played.
  Caller presses 1=Hebrew 2=English 3=Arabic 4=Russian (DTMF).
  Language can be changed at any time during the call with the same keys.
  If the caller speaks before pressing a key, Hebrew is used by default.

Barge-in:
  While AI audio is playing, if Twilio receives voice energy above threshold
  → server sends CLEAR to Twilio + aborts ElevenLabs stream immediately.

Caller context:
  Passed as Twilio Stream <Parameter> tags from the main backend, so this
  microservice needs no DB access.

Endpoints:
  GET  /health           → 200 OK
  WS   /ws               → Twilio Media Streams WebSocket handler
"""
from __future__ import annotations

import asyncio
import base64
import io
import json
import logging
import os
import struct
import time
import wave
from dataclasses import dataclass, field
from typing import AsyncGenerator

import websockets
import websockets.exceptions
import httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from openai import AsyncOpenAI

# ── Logging ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("voice-stream")

# ── Config (from environment) ─────────────────────────────────────────────────

ELEVENLABS_API_KEY  = os.environ.get("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.environ.get("ELEVENLABS_VOICE_ID", "")   # Hebrew-capable voice
ELEVENLABS_MODEL    = os.environ.get("ELEVENLABS_MODEL", "eleven_turbo_v2_5")
OPENAI_API_KEY      = os.environ.get("OPENAI_API_KEY", "")
PORT                = int(os.environ.get("PORT", "8001"))
# Internal backend URL for sending WhatsApp/SMS links
BACKEND_INTERNAL_URL = os.environ.get("BACKEND_INTERNAL_URL", "http://localbiz-backend:8000")

# ElevenLabs WebSocket URL — ulaw_8000 is exactly what Twilio Media Streams
# expects, so we forward the base64 payload without re-encoding.
# Auth is sent via the xi-api-key header (URL query-param auth was deprecated).
_EL_WS_URL = (
    f"wss://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
    f"/stream-input"
    f"?model_id={ELEVENLABS_MODEL}"
    f"&output_format=ulaw_8000"
    f"&optimize_streaming_latency=4"
)

# ── Language configuration ────────────────────────────────────────────────────

_LANG_CONFIG: dict[str, dict] = {
    "he": {
        "name": "עברית",
        "whisper": "he",
        "lang_code": "he",
        "farewell": (
            "להתראות", "ביי", "bye",
            "תודה להתראות", "לא מעניין",
            "לא תודה", "לא צריך", "יופי תודה",
            "תודה שלום", "ביי ביי", "הכל בסדר תודה", "הכל טוב תודה",
        ),
        "system": (
            "אתה נציג שירות לקוחות של TAZO — קבוצת שירותים דיגיטליים ישראלית.\n"
            "שמך הוא טאזו. תמיד דבר בגוף ראשון.\n"
            "השתמש בשמו הפרטי של המתקשר במהלך השיחה כשזה טבעי.\n"
            "\n=== שירותי TAZO ===\n"
            "• TAZO-WEB (tazo-web.com): בניית אתרי עסקים, דף עסקי, קבלת הזמנות WhatsApp,\n"
            "  ניהול לקוחות ונאמנות, שיווק אוטומטי וסטטיסטיקות. לבעלי עסקים.\n"
            "• TAZO-GO (tazo-go.com): מערכת הסעות — נוסעים, נהגי מונית/שיתופי ושליחים.\n"
            "  נוסע: tazo-go.com | נהג: driver.tazo-go.com\n"
            "• TAZO-SYNC (tazo-sync.com): חנות אונליין, מסחר לילה (Night Rescue), ניהול משלוחים.\n"
            "• ODIN (tazo-app.com): כניסה מרכזית לכל שירותי TAZO (SSO + אימות זהות).\n"
            "• VAULT: מטבע דיגיטלי TAZ — נצבר לנהגים ומשולם על נסיעות.\n"
            "\n=== הכניסה לשירותים ===\n"
            "• TAZO-WEB: כניסה ב-tazo-web.com, אימות דרך WhatsApp (ללא סיסמה).\n"
            "• TAZO-GO נוסע: כניסה ב-tazo-go.com, מספר טלפון → קישור WhatsApp.\n"
            "• TAZO-GO נהג/שליח: רישום ב-tazo-go.com → אימות זהות (KYC) → driver.tazo-go.com.\n"
            "\n=== כלים שיש לך ===\n"
            "• שליחת קישור ב-WhatsApp או SMS:\n"
            "  כשהמשתמש מבקש קישור/לינק/הרשמה —\n"
            "  שאל אותו: 'אשלח לך את הקישור — מה אתה מעדיף, WhatsApp או SMS?'\n"
            "  לפי תשובתו:\n"
            "    WhatsApp → [SEND_LINK:wa] (או [SEND_LINK:wa:driver] וכו')\n"
            "    SMS       → [SEND_LINK:sms] (או [SEND_LINK:sms:driver] וכו')\n"
            "  אם אמר שאין לו WhatsApp → שלח ב-SMS אוטומטית.\n"
            "  אם לא ציין העדפה → שאל לפני שליחה.\n"
            "  ⚠️ אסור לומר 'שולח/שלחתי קישור' בלי [SEND_LINK] — בלעדיו לא נשלח כלום!\n"
            "• הסלמה למנהל: אם המתקשר מבקש לדבר עם מנהל/אחראי, ציין [ESCALATE_MANAGER: <סיבה קצרה>]\n"
            "  בתחילת תגובתך, ואמור: 'בשמחה! הצוות יחזור אליך בהקדם. יום נעים, להתראות!'\n"
            "\n=== כללים ===\n"
            "1. ענה אך ורק בעברית תקינה.\n"
            "2. תשובות קצרות ותמציתיות — עד 2 משפטים (שיחת טלפון!).\n"
            "3. היה ידידותי, חם ומקצועי.\n"
            "4. סיים שיחה רק אם הלקוח אמר בבירור שהסתיים: 'להתראות', 'ביי', 'לא מעניין', 'לא צריך' —\n"
            "   ענה: 'תודה שפנית, יום נעים. להתראות!' ואל תוסיף שאלות.\n"
            "   אל תסיים שיחה רק בגלל 'תודה' — יכול להיות שהשיחה נמשכת.\n"
            "   אם שאלת שאלה ובמשיב אומר רק 'לא' — תאמר: 'בסדר גמור, אם תצטרך עזרה — אני כאן. יום נעים!'\n"
            "5. אל תחשוף מידע פנימי: קוד, שמות לקוחות, פרטי שרת, מחירים מדויקים.\n"
            "6. אם אינך יודע — אמור שהצוות יחזור בהקדם.\n"
            "7. אם שאלת הלקוח מעורפלת — שאל שאלת הבהרה קצרה, אל תנחש.\n"
            "8. אתה יכול לעזור גם בשאלות כלליות (מסלולים, שעות, מזג אוויר כללי, המלצות וכו').\n"
            "   אם השאלה אינה קשורה ל-TAZO ואינך יכול לעזור — אמור בנימוס שאתה מתמחה ב-TAZO.\n"
            "9. לעולם אל תדון בנושאים רגישים: נומרולוגיה, אסטרולוגיה, פוליטיקה, דת, רפואה."
        ),
        "farewell_reply": "תודה שפנית לטאזו! יום נעים ומוצלח. להתראות!",
        "lang_change_ack": "עוברים לעברית.",
    },
    "en": {
        "name": "English",
        "whisper": "en",
        "lang_code": "en",
        "farewell": ("goodbye", "bye", "not interested", "no thanks"),
        "system": (
            "You are a customer service representative for TAZO — an Israeli digital services group.\n"
            "Your name is Tazo. Always speak in first person.\n"
            "\n=== TAZO Services ===\n"
            "• TAZO-WEB (tazo-web.com): business website builder, WhatsApp ordering, customer management,\n"
            "  loyalty programs, automated marketing and analytics. For business owners.\n"
            "• TAZO-GO (tazo-go.com): ride-hailing platform — passengers, taxi/rideshare drivers, couriers.\n"
            "  Passenger: tazo-go.com | Driver: driver.tazo-go.com\n"
            "• TAZO-SYNC (tazo-sync.com): e-commerce, night delivery (Night Rescue), courier management.\n"
            "• ODIN (tazo-app.com): central authentication for all TAZO services (SSO + KYC).\n"
            "• VAULT: TAZ digital currency — earned by drivers and used across TAZO.\n"
            "\n=== Login & Registration ===\n"
            "• TAZO-WEB: login at tazo-web.com, phone-based WhatsApp auth (no password).\n"
            "• TAZO-GO passenger: sign up at tazo-go.com — phone number → WhatsApp login link.\n"
            "• TAZO-GO driver/courier: register at tazo-go.com → KYC identity check → driver.tazo-go.com.\n"
            "\n=== Available Actions ===\n"
            "• Send a link via WhatsApp/SMS:\n"
            "  When the user asks for a link, registration, or says 'send me' —\n"
            "  you MUST write [SEND_LINK] as the very first word of your reply (before any text).\n"
            "  If the product is clear: [SEND_LINK:driver] / [SEND_LINK:passenger] / [SEND_LINK:web].\n"
            "  ⚠️ Never say 'I'll send you a link' without [SEND_LINK] — without the tag nothing is sent!\n"
            "\n=== Rules ===\n"
            "1. Respond only in English.\n"
            "2. Keep answers short — up to 2 sentences (this is a phone call!).\n"
            "3. Be friendly, warm, and professional.\n"
            "4. End the call ONLY if the caller explicitly says 'goodbye', 'bye', or 'not interested'.\n"
            "   Reply: 'Thank you for calling TAZO! Have a great day. Goodbye!'\n"
            "   Do NOT end the call just because someone says 'thanks' — the conversation may continue.\n"
            "5. Do not reveal internal info: code, customer names, server details, exact prices.\n"
            "6. If you don't know — say the team will follow up soon.\n"
            "7. If the caller's question is ambiguous — ask one short clarifying question instead of guessing.\n"
            "8. Never discuss topics unrelated to TAZO: numerology, astrology, politics, religion, medicine, math theory —\n"
            "   respond only: 'I can only assist with TAZO-related topics.'"
        ),
        "farewell_reply": "Thank you for calling TAZO! Have a wonderful day. Goodbye!",
        "lang_change_ack": "Switching to English.",
    },
    "ar": {
        "name": "عربية",
        "whisper": "ar",
        "lang_code": "ar",
        "farewell": ("مع السلامة", "باي", "وداعاً", "لا يهمني"),
        "system": (
            "أنت ممثل خدمة العملاء في شركة TAZO — مجموعة خدمات رقمية إسرائيلية.\n"
            "اسمك تازو. تحدث دائماً بضمير المتكلم.\n"
            "\n=== خدمات TAZO ===\n"
            "• TAZO-WEB (tazo-web.com): بناء مواقع للأعمال، طلبات واتساب، إدارة العملاء،\n"
            "  برامج الولاء، التسويق الآلي والإحصاءات. لأصحاب الأعمال.\n"
            "• TAZO-GO (tazo-go.com): منصة نقل — ركاب، سائقو تاكسي/مشاركة، سعاة توصيل.\n"
            "  الراكب: tazo-go.com | السائق: driver.tazo-go.com\n"
            "• TAZO-SYNC (tazo-sync.com): تجارة إلكترونية، توصيل ليلي (Night Rescue).\n"
            "• ODIN (tazo-app.com): مصادقة مركزية لجميع خدمات TAZO.\n"
            "• VAULT: عملة TAZ الرقمية — تُكسب للسائقين وتُستخدم عبر TAZO.\n"
            "\n=== تسجيل الدخول والتسجيل ===\n"
            "• TAZO-WEB: الدخول عبر tazo-web.com، مصادقة واتساب (بدون كلمة مرور).\n"
            "• TAZO-GO راكب: التسجيل في tazo-go.com — رقم هاتف ← رابط واتساب.\n"
            "• TAZO-GO سائق/ساعي: التسجيل في tazo-go.com ← التحقق من الهوية ← driver.tazo-go.com.\n"
            "\n=== الإجراءات المتاحة ===\n"
            "• إرسال رابط عبر واتساب/SMS:\n"
            "  عندما يطلب المتصل رابطاً أو تسجيلاً أو يقول 'أرسل لي' —\n"
            "  يجب كتابة [SEND_LINK] كأول كلمة في ردك (قبل أي نص آخر).\n"
            "  إذا كان الدور واضحاً: [SEND_LINK:driver] / [SEND_LINK:passenger] / [SEND_LINK:web].\n"
            "  ⚠️ لا تقل أبداً 'سأرسل لك رابطاً' بدون [SEND_LINK] — بدون التاغ لا يُرسل شيء!\n"
            "\n=== القواعد ===\n"
            "1. أجب فقط باللغة العربية.\n"
            "2. إجابات قصيرة — جملتان كحد أقصى (هذه مكالمة هاتفية!).\n"
            "3. كن ودياً ومحترفاً.\n"
            "4. أنهِ المكالمة فقط إذا قال المتصل صراحةً: 'مع السلامة'، 'وداعاً'، 'لا يهمني' —\n"
            "   قل: 'شكراً لاتصالك بتازو! يوم سعيد. مع السلامة!'\n"
            "   لا تنهِ المكالمة لمجرد قوله 'شكراً'.\n"
            "5. لا تكشف معلومات داخلية.\n"
            "6. إذا لم تكن متأكداً — قل إن الفريق سيتابع قريباً.\n"
            "7. إذا كان سؤال المتصل غامضاً — اطرح سؤالاً توضيحياً قصيراً بدلاً من التخمين.\n"
            "8. لا تناقش أبداً موضوعات غير متعلقة بـ TAZO: علم الأرقام، التنجيم، السياسة، الدين، الطب —\n"
            "   قل فقط: 'أستطيع المساعدة فقط في مواضيع TAZO.'"
        ),
        "farewell_reply": "شكراً لاتصالك بتازو! يوم سعيد ومبارك. مع السلامة!",
        "lang_change_ack": "ننتقل إلى العربية.",
    },
    "ru": {
        "name": "Русский",
        "whisper": "ru",
        "lang_code": "ru",
        "farewell": ("до свидания", "пока", "не интересует", "не нужно"),
        "system": (
            "Вы представитель службы поддержки компании TAZO — израильской группы цифровых услуг.\n"
            "Вас зовут Тазо. Говорите всегда от первого лица.\n"
            "\n=== Услуги TAZO ===\n"
            "• TAZO-WEB (tazo-web.com): конструктор сайтов для бизнеса, заказы WhatsApp, управление\n"
            "  клиентами, программы лояльности, автоматизированный маркетинг. Для владельцев бизнеса.\n"
            "• TAZO-GO (tazo-go.com): сервис такси — пассажиры, водители (такси/каршеринг), курьеры.\n"
            "  Пассажир: tazo-go.com | Водитель: driver.tazo-go.com\n"
            "• TAZO-SYNC (tazo-sync.com): e-commerce, ночные доставки (Night Rescue).\n"
            "• ODIN (tazo-app.com): централизованная аутентификация для всех сервисов TAZO.\n"
            "• VAULT: цифровая валюта TAZ — начисляется водителям, используется в экосистеме.\n"
            "\n=== Вход и регистрация ===\n"
            "• TAZO-WEB: вход на tazo-web.com, аутентификация через WhatsApp (без пароля).\n"
            "• TAZO-GO пассажир: регистрация на tazo-go.com — номер телефона → ссылка в WhatsApp.\n"
            "• TAZO-GO водитель/курьер: регистрация → верификация личности (KYC) → driver.tazo-go.com.\n"
            "\n=== Доступные действия ===\n"
            "• Отправить ссылку через WhatsApp/SMS:\n"
            "  Когда клиент просит ссылку или говорит 'пришли мне' —\n"
            "  ОБЯЗАТЕЛЬНО пишите [SEND_LINK] как первое слово в ответе (перед любым текстом).\n"
            "  Если роль ясна: [SEND_LINK:driver] / [SEND_LINK:passenger] / [SEND_LINK:web].\n"
            "  ⚠️ Никогда не говорите 'отправлю ссылку' без [SEND_LINK] — без тега ничего не отправится!\n"
            "\n=== Правила ===\n"
            "1. Отвечайте только на русском языке.\n"
            "2. Краткие ответы — максимум 2 предложения (это телефонный звонок!).\n"
            "3. Будьте дружелюбны и профессиональны.\n"
            "4. Завершайте звонок ТОЛЬКО если клиент явно говорит: 'до свидания', 'пока', 'не интересует' —\n"
            "   ответьте: 'Спасибо за звонок в TAZO! Хорошего дня. До свидания!'\n"
            "   Не завершайте звонок только из-за слова 'спасибо' — разговор может продолжаться.\n"
            "5. Не раскрывайте внутреннюю информацию.\n"
            "6. Если не знаете — скажите, что команда свяжется.\n"
            "7. Если вопрос клиента неясен — задайте один уточняющий вопрос вместо угадывания.\n"
            "8. Никогда не обсуждайте темы, не связанные с TAZO: нумерология, астрология,\n"
            "   политика, религия, медицина — отвечайте только: 'Я могу помочь только по вопросам TAZO.'"
        ),
        "farewell_reply": "Спасибо за звонок в TAZO! Хорошего дня. До свидания!",
        "lang_change_ack": "Переключаемся на русский.",
    },
}

# DTMF digit → language code
_DTMF_TO_LANG: dict[str, str] = {"1": "he", "2": "en", "3": "ar", "4": "ru"}

# Multilingual menu played at call start before greeting
_LANG_MENU = (
    "ברוכים הבאים לטאזו! "
    "לעברית לחצו 1. "
    "For English press 2. "
    "للعربية اضغط 3. "
    "На русском нажмите 4."
)

_FAREWELL_WORDS = ("להתראות", "ביי", "bye")  # kept for backwards-compat; per-lang used instead

# ── VAD parameters ────────────────────────────────────────────────────────────

# Twilio sends 20 ms chunks of μ-law 8 kHz audio = 160 bytes / chunk
_FRAME_MS           = 20
_SPEECH_THRESHOLD   = 300    # μ-law linear-energy threshold to detect voice
_BARGE_IN_THRESHOLD = 500    # lower than before — detect human interruption more sensitively
_BARGE_IN_CONSEC    = 3      # 3 consecutive frames = 60ms to confirm barge-in (faster response)
_SILENCE_FRAMES     = 25     # 25 × 20 ms = 500 ms — wait longer before ending utterance
_MIN_SPEECH_FRAMES  = 6      # at least 120 ms of voice before processing

# ── μ-law helpers ─────────────────────────────────────────────────────────────

# Pre-compute absolute linear value for each μ-law byte (energy lookup table)
_ULAW_ABS: list[int] = []
for _i in range(256):
    _u = (~_i) & 0xFF
    _exp = (_u >> 4) & 0x07
    _man = _u & 0x0F
    _v = abs(((_man << 3 | 0x84) << _exp) - 132)
    _ULAW_ABS.append(_v)


def _ulaw_energy(data: bytes) -> float:
    """Fast mean-energy estimate from μ-law encoded audio (uses lookup table)."""
    if not data:
        return 0.0
    return sum(_ULAW_ABS[b] for b in data) / len(data)


# Decode table: μ-law byte → 16-bit signed PCM int
_ULAW_DECODE: list[int] = []
for _i in range(256):
    _u = (~_i) & 0xFF
    _sign = -1 if (_u & 0x80) else 1
    _exp  = (_u >> 4) & 0x07
    _man  = _u & 0x0F
    _lin  = _sign * (((_man << 3) | 0x84) << _exp) - _sign * 132
    _ULAW_DECODE.append(max(-32768, min(32767, _lin)))


def _ulaw_to_wav(mulaw_bytes: bytes, sample_rate: int = 8000) -> bytes:
    """Convert raw μ-law 8 kHz bytes → WAV bytes (PCM 16-bit mono)."""
    pcm = struct.pack(f"<{len(mulaw_bytes)}h", *(_ULAW_DECODE[b] for b in mulaw_bytes))
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm)
    return buf.getvalue()


# ── Session ───────────────────────────────────────────────────────────────────

@dataclass
class VoiceSession:
    ws: WebSocket                   # Twilio Media Streams WebSocket
    stream_sid: str = ""
    call_sid:   str = ""

    # Caller context (passed via Stream <Parameter> tags from backend)
    caller_phone:   str = ""
    caller_name:    str = ""
    is_customer:    bool = False
    business_name:  str = ""
    # Role across the TAZO ecosystem: web_customer | lead | go_driver | go_passenger | go_courier | unknown
    user_role:      str = "unknown"
    # Best portal link for this caller
    portal_link:    str = "https://tazo-web.com"
    # TAZO-GO profile
    go_role:           str   = ""   # driver | passenger | courier | ""
    taz_balance:       float = 0.0  # TAZ coins in DriverWallet
    passenger_balance: float = 0.0  # prepaid ₪ in PassengerWallet

    # Language selection (1=he 2=en 3=ar 4=ru via DTMF, or auto-detected)
    language:      str  = "he"
    lang_selected: bool = False   # True once caller has chosen or first speech arrived

    # Conversation history for GPT
    messages: list[dict] = field(default_factory=list)
    manager_alert_sent: bool = False

    # VAD state
    audio_buffer:  bytearray = field(default_factory=bytearray)
    speech_frames: int  = 0
    silence_frames: int = 0
    in_speech:     bool = False

    # TTS / barge-in state
    ai_speaking:      bool = False
    barge_in:         asyncio.Event = field(default_factory=asyncio.Event)
    barge_in_frames:  int  = 0       # consecutive high-energy frames (self-echo guard)

    # Long-term memory: summaries of previous calls with this caller
    past_calls_summary: str = ""
    # Orders/system context fetched from backend at call start
    orders_summary: str = ""
    # Communication preference: '' (unknown) | 'wa' (WhatsApp) | 'sms'
    comm_pref: str = ""

    # Guards: only one TTS stream + one utterance processor at a time
    _tts_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    _proc_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    # Startup grace: ignore audio until this timestamp (avoids processing
    # Twilio menu echo / initial noise before the greeting starts)
    _ready_at: float = 0.0

    def system_prompt(self) -> str:
        cfg = _LANG_CONFIG[self.language]
        base = cfg["system"]
        extra = ""
        lang = self.language

        # ── caller identity section (language-aware) ─────────────────────
        if lang == "he":
            if self.is_customer:
                extra = "\n=== מידע על המתקשר ===\n"
                if self.caller_name:
                    extra += f"שם: {self.caller_name}\n"
                if self.business_name:
                    extra += f"עסק: {self.business_name}\n"
                extra += "המתקשר הוא לקוח קיים — פנה אליו בשמו ועזור בחום.\n"
            elif self.caller_name:
                extra = f"\nמתקשר מוכר: {self.caller_name}. עודד אותו להצטרף ל-TAZO.\n"
            if self.portal_link:
                extra += f"קישור מתאים למתקשר: {self.portal_link}\n"
            _role_notes = {
                "web_customer": "לקוח עסקי קיים של TAZO-WEB.",
                "lead":         "ליד ידוע — עודד אותו להירשם ב-TAZO-WEB.",
                "go_driver":    "נהג TAZO-GO — התמקד בסיוע לנהגים ובאפליקציית הנהגים.",
                "go_passenger": "נוסע TAZO-GO — התמקד בהזמנת נסיעות ובסיוע לנוסעים.",
                "go_courier":   "שליח TAZO-GO — התמקד בסיוע לשליחים ובאפליקציית השליחים.",
            }
            if self.user_role in _role_notes:
                extra += f"תפקיד המתקשר: {_role_notes[self.user_role]}\n"
            if self.go_role in ("driver", "courier"):
                extra += f"יתרת TAZ של המתקשר: {self.taz_balance:.2f} מטבעות TAZ\n"
                extra += "אם שואלים 'כמה TAZ יש לי' — השב עם היתרה המדויקת הזו.\n"
            elif self.go_role == "passenger" and self.passenger_balance > 0:
                extra += f"יתרת ארנק של המתקשר: ₪{self.passenger_balance:.2f}\n"
                extra += "אם שואלים על יתרה/כסף — השב עם הסכום המדויק הזה.\n"
        else:
            # English / Arabic / Russian — keep extra in English
            if self.is_customer:
                extra = "\n=== Caller info ===\n"
                if self.caller_name:
                    extra += f"Name: {self.caller_name}\n"
                if self.business_name:
                    extra += f"Business: {self.business_name}\n"
                extra += "Existing customer — greet by name and assist warmly.\n"
            elif self.caller_name:
                extra = f"\nKnown contact: {self.caller_name}. Encourage them to join TAZO.\n"
            if self.portal_link:
                extra += f"Best link for this caller: {self.portal_link}\n"
            _role_notes_en = {
                "web_customer": "Existing TAZO-WEB business customer.",
                "lead":         "Known lead — encourage to register on TAZO-WEB.",
                "go_driver":    "TAZO-GO driver — focus on driver app and support.",
                "go_passenger": "TAZO-GO passenger — focus on ride booking and support.",
                "go_courier":   "TAZO-GO courier — focus on courier app and support.",
            }
            if self.user_role in _role_notes_en:
                extra += f"Caller role: {_role_notes_en[self.user_role]}\n"
            if self.go_role in ("driver", "courier"):
                extra += f"Caller TAZ balance: {self.taz_balance:.2f} TAZ\n"
                extra += "If asked 'how much TAZ/money do I have', answer with this exact balance.\n"
            elif self.go_role == "passenger" and self.passenger_balance > 0:
                extra += f"Caller prepaid balance: ₪{self.passenger_balance:.2f}\n"
                extra += "If asked about balance/money, answer with this exact amount.\n"

        # ── Long-term memory: past calls ────────────────────────────────────
        if self.past_calls_summary:
            if lang == "he":
                extra += f"\n=== שיחות קודמות עם מתקשר זה ===\n{self.past_calls_summary}\n"
                extra += "השתמש בהיסטוריה זו להמשכיות — אל תשאל שוב על דברים שכבר סוכמו.\n"
            else:
                extra += f"\n=== Previous calls with this caller ===\n{self.past_calls_summary}\n"
                extra += "Use this history for continuity — don't ask again about things already resolved.\n"

        # ── System access: orders & activity ────────────────────────────────
        if self.orders_summary:
            if lang == "he":
                extra += f"\n=== הזמנות/פעילות אחרונה ===\n{self.orders_summary}\n"
            else:
                extra += f"\n=== Recent orders/activity ===\n{self.orders_summary}\n"

        return base + extra

    def greeting_text(self) -> str:
        lang = self.language
        biz = f" — {self.business_name}" if self.business_name else ""
        if lang == "he":
            if self.is_customer and self.caller_name:
                first = self.caller_name.split()[0]
                biz_he = f" בנושא {self.business_name}" if self.business_name else ""
                return f"שלום {first}! שמחים שהתקשרת. כיצד אוכל לעזור לך היום{biz_he}?"
            if self.caller_name:
                first = self.caller_name.split()[0]
                return f"שלום {first}! אני טאזו מ-TAZO. כיצד אוכל לעזור?"
            return (
                "שלום! הגעת לשירות הלקוחות של TAZO. "
                "אני טאזו, כאן כדי לעזור. כיצד אוכל לסייע?"
            )
        elif lang == "en":
            if self.caller_name:
                first = self.caller_name.split()[0]
                return f"Hello {first}! Great to hear from you. How can I help you today{biz}?"
            return "Hello! You've reached TAZO customer service. I'm Tazo, here to help. How can I assist you?"
        elif lang == "ar":
            if self.caller_name:
                first = self.caller_name.split()[0]
                return f"مرحباً {first}! سعيد بسماعك. كيف يمكنني مساعدتك{biz}؟"
            return "مرحباً! وصلت إلى خدمة عملاء TAZO. أنا تازو، هنا للمساعدة. كيف يمكنني مساعدتك؟"
        elif lang == "ru":
            if self.caller_name:
                first = self.caller_name.split()[0]
                return f"Здравствуйте, {first}! Рады вашему звонку. Чем могу помочь{biz}?"
            return "Здравствуйте! Вы позвонили в службу поддержки TAZO. Меня зовут Тазо. Чем могу помочь?"
        # fallback
        return "Hello! You've reached TAZO. How can I help?"


# ── Whisper STT ───────────────────────────────────────────────────────────────

async def _transcribe(mulaw_bytes: bytes, whisper_lang: str = "he") -> str:
    """Convert μ-law buffer → WAV → Whisper transcription."""
    wav = _ulaw_to_wav(mulaw_bytes)
    try:
        oai = AsyncOpenAI(api_key=OPENAI_API_KEY)
        result = await oai.audio.transcriptions.create(
            model="whisper-1",
            file=("audio.wav", io.BytesIO(wav), "audio/wav"),
            language=whisper_lang,
        )
        return result.text.strip()
    except Exception as exc:
        logger.error("[STT] Whisper error: %s", exc)
        return ""


# ── WhatsApp / SMS link sender ────────────────────────────────────────────────

# Map session user_role to backend link_type
_ROLE_TO_LINK_TYPE: dict[str, str] = {
    "web_customer": "web",
    "lead":         "web",
    "go_driver":    "driver",
    "go_passenger": "passenger",
    "go_courier":   "courier",
    "unknown":      "general",
}


async def _load_caller_memory(session: VoiceSession) -> None:
    """Load past call summaries and recent orders from backend (fire-and-forget on call start)."""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(
                f"{BACKEND_INTERNAL_URL}/api/v1/internal/voice/caller-memory",
                params={"phone": session.caller_phone},
            )
            if resp.status_code == 200:
                data = resp.json()
                session.past_calls_summary = data.get("past_calls_summary", "")
                session.orders_summary     = data.get("orders_summary", "")
                session.comm_pref          = data.get("comm_pref", "")
                if session.past_calls_summary:
                    logger.info("[WS] call=%s loaded past call history (comm_pref=%s)",
                                session.call_sid[:8], session.comm_pref or "?")
    except Exception as exc:
        logger.debug("[WS] call=%s memory load failed: %s", session.call_sid[:8], exc)


async def _save_call_memory(session: VoiceSession) -> None:
    """Save call transcript + auto-summary to backend DB after call ends."""
    import json as _json
    try:
        user_turns = [m["content"] for m in session.messages if m["role"] == "user"]
        bot_turns  = [m["content"] for m in session.messages if m["role"] == "assistant"]
        # Quick summary for next call context
        summary_parts = []
        if user_turns:
            summary_parts.append(f"המתקשר שאל על: {'; '.join(user_turns[-3:])}")
        if bot_turns:
            last_bot = bot_turns[-1][:120] if bot_turns else ""
            if last_bot:
                summary_parts.append(f"הבוט ענה: {last_bot}")
        outcome = "completed"
        if session.manager_alert_sent:
            outcome = "escalated"
        elif any("[SEND_LINK]" in (m.get("content") or "") for m in session.messages):
            outcome = "link_sent"

        async with httpx.AsyncClient(timeout=8) as client:
            await client.post(
                f"{BACKEND_INTERNAL_URL}/api/v1/internal/voice/save-call-log",
                json={
                    "call_sid":      session.call_sid,
                    "caller_phone":  session.caller_phone,
                    "caller_name":   session.caller_name,
                    "business_name": session.business_name,
                    "user_role":     session.user_role,
                    "language":      session.language,
                    "transcript":    _json.dumps(session.messages, ensure_ascii=False),
                    "summary":       " | ".join(summary_parts)[:500],
                    "duration_turns": len(user_turns),
                    "link_sent":     any("[SEND_LINK]" in (m.get("content") or "") for m in session.messages),
                    "escalated":     session.manager_alert_sent,
                    "call_outcome":  outcome,
                    "comm_pref":     session.comm_pref,
                },
            )
        logger.info("[WS] call=%s saved to call log DB (comm_pref=%s)", session.call_sid[:8], session.comm_pref or "—")
    except Exception as exc:
        logger.debug("[WS] call=%s save memory failed: %s", session.call_sid[:8], exc)


async def _send_whatsapp_link(session: VoiceSession, link_type_override: str = "") -> None:
    """Send link via WhatsApp or SMS based on:
    1. Explicit channel in link_type_override (e.g. "wa:driver" or "sms:driver")
    2. session.comm_pref ('wa' | 'sms' | '')
    3. Default: try WhatsApp, fall back to SMS automatically on backend.
    """
    if not session.caller_phone:
        return

    # Parse channel and product from override (e.g. "wa:driver" → channel="wa", product="driver")
    channel = ""
    product = link_type_override
    if ":" in link_type_override:
        parts = link_type_override.split(":", 1)
        if parts[0] in ("wa", "sms"):
            channel, product = parts[0], parts[1]
        else:
            product = link_type_override

    # Use stored preference if no explicit channel in the tag
    if not channel:
        channel = session.comm_pref or "wa"  # default to WhatsApp

    # Derive product from session role if not specified
    link_type = product or _ROLE_TO_LINK_TYPE.get(session.user_role, "general")

    # Save preference to session and backend
    if channel in ("wa", "sms") and channel != session.comm_pref:
        session.comm_pref = channel
        asyncio.create_task(_save_comm_pref(session.caller_phone, channel))

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{BACKEND_INTERNAL_URL}/api/v1/webhooks/twilio/ai-voice-wa",
                data={
                    "caller_phone": session.caller_phone,
                    "link_type":    link_type,
                    "language":     session.language,
                    "channel":      channel,   # 'wa' or 'sms'
                },
            )
        if resp.status_code == 200:
            logger.info("[WS] call=%s link sent via %s (type=%s)", session.call_sid[:8], channel, link_type)
        else:
            logger.warning("[WS] call=%s link failed: HTTP %s", session.call_sid[:8], resp.status_code)
    except Exception as exc:
        logger.warning("[WS] call=%s link error: %s", session.call_sid[:8], exc)


async def _save_comm_pref(phone: str, pref: str) -> None:
    """Persist communication preference to backend (fire-and-forget)."""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            await client.post(
                f"{BACKEND_INTERNAL_URL}/api/v1/internal/voice/save-comm-pref",
                json={"phone": phone, "comm_pref": pref},
            )
    except Exception:
        pass


# ── GPT streaming ─────────────────────────────────────────────────────────────

async def _gpt_stream(session: VoiceSession) -> AsyncGenerator[str, None]:
    """Stream gpt-4.1-mini reply tokens for the current conversation."""
    try:
        oai = AsyncOpenAI(api_key=OPENAI_API_KEY)
        stream = await oai.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "system", "content": session.system_prompt()}]
            + session.messages[-20:],
            max_tokens=100,
            temperature=0.7,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content if chunk.choices else None
            if delta:
                yield delta
    except Exception as exc:
        logger.error("[LLM] GPT error: %s", exc)
        yield "סליחה, יש תקלה רגעית."


# ── ElevenLabs TTS stream ──────────────────────────────────────────────────────

async def _play_tts(session: VoiceSession, text_gen: AsyncGenerator[str, None]) -> str:
    """
    Stream text from `text_gen` to ElevenLabs and forward mulaw audio to Twilio.
    Returns the full text that was spoken (for conversation history).
    Respects barge-in: exits cleanly when session.barge_in is set.
    """
    if not ELEVENLABS_API_KEY or not ELEVENLABS_VOICE_ID:
        logger.warning("[TTS] ElevenLabs not configured — skipping TTS")
        return ""

    full_text: list[str] = []
    session.ai_speaking = True
    session.barge_in.clear()

    try:
        async with websockets.connect(
            _EL_WS_URL,
            extra_headers={"xi-api-key": ELEVENLABS_API_KEY},
            ping_interval=None,
        ) as el_ws:
            # ── BOS (Beginning of Stream) ────────────────────────────────────
            await el_ws.send(json.dumps({
                "text": " ",
                "voice_settings": {
                    "stability": 0.45,
                    "similarity_boost": 0.80,
                    "use_speaker_boost": True,
                },
                "generation_config": {
                    "chunk_length_schedule": [50, 100, 150],
                },
            }))

            # ── Task: send GPT text chunks to ElevenLabs ─────────────────────
            async def _send_text() -> None:
                async for chunk in text_gen:
                    if session.barge_in.is_set():
                        break
                    full_text.append(chunk)
                    await el_ws.send(json.dumps({
                        "text": chunk,
                        "try_trigger_generation": True,
                    }))
                # EOS — flush remaining audio
                if not session.barge_in.is_set():
                    await el_ws.send(json.dumps({"text": ""}))

            # ── Task: receive audio from ElevenLabs → Twilio ─────────────────
            async def _recv_audio() -> None:
                try:
                    async for raw in el_ws:
                        if session.barge_in.is_set():
                            break
                        try:
                            data = json.loads(raw)
                        except json.JSONDecodeError:
                            continue

                        if data.get("audio"):
                            # Forward base64 mulaw_8000 directly to Twilio
                            await session.ws.send_text(json.dumps({
                                "event": "media",
                                "streamSid": session.stream_sid,
                                "media": {"payload": data["audio"]},
                            }))

                        if data.get("isFinal") is True and not data.get("audio"):
                            break  # clean end of stream

                except websockets.exceptions.ConnectionClosed:
                    pass

            # Run both tasks concurrently; cancel send if recv finishes first
            send_task = asyncio.create_task(_send_text())
            recv_task = asyncio.create_task(_recv_audio())
            done, pending = await asyncio.wait(
                [send_task, recv_task],
                return_when=asyncio.ALL_COMPLETED,
            )
            for t in pending:
                t.cancel()

    except websockets.exceptions.WebSocketException as exc:
        logger.error("[TTS] ElevenLabs WS error: %s", exc)
    except Exception as exc:
        logger.error("[TTS] Unexpected TTS error: %s", exc)
    finally:
        session.ai_speaking = False
        # Brief echo-prevention window: Twilio echoes bot audio back into the
        # input stream for ~0.5-1s after playback ends — drop it.
        session._ready_at = time.time() + 0.8
        # Send mark so we know AI audio finished
        if session.stream_sid:
            try:
                await session.ws.send_text(json.dumps({
                    "event": "mark",
                    "streamSid": session.stream_sid,
                    "mark": {"name": "tts_done"},
                }))
            except Exception:
                pass

    return "".join(full_text)


# ── Manager escalation (הסלמה למנהל) ─────────────────────────────────────────

async def _send_manager_alert(session: VoiceSession, reason: str) -> None:
    """
    Fire-and-forget: notify the TAZO manager via WhatsApp with caller details + conversation summary.
    Calls the backend POST /api/v1/webhooks/twilio/ai-voice-manager endpoint.
    """
    import time as _time
    # Build a concise transcript summary from the last turns (user+assistant)
    turns: list[str] = []
    for m in session.messages[-8:]:
        role = "לקוח" if m.get("role") == "user" else "בוט"
        content = (m.get("content") or "").strip()
        if content:
            turns.append(f"{role}: {content}")
    summary = " | ".join(turns)[:1400] if turns else "לא דווח"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{BACKEND_INTERNAL_URL}/api/v1/webhooks/twilio/ai-voice-manager",
                data={
                    "caller_phone": session.caller_phone,
                    "caller_name":  session.caller_name or "לא ידוע",
                    "call_sid":      session.call_sid,
                    "channel":       "voice_bot",
                    "business_name": session.business_name or "",
                    "user_role":     session.user_role or "unknown",
                    "portal_link":   session.portal_link or "",
                    "language":      session.language,
                    "summary":      summary,
                    "reason":       reason,
                    "timestamp":    _time.strftime("%d/%m/%Y %H:%M"),
                },
            )
        if resp.status_code == 200:
            logger.info("[MGR] call=%s manager alert sent", session.call_sid[:8])
        else:
            logger.warning("[MGR] call=%s manager alert failed: HTTP %s", session.call_sid[:8], resp.status_code)
    except Exception as exc:
        logger.warning("[MGR] call=%s manager alert error: %s", session.call_sid[:8], exc)


# ── Utterance processing ──────────────────────────────────────────────────────

async def _process_utterance(session: VoiceSession, audio: bytes) -> None:
    """
    Full pipeline: μ-law audio → Whisper → GPT streaming → ElevenLabs → Twilio.
    Protected by _proc_lock so only one pipeline runs at a time.
    """
    if session._proc_lock.locked():
        logger.info("[PROC] Already processing — dropping utterance")
        return

    async with session._proc_lock:
        # If language not yet selected, lock in default (Hebrew) now
        if not session.lang_selected:
            session.lang_selected = True
            logger.info("[PROC] Language defaulted to 'he' (no DTMF received)")

        cfg = _LANG_CONFIG[session.language]

        # 2a. Interim phrase — fire BEFORE STT so there's no silence while Whisper runs
        _INTERIM_PHRASES = {
            "he": ["שנייה...", "כן, שמעתי...", "רגע...", "אני כאן, שנייה...", "הבנתי..."],
            "en": ["Just a second...", "One moment...", "Sure, hold on...", "Give me a second..."],
            "ar": ["لحظة...", "نعم، سمعتك..."],
            "ru": ["Секунду...", "Да, слушаю..."],
        }

        async def _play_interim_phrase() -> None:
            import random
            phrase = random.choice(_INTERIM_PHRASES.get(session.language, _INTERIM_PHRASES["he"]))
            try:
                async with session._tts_lock:
                    if session.language == "he":
                        await _play_tts_rest(session, phrase)
                    else:
                        await _play_tts(session, _iter_str(phrase))
            except Exception as _e:
                logger.debug("[PROC] interim phrase failed: %s", _e)

        # 1. STT — transcribe FIRST, then play interim phrase while GPT runs
        # (Previously, the interim played before transcription causing race conditions
        #  when the transcript was empty — the bot said "בודקת" then ended the loop)
        speech = await _transcribe(audio, cfg["whisper"])
        if not speech:
            # Play a soft "didn't hear you" prompt instead of silently dropping
            _no_hear = {"he": "לא שמעתי, תוכל לחזור?", "en": "Sorry, I didn't catch that. Could you repeat?",
                        "ar": "لم أسمعك، هل يمكنك الإعادة؟", "ru": "Не расслышал. Повторите, пожалуйста."}
            async with session._tts_lock:
                await _play_tts_rest(session, _no_hear.get(session.language, _no_hear["he"]))
            return

        logger.info("[PROC] call=%s user: %r", session.call_sid[:8], speech)
        session.messages.append({"role": "user", "content": speech})

        # Now play interim while GPT processes — transcript is confirmed non-empty
        asyncio.create_task(_play_interim_phrase())

        # 2b. Farewell shortcut — language-aware
        lower = speech.lower().strip()
        # Also detect: short "לא" reply after bot asked a question
        _last_bot = session.messages[-2]["content"] if len(session.messages) >= 2 and session.messages[-2]["role"] == "assistant" else ""
        _short_no = (lower in ("לא", "לא.", "לא!") and _last_bot.rstrip().endswith("?") and len(speech) <= 5)
        if (any(w in lower for w in cfg["farewell"]) and len(speech) < 40) or _short_no:
            if _short_no:
                bye = "בסדר גמור! אם תצטרך עזרה — אני כאן. יום נעים!"
            else:
                bye = cfg["farewell_reply"]
            session.messages.append({"role": "assistant", "content": bye})
            async with session._tts_lock:
                if session.language == "he":
                    await _play_tts_rest(session, bye)
                else:
                    await _play_tts(session, _iter_str(bye))
            # Hang up
            if session.stream_sid:
                try:
                    await session.ws.send_text(json.dumps({
                        "event": "mark",
                        "streamSid": session.stream_sid,
                        "mark": {"name": "hangup"},
                    }))
                except Exception:
                    pass
            return

        # 3. GPT → collect all tokens (needed for Hebrew REST TTS and [SEND_LINK] detection)
        # Wait for TTS lock so GPT response doesn't interrupt interim phrase mid-syllable
        tokens: list[str] = []
        async for token in _gpt_stream(session):
            tokens.append(token)
        spoken_text = "".join(tokens)

        if spoken_text:
            # Detect [SEND_LINK] / [SEND_LINK:type] and [ESCALATE_MANAGER: reason] before speaking
            import re as _re
            _tag_pat = _re.compile(r"\[SEND_LINK(?::([a-z_]+))?\]", _re.IGNORECASE)
            _esc_pat = _re.compile(r"\[ESCALATE_MANAGER:\s*([^\]]+)\]", _re.IGNORECASE)
            tag_match = _tag_pat.search(spoken_text)
            esc_match = _esc_pat.search(spoken_text)
            link_type_override = tag_match.group(1) if tag_match and tag_match.group(1) else ""
            should_send_link = tag_match is not None
            should_escalate = esc_match is not None
            escalate_reason = esc_match.group(1).strip() if esc_match else ""
            tts_text = _esc_pat.sub("", _tag_pat.sub("", spoken_text)).strip()

            if should_escalate:
                _ESC_ACK = {
                    "he": "בשמחה. העברתי עכשיו את הבקשה למנהל אריאל. נחזור אליך בהקדם ועד 24 שעות.",
                    "en": "Done. I have forwarded your request to manager Ariel. We will get back to you within 24 hours.",
                    "ar": "تم إرسال طلبك الآن إلى المدير أريئيل. سنعود إليك خلال 24 ساعة.",
                    "ru": "Запрос передан менеджеру Ариэлю. Мы свяжемся с вами в течение 24 часов.",
                }
                # Always confirm SLA verbally when escalation is triggered.
                tts_text = _ESC_ACK.get(session.language, _ESC_ACK["he"])

            # ── Verbal fallback: GPT said "sending a link" without the tag ──
            # Catches cases where the model verbally promises a link but omits [SEND_LINK].
            if not should_send_link and session.caller_phone:
                _lower_spoken = spoken_text.lower()
                _verbal_he = any(w in _lower_spoken for w in (
                    "שולח", "שולחת", "שלחתי", "אשלח", "נשלח",
                ))
                _verbal_content = any(w in _lower_spoken for w in (
                    "קישור", "לינק", "link", "וואטסאפ", "whatsapp",
                    "הרשמה", "הצטרפות", "sms", "אסמס",
                ))
                _verbal_en = any(p in _lower_spoken for p in (
                    "sending you", "sent you", "i'll send", "i will send",
                    "i've sent", "sending a link", "sending the link",
                ))
                if (_verbal_he and _verbal_content) or _verbal_en:
                    should_send_link = True
                    logger.info(
                        "[PROC] call=%s verbal SEND_LINK fallback triggered (no tag in GPT output)",
                        session.call_sid[:8],
                    )

            async with session._tts_lock:
                if tts_text:
                    if session.language == "he":
                        await _play_tts_rest(session, tts_text)
                    else:
                        await _play_tts(session, _iter_str(tts_text))

            if should_send_link and session.caller_phone:
                asyncio.create_task(_send_whatsapp_link(session, link_type_override))
                logger.info(
                    "[PROC] call=%s [SEND_LINK] triggered (type=%r)",
                    session.call_sid[:8], link_type_override or "auto",
                )
                # GPT returned only [SEND_LINK] with no spoken text — add a fallback confirmation
                if not tts_text:
                    _LINK_CONFIRM = {
                        "he": "שלחתי לך הודעה ב-וואטסאפ. יש עוד שאלה?",
                        "en": "I sent you a WhatsApp message. Anything else?",
                        "ar": "أرسلت لك رسالة واتساب. هل تحتاج شيئاً آخر؟",
                        "ru": "Я отправил вам сообщение в WhatsApp. Что-то ещё?",
                    }
                    tts_text = _LINK_CONFIRM.get(session.language, _LINK_CONFIRM["he"])
                    async with session._tts_lock:
                        if session.language == "he":
                            await _play_tts_rest(session, tts_text)
                        else:
                            await _play_tts(session, _iter_str(tts_text))

            if should_escalate and not session.manager_alert_sent:
                session.manager_alert_sent = True
                asyncio.create_task(_send_manager_alert(session, escalate_reason))
                logger.info(
                    "[PROC] call=%s [ESCALATE_MANAGER] triggered (reason=%r)",
                    session.call_sid[:8], escalate_reason[:60],
                )

            session.messages.append({"role": "assistant", "content": tts_text})
            logger.info("[PROC] call=%s bot: %r", session.call_sid[:8], tts_text[:80])


async def _iter_str(text: str) -> AsyncGenerator[str, None]:
    """Wrap a static string as an async generator (for _play_tts)."""
    yield text


# ── Twilio Media Streams WebSocket handler ────────────────────────────────────

async def _handle_media_stream(ws: WebSocket) -> None:
    await ws.accept()
    session: VoiceSession | None = None

    try:
        async for raw in ws.iter_text():
            msg = json.loads(raw)
            event = msg.get("event")

            # ── connected ──────────────────────────────────────────────────
            if event == "connected":
                logger.info("[WS] Twilio connected (protocol=%s)", msg.get("protocol"))

            # ── start ──────────────────────────────────────────────────────
            elif event == "start":
                start_data  = msg["start"]
                params      = start_data.get("customParameters", {})
                session = VoiceSession(ws=ws)
                session.stream_sid    = start_data["streamSid"]
                session.call_sid      = start_data["callSid"]
                session.caller_phone  = params.get("caller_phone", "")
                session.caller_name   = params.get("caller_name", "")
                session.is_customer   = params.get("is_customer", "").lower() == "true"
                session.business_name = params.get("business_name", "")
                session.user_role     = params.get("user_role", "unknown")
                session.portal_link   = params.get("portal_link", "https://tazo-web.com")
                session.go_role           = params.get("go_role", "")
                session.taz_balance       = float(params.get("taz_balance", "0") or "0")
                session.passenger_balance = float(params.get("passenger_balance", "0") or "0")
                # Ignore audio for the first 2.5 s — Twilio may feed menu/ring
                # audio into the stream before the caller actually speaks
                session._ready_at = time.time() + 2.5

                # Load past call history + orders in background (non-blocking)
                if session.caller_phone:
                    asyncio.create_task(_load_caller_memory(session))

                logger.info(
                    "[WS] Stream started — call=%s phone=%s*** name=%r customer=%s",
                    session.call_sid[:8],
                    (session.caller_phone or "")[:7],
                    session.caller_name,
                    session.is_customer,
                )

                # If language was already chosen via Twilio <Gather>, skip ElevenLabs menu
                pre_lang = params.get("lang", "")
                if pre_lang in _LANG_CONFIG:
                    session.language = pre_lang
                    session.lang_selected = True
                    greeting = session.greeting_text()
                    session.messages.append({"role": "assistant", "content": greeting})
                    asyncio.create_task(_play_greeting(session, greeting))
                else:
                    # No pre-selection: play multilingual menu via ElevenLabs (fallback)
                    asyncio.create_task(_play_greeting(session, _LANG_MENU))

            # ── dtmf (language selection / change) ────────────────────────
            elif event == "dtmf" and session:
                digit = msg.get("dtmf", {}).get("digit", "")
                lang = _DTMF_TO_LANG.get(digit)
                if lang:
                    prev_lang = session.language
                    session.language = lang
                    session.lang_selected = True
                    logger.info(
                        "[WS] call=%s language %s→%s via DTMF %s",
                        session.call_sid[:8], prev_lang, lang, digit,
                    )
                    if prev_lang == lang and session.messages:
                        # Same language re-selected mid-call: just acknowledge quietly
                        ack = _LANG_CONFIG[lang]["lang_change_ack"]
                        asyncio.create_task(_play_greeting(session, ack))
                    else:
                        # New language (or initial selection): play full greeting
                        greeting = session.greeting_text()
                        session.messages = []   # reset conversation for new language
                        session.messages.append({"role": "assistant", "content": greeting})
                        asyncio.create_task(_play_greeting(session, greeting))

            # ── media (audio from caller) ──────────────────────────────────
            elif event == "media" and session:
                payload = base64.b64decode(msg["media"]["payload"])
                energy  = _ulaw_energy(payload)

                # Grace period: drop all audio for the first few seconds so that
                # Twilio ring/menu residual audio isn't processed as speech
                if time.time() < session._ready_at:
                    continue

                # Barge-in detection: caller speaks while AI is talking.
                # Requires _BARGE_IN_CONSEC consecutive frames above threshold to
                # avoid self-triggering on Twilio's loopback echo of the bot's audio.
                if session.ai_speaking and energy > _BARGE_IN_THRESHOLD:
                    session.barge_in_frames += 1
                    if session.barge_in_frames >= _BARGE_IN_CONSEC:
                        logger.info(
                            "[VAD] Barge-in confirmed (%d frames, energy=%.0f)",
                            session.barge_in_frames, energy,
                        )
                        session.barge_in.set()
                        session.barge_in_frames = 0
                        # Clear Twilio's audio buffer
                        await ws.send_text(json.dumps({
                            "event": "clear",
                            "streamSid": session.stream_sid,
                        }))
                        session.ai_speaking = False
                else:
                    session.barge_in_frames = 0

                # VAD: accumulate speech when AI is silent
                if not session.ai_speaking:
                    if energy > _SPEECH_THRESHOLD:
                        session.speech_frames += 1
                        session.silence_frames  = 0
                        session.in_speech = True
                        session.audio_buffer.extend(payload)
                    elif session.in_speech:
                        session.silence_frames += 1
                        session.audio_buffer.extend(payload)

                        # End of utterance detected
                        if (
                            session.silence_frames >= _SILENCE_FRAMES
                            and session.speech_frames >= _MIN_SPEECH_FRAMES
                        ):
                            captured = bytes(session.audio_buffer)
                            session.audio_buffer  = bytearray()
                            session.speech_frames = 0
                            session.silence_frames = 0
                            session.in_speech = False

                            # If no language chosen yet, default to Hebrew and
                            # synthesise a greeting into the history before processing
                            if not session.lang_selected:
                                session.lang_selected = True
                                greeting = session.greeting_text()
                                session.messages.append({"role": "assistant", "content": greeting})

                            asyncio.create_task(_process_utterance(session, captured))

            # ── stop ───────────────────────────────────────────────────────
            elif event == "stop":
                logger.info("[WS] Stream stopped — call=%s", (session.call_sid if session else "?")[:8])
                if session and session.caller_phone and len(session.messages) > 1:
                    asyncio.create_task(_save_call_memory(session))
                break

    except WebSocketDisconnect:
        logger.info("[WS] Twilio disconnected")
    except Exception as exc:
        logger.error("[WS] Unexpected error: %s", exc)


async def _play_tts_rest(session: VoiceSession, text: str) -> str:
    """
    Use ElevenLabs REST streaming TTS with eleven_v3 (supports Hebrew + 70 languages).
    Streams raw μ-law 8 kHz audio bytes directly to Twilio.
    Returns the spoken text (for conversation history).
    """
    if not ELEVENLABS_API_KEY or not ELEVENLABS_VOICE_ID:
        logger.warning("[TTS-REST] ElevenLabs not configured — skipping")
        return text

    session.ai_speaking = True
    session.barge_in.clear()
    session.barge_in_frames = 0
    # Brief immunity at TTS start: prevents the bot's own echo (arrives ~50-200ms
    # after playback begins via Twilio loopback) from immediately triggering barge-in.
    session._ready_at = time.time() + 0.5

    try:
        url = (
            f"https://api.elevenlabs.io/v1/text-to-speech"
            f"/{ELEVENLABS_VOICE_ID}/stream"
            f"?output_format=ulaw_8000"
        )
        headers = {
            "xi-api-key": ELEVENLABS_API_KEY,
            "Content-Type": "application/json",
        }
        payload = {
            "text": text,
            "model_id": "eleven_v3",
            "voice_settings": {
                "stability": 0.45,
                "similarity_boost": 0.80,
                "use_speaker_boost": True,
            },
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            async with client.stream("POST", url, json=payload, headers=headers) as resp:
                if resp.status_code != 200:
                    logger.error("[TTS-REST] ElevenLabs error %s", resp.status_code)
                    return text

                buffer = b""
                async for chunk in resp.aiter_bytes(chunk_size=320):
                    if session.barge_in.is_set():
                        break
                    buffer += chunk
                    while len(buffer) >= 160:
                        frame, buffer = buffer[:160], buffer[160:]
                        b64 = base64.b64encode(frame).decode()
                        await session.ws.send_text(json.dumps({
                            "event": "media",
                            "streamSid": session.stream_sid,
                            "media": {"payload": b64},
                        }))

                if buffer and not session.barge_in.is_set():
                    b64 = base64.b64encode(buffer).decode()
                    await session.ws.send_text(json.dumps({
                        "event": "media",
                        "streamSid": session.stream_sid,
                        "media": {"payload": b64},
                    }))

    except Exception as exc:
        logger.error("[TTS-REST] Error: %s", exc)
    finally:
        session.ai_speaking = False
        # Brief echo-prevention window: Twilio echoes bot audio back into the
        # input stream for ~0.5-1s after playback ends — drop it.
        session._ready_at = time.time() + 0.8
        if session.stream_sid:
            try:
                await session.ws.send_text(json.dumps({
                    "event": "mark",
                    "streamSid": session.stream_sid,
                    "mark": {"name": "tts_done"},
                }))
            except Exception:
                pass

    return text


async def _play_greeting(session: VoiceSession, greeting: str) -> None:
    """Play the greeting via TTS — Hebrew uses REST (eleven_v3), others use WebSocket."""
    async with session._tts_lock:
        if session.language == "he":
            await _play_tts_rest(session, greeting)
        else:
            await _play_tts(session, _iter_str(greeting))


# ── FastAPI app ───────────────────────────────────────────────────────────────

app = FastAPI(title="TAZO Voice Stream", docs_url=None, redoc_url=None)


@app.get("/health")
async def health() -> JSONResponse:
    return JSONResponse({"status": "ok", "service": "voice-stream"})


@app.websocket("/ws")
async def media_stream(ws: WebSocket) -> None:
    await _handle_media_stream(ws)


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=PORT, log_level="info")
