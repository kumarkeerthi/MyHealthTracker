import json
from dataclasses import dataclass
from datetime import datetime
from threading import Lock
from time import time
from typing import Any
from urllib import error, request

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import DailyLog, FoodItem, MetabolicProfile, User
from app.services.insulin_engine import calculate_insulin_load_score
from app.services.rule_engine import validate_carb_limit, validate_fasting_window, validate_oil_limit


@dataclass
class CachedLLMResponse:
    payload: dict[str, Any]
    expires_at: float


class LLMService:
    def __init__(self, api_key: str | None, model: str, cache_ttl_seconds: int = 900):
        self.api_key = api_key
        self.model = model
        self.cache_ttl_seconds = cache_ttl_seconds
        self._cache: dict[str, CachedLLMResponse] = {}
        self._lock = Lock()

    def analyze(self, db: Session, user: User, profile: MetabolicProfile, text: str, consumed_at: datetime) -> dict[str, Any]:
        cache_key = f"{user.id}:{consumed_at.date().isoformat()}:{text.strip().lower()}"
        extracted = self._from_cache(cache_key)
        if extracted is None:
            extracted = self._extract_from_llm(text)
            if extracted is None:
                extracted = self._fallback_extract(db, text)
            self._save_cache(cache_key, extracted)

        macro_totals = self._calculate_macro_totals(extracted)
        oil_delta = macro_totals["hidden_oil"]
        carb_delta = macro_totals["carbs"]
        protein_delta = macro_totals["protein"]
        meal_delta_score, _raw = calculate_insulin_load_score(carb_delta, oil_delta, protein_delta, 0)

        today_log = db.scalar(
            select(DailyLog).where(DailyLog.user_id == user.id, DailyLog.log_date == consumed_at.date())
        )
        total_carbs = carb_delta + (today_log.total_carbs if today_log else 0.0)
        total_oil = oil_delta + (today_log.total_hidden_oil if today_log else 0.0)

        fasting_ok = validate_fasting_window(consumed_at, profile.fasting_start_time, profile.fasting_end_time)
        carb_ok = validate_carb_limit(total_carbs, profile.carb_ceiling)
        oil_ok = validate_oil_limit(total_oil, profile.oil_limit_tsp)

        blocking_reasons: list[str] = []
        if not fasting_ok:
            blocking_reasons.append("Input falls inside the configured fasting window.")
        if not carb_ok:
            blocking_reasons.append(
                f"Carb ceiling exceeded: projected {round(total_carbs, 2)}g > {profile.carb_ceiling}g."
            )
        if not oil_ok:
            blocking_reasons.append(
                f"Oil cap exceeded: projected {round(total_oil, 2)} tsp > {profile.oil_limit_tsp} tsp."
            )

        if blocking_reasons:
            approval_status = "rejected"
            recommended_adjustment = "Reduce portion or replace with lower-carb/lower-oil option and retry within eating window."
            reasoning = " ".join(blocking_reasons)
        else:
            approval_status = "approved"
            recommended_adjustment = self._build_recommendation(profile, total_carbs, total_oil, extracted)
            reasoning = extracted.get("reasoning") or "Food estimate processed and validated against profile rules."

        return {
            "approval_status": approval_status,
            "reasoning": reasoning,
            "insulin_load_delta": meal_delta_score,
            "recommended_adjustment": recommended_adjustment,
            "food_items": extracted.get("food_items", []),
            "portion": extracted.get("portion", "unspecified"),
            "estimated_macros": extracted.get("estimated_macros", {"protein": 0.0, "carbs": 0.0, "fats": 0.0, "hidden_oil": 0.0}),
            "source": extracted.get("source", "llm"),
        }

    def _build_recommendation(
        self,
        profile: MetabolicProfile,
        projected_carbs: float,
        projected_oil: float,
        extracted: dict[str, Any],
    ) -> str:
        headroom_carbs = max(0.0, round(profile.carb_ceiling - projected_carbs, 2))
        headroom_oil = max(0.0, round(profile.oil_limit_tsp - projected_oil, 2))
        foods = ", ".join(extracted.get("food_items", [])) or "this item"
        return (
            f"{foods}: keep portions conservative. Remaining allowance ≈ {headroom_carbs}g carbs "
            f"and {headroom_oil} tsp hidden oil for today."
        )

    def _from_cache(self, key: str) -> dict[str, Any] | None:
        with self._lock:
            cached = self._cache.get(key)
            if not cached:
                return None
            if cached.expires_at <= time():
                del self._cache[key]
                return None
            return cached.payload

    def _save_cache(self, key: str, payload: dict[str, Any]):
        with self._lock:
            self._cache[key] = CachedLLMResponse(payload=payload, expires_at=time() + self.cache_ttl_seconds)

    def _extract_from_llm(self, text: str) -> dict[str, Any] | None:
        if not self.api_key:
            return None

        schema = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "food_items": {"type": "array", "items": {"type": "string"}},
                "portion": {"type": "string"},
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
                "reasoning": {"type": "string"},
            },
            "required": ["food_items", "portion", "estimated_macros", "reasoning"],
        }

        body = {
            "model": self.model,
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": "food_intake_analysis", "strict": True, "schema": schema},
            },
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Extract food and macro estimates from user text. If text is non-food, return empty food_items and zero macros."
                    ),
                },
                {"role": "user", "content": text},
            ],
            "temperature": 0,
        }

        http_request = request.Request(
            url="https://api.openai.com/v1/chat/completions",
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )

        try:
            with request.urlopen(http_request, timeout=20) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (error.URLError, TimeoutError, json.JSONDecodeError):
            return None

        content = (
            payload.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
        )
        if not content:
            return None

        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            return None

        parsed["source"] = "llm"
        return parsed

    def _fallback_extract(self, db: Session, text: str) -> dict[str, Any]:
        lowered = text.lower()
        foods = db.scalars(select(FoodItem)).all()
        matched = [food for food in foods if food.name.lower() in lowered]

        if matched:
            protein = round(sum(item.protein for item in matched), 2)
            carbs = round(sum(item.carbs for item in matched), 2)
            fats = round(sum(item.fats for item in matched), 2)
            hidden_oil = round(sum(item.hidden_oil_estimate for item in matched), 2)
            food_names = [item.name for item in matched]
        else:
            protein = carbs = fats = hidden_oil = 0.0
            food_names = []

        return {
            "food_items": food_names,
            "portion": "estimated default serving",
            "estimated_macros": {
                "protein": protein,
                "carbs": carbs,
                "fats": fats,
                "hidden_oil": hidden_oil,
            },
            "reasoning": "Fallback extraction used based on known food catalog matching.",
            "source": "fallback",
        }

    @staticmethod
    def _calculate_macro_totals(extracted: dict[str, Any]) -> dict[str, float]:
        estimated_macros = extracted.get("estimated_macros", {})
        return {
            "protein": float(estimated_macros.get("protein", 0.0) or 0.0),
            "carbs": float(estimated_macros.get("carbs", 0.0) or 0.0),
            "fats": float(estimated_macros.get("fats", 0.0) or 0.0),
            "hidden_oil": float(estimated_macros.get("hidden_oil", 0.0) or 0.0),
        }


llm_service = LLMService(
    api_key=settings.openai_api_key,
    model=settings.openai_model,
    cache_ttl_seconds=settings.llm_cache_ttl_seconds,
)
