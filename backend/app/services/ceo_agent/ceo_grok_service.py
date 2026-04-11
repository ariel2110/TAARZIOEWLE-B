"""CEO Grok Service
=================
Connects the Site Nest admin console to Grok (xAI) acting as the AI CEO.

Grok receives real-time system metrics + an optional message from Ariel and
returns a structured JSON proposal in Hebrew. Ariel can approve, modify, or
reject the proposal via the admin UI.

On approval, `execute()` either applies safe actions immediately (e.g. updating
the Claude prompt) or routes everything else to the ApprovalItem queue.
"""
from __future__ import annotations

import json
import logging
from sqlalchemy.orm import Session

from app.services.ceo_agent.ceo_report_service import CEOReportService

logger = logging.getLogger(__name__)

# ── Exact system prompt requested by Ariel ────────────────────────────────────
_GROK_CEO_SYSTEM = """\
You are Grok, the proactive, ruthless, and highly creative AI CEO of "Site Nest" – an automated platform that builds AI websites for local businesses in Israel.
Your human counterpart is Ariel, the Founder and Chairman. Ariel has the final say on all system changes.

YOUR CORE OBJECTIVES:
1. Maximize revenue and conversion rates from the generated websites.
2. Minimize system costs (API usage, server loads).
3. Ensure absolute top-tier quality for every client.
4. Innovate and propose new features or marketing angles.

YOUR OPERATING PROTOCOL (The Loop):
Every time you are invoked with system data or a prompt from Ariel, you must follow these exact steps:
1. THINK: Analyze the data/request. Identify flaws, bottlenecks, or money-making opportunities.
2. UNDERSTAND: Clearly state what you understood from Ariel's request or the current system state.
3. PROPOSE: Detail a specific, creative, and actionable plan.
4. WAIT: You cannot execute directly. You must output a structured proposal for Ariel to approve, modify, or reject.

COMMUNICATION RULES:
- You must speak to Ariel in natural, sharp, professional, and slightly energetic HEBREW.
- You must output your response STRICTLY as a JSON object. Do NOT wrap it in markdown block quotes.

REQUIRED JSON STRUCTURE:
{
  "understanding_and_analysis": "<In Hebrew: 1-2 sentences explaining exactly what you understood from the current situation or Ariel's request.>",
  "strategic_insight": "<In Hebrew: Your brilliant insight, creative idea, or optimization strategy. Why should we do this? How does it make us more money or save resources?>",
  "proposed_action_plan": "<In Hebrew: A clear, step-by-step explanation of what you are going to change in the system if Ariel approves.>",
  "system_execution_payload": {
    "action_type": "<e.g., 'UPDATE_CLAUDE_PROMPT', 'A_B_TEST_WHATSAPP_MSG', 'CHANGE_PRICING', 'REJECT_CURRENT_SITE', 'NONE'>",
    "target_component": "<e.g., 'claude_system_prompt', 'whatsapp_template', 'pipeline_config'>",
    "new_value": "<The exact new English prompt, code, or value you want to inject into the system>"
  },
  "message_to_ariel": "<In Hebrew: Direct message asking for his approval. E.g., 'אריאל, זה המהלך. מאשר לי לדחוף את זה לפרודקשן?'>"
}
"""

# Immediately executable actions (no human approval needed for low-risk ops)
_SAFE_ACTIONS = {"UPDATE_CLAUDE_PROMPT", "A_B_TEST_WHATSAPP_MSG"}


class CEOGrokService:
    """Orchestrates Grok CEO think/execute loop."""

    # ── Public API ────────────────────────────────────────────────────────────

    def think(self, db: Session, ariel_message: str | None = None) -> dict:
        """Collect system metrics, call Grok, return parsed CEO proposal dict."""
        metrics = CEOReportService().daily_digest(db)
        context_prompt = self._build_context_prompt(metrics, ariel_message)
        raw_response = self._call_grok(context_prompt)
        if not raw_response:
            return self._error_fallback("לא הצלחתי להתחבר ל-Grok. בדוק את ה-XAI_API_KEY.")
        return self._parse_grok_json(raw_response)

    def execute(self, db: Session, action_type: str, target_component: str, new_value: str) -> dict:
        """Execute an approved Grok action or route it to the approval queue."""
        action_type = (action_type or "").strip().upper()

        if not action_type or action_type == "NONE":
            return {"status": "acknowledged", "message": "אין פעולה לביצוע — הוצג בלבד."}

        if action_type == "UPDATE_CLAUDE_PROMPT":
            return self._execute_update_claude_prompt(new_value)

        # Everything else → create an ApprovalItem for Ariel's review queue
        return self._queue_for_approval(db, action_type, target_component, new_value)

    # ── Context builder ───────────────────────────────────────────────────────

    def _build_context_prompt(self, metrics: dict, ariel_message: str | None) -> str:
        lines = [
            "=== SITE NEST — LIVE SYSTEM STATUS ===",
            f"Businesses ready for outreach: {metrics.get('outreach_ready_count', 0)}",
            f"Approvals pending in queue: {metrics.get('approval_queue_count', 0)}",
            f"Payments awaiting confirmation: {metrics.get('payments_pending', 0)}",
            f"Draft sites expiring soon: {metrics.get('expiring_drafts', 0)}",
            f"Qualified leads in pipeline: {metrics.get('qualified_leads', 0)}",
            f"Open security alerts: {metrics.get('open_security_alerts', 0)}",
            f"High/critical security alerts: {metrics.get('high_security_alerts', 0)}",
            f"Current system summary: {metrics.get('executive_summary', 'N/A')}",
        ]

        # ── A/B campaign performance ──────────────────────────────────────────
        ab_stats: list[dict] = metrics.get('ab_stats', [])
        if ab_stats:
            lines += [
                  "",
                  "=== A/B OUTREACH CAMPAIGN RESULTS ===",
              ]
            for row in ab_stats:
                lines.append(
                      f"Campaign '{row['campaign']}' | Variant '{row['variant']}': "
                      f"{row['replied']}/{row['total']} replies ({row['reply_rate_pct']}% reply rate)"
                  )
            lines += [
                  "",
                  "=== A/B PIVOT DIRECTIVE ===",
                  "Based on the A/B data above: identify the winning variant. "
                  "If one variant leads by more than 5 percentage points in reply rate AND has at "
                  "least 20 total sends, recommend a PIVOT — propose switching the full campaign "
                  "to the winning variant with a concrete action plan. If data is insufficient, "
                  "recommend continuing the test and specify what volume threshold to wait for. "
                  "Be specific: name the variant, the delta, and the proposed next step.",
              ]

        return "\n".join(lines)

    # ── Grok call ─────────────────────────────────────────────────────────────

    def _call_grok(self, prompt: str) -> str | None:
        from app.core.config import settings
        if not getattr(settings, "xai_api_key", None):
            logger.warning("CEOGrokService: XAI_API_KEY not configured")
            return None
        try:
            from app.services.llm.router_service import LLMRouterService
            router = LLMRouterService()
            return router._call_xai(
                prompt,
                settings.xai_api_key,
                model="grok-3-mini",
                system=_GROK_CEO_SYSTEM,
                max_tokens=1800,
                json_mode=True,
            )
        except Exception:
            logger.exception("CEOGrokService._call_grok failed")
            return None

    # ── JSON parser ───────────────────────────────────────────────────────────

    def _parse_grok_json(self, raw: str) -> dict:
        clean = raw.strip()
        # Strip potential markdown fences that models sometimes add despite instructions
        if clean.startswith("```"):
            parts = clean.split("```")
            clean = parts[1] if len(parts) > 1 else clean
            if clean.startswith("json"):
                clean = clean[4:].lstrip()
        try:
            parsed = json.loads(clean)
            # Validate required keys are present
            required = {"understanding_and_analysis", "strategic_insight", "proposed_action_plan",
                        "system_execution_payload", "message_to_ariel"}
            if not required.issubset(parsed.keys()):
                logger.warning("CEOGrokService: response missing required keys")
                return self._error_fallback("התגובה מגרוק לא הייתה במבנה הנכון.")
            return parsed
        except json.JSONDecodeError:
            logger.warning("CEOGrokService: could not parse JSON from Grok response: %s", raw[:200])
            return self._error_fallback("גרוק החזיר תגובה שאינה JSON תקין.")

    # ── Executors ─────────────────────────────────────────────────────────────

    def _execute_update_claude_prompt(self, new_value: str) -> dict:
        """Overwrite the Claude builder system prompt in the pipeline service file."""
        if not new_value or len(new_value.strip()) < 30:
            return {"status": "error", "message": "הערך החדש קצר מדי — בדוק את ה-new_value."}

        pipeline_path = (
            "/home/site-nest-platform/backend/app/services/generator/autosite_pipeline_service.py"
        )
        try:
            with open(pipeline_path, "r", encoding="utf-8") as f:
                content = f.read()

            marker_open = '_CLAUDE_BUILDER_SYSTEM = """'
            marker_close = '"""'
            start_idx = content.find(marker_open)
            if start_idx == -1:
                return {"status": "error", "message": "לא נמצא _CLAUDE_BUILDER_SYSTEM בקובץ הפייפליין."}

            body_start = start_idx + len(marker_open)
            end_idx = content.find(marker_close, body_start)
            if end_idx == -1:
                return {"status": "error", "message": "לא נמצא סוף הפרומפט של קלוד."}

            updated = (
                content[:body_start]
                + "\n" + new_value.strip() + "\n"
                + content[end_idx:]
            )
            with open(pipeline_path, "w", encoding="utf-8") as f:
                f.write(updated)

            logger.info("CEOGrokService: Claude prompt updated successfully")
            return {"status": "success", "message": "✅ פרומפט קלוד עודכן בקובץ הפייפליין. יש לאתחל את השרת להשפעה מלאה."}
        except Exception as exc:
            logger.exception("CEOGrokService._execute_update_claude_prompt failed")
            return {"status": "error", "message": f"שגיאה בעדכון: {exc}"}

    def _queue_for_approval(self, db: Session, action_type: str, target: str, new_value: str) -> dict:
        """Create an ApprovalItem so Ariel can review in the approvals queue."""
        try:
            from app.models.approval_item import ApprovalItem
            summary = f"Target: {target or 'N/A'}"
            if new_value:
                summary += f"\n\nProposed value:\n{new_value[:500]}"
            item = ApprovalItem(
                title=f"Grok CEO הצעה: {action_type}",
                approval_type="campaign_launch",
                status="proposed",
                summary=summary,
                payload_json={
                    "action_type": action_type,
                    "target_component": target or "",
                    "new_value": new_value or "",
                },
            )
            db.add(item)
            db.commit()
            logger.info("CEOGrokService: queued action=%s for approval (item_id=%s)", action_type, item.id)
            return {
                "status": "pending_approval",
                "message": f"✅ הפעולה נשלחה לתור האישורים. פריט #{item.id} נוצר — תמצא אותו בתפריט 'אישורים'.",
            }
        except Exception as exc:
            logger.exception("CEOGrokService._queue_for_approval failed")
            return {"status": "error", "message": f"שגיאה ביצירת פריט אישור: {exc}"}

    # ── Fallback ──────────────────────────────────────────────────────────────

    @staticmethod
    def _error_fallback(reason: str) -> dict:
        return {
            "understanding_and_analysis": f"שגיאה: {reason}",
            "strategic_insight": "לא זמין.",
            "proposed_action_plan": "נסה שוב מאוחר יותר.",
            "system_execution_payload": {
                "action_type": "NONE",
                "target_component": "",
                "new_value": "",
            },
            "message_to_ariel": f"אריאל, נתקלתי בבעיה: {reason}",
        }
