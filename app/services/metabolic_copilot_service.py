import asyncio
import json
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from threading import Lock
from time import time
from typing import Any, Callable
from urllib import error, request

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import (
    AIActionLog,
    AIConversation,
    AIMessage,
    AIMessageRole,
    DailyLog,
    ExerciseEntry,
    FoodItem,
    MealEntry,
    MetabolicProfile,
    User,
    VitalsEntry,
)


@dataclass
class CachedSnapshot:
    data: dict[str, Any]
    expires_at: float


class MetabolicCopilotService:
    def __init__(self, api_key: str | None, model: str, snapshot_ttl_seconds: int = 60):
        self.api_key = api_key
        self.model = model
        self.snapshot_ttl_seconds = snapshot_ttl_seconds
        self._snapshot_cache: dict[int, CachedSnapshot] = {}
        self._lock = Lock()

    async def process_message(self, db: Session, user_id: int, user_message: str, conversation_id: int | None = None) -> dict[str, Any]:
        clean_message = user_message.strip()[: settings.llm_max_input_chars]
        if not clean_message:
            raise ValueError("Message cannot be empty")

        conversation = self._get_or_create_conversation(db, user_id=user_id, conversation_id=conversation_id)
        db.add(AIMessage(conversation_id=conversation.id, role=AIMessageRole.USER, content=clean_message))

        if self._contains_harmful_medical_request(clean_message):
            safe = (
                "I can help with metabolic education, but I can’t provide harmful or unsafe medical guidance. "
                "Please consult a licensed clinician for treatment-critical decisions."
            )
            db.add(AIMessage(conversation_id=conversation.id, role=AIMessageRole.ASSISTANT, content=safe))
            db.flush()
            return {
                "conversation_id": conversation.id,
                "assistant_message": safe,
                "actions_executed": [],
            }

        snapshot = self._get_grounding_snapshot(db, user_id)
        messages, summary = self._build_context(db, conversation.id)
        system_prompt = self._build_system_prompt(snapshot=snapshot, summary=summary)

        parsed = await self._call_structured_llm(system_prompt=system_prompt, messages=messages, user_message=clean_message)
        assistant_message = parsed.get("assistant_message", "I could not generate a response.")
        actions_executed: list[dict[str, Any]] = []

        action = parsed.get("action")
        if isinstance(action, dict) and action.get("action") == "log_meal":
            action_result = self._execute_log_meal_action(
                db=db,
                user_id=user_id,
                conversation=conversation,
                action=action,
                snapshot=snapshot,
            )
            actions_executed.append(action_result)
            assistant_message = action_result["confirmation"]

        db.add(AIMessage(conversation_id=conversation.id, role=AIMessageRole.ASSISTANT, content=assistant_message[:4000]))
        conversation.updated_at = datetime.utcnow()
        self._refresh_summary(db, conversation)
        db.flush()

        return {
            "conversation_id": conversation.id,
            "assistant_message": assistant_message,
            "actions_executed": actions_executed,
        }

    def _get_or_create_conversation(self, db: Session, *, user_id: int, conversation_id: int | None) -> AIConversation:
        if conversation_id:
            conversation = db.scalar(
                select(AIConversation).where(AIConversation.id == conversation_id, AIConversation.user_id == user_id)
            )
            if conversation:
                return conversation
            raise ValueError("Conversation not found")

        conversation = AIConversation(user_id=user_id, title="Metabolic Copilot")
        db.add(conversation)
        db.flush()
        return conversation

    def _build_context(self, db: Session, conversation_id: int) -> tuple[list[dict[str, str]], str]:
        message_rows = db.scalars(
            select(AIMessage)
            .where(AIMessage.conversation_id == conversation_id)
            .order_by(AIMessage.created_at.asc(), AIMessage.id.asc())
        ).all()
        summary = ""
        if len(message_rows) > 10:
            older = message_rows[:-10]
            summary = " ".join(f"{m.role.value}: {m.content}" for m in older)[-2000:]
            message_rows = message_rows[-10:]

        prompt_messages = [{"role": msg.role.value, "content": msg.content[:2000]} for msg in message_rows]
        return prompt_messages, summary

    def _refresh_summary(self, db: Session, conversation: AIConversation) -> None:
        message_rows = db.scalars(
            select(AIMessage)
            .where(AIMessage.conversation_id == conversation.id)
            .order_by(AIMessage.created_at.asc(), AIMessage.id.asc())
        ).all()
        if len(message_rows) <= 10:
            return
        older = message_rows[:-10]
        conversation.summary = " ".join(f"{m.role.value}: {m.content}" for m in older)[-3000:]

    def _get_grounding_snapshot(self, db: Session, user_id: int) -> dict[str, Any]:
        cached = self._from_cache(user_id)
        if cached:
            return cached

        user = db.get(User, user_id)
        if not user:
            raise ValueError("User not found")
        profile = db.scalar(select(MetabolicProfile).where(MetabolicProfile.user_id == user_id))

        today = date.today()
        week_start = today - timedelta(days=6)
        today_log = db.scalar(select(DailyLog).where(DailyLog.user_id == user_id, DailyLog.log_date == today))
        week_logs = db.scalars(
            select(DailyLog).where(DailyLog.user_id == user_id, DailyLog.log_date >= week_start, DailyLog.log_date <= today)
        ).all()
        last_vitals = db.scalar(
            select(VitalsEntry).where(VitalsEntry.user_id == user_id).order_by(VitalsEntry.recorded_at.desc(), VitalsEntry.id.desc())
        )
        movement = db.scalar(
            select(
                func.coalesce(func.sum(ExerciseEntry.step_count), 0).label("steps"),
            ).where(ExerciseEntry.user_id == user_id, ExerciseEntry.performed_at >= datetime.utcnow() - timedelta(days=7))
        )
        strength_index = db.scalar(
            select(func.coalesce(func.avg(ExerciseEntry.pull_strength_score), 0.0)).where(ExerciseEntry.user_id == user_id)
        )

        snapshot = {
            "metabolic_profile": {
                "carb_ceiling": profile.carb_ceiling if profile else user.carb_ceiling,
                "protein_target_min": profile.protein_target_min if profile else user.protein_target_min,
                "protein_target_max": profile.protein_target_max if profile else user.protein_target_max,
                "oil_limit_tsp": profile.oil_limit_tsp if profile else user.oil_limit_tsp,
                "eating_window": {
                    "start": user.eating_window_start,
                    "end": user.eating_window_end,
                },
            },
            "today_macros": {
                "protein": float(today_log.total_protein if today_log else 0.0),
                "carbs": float(today_log.total_carbs if today_log else 0.0),
                "fats": float(today_log.total_fats if today_log else 0.0),
                "hidden_oil": float(today_log.total_hidden_oil if today_log else 0.0),
            },
            "last_7_days_carb_intake": [
                {"date": row.log_date.isoformat(), "carbs": float(row.total_carbs)} for row in sorted(week_logs, key=lambda x: x.log_date)
            ],
            "biomarkers": {
                "triglycerides": float(last_vitals.triglycerides if last_vitals and last_vitals.triglycerides is not None else user.triglycerides),
                "hdl": float(last_vitals.hdl if last_vitals and last_vitals.hdl is not None else user.hdl),
                "hba1c": float(last_vitals.hba1c if last_vitals and last_vitals.hba1c is not None else user.hba1c),
            },
            "strength_index": round(float(strength_index or 0.0), 2),
            "movement_stats": {
                "steps_last_7_days": int(movement or 0),
            },
        }
        self._save_cache(user_id, snapshot)
        return snapshot

    def _build_system_prompt(self, *, snapshot: dict[str, Any], summary: str) -> str:
        return (
            "You are Metabolic Copilot, a grounded metabolic assistant. Use only the provided JSON grounding data. "
            "Never hallucinate unknown values. If data is missing, ask clarification. Detect meal logging intent. "
            "For harmful medical requests, provide safe disclaimer guidance only. "
            "If recommending, use sections: Current metabolic status, Impact analysis, Suggestion, Clear yes/no. "
            "If the user clearly states they consumed food, return an action block with action=log_meal, items, estimated_macros, confidence. "
            f"Conversation summary: {summary or 'none'}. Grounding data: {json.dumps(snapshot)}"
        )

    async def _call_structured_llm(self, *, system_prompt: str, messages: list[dict[str, str]], user_message: str) -> dict[str, Any]:
        schema = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "assistant_message": {"type": "string"},
                "action": {
                    "anyOf": [
                        {"type": "null"},
                        {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "action": {"type": "string", "enum": ["log_meal", "log_water", "log_exercise", "log_vitals", "upload_lab_report"]},
                                "items": {"type": "array", "items": {"type": "string"}},
                                "estimated_macros": {
                                    "type": "object",
                                    "additionalProperties": False,
                                    "properties": {
                                        "protein": {"type": "number"},
                                        "carbs": {"type": "number"},
                                        "fats": {"type": "number"},
                                        "hidden_oil": {"type": "number"},
                                    },
                                    "required": ["protein", "carbs", "fats", "hidden_oil"],
                                },
                                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                            },
                            "required": ["action", "items", "estimated_macros", "confidence"],
                        },
                    ]
                },
            },
            "required": ["assistant_message", "action"],
        }

        payload = {
            "model": self.model,
            "temperature": 0,
            "max_tokens": min(settings.llm_max_tokens, 500),
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": "metabolic_copilot", "strict": True, "schema": schema},
            },
            "messages": [{"role": "system", "content": system_prompt}, *messages[-10:], {"role": "user", "content": user_message}],
        }

        if not self.api_key:
            return {"assistant_message": "Copilot is currently unavailable. Please try again later.", "action": None}

        try:
            raw = await asyncio.wait_for(asyncio.to_thread(self._post_chat_completion, payload), timeout=20)
        except TimeoutError:
            return {"assistant_message": "Copilot timed out. Please retry.", "action": None}
        except Exception:
            return {"assistant_message": "Copilot is temporarily unavailable. Please retry.", "action": None}

        content = raw.get("choices", [{}])[0].get("message", {}).get("content", "")
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            return {"assistant_message": "I could not parse a reliable response. Please rephrase.", "action": None}

        if not isinstance(parsed, dict):
            return {"assistant_message": "I could not parse a reliable response. Please rephrase.", "action": None}

        parsed["assistant_message"] = str(parsed.get("assistant_message", "")).strip()[:3000]
        return parsed

    def _post_chat_completion(self, payload: dict[str, Any]) -> dict[str, Any]:
        http_request = request.Request(
            url="https://api.openai.com/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        try:
            with request.urlopen(http_request, timeout=20) as response:
                return json.loads(response.read().decode("utf-8"))
        except (error.URLError, json.JSONDecodeError) as exc:
            raise RuntimeError("llm_call_failed") from exc

    def _execute_log_meal_action(
        self,
        *,
        db: Session,
        user_id: int,
        conversation: AIConversation,
        action: dict[str, Any],
        snapshot: dict[str, Any],
    ) -> dict[str, Any]:
        items = [self._normalize_food_name(item) for item in action.get("items", []) if str(item).strip()]
        estimated = action.get("estimated_macros") or {}
        if not items:
            raise ValueError("Unable to log meal without item names")

        now = datetime.utcnow()
        today = now.date()
        daily_log = db.scalar(select(DailyLog).where(DailyLog.user_id == user_id, DailyLog.log_date == today))
        if not daily_log:
            daily_log = DailyLog(user_id=user_id, log_date=today)
            db.add(daily_log)
            db.flush()

        carbs = float(max(0.0, estimated.get("carbs", 0.0)))
        protein = float(max(0.0, estimated.get("protein", 0.0)))
        fats = float(max(0.0, estimated.get("fats", 0.0)))
        hidden_oil = float(max(0.0, estimated.get("hidden_oil", 0.0)))

        daily_log.total_carbs += carbs
        daily_log.total_protein += protein
        daily_log.total_fats += fats
        daily_log.total_hidden_oil += hidden_oil

        per_item = {
            "protein": protein / len(items),
            "carbs": carbs / len(items),
            "fats": fats / len(items),
            "hidden_oil": hidden_oil / len(items),
        }

        for item in items:
            food = db.scalar(select(FoodItem).where(FoodItem.name == item))
            if not food:
                food = FoodItem(
                    name=item,
                    protein=round(per_item["protein"], 2),
                    carbs=round(per_item["carbs"], 2),
                    fats=round(per_item["fats"], 2),
                    sugar=0.0,
                    fiber=0.0,
                    glycemic_load=max(1.0, round(per_item["carbs"] * 0.6, 2)),
                    hdl_support_score=0.0,
                    triglyceride_risk_weight=0.0,
                    food_group="llm_estimate",
                    high_carb_flag=per_item["carbs"] > 20,
                    nut_seed_exception=False,
                    hidden_oil_estimate=round(per_item["hidden_oil"], 2),
                )
                db.add(food)
                db.flush()
            db.add(MealEntry(daily_log_id=daily_log.id, food_item_id=food.id, consumed_at=now, servings=1.0, manual_adjustment_flag=True))

        outside_window = self._outside_eating_window(snapshot, now)
        payload = {
            "items": items,
            "estimated_macros": {
                "protein": round(protein, 2),
                "carbs": round(carbs, 2),
                "fats": round(fats, 2),
                "hidden_oil": round(hidden_oil, 2),
            },
            "confidence": float(action.get("confidence", 0.0)),
            "outside_eating_window": outside_window,
        }
        db.add(AIActionLog(user_id=user_id, conversation_id=conversation.id, action_type="meal_logged", payload=self._sanitize_payload(payload)))

        warnings = " Outside your eating window." if outside_window else ""
        confirmation = f"Logged successfully. Today’s carbs: {round(daily_log.total_carbs, 1)}g/{snapshot['metabolic_profile']['carb_ceiling']}g.{warnings}"
        return {"action_type": "meal_logged", "items": items, "db_action": True, "confirmation": confirmation}

    def _outside_eating_window(self, snapshot: dict[str, Any], now: datetime) -> bool:
        start = snapshot["metabolic_profile"]["eating_window"]["start"]
        end = snapshot["metabolic_profile"]["eating_window"]["end"]
        current = now.strftime("%H:%M")
        return not (start <= current <= end)

    def _normalize_food_name(self, value: str) -> str:
        cleaned = re.sub(r"[^a-zA-Z0-9\s\-]", "", value).strip().lower()
        return cleaned[:120] or "unknown meal"

    def _sanitize_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        redacted = json.dumps(payload)
        redacted = re.sub(r"[\w\.-]+@[\w\.-]+", "[redacted_email]", redacted)
        redacted = re.sub(r"\+?\d[\d\-\s]{7,}\d", "[redacted_phone]", redacted)
        return json.loads(redacted)

    def _contains_harmful_medical_request(self, message: str) -> bool:
        lowered = message.lower()
        risky_terms = ("overdose", "self-harm", "stop insulin", "dangerous dose", "harm myself")
        return any(term in lowered for term in risky_terms)

    def _from_cache(self, user_id: int) -> dict[str, Any] | None:
        with self._lock:
            snapshot = self._snapshot_cache.get(user_id)
            if not snapshot:
                return None
            if snapshot.expires_at <= time():
                del self._snapshot_cache[user_id]
                return None
            return snapshot.data

    def _save_cache(self, user_id: int, data: dict[str, Any]) -> None:
        with self._lock:
            self._snapshot_cache[user_id] = CachedSnapshot(data=data, expires_at=time() + self.snapshot_ttl_seconds)


metabolic_copilot_service = MetabolicCopilotService(api_key=settings.openai_api_key, model=settings.openai_model)
