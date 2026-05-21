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
        "farewell": ("להתראות", "ביי", "bye"),
        "system": (
            "אתה נציג שירות לקוחות של חברת TAZO — פלטפורמה המסייעת לעסקים מקומיים.\n"
            "שמך הוא טאזו.\n"
            "\nכללים חשובים:\n"
            "1. ענה אך ורק בעברית תקינה.\n"
            "2. תשובות קצרות ותמציתיות — עד 2 משפטים (שיחת טלפון!).\n"
            "3. היה ידידותי, חם ומקצועי.\n"
            "4. אם הלקוח אומר להתראות/ביי/תודה/לא מעניין — סיים: "
            "'תודה שפנית, יום נעים. להתראות!'\n"
            "5. TAZO מאפשרת לעסקים: הזמנות WhatsApp, דף עסקי, ניהול לקוחות, שיווק אוטומטי.\n"
            "6. אם הלקוח מבקש קישור/הרשמה/להצטרף — ציין [SEND_LINK] בתחילת התשובה.\n"
            "7. אל תחשוף מידע פנימי. אם אינך יודע — אמור שהצוות יחזור בהקדם."
        ),
        "farewell_reply": "תודה שפנית לטאזו! יום נעים ומוצלח. להתראות!",
        "lang_change_ack": "עוברים לעברית.",
    },
    "en": {
        "name": "English",
        "whisper": "en",
        "farewell": ("goodbye", "bye", "that's all", "no thanks", "not interested"),
        "system": (
            "You are a customer service representative for TAZO — a platform helping local businesses.\n"
            "Your name is Tazo.\n"
            "\nImportant rules:\n"
            "1. Respond only in English.\n"
            "2. Keep answers short — up to 2 sentences (this is a phone call!).\n"
            "3. Be friendly, warm, and professional.\n"
            "4. If the caller says goodbye/bye/not interested — end with: "
            "'Thank you for calling TAZO! Have a great day. Goodbye!'\n"
            "5. TAZO helps businesses with: WhatsApp orders, business pages, "
            "customer management, automated marketing.\n"
            "6. If the caller asks for a link/signup — prefix your reply with [SEND_LINK].\n"
            "7. Do not reveal internal information. If unsure — say the team will follow up."
        ),
        "farewell_reply": "Thank you for calling TAZO! Have a wonderful day. Goodbye!",
        "lang_change_ack": "Switching to English.",
    },
    "ar": {
        "name": "عربية",
        "whisper": "ar",
        "farewell": ("مع السلامة", "باي", "شكراً", "وداعاً", "لا يهمني"),
        "system": (
            "أنت ممثل خدمة العملاء في شركة TAZO — منصة تساعد الأعمال التجارية المحلية.\n"
            "اسمك تازو.\n"
            "\nقواعد مهمة:\n"
            "1. أجب فقط باللغة العربية.\n"
            "2. إجابات قصيرة وموجزة — جملتان كحد أقصى (هذه مكالمة هاتفية!).\n"
            "3. كن ودياً ومحترفاً.\n"
            "4. إذا قال المتصل وداعاً — أنهِ بـ: 'شكراً لاتصالك بتازو! يوم سعيد. مع السلامة!'\n"
            "5. TAZO تساعد الأعمال على: طلبات واتساب، صفحة الأعمال، إدارة العملاء، التسويق الآلي.\n"
            "6. إذا طلب رابطاً أو تسجيلاً — ابدأ ردك بـ [SEND_LINK].\n"
            "7. لا تكشف معلومات داخلية. إذا لم تكن متأكداً — قل إن الفريق سيتابع قريباً."
        ),
        "farewell_reply": "شكراً لاتصالك بتازو! يوم سعيد ومبارك. مع السلامة!",
        "lang_change_ack": "ننتقل إلى العربية.",
    },
    "ru": {
        "name": "Русский",
        "whisper": "ru",
        "farewell": ("до свидания", "пока", "спасибо", "не интересует", "всё"),
        "system": (
            "Вы представитель службы поддержки компании TAZO — платформы для местного бизнеса.\n"
            "Вас зовут Тазо.\n"
            "\nВажные правила:\n"
            "1. Отвечайте только на русском языке.\n"
            "2. Краткие ответы — максимум 2 предложения (это телефонный звонок!).\n"
            "3. Будьте дружелюбны и профессиональны.\n"
            "4. Если клиент говорит до свидания/пока — завершите: "
            "'Спасибо за звонок в TAZO! Хорошего дня. До свидания!'\n"
            "5. TAZO помогает бизнесу: заказы WhatsApp, бизнес-страница, "
            "управление клиентами, автоматизированный маркетинг.\n"
            "6. Если клиент просит ссылку/регистрацию — начните ответ с [SEND_LINK].\n"
            "7. Не раскрывайте внутреннюю информацию. Если не знаете — скажите, что команда свяжется."
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
_BARGE_IN_THRESHOLD = 250    # lower threshold for barge-in detection (more sensitive)
_SILENCE_FRAMES     = 25     # 25 × 20 ms = 500 ms of silence → end of utterance
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

    # Language selection (1=he 2=en 3=ar 4=ru via DTMF, or auto-detected)
    language:      str  = "he"
    lang_selected: bool = False   # True once caller has chosen or first speech arrived

    # Conversation history for GPT
    messages: list[dict] = field(default_factory=list)

    # VAD state
    audio_buffer:  bytearray = field(default_factory=bytearray)
    speech_frames: int  = 0
    silence_frames: int = 0
    in_speech:     bool = False

    # TTS / barge-in state
    ai_speaking:   bool = False
    barge_in:      asyncio.Event = field(default_factory=asyncio.Event)

    # Guards: only one TTS stream + one utterance processor at a time
    _tts_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    _proc_lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    def system_prompt(self) -> str:
        cfg = _LANG_CONFIG[self.language]
        base = cfg["system"]
        extra = ""
        if self.is_customer:
            extra = "\n=== Existing customer ===\n"
            if self.caller_name:
                extra += f"Name: {self.caller_name}\n"
            if self.business_name:
                extra += f"Business: {self.business_name}\n"
            extra += "Greet them by name and assist warmly.\n"
        elif self.caller_name:
            extra = f"\nKnown contact: {self.caller_name}. Encourage them to join TAZO.\n"
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


# ── GPT streaming ─────────────────────────────────────────────────────────────

async def _gpt_stream(session: VoiceSession) -> AsyncGenerator[str, None]:
    """Stream GPT-4o-mini reply tokens for the current conversation."""
    try:
        oai = AsyncOpenAI(api_key=OPENAI_API_KEY)
        async with oai.chat.completions.stream(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": session.system_prompt()}]
            + session.messages[-20:],
            max_tokens=150,
            temperature=0.7,
        ) as stream:
            async for event in stream:
                delta = event.choices[0].delta.content if event.choices else None
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

        # 1. STT — use language-appropriate Whisper hint
        speech = await _transcribe(audio, cfg["whisper"])
        if not speech:
            logger.warning("[PROC] Empty transcript — skipping")
            return

        logger.info("[PROC] call=%s user: %r", session.call_sid[:8], speech)
        session.messages.append({"role": "user", "content": speech})

        # 2. Farewell shortcut — language-aware
        lower = speech.lower()
        if any(w in lower for w in cfg["farewell"]) and len(speech) < 30:
            bye = cfg["farewell_reply"]
            session.messages.append({"role": "assistant", "content": bye})
            async with session._tts_lock:
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

        # 3. GPT streaming → TTS (pipeline: GPT tokens flow directly into TTS)
        async with session._tts_lock:
            spoken_text = await _play_tts(session, _gpt_stream(session))

        if spoken_text:
            # Strip internal tags before storing in history
            clean = spoken_text.replace("[SEND_LINK]", "").strip()
            session.messages.append({"role": "assistant", "content": clean})
            logger.info("[PROC] call=%s bot: %r", session.call_sid[:8], clean[:80])


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

                logger.info(
                    "[WS] Stream started — call=%s phone=%s*** name=%r customer=%s",
                    session.call_sid[:8],
                    (session.caller_phone or "")[:7],
                    session.caller_name,
                    session.is_customer,
                )

                # Play language selection menu (greeting deferred until language chosen)
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

                # Barge-in detection: caller speaks while AI is talking
                if session.ai_speaking and energy > _BARGE_IN_THRESHOLD:
                    logger.info("[VAD] Barge-in detected (energy=%.0f)", energy)
                    session.barge_in.set()
                    # Clear Twilio's audio buffer
                    await ws.send_text(json.dumps({
                        "event": "clear",
                        "streamSid": session.stream_sid,
                    }))
                    session.ai_speaking = False

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
                break

    except WebSocketDisconnect:
        logger.info("[WS] Twilio disconnected")
    except Exception as exc:
        logger.error("[WS] Unexpected error: %s", exc)


async def _play_greeting(session: VoiceSession, greeting: str) -> None:
    """Play the greeting via TTS — wrapped in tts_lock."""
    async with session._tts_lock:
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
