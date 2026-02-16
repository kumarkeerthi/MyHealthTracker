from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ExerciseCategory, ExerciseEntry, MetabolicRecommendationLog, User, VitalsEntry
from app.services.llm_service import llm_service
from app.services.rule_engine import get_or_create_metabolic_profile
from app.services.strength_engine import compute_strength_score


class MetabolicAdvisorService:
    def run_weekly_recommendations(
        self,
        db: Session,
        user_id: int,
        week_end: date | None = None,
    ) -> MetabolicRecommendationLog | None:
        user = db.get(User, user_id)
        if not user:
            return None

        reference_end = week_end or datetime.utcnow().date()
        reference_start = reference_end - timedelta(days=6)
        previous_start = reference_start - timedelta(days=7)
        previous_end = reference_start - timedelta(days=1)

        profile = get_or_create_metabolic_profile(db, user)

        recent_waist = self._average_waist(db, user_id, reference_start, reference_end)
        prior_waist = self._average_waist(db, user_id, previous_start, previous_end)
        waist_not_dropping = bool(recent_waist is not None and prior_waist is not None and recent_waist >= prior_waist)

        strength_increasing, strength_delta = self._strength_increasing(
            db,
            user_id,
            reference_start,
            reference_end,
            previous_start,
            previous_end,
        )

        carb_before = profile.carb_ceiling
        protein_before = profile.protein_target_min
        carb_after = carb_before
        protein_after = protein_before

        recommendations: list[str] = ["Analyze patterns: completed weekly trend check."]

        if waist_not_dropping:
            carb_after = max(20, carb_before - 10)
            profile.carb_ceiling = carb_after
            user.carb_ceiling = carb_after
            recommendations.append(f"Waist not dropping: reduce carb ceiling by 10g to {carb_after}g.")
        else:
            recommendations.append(f"Carb ceiling adjustment: no change ({carb_after}g).")

        protein_after = protein_before + 5
        profile.protein_target_min = protein_after
        profile.protein_target_max = max(profile.protein_target_max, protein_after + 15)
        recommendations.append(f"Suggest protein increase: raise minimum daily protein to {protein_after}g.")

        recommend_strength_volume_increase = not strength_increasing
        if recommend_strength_volume_increase:
            recommendations.append("Suggest strength volume increase: add 1 extra strength set per major movement.")
        else:
            recommendations.append("Strength trend increasing: maintain current strength volume.")

        allow_refeed_meal = False
        if strength_increasing:
            allow_refeed_meal = True
            recommendations.append("Strength increasing: allow 1 refeed meal weekly.")

        report = self._build_report(
            user_id=user_id,
            week_start=reference_start,
            week_end=reference_end,
            waist_not_dropping=waist_not_dropping,
            strength_increasing=strength_increasing,
            strength_delta=strength_delta,
            carb_before=carb_before,
            carb_after=carb_after,
            protein_before=protein_before,
            protein_after=protein_after,
            allow_refeed_meal=allow_refeed_meal,
            recommendations=recommendations,
        )

        log = MetabolicRecommendationLog(
            user_id=user_id,
            week_start=reference_start,
            week_end=reference_end,
            waist_not_dropping=waist_not_dropping,
            strength_increasing=strength_increasing,
            carb_ceiling_before=carb_before,
            carb_ceiling_after=carb_after,
            protein_target_min_before=protein_before,
            protein_target_min_after=protein_after,
            recommend_strength_volume_increase=recommend_strength_volume_increase,
            allow_refeed_meal=allow_refeed_meal,
            recommendations="\n".join(recommendations),
            advisor_report=report,
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    def get_latest_report(self, db: Session, user_id: int) -> MetabolicRecommendationLog | None:
        return db.scalar(
            select(MetabolicRecommendationLog)
            .where(MetabolicRecommendationLog.user_id == user_id)
            .order_by(MetabolicRecommendationLog.created_at.desc())
            .limit(1)
        )

    @staticmethod
    def _average_waist(db: Session, user_id: int, start_day: date, end_day: date) -> float | None:
        rows = db.scalars(
            select(VitalsEntry.waist_cm).where(
                VitalsEntry.user_id == user_id,
                VitalsEntry.recorded_at >= datetime.combine(start_day, datetime.min.time()),
                VitalsEntry.recorded_at <= datetime.combine(end_day, datetime.max.time()),
                VitalsEntry.waist_cm.is_not(None),
            )
        ).all()
        if not rows:
            return None
        return round(sum(float(v) for v in rows) / len(rows), 2)

    @staticmethod
    def _strength_increasing(
        db: Session,
        user_id: int,
        recent_start: date,
        recent_end: date,
        previous_start: date,
        previous_end: date,
    ) -> tuple[bool, float]:
        strength_categories = [ExerciseCategory.STRENGTH, ExerciseCategory.BODYWEIGHT, ExerciseCategory.MONKEY_BAR]
        entries = db.scalars(
            select(ExerciseEntry).where(
                ExerciseEntry.user_id == user_id,
                ExerciseEntry.exercise_category.in_(strength_categories),
                ExerciseEntry.performed_at >= datetime.combine(previous_start, datetime.min.time()),
                ExerciseEntry.performed_at <= datetime.combine(recent_end, datetime.max.time()),
            )
        ).all()

        recent_entries = [
            entry
            for entry in entries
            if recent_start <= entry.performed_at.date() <= recent_end
        ]
        previous_entries = [
            entry
            for entry in entries
            if previous_start <= entry.performed_at.date() <= previous_end
        ]

        recent_score = float(compute_strength_score(recent_entries)["strength_index"])
        previous_score = float(compute_strength_score(previous_entries)["strength_index"])
        delta = round(recent_score - previous_score, 2)
        return delta > 0, delta

    @staticmethod
    def _build_report(
        *,
        user_id: int,
        week_start: date,
        week_end: date,
        waist_not_dropping: bool,
        strength_increasing: bool,
        strength_delta: float,
        carb_before: int,
        carb_after: int,
        protein_before: int,
        protein_after: int,
        allow_refeed_meal: bool,
        recommendations: list[str],
    ) -> str:
        llm_report = llm_service.summarize_metabolic_advisor_report(
            user_id=user_id,
            week_start=week_start,
            week_end=week_end,
            waist_not_dropping=waist_not_dropping,
            strength_increasing=strength_increasing,
            strength_delta=strength_delta,
            carb_before=carb_before,
            carb_after=carb_after,
            protein_before=protein_before,
            protein_after=protein_after,
            allow_refeed_meal=allow_refeed_meal,
            recommendations=recommendations,
        )
        if llm_report:
            return llm_report

        waist_line = "Waist trend not dropping; carb tightening applied." if waist_not_dropping else "Waist trend improving or stable."
        strength_line = (
            f"Strength increased by {strength_delta} points; one weekly refeed meal allowed."
            if strength_increasing
            else f"Strength not increasing (delta {strength_delta}); focus on extra strength volume."
        )

        return (
            f"Metabolic Advisor Report ({week_start} to {week_end})\n"
            f"- User: {user_id}\n"
            f"- {waist_line}\n"
            f"- {strength_line}\n"
            f"- Carb ceiling: {carb_before}g -> {carb_after}g\n"
            f"- Protein minimum: {protein_before}g -> {protein_after}g\n"
            f"- Recommendations:\n  - " + "\n  - ".join(recommendations)
        )


metabolic_advisor_service = MetabolicAdvisorService()
