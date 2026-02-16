from __future__ import annotations

from collections import Counter
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import HabitChallengeType, HabitCheckin, HabitDefinition


WEEKDAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


class HabitIntelligenceEngine:
    def _longest_streak(self, outcomes: list[bool]) -> int:
        longest = 0
        current = 0
        for outcome in outcomes:
            if outcome:
                current += 1
                longest = max(longest, current)
            else:
                current = 0
        return longest

    def _current_streak(self, outcomes: list[bool]) -> int:
        current = 0
        for outcome in reversed(outcomes):
            if outcome:
                current += 1
            else:
                break
        return current

    def _next_challenge_type(self, failures: int, current_type: HabitChallengeType) -> HabitChallengeType:
        if failures < 3:
            return current_type

        if current_type == HabitChallengeType.STRICT:
            return HabitChallengeType.MICRO
        if current_type == HabitChallengeType.MICRO:
            return HabitChallengeType.SUPPORT
        return HabitChallengeType.SUPPORT

    def summarize(self, db: Session, user_id: int, days: int = 90) -> dict:
        end_date = date.today()
        start_date = end_date - timedelta(days=max(days - 1, 0))

        habits = db.scalars(select(HabitDefinition).where(HabitDefinition.active.is_(True)).order_by(HabitDefinition.id.asc())).all()
        if not habits:
            return {
                "habits": [],
                "heatmap": [],
                "insights": [],
                "overall_success_rate": 0,
            }

        checkins = db.scalars(
            select(HabitCheckin)
            .where(
                HabitCheckin.user_id == user_id,
                HabitCheckin.habit_date >= start_date,
                HabitCheckin.habit_date <= end_date,
            )
            .order_by(HabitCheckin.habit_date.asc())
        ).all()

        grouped: dict[int, list[HabitCheckin]] = {habit.id: [] for habit in habits}
        for checkin in checkins:
            if checkin.habit_id in grouped:
                grouped[checkin.habit_id].append(checkin)

        day_scores: dict[date, list[int]] = {}
        for checkin in checkins:
            day_scores.setdefault(checkin.habit_date, []).append(1 if checkin.success else 0)

        heatmap = []
        cursor = start_date
        while cursor <= end_date:
            values = day_scores.get(cursor, [])
            ratio = sum(values) / len(values) if values else 0
            heatmap.append({"date": cursor, "intensity": ratio, "count": len(values)})
            cursor += timedelta(days=1)

        failures_by_weekday = Counter()
        overall_successes = 0
        overall_total = 0
        habits_payload = []

        for habit in habits:
            rows = grouped.get(habit.id, [])
            outcomes = [row.success for row in rows]
            total = len(outcomes)
            success_count = sum(1 for x in outcomes if x)
            failure_count = total - success_count
            success_rate = (success_count / total) if total else 0
            current_streak = self._current_streak(outcomes)
            longest_streak = self._longest_streak(outcomes)
            reasons = Counter(row.failure_reason for row in rows if not row.success and row.failure_reason)

            for row in rows:
                if not row.success:
                    failures_by_weekday[WEEKDAY_NAMES[row.habit_date.weekday()]] += 1

            recommended_challenge_type = self._next_challenge_type(failure_count, habit.challenge_type)
            habits_payload.append(
                {
                    "habit_id": habit.id,
                    "code": habit.code,
                    "name": habit.name,
                    "description": habit.description,
                    "challenge_type": habit.challenge_type.value,
                    "recommended_challenge_type": recommended_challenge_type.value,
                    "current_streak": current_streak,
                    "longest_streak": longest_streak,
                    "success_rate": round(success_rate, 3),
                    "failures": failure_count,
                    "failure_patterns": [
                        {"reason": reason, "count": count} for reason, count in reasons.most_common(3)
                    ],
                }
            )
            overall_successes += success_count
            overall_total += total

        insights: list[str] = []
        if failures_by_weekday:
            top_day, _ = failures_by_weekday.most_common(1)[0]
            insights.append(f"Carb spike tends to occur on {top_day}s.")

        adaptive_habits = [
            habit["name"]
            for habit in habits_payload
            if habit["challenge_type"] != habit["recommended_challenge_type"]
        ]
        if adaptive_habits:
            insights.append(
                "Repeated misses detected. Challenge intensity adjusted for: " + ", ".join(adaptive_habits) + "."
            )

        return {
            "habits": habits_payload,
            "heatmap": heatmap,
            "insights": insights,
            "overall_success_rate": round((overall_successes / overall_total) if overall_total else 0, 3),
        }


habit_intelligence_engine = HabitIntelligenceEngine()
