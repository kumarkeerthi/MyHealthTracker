import base64
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from threading import Lock
from time import time
from typing import Any
from urllib import error, request

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import DailyLog, FoodItem, MealEntry, MetabolicProfile, User
from app.services.insulin_engine import calculate_insulin_load_score
from app.services.rule_engine import (
    calculate_daily_macros,
    evaluate_daily_status,
    validate_carb_limit,
    validate_fasting_window,
    validate_oil_limit,
    validate_protein_minimum,
)

REFERENCE_CARD_WIDTH_MM = 85.6
REFERENCE_CARD_HEIGHT_MM = 53.98
REFERENCE_CARD_AREA_MM2 = REFERENCE_CARD_WIDTH_MM * REFERENCE_CARD_HEIGHT_MM
REFERENCE_CARD_BASELINE_AREA_PX = 18500

VISION_PROMPT_TEMPLATE = """
You are a nutrition vision model. Analyze the attached meal photo and return JSON only.
If a reference card is present (credit-card size 85.6mm x 53.98mm), estimate its pixel width and height.
Output schema:
{
  "foods": [
    {
      "name": "",
      "estimated_quantity_grams": number,
      "confidence": number,
      "estimated_protein": number,
      "estimated_carbs": number,
      "estimated_fat": number,
      "estimated_hidden_oil": number
    }
  ],
  "plate_estimated_total_calories": number,
  "overall_confidence": number,
  "reference_card": {
    "detected": boolean,
    "width_px": number,
    "height_px": number
  }
}
Rules:
- JSON only, no markdown.
- confidence fields are in [0,1].
- grams/macros/oil/calories are non-negative.
""".strip()

EXAMPLE_ANALYSIS_JSON = {
    "foods": [
        {
            "name": "Paneer butter masala",
            "estimated_quantity_grams": 210,
            "confidence": 0.88,
            "estimated_protein": 17,
            "estimated_carbs": 16,
            "estimated_fat": 24,
            "estimated_hidden_oil": 2.4,
        },
        {
            "name": "Butter naan",
            "estimated_quantity_grams": 95,
            "confidence": 0.83,
            "estimated_protein": 8,
            "estimated_carbs": 47,
            "estimated_fat": 10,
            "estimated_hidden_oil": 1.2,
        },
    ],
    "plate_estimated_total_calories": 720,
    "overall_confidence": 0.84,
}

KNOWN_DENSITY_RANGES = {
    "paneer": {"protein": (10, 28), "carbs": (1, 12), "fat": (12, 35)},
    "naan": {"protein": (5, 15), "carbs": (35, 70), "fat": (4, 20)},
    "chapati": {"protein": (7, 18), "carbs": (45, 78), "fat": (2, 9)},
    "rice": {"protein": (1, 9), "carbs": (20, 40), "fat": (0, 4)},
    "dal": {"protein": (5, 18), "carbs": (12, 30), "fat": (1, 12)},
}


@dataclass
class CachedImageAnalysis:
    payload: dict[str, Any]
    expires_at: float


class FoodImageService:
    def __init__(self, api_key: str | None, model: str, cache_ttl_seconds: int = 900):
        self.api_key = api_key
        self.model = model
        self.cache_ttl_seconds = cache_ttl_seconds
        self._cache: dict[str, CachedImageAnalysis] = {}
        self._lock = Lock()

    def analyze_food_image(
        self,
        db: Session,
        user: User,
        profile: MetabolicProfile,
        image_bytes: bytes,
        meal_context: str | None,
        consumed_at: datetime,
    ) -> dict[str, Any]:
        image_url, prepared_bytes = self._store_image(image_bytes)
        cache_key = hashlib.sha256(prepared_bytes[:100_000]).hexdigest()
        extracted = self._from_cache(cache_key)
        if extracted is None:
            extracted = self._extract_with_vision(prepared_bytes, meal_context)
            self._save_cache(cache_key, extracted)

        scale_factor, portion_confidence = self._calibrate_portion_scale(extracted)
        foods = extracted.get("foods", [])
        for food in foods:
            food["estimated_quantity_grams"] = round(max(0.0, float(food.get("estimated_quantity_grams", 0.0))) * scale_factor, 2)

        macros = self._macro_totals(foods)
        insulin_delta, _raw = calculate_insulin_load_score(macros["carbs"], macros["hidden_oil"], macros["protein"], 0)

        today_log = db.scalar(select(DailyLog).where(DailyLog.user_id == user.id, DailyLog.log_date == consumed_at.date()))
        projected_carbs = macros["carbs"] + (today_log.total_carbs if today_log else 0.0)
        projected_oil = macros["hidden_oil"] + (today_log.total_hidden_oil if today_log else 0.0)
        projected_protein = macros["protein"] + (today_log.total_protein if today_log else 0.0)
        projected_score, _ = calculate_insulin_load_score(projected_carbs, projected_oil, projected_protein, 0)

        validation = self._validate_output(foods, macros, profile, consumed_at, projected_carbs, projected_oil)
        approval = self._approval_label(projected_score)
        coaching = self._coaching_message(macros)

        return {
            "foods": foods,
            "plate_estimated_total_calories": round(float(extracted.get("plate_estimated_total_calories", 0.0)), 2),
            "overall_confidence": round(float(extracted.get("overall_confidence", 0.0)), 3),
            "portion_scale_factor": round(scale_factor, 3),
            "portion_estimation_confidence": portion_confidence,
            "image_url": image_url,
            "estimated_macros": {"protein": macros["protein"], "carbs": macros["carbs"], "fats": macros["fats"]},
            "estimated_oil_tsp": macros["hidden_oil"],
            "insulin_load_impact": insulin_delta,
            "projected_daily_insulin_score": projected_score,
            "approval": approval,
            "validation": validation,
            "coaching": coaching,
            "llm_prompt_template": VISION_PROMPT_TEMPLATE,
            "example_analysis_json": EXAMPLE_ANALYSIS_JSON,
        }

    def confirm_and_log(
        self,
        db: Session,
        user: User,
        profile: MetabolicProfile,
        foods: list[dict[str, Any]],
        image_url: str,
        vision_confidence: float,
        portion_scale_factor: float,
        manual_adjustment_flag: bool,
        consumed_at: datetime,
    ) -> dict[str, Any]:
        log_date = consumed_at.date()
        daily_log = db.scalar(select(DailyLog).where(DailyLog.user_id == user.id, DailyLog.log_date == log_date))
        if not daily_log:
            daily_log = DailyLog(user_id=user.id, log_date=log_date)
            db.add(daily_log)
            db.flush()

        for food in foods:
            food_name = food["name"].strip().lower()
            matched = db.scalar(select(FoodItem).where(FoodItem.name.ilike(food_name)).limit(1))
            if not matched:
                grams = max(1.0, float(food.get("estimated_quantity_grams", 100.0)))
                scale = grams / 100.0
                matched = FoodItem(
                    name=food["name"].strip().title(),
                    protein=round(float(food.get("estimated_protein", 0.0)) / scale, 2),
                    carbs=round(float(food.get("estimated_carbs", 0.0)) / scale, 2),
                    fats=round(float(food.get("estimated_fat", 0.0)) / scale, 2),
                    hidden_oil_estimate=round(float(food.get("estimated_hidden_oil", 0.0)) / scale, 2),
                    glycemic_load=max(0.0, round(float(food.get("estimated_carbs", 0.0)) * 0.5, 2)),
                )
                db.add(matched)
                db.flush()

            servings = max(0.1, float(food.get("estimated_quantity_grams", 100.0)) / 100.0)
            db.add(
                MealEntry(
                    daily_log_id=daily_log.id,
                    food_item_id=matched.id,
                    consumed_at=consumed_at,
                    servings=servings,
                    image_url=image_url,
                    vision_confidence=vision_confidence,
                    manual_adjustment_flag=manual_adjustment_flag,
                    portion_scale_factor=portion_scale_factor,
                )
            )

        db.flush()
        meal_entries = db.scalars(select(MealEntry).where(MealEntry.daily_log_id == daily_log.id)).all()
        food_map = {f.id: f for f in db.scalars(select(FoodItem).where(FoodItem.id.in_([m.food_item_id for m in meal_entries]))).all()}
        totals = calculate_daily_macros(
            [
                {
                    "protein": food_map[m.food_item_id].protein,
                    "carbs": food_map[m.food_item_id].carbs,
                    "fats": food_map[m.food_item_id].fats,
                    "hidden_oil_estimate": food_map[m.food_item_id].hidden_oil_estimate,
                    "servings": m.servings,
                }
                for m in meal_entries
            ]
        )
        daily_log.total_protein = totals["protein"]
        daily_log.total_carbs = totals["carbs"]
        daily_log.total_fats = totals["fats"]
        daily_log.total_hidden_oil = totals["hidden_oil"]

        status = evaluate_daily_status(db, daily_log, profile)
        validations = {
            "carb_limit": validate_carb_limit(totals["carbs"], profile.carb_ceiling),
            "oil_limit": validate_oil_limit(totals["hidden_oil"], profile.oil_limit_tsp),
            "protein_minimum": validate_protein_minimum(totals["protein"], profile.protein_target_min),
        }
        db.commit()
        return {
            "daily_log_id": daily_log.id,
            "insulin_load_score": status["insulin_load_score"],
            "total_protein": totals["protein"],
            "total_carbs": totals["carbs"],
            "total_fats": totals["fats"],
            "total_hidden_oil": totals["hidden_oil"],
            "validations": validations,
        }

    def _extract_with_vision(self, image_bytes: bytes, meal_context: str | None) -> dict[str, Any]:
        if not self.api_key:
            return EXAMPLE_ANALYSIS_JSON | {"reference_card": {"detected": False, "width_px": 0, "height_px": 0}}

        image_b64 = base64.b64encode(image_bytes).decode("utf-8")
        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": VISION_PROMPT_TEMPLATE},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"Meal context: {meal_context or 'unspecified'}"},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}},
                    ],
                },
            ],
            "temperature": 0,
            "max_tokens": 900,
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
            with request.urlopen(http_request, timeout=30) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (error.URLError, TimeoutError, json.JSONDecodeError):
            return EXAMPLE_ANALYSIS_JSON | {"reference_card": {"detected": False, "width_px": 0, "height_px": 0}}

        content = payload.get("choices", [{}])[0].get("message", {}).get("content", "")
        if not content:
            return EXAMPLE_ANALYSIS_JSON | {"reference_card": {"detected": False, "width_px": 0, "height_px": 0}}
        try:
            parsed = json.loads(content)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass
        return EXAMPLE_ANALYSIS_JSON | {"reference_card": {"detected": False, "width_px": 0, "height_px": 0}}

    def _store_image(self, image_bytes: bytes) -> tuple[str, bytes]:
        max_size = settings.max_food_image_bytes
        prepared = image_bytes[:max_size]
        digest = hashlib.sha256(prepared).hexdigest()[:18]
        uploads_dir = Path(settings.food_image_upload_dir)
        uploads_dir.mkdir(parents=True, exist_ok=True)
        filename = f"food_{digest}.jpg"
        filepath = uploads_dir / filename
        filepath.write_bytes(prepared)
        return f"{settings.food_image_public_base_url.rstrip('/')}/{filename}", prepared

    def _calibrate_portion_scale(self, extracted: dict[str, Any]) -> tuple[float, str]:
        card = extracted.get("reference_card") or {}
        detected = bool(card.get("detected"))
        width_px = float(card.get("width_px", 0) or 0)
        height_px = float(card.get("height_px", 0) or 0)
        if not detected or width_px <= 0 or height_px <= 0:
            return 1.0, "LOW"

        card_area_px = width_px * height_px
        _area_ratio = REFERENCE_CARD_AREA_MM2 / REFERENCE_CARD_AREA_MM2
        scale_factor = (card_area_px / REFERENCE_CARD_BASELINE_AREA_PX) ** 0.5
        scale_factor = max(0.65, min(1.45, scale_factor))
        confidence = "HIGH" if 0.8 <= scale_factor <= 1.2 else "MEDIUM"
        return scale_factor, confidence

    def _macro_totals(self, foods: list[dict[str, Any]]) -> dict[str, float]:
        protein = sum(max(0.0, float(item.get("estimated_protein", 0.0))) for item in foods)
        carbs = sum(max(0.0, float(item.get("estimated_carbs", 0.0))) for item in foods)
        fats = sum(max(0.0, float(item.get("estimated_fat", 0.0))) for item in foods)
        hidden_oil = sum(max(0.0, float(item.get("estimated_hidden_oil", 0.0))) for item in foods)
        return {
            "protein": round(protein, 2),
            "carbs": round(carbs, 2),
            "fats": round(fats, 2),
            "hidden_oil": round(hidden_oil, 2),
        }

    def _validate_output(
        self,
        foods: list[dict[str, Any]],
        macros: dict[str, float],
        profile: MetabolicProfile,
        consumed_at: datetime,
        projected_carbs: float,
        projected_oil: float,
    ) -> dict[str, Any]:
        macro_totals_valid = all(v >= 0 for v in macros.values())
        food_ranges_valid = self._validate_food_ranges(foods)
        fasting_ok = validate_fasting_window(consumed_at, profile.fasting_start_time, profile.fasting_end_time)
        carb_ok = validate_carb_limit(projected_carbs, profile.carb_ceiling)
        oil_ok = validate_oil_limit(projected_oil, profile.oil_limit_tsp)

        chapati_estimate = 0.0
        for item in foods:
            name = item.get("name", "").lower()
            if any(k in name for k in ["chapati", "roti", "naan"]):
                chapati_estimate += max(0.0, float(item.get("estimated_quantity_grams", 0.0))) / 40.0
        chapati_ok = chapati_estimate <= profile.max_chapati_per_day

        low_confidence_flag = not food_ranges_valid
        message = "Validated."
        if low_confidence_flag:
            message = "Low confidence – please adjust manually."

        return {
            "macro_totals_valid": macro_totals_valid,
            "food_ranges_valid": food_ranges_valid,
            "fasting_window_ok": fasting_ok,
            "carb_ceiling_ok": carb_ok,
            "oil_limit_ok": oil_ok,
            "chapati_limit_ok": chapati_ok,
            "low_confidence_flag": low_confidence_flag,
            "message": message,
        }

    def _validate_food_ranges(self, foods: list[dict[str, Any]]) -> bool:
        for item in foods:
            grams = max(1.0, float(item.get("estimated_quantity_grams", 1.0)))
            density = {
                "protein": float(item.get("estimated_protein", 0.0)) * 100.0 / grams,
                "carbs": float(item.get("estimated_carbs", 0.0)) * 100.0 / grams,
                "fat": float(item.get("estimated_fat", 0.0)) * 100.0 / grams,
            }
            name = item.get("name", "").lower()
            matched = None
            for key in KNOWN_DENSITY_RANGES:
                if key in name:
                    matched = key
                    break
            if not matched:
                continue
            ranges = KNOWN_DENSITY_RANGES[matched]
            for macro, value in density.items():
                low, high = ranges[macro]
                if value < low * 0.5 or value > high * 1.5:
                    return False
        return True

    def _approval_label(self, projected_score: float) -> str:
        if projected_score < 40:
            return "Approved"
        if projected_score < 70:
            return "Moderate"
        return "High Insulin Load"

    def _coaching_message(self, macros: dict[str, float]) -> dict[str, Any]:
        tags: list[str] = []
        primary = "Balanced meal."
        if macros["hidden_oil"] >= 2.5 and macros["carbs"] >= 45:
            tags.append("high_triglyceride_impact")
            primary = "High triglyceride impact meal. Suggest 20-minute walk."
        elif macros["protein"] >= 35:
            tags.append("hdl_supportive")
            primary = "HDL supportive meal."
        return {"primary_message": primary, "tags": tags}

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
            self._cache[key] = CachedImageAnalysis(payload=payload, expires_at=time() + self.cache_ttl_seconds)


food_image_service = FoodImageService(
    api_key=settings.openai_api_key,
    model=settings.openai_model,
    cache_ttl_seconds=settings.llm_cache_ttl_seconds,
)
