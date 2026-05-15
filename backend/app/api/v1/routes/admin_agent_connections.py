from __future__ import annotations
import time
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from app.api.deps import get_current_admin
from app.models.user import User

router = APIRouter(prefix='/admin/agents', tags=['admin-agents'])


class AgentConnectionResult(BaseModel):
    agent: str
    ok: bool
    latency_ms: float
    detail: str
    extra: Optional[dict] = None


class AgentConnectionTestResponse(BaseModel):
    all_ok: bool
    tested_at: str
    test_business: str
    results: list[AgentConnectionResult]


def _test_provider(name: str, api_key: str, test_fn) -> AgentConnectionResult:
    if not api_key:
        return AgentConnectionResult(agent=name, ok=False, latency_ms=0, detail='API key not configured')
    t0 = time.monotonic()
    try:
        detail = test_fn()
        latency_ms = round((time.monotonic() - t0) * 1000, 1)
        return AgentConnectionResult(agent=name, ok=True, latency_ms=latency_ms, detail=detail)
    except Exception as e:
        latency_ms = round((time.monotonic() - t0) * 1000, 1)
        return AgentConnectionResult(agent=name, ok=False, latency_ms=latency_ms, detail=str(e)[:200])


@router.get('/connection-test', response_model=AgentConnectionTestResponse)
async def connection_test(_: User = Depends(get_current_admin)):
    from app.core.config import settings
    results = []

    # OpenAI
    def test_openai():
        import httpx
        r = httpx.get('https://api.openai.com/v1/models', headers={'Authorization': f'Bearer {settings.openai_api_key}'}, timeout=8)
        return f'HTTP {r.status_code}'
    results.append(_test_provider('openai', settings.openai_api_key or '', test_openai))

    # Anthropic
    def test_anthropic():
        import httpx
        r = httpx.post('https://api.anthropic.com/v1/messages',
            headers={'x-api-key': settings.anthropic_api_key or '', 'anthropic-version': '2023-06-01', 'content-type': 'application/json'},
            json={'model': 'claude-3-haiku-20240307', 'max_tokens': 1, 'messages': [{'role': 'user', 'content': 'hi'}]},
            timeout=10)
        return f'HTTP {r.status_code}'
    results.append(_test_provider('anthropic', settings.anthropic_api_key or '', test_anthropic))

    # Gemini
    def test_gemini():
        import httpx
        r = httpx.get(f'https://generativelanguage.googleapis.com/v1beta/models?key={settings.gemini_api_key}', timeout=8)
        return f'HTTP {r.status_code}'
    results.append(_test_provider('gemini', settings.gemini_api_key or '', test_gemini))

    all_ok = all(r.ok for r in results)
    return AgentConnectionTestResponse(
        all_ok=all_ok,
        tested_at=datetime.now(timezone.utc).isoformat(),
        test_business='connection-test',
        results=results,
    )
